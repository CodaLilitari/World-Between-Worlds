"""Local conversion orchestration and explicitly requested installation checks."""
import hashlib
import json
import os
import re
from pathlib import Path
import tempfile
import threading
import uuid
import sys

import bridge
import custom_registry
import verify_retail
import blackwing_revisions
import blackwing_picker
from gob import Gob
from blackwing_catalog import canonical, recipe_details, selection, source_hashes, require_consistent_sources
from blackwing_version import VERSION

MAX_ARCHIVES = 5000
MAX_ARCHIVE_BYTES = 500_000_000
PATH_KEYS = ('jk_root', 'mots_root', 'archive_dir', 'output_dir')


def digest(path):
    hasher = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(block)
    return hasher.hexdigest()


def user_data_dir():
    override = os.environ.get('BLACKWING_USER_DATA_DIR')
    if override:
        return Path(override).expanduser().resolve()
    if os.name == 'nt':
        return Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData/Local'))) / 'World Between Worlds'
    return Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'world-between-worlds'


def normalize_settings(value):
    if not isinstance(value, dict):
        raise ValueError('Settings must be an object.')
    result = {}
    for key in PATH_KEYS:
        item = value.get(key, '')
        if not isinstance(item, str) or len(item) > 4096 or '\x00' in item:
            raise ValueError('Invalid path for ' + key)
        result[key] = item.strip()
    if not result['output_dir']:
        result['output_dir'] = str(Path.home() / 'Documents' / 'World Between Worlds conversions')
    return result


def load_settings(directory=None):
    path = (directory or user_data_dir()) / 'settings.json'
    try:
        return normalize_settings(json.loads(path.read_text(encoding='utf-8')))
    except (OSError, ValueError, TypeError):
        return normalize_settings({})


def save_settings(value, directory=None):
    value = normalize_settings(value)
    directory = directory or user_data_dir()
    directory.mkdir(parents=True, exist_ok=True)
    # This file contains paths only; archives, generated assets and credentials
    # never enter the application source tree or settings store.
    path = directory / 'settings.json'
    temporary = directory / ('settings-' + uuid.uuid4().hex + '.tmp')
    with temporary.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
    os.replace(temporary, path)
    return value


def path_value(value, label, *, existing=False):
    if not isinstance(value, str) or not value.strip() or len(value) > 4096 or '\x00' in value:
        raise ValueError('Choose ' + label + '.')
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError(label + ' must be an absolute path.')
    path = path.resolve(strict=existing)
    if existing and not path.is_dir():
        raise ValueError(label + ' must be a folder.')
    return path


def overlaps(first, second):
    return first == second or first.is_relative_to(second) or second.is_relative_to(first)


def validate_request(value):
    if not isinstance(value, dict):
        raise ValueError('Conversion request must be an object.')
    rows = selection(value.get('ids'))
    settings = normalize_settings(value)
    paths = {key: path_value(settings[key], key.replace('_', ' '), existing=key != 'output_dir')
             for key in ('jk_root', 'mots_root', 'output_dir')}
    archive_dir = value.get('archive_dir', '')
    if archive_dir:
        paths['archive_dir'] = path_value(archive_dir, 'original archive folder', existing=True)
    protected = [paths['jk_root'], paths['mots_root'], Path(__file__).resolve().parent, user_data_dir().resolve()]
    if getattr(sys, 'frozen', False):
        protected.append(Path(sys.executable).resolve().parent)
    if 'archive_dir' in paths:
        protected.append(paths['archive_dir'])
    if any(overlaps(paths['output_dir'], item) for item in protected):
        raise ValueError('Choose a separate output folder outside the application, game installations, original archives and app settings.')
    overrides = value.get('archives', {})
    if not isinstance(overrides, dict) or any(key not in {row['id'] for row in rows} for key in overrides):
        raise ValueError('Archive overrides must belong to the selected recipes.')
    for key, item in overrides.items():
        if not isinstance(item, str) or len(item) > 4096 or '\x00' in item:
            raise ValueError('Invalid original archive path for ' + key)
        if item:
            path = Path(item).expanduser()
            if not path.is_absolute() or not path.is_file():
                raise ValueError('Choose an existing original archive for ' + key)
            if path.resolve().is_relative_to(paths['output_dir']):
                raise ValueError('Original archives must be outside the output folder.')
    return rows, paths, overrides


def original_hashes(key):
    import recipe_adapters
    adapter = recipe_adapters.for_recipe(key)
    if adapter:
        return set(adapter.original_hashes(key))
    if key in custom_registry.entries():
        spec = custom_registry.entries()[key]
        return {spec['gob_sha256'], spec['zip_sha256']}
    if key == 'dojo':
        return {bridge.DOJO_GOB_SHA256, bridge.DOJO_ZIP_SHA256}
    if key == 'caesars':
        return {bridge.CAESARS_GOB_SHA256, bridge.CAESARS_ZIP_SHA256}
    if key == 'ninja-kage':
        import ninja_converter
        return set(ninja_converter.original_hashes())
    if key not in bridge.STOCK_MAPS:
        raise ValueError('Unknown recipe: ' + key)
    return set()


def find_originals(rows, paths, overrides, log):
    found = {}
    wanted = {}
    for row in rows:
        key = row['id']
        if not row['requires_archive']:
            continue
        hashes = original_hashes(key)
        if overrides.get(key):
            path = Path(overrides[key]).expanduser().resolve(strict=True)
            if path.stat().st_size > MAX_ARCHIVE_BYTES or digest(path) not in hashes:
                raise ValueError('Original archive does not match the reviewed version of ' + row['title'])
            found[key] = path
        else:
            for value in hashes:
                wanted[value] = key
    if wanted:
        if 'archive_dir' not in paths:
            raise ValueError('Choose the original archive folder or an exact archive for each selected custom map/mod.')
        log('Matching selected recipes against original archives in the chosen folder…')
        seen = 0
        root = paths['archive_dir']
        for directory, folders, files in os.walk(root, followlinks=False):
            relative = Path(directory).relative_to(root)
            folders[:] = sorted(folder for folder in folders if not (Path(directory) / folder).is_symlink()) if len(relative.parts) < 5 else []
            for name in sorted(files):
                path = Path(directory) / name
                if path.suffix.lower() not in {'.zip', '.gob'} or path.is_symlink():
                    continue
                seen += 1
                if seen > MAX_ARCHIVES:
                    raise ValueError('Archive folder is too large; choose a narrower folder or exact archive paths.')
                if path.stat().st_size > MAX_ARCHIVE_BYTES:
                    continue
                key = wanted.get(digest(path))
                if key is not None:
                    found.setdefault(key, path.resolve())
            if all(key in found for key in wanted.values()):
                break
        missing = sorted(set(wanted.values()) - found.keys())
        if missing:
            raise ValueError('Reviewed original archive not found for: ' + ', '.join(missing) + '. Use the catalog source link and the exact reviewed version.')
    return found


def tree_hashes(directory):
    return {path.relative_to(directory).as_posix(): digest(path)
            for path in sorted(directory.rglob('*')) if path.is_file()}


def scan_installed(value):
    """Read only the chosen MotS installation; never convert or install a result."""
    if not isinstance(value, dict):
        raise ValueError('Scan request must be an object.')
    require_consistent_sources()
    selected = value.get('mots_root')
    if not isinstance(selected, str) or not selected.strip() or len(selected) > 4096 or '\x00' in selected:
        raise ValueError('Choose the MotS installation to scan.')
    # Keep the selected spelling until the scanner checks every path component;
    # resolving here would hide a user path that traverses a junction or link.
    root = Path(selected.strip()).expanduser()
    from blackwing_catalog import recipes
    result = blackwing_revisions.scan_installation(root, recipes())
    require_consistent_sources()
    return {**result, 'version': VERSION,
            'comparison': 'Recipe revisions in this installed WBW catalog'}


def pick_local_path(value, directory=None):
    """Return one path from an explicitly invoked desktop chooser."""
    if not isinstance(value, dict) or value.get('kind') not in blackwing_picker.KINDS:
        raise ValueError('Choose a supported folder or original archive.')
    kind = value['kind']
    settings = load_settings(directory)
    if kind == 'original_archive':
        rows = selection([value.get('recipe_id')])
        if not rows[0]['requires_archive']:
            raise ValueError('This stock level reads your game installation; it needs no downloaded archive.')
        initial = settings['archive_dir'] or None
    else:
        initial = settings[kind] or None
    try:
        return {'path': blackwing_picker.pick_path(kind, initial_path=initial)}
    except blackwing_picker.PickerError as exc:
        raise ValueError(str(exc)) from exc


def track_outputs(row, stage, result, lock):
    """Wrap independently verified payloads with inert revision metadata."""
    stage = Path(stage).resolve()
    original_primary = result['filename']
    artifacts = []
    for path in sorted(stage.rglob('*.goo')):
        relative = path.relative_to(stage).as_posix()
        renamed = blackwing_revisions.versioned_name(relative, row['revision'])
        target = stage / renamed
        if not target.resolve().is_relative_to(stage) or target.exists():
            raise ValueError('Tracked output name collides or leaves staging folder.')
        payload = path.read_bytes()
        stamped, metadata = blackwing_revisions.stamp_archive(
            payload, row['id'], row['revision'], tool_version=VERSION,
            role='primary' if relative == original_primary else 'startup',
            recipe_sha256=lock['recipe_sha256'])
        with target.open('xb') as stream:
            stream.write(stamped)
        if blackwing_revisions.validate_archive(target.read_bytes()) != metadata:
            raise ValueError('Post-write recipe tracking verification failed.')
        artifacts.append(dict(source_filename=relative, filename=renamed,
                              payload_sha256=hashlib.sha256(payload).hexdigest(),
                              sha256=digest(target), metadata=metadata))
        path.unlink()  # Only this conversion's newly created staging file.
        if relative == original_primary:
            result = {**result, 'filename': renamed}
    if not artifacts or result['filename'] == original_primary:
        raise ValueError('Conversion produced no primary GOO to track.')
    # Keep the original payload manifests unchanged. The new outer manifest
    # binds them to the final archives and explains the verification boundary.
    original_manifest = result['manifest_filename']
    final_manifest = Path(result['filename']).with_suffix('.manifest.json').as_posix()
    manifest = dict(schema='blackwing.tracked-conversion.v1', recipe_id=row['id'],
                    recipe_revision=row['revision'], version=VERSION,
                    payload_manifest=original_manifest, archives=artifacts,
                    verification=result['verification'],
                    verification_scope='Game payload was independently verified before inert WBW metadata was added; embedded revision and payload checksum were then verified.',
                    output=Gob((stage / result['filename']).read_bytes(), label=result['filename']).inventory())
    (stage / final_manifest).write_bytes(canonical(manifest) + b'\n')
    # Generated installation notes must name the exported files and episodes.
    from blackwing_catalog import recipes
    episode_names = [(Path(old).stem, Path(item['output_filename']).stem)
                     for item in recipes() for old in item['legacy_filenames']]
    for path in sorted(stage.rglob('README.txt')):
        if path.is_file():
            before = path.read_text(encoding='utf-8')
            after = before
            for artifact in artifacts:
                after = after.replace(Path(artifact['source_filename']).name,
                                      Path(artifact['filename']).name)
                after = after.replace(artifact['payload_sha256'], artifact['sha256'])
            for old, new in episode_names:
                after = re.sub(r'(-episode\s+)' + re.escape(old) + r'(?=\s|$)',
                               lambda match: match[1] + new, after)
            after = after.replace('Its only internal member must be misc/items.dat.',
                                  'Its game payload is misc/items.dat; wbw/recipe.json records the conversion revision.')
            after = after.replace('The manifest records all input\nand member hashes.',
                                  'The original payload manifest records input and game-member hashes.\nThe tracked conversion manifest records final archive hashes.')
            after += ('\nWBW recipe tracking: these GOOs also contain inert wbw/recipe.json metadata.\n'
                      'Original payload manifests are preserved; the tracked conversion manifest and receipt bind the final archives.\n')
            if after != before:
                path.write_text(after, encoding='utf-8')
    return {**result, 'manifest_filename': final_manifest,
            'recipe_revision': row['revision'], 'revision_label': row['revision_label'],
            'tracked_archives': artifacts}


def build_one(row, archives, original_path, stage):
    key = row['id']
    import recipe_adapters
    adapter = recipe_adapters.for_recipe(key)
    if adapter:
        return adapter.build_to_directory(archives, original_path, stage, key)
    kwargs = {}
    if key in bridge.STOCK_MAPS:
        kwargs['stock_map'] = key
        filename = bridge.stock_output_name(key)
    elif key == 'dojo':
        kwargs['dojo'] = bridge.open_dojo(original_path)
        filename = 'bridge-dojo-v1.goo'
    elif key == 'caesars':
        kwargs['caesars'] = bridge.open_caesars(original_path)
        filename = 'bridge-caesars-v3.goo'
    elif key in custom_registry.entries():
        kwargs.update(community=custom_registry.open_original(original_path, key), community_key=key)
        filename = custom_registry.output_name(key)
    elif key == 'ninja-kage':
        import ninja_converter
        return ninja_converter.build_to_directory(archives, original_path, stage)
    else:
        raise ValueError('Unknown recipe: ' + key)
    data, manifest = bridge.recipe(archives, **kwargs)
    target = stage / filename
    bridge.write_candidate(target, data, manifest)
    if key.startswith('ctf-'):
        bridge.write_ctf_startup(stage / bridge.CTF_STARTUP_FOLDER, *bridge.ctf_startup_candidate(archives))
    verification_kwargs = dict(kwargs)
    if 'community_key' in kwargs:
        spec = custom_registry.entries()[key]
        verification_kwargs['community_startup'] = stage / ('bridge-' + spec['tag'] + '-startup')
    verified = verify_retail.check(archives, Gob.open(target), **verification_kwargs)
    if key.startswith('ctf-'):
        verified['ctf_startup'] = verify_retail.check_ctf_startup(archives, stage / bridge.CTF_STARTUP_FOLDER)
    return dict(filename=filename, manifest_filename=target.with_suffix('.manifest.json').name,
                verification=verified, startup_overlay=row.get('startup_overlay'))


def convert_selected(value, progress=None):
    """Run exactly the explicit selection, staging each independently verified result."""
    progress = progress or (lambda **fields: None)
    require_consistent_sources()
    rows, paths, overrides = validate_request(value)
    log = lambda message: progress(log=message)
    originals = find_originals(rows, paths, overrides, log)
    source_before = source_hashes()
    log('Verifying owned JK and MotS archives…')
    specs = custom_registry.entries()
    archives = bridge.pinned_archives(jk_root=paths['jk_root'], mots_root=paths['mots_root'],
        include_jksp=any(bridge.STOCK_MAPS.get(row['id'], {}).get('requires_jksp') or specs.get(row['id'], {}).get('requires_jksp') or 'jksp' in row.get('required_owned_archives', []) for row in rows),
        include_jkctf=any(row['id'].startswith('ctf-') for row in rows),
        include_motssp=any('motssp' in row.get('required_owned_archives', []) for row in rows))
    paths['output_dir'].mkdir(parents=True, exist_ok=True)
    results = []
    for index, row in enumerate(rows):
        key = row['id']
        progress(current=row['title'], progress=index)
        log('Converting and independently verifying ' + row['title'] + '…')
        try:
            lock = recipe_details(key)
            original_hash = digest(originals[key]) if key in originals else None
            with tempfile.TemporaryDirectory(prefix='.blackwing-stage-', dir=paths['output_dir']) as directory:
                stage = Path(directory)
                result = build_one(row, archives, originals.get(key), stage)
                if source_hashes() != source_before:
                    raise ValueError('Converter source changed during this run; restart with a consistent release.')
                if key in originals and digest(originals[key]) != original_hash:
                    raise ValueError('Original archive changed during conversion; restore the reviewed download and try again.')
                result = track_outputs(row, stage, result, lock)
                if source_hashes() != source_before:
                    raise ValueError('Converter source changed during tracking; restart with a consistent release.')
                output_hash = digest(stage / result['filename'])
                receipt = dict(schema='blackwing.conversion-receipt.v1', version=VERSION,
                               selected_recipe=lock, recipe_revision=row['revision'],
                               tracked_archives=result['tracked_archives'],
                               original_archive_sha256=original_hash,
                               owned_archive_sha256={name: archive.sha256 for name, archive in archives.items()},
                               generated_files=tree_hashes(stage), verification=result['verification'],
                               runtime_test={'status': 'not-run-on-this-output',
                                             'note': 'Structural verification does not launch OpenJKDF2.'})
                (stage / 'blackwing-receipt.json').write_bytes(canonical(receipt) + b'\n')
                (stage / 'blackwing-recipe.json').write_bytes(canonical(lock) + b'\n')
                final = paths['output_dir'] / (key + '-' + output_hash[:12] + '-' + lock['recipe_sha256'][:8])
                if final.exists():
                    if not final.is_dir() or tree_hashes(final) != tree_hashes(stage):
                        raise ValueError('Existing result folder differs; choose a fresh output folder.')
                    reused = True
                else:
                    os.rename(stage, final)
                    reused = False
                result = dict(id=key, title=row['title'], status='verified', reused=reused,
                              recipe_revision=row['revision'], revision_label=row['revision_label'],
                              output=str(final / result['filename']),
                              manifest=str(final / result['manifest_filename']),
                              receipt=str(final / 'blackwing-receipt.json'),
                              recipe=str(final / 'blackwing-recipe.json'),
                              sha256=output_hash, verification=result['verification'],
                              startup_overlay=str(final / result['startup_overlay']) if result.get('startup_overlay') else None,
                              runtime_test=receipt['runtime_test'])
                results.append(result)
                progress(result=result, progress=index + 1)
                log(row['title'] + ': structure verified; conversion receipt saved.')
        except Exception as exc:
            result = dict(id=key, title=row['title'], status='failed', error=str(exc))
            results.append(result)
            progress(result=result, progress=index + 1)
            log(row['title'] + ': ' + str(exc))
    return results


class JobManager:
    def __init__(self):
        self.jobs = {}
        self.lock = threading.Lock()

    def start(self, value):
        rows, _, _ = validate_request(value)
        with self.lock:
            if any(job['status'] in {'queued', 'running'} for job in self.jobs.values()):
                raise ValueError('A conversion is already running. Wait for it to finish.')
            job_id = uuid.uuid4().hex
            self.jobs[job_id] = dict(id=job_id, status='queued', total=len(rows), progress=0,
                                     current='', results=[], logs=[])
        threading.Thread(target=self._run, args=(job_id, value), daemon=True).start()
        return job_id

    def snapshot(self, job_id):
        with self.lock:
            if job_id not in self.jobs:
                raise KeyError('Unknown job')
            return json.loads(json.dumps(self.jobs[job_id]))

    def _run(self, job_id, value):
        def update(**fields):
            with self.lock:
                job = self.jobs[job_id]
                if 'log' in fields:
                    job['logs'].append(fields.pop('log'))
                if 'result' in fields:
                    job['results'].append(fields.pop('result'))
                job.update(fields)
        update(status='running')
        try:
            results = convert_selected(value, update)
            update(status='completed' if results and all(row['status'] == 'verified' for row in results) else 'failed', current='')
        except Exception as exc:
            update(status='failed', current='', error=str(exc), log=str(exc))

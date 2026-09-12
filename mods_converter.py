"""Exact, optional MotS mod recipes; source assets are always supplied locally.

Only individually catalogued material-only recipes are accepted by this first
family. It does not apply Ninja Kage's weapon, inventory or Force translations.
"""
import copy
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

from gob import ArchiveError, Gob, build_gob
import mods_catalog as catalog


class ModError(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ModError(message)


def recipe_details(recipe_id):
    require(recipe_id in catalog.SPECS, 'Unknown reviewed mod recipe')
    return {**copy.deepcopy(catalog.SPECS[recipe_id]),
            'native_sources': dict(catalog.NATIVE_HASHES),
            'native_sabers_sha256': catalog.NATIVE_SABERS_SHA256}


def original_hashes(recipe_id):
    return {recipe_details(recipe_id)['zip_sha256']}


def catalog_entries():
    return [{'id': key, 'title': spec['title'], 'author': spec['author'],
             'kind': 'mod', 'gameplay': ['mp'], 'requires_archive': True,
             'archive_hint': spec['archive_hint'], 'source_url': spec['source_url'],
             'download_url': spec['download_url'], 'status': 'prototype',
             'startup_overlay': spec['startup_overlay'], 'legacy_filenames': [spec['filename']],
             'output_filename': spec['filename'], 'runtime_test': copy.deepcopy(spec['runtime_test']),
             'summary': 'Optional native saber-material override; exact source bytes and paths preserved. Runtime checks are reported separately.'}
            for key, spec in catalog.SPECS.items()]


def read_original(path, spec):
    path = Path(path)
    require(path.stat().st_size == spec['zip_bytes'], 'Select the exact original ZIP from Massassi')
    with path.open('rb') as handle:
        data = handle.read(16 * 1024**2 + 1)
    require(len(data) <= 16 * 1024**2 and digest(data) == spec['zip_sha256'],
            'Original mod ZIP differs from the reviewed source')
    members = {}
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            expected = {item['path']: item for item in spec['zip_members']}
            files = [item for item in archive.infolist() if not item.is_dir()]
            require(len(files) == len(expected) and {item.filename for item in files} == set(expected),
                    'Original ZIP member set differs')
            for item in files:
                require(item.file_size == expected[item.filename]['bytes'] and item.file_size <= 32 * 1024**2,
                        'Original ZIP member exceeds reviewed size')
                payload = archive.read(item)
                require(digest(payload) == expected[item.filename]['sha256'], 'Original member hash differs: ' + item.filename)
                members[item.filename] = payload
    except (zipfile.BadZipFile, RuntimeError) as exc:
        raise ModError('Cannot read the pinned original ZIP') from exc
    source = Gob(members[spec['gob_member']], spec['gob_member'])
    require(source.sha256 == spec['gob_sha256'], 'Original GOB hash differs')
    expected = {item['path']: (item['bytes'], item['sha256']) for item in spec['resources']}
    actual = {name: (entry.size, digest(source.read(name))) for name, entry in source.entries.items()}
    require(actual == expected, 'Original GOB resource set differs from reviewed recipe')
    require(set(source.entries) - set(spec['native_overrides']) <= {'patchinfo.txt'},
            'Material-only recipe may not silently accept gameplay or unrelated resources')
    return source, members


def native_contract(archives, spec):
    for key, expected in catalog.NATIVE_HASHES.items():
        require(key in archives and archives[key].sha256 == expected, 'Owned source archive differs: ' + key)
    native = archives['motsres']
    sabers = native.read('misc/sabers.dat')
    require(digest(sabers) == catalog.NATIVE_SABERS_SHA256, 'Native saber registration differs')
    for path, expected in spec['native_overrides'].items():
        require(path.startswith('mat/') and path.endswith('.mat'), 'Only declared native material overrides are allowed')
        require(path in native.entries and digest(native.read(path)) == expected, 'Native target material differs: ' + path)
        require(re.search(rb'(?i)(?<![\w.])' + re.escape(path[4:].encode('ascii')) + rb'(?![\w.])', sabers) is not None,
                'Native saber registration does not reference target material: ' + path)


def verify(archives, source, payload, spec):
    native_contract(archives, spec)
    require(source.sha256 == spec['gob_sha256'], 'Verifier original GOB differs from reviewed source')
    output = Gob(payload, spec['filename'])
    require(set(output.entries) == set(source.entries), 'Output member set changed')
    for path in source.entries:
        require(output.read(path) == source.read(path), 'Authored material or metadata bytes changed: ' + path)
    require(not any(path.startswith(('cog/', 'jkl/', 'misc/')) for path in output.entries),
            'Material-only output unexpectedly replaces native gameplay data')
    return {'status': 'structural-pass', 'gameplay': 'not-run', 'sha256': digest(payload),
            'resources': len(output.entries), 'native_material_overrides': sorted(spec['native_overrides']),
            'checks': ['Exact source ZIP, every member and original GOB hashes matched.',
                       'Every output entry retains the exact original full virtual path and payload.',
                       'Every material target exists in the pinned native archive and saber registration.',
                       'No weapon, Force, player, inventory, model-list or static-world resources emitted.'],
            'limits': ['Visual appearance, animation, colors and remote-player rendering need engine testing.',
                       'Separate optional startup mod; do not combine competing saber-material mods.',
                       'No gameplay, multiplayer checksum or retail rendering parity is certified.']}


def build_to_directory(archives, original_path, stage, recipe_id):
    spec = recipe_details(recipe_id)
    require(spec['mode'] == 'exact-material-repack-v1', 'Unsupported mod conversion family')
    stage = Path(stage).resolve()
    project = Path(__file__).resolve().parent
    require(stage != project and project not in stage.parents, 'Generated mod assets must remain outside the source repository')
    source, originals = read_original(original_path, spec)
    native_contract(archives, spec)
    resources = {path: source.read(path) for path in source.entries}
    payload = build_gob(resources)
    verification = verify(archives, source, payload, spec)
    manifest = {'schema': 1, 'recipe_id': recipe_id, 'recipe': spec['mode'], 'revision': spec['revision'],
                'title': spec['title'], 'author': spec['author'], 'source_url': spec['source_url'],
                'original_zip_sha256': spec['zip_sha256'], 'original_gob_sha256': spec['gob_sha256'],
                'native_sources': dict(catalog.NATIVE_HASHES), 'native_sabers_sha256': catalog.NATIVE_SABERS_SHA256,
                'scope': 'explicit-isolated-startup-mod', 'output_sha256': digest(payload),
                'resources': [{'path': path, 'bytes': len(resources[path]), 'sha256': digest(resources[path]),
                               'operation': 'preserve-original-bytes-and-full-path',
                               'ownership': 'declared-native-material-override' if path in spec['native_overrides'] else 'original-patch-metadata',
                               'native_sha256': spec['native_overrides'].get(path)} for path in sorted(resources)],
                'verification': verification}
    folder = stage / spec['startup_overlay']
    require(not folder.exists(), 'Mod output already exists; choose a fresh output directory')
    folder.mkdir(parents=True)
    filename, manifest_path = folder / spec['filename'], folder / 'source.manifest.json'
    with filename.open('xb') as handle:
        handle.write(payload)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    for index, item in enumerate(spec['readmes'], 1):
        (folder / f'ORIGINAL-{index:02d}-{Path(item["path"]).name}').write_bytes(originals[item['path']])
    readme = (f"{spec['title']} - local MotS material conversion\n"
              f"Original mod: {spec['author']}. Original readme supplied unchanged beside this file.\n"
              "Converter: World Between Worlds / Andrei Pemberton with Coda Lilitari.\n"
              f"Original source: {spec['source_url']}\n\n"
              "This separately selectable mod intentionally overrides native saber material paths.\n"
              "No COG, weapon, Force, inventory or player logic is replaced. All original material bytes and paths are retained.\n"
              "Place this entire folder beside the game's resource/ and episode/ folders.\n"
              f"Launch OpenJKDF2 in MotS mode with: -motsCompat -path {spec['startup_overlay']}\n"
              f"Select {spec['selected_saber']} to inspect the authored materials.\n"
              "Use this startup mod alone; restart without its -path argument before using a different overlay.\n"
              "Keep all participants on the same tested mod/profile for multiplayer comparison.\n"
              "Conversion ran exact source/resource checks, not a game. Runtime visual and multiplayer verification are separate.\n")
    (folder / 'README.txt').write_text(readme, encoding='utf-8')
    require(filename.read_bytes() == payload, 'Post-write artifact verification failed')
    return {'filename': filename.relative_to(stage).as_posix(),
            'manifest_filename': manifest_path.relative_to(stage).as_posix(),
            'verification': verification, 'startup_overlay': spec['startup_overlay']}

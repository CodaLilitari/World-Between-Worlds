"""Hash-pinned, per-map startup adaptations built only from owned game assets."""
import hashlib
from pathlib import Path
import re

from custom_registry import apply_cog_edits
from gob import build_gob


def patch_native_templates(native_rows, source_rows, rules, resource_names):
    """Transfer only reviewed authored fields into the MotS weapon templates."""
    source = {row.split()[0].lower(): row for row in source_rows}
    result = list(native_rows)
    applied = []
    for name, rule in rules.items():
        positions = [i for i, row in enumerate(result) if row.split()[0].lower() == name]
        if len(positions) != 1 or not rule.get('reason'):
            raise ValueError('Unreviewed native template override: ' + name)
        original = source[rule.get('source_template', name)]
        for field in rule['fields']:
            pattern = r'(?<!\S)' + re.escape(field) + r'=([^\s]+)'
            matches = re.findall(pattern, original, re.I)
            if len(matches) != 1:
                raise ValueError('Expected one source template field: ' + name + '.' + field)
            value = resource_names.get(matches[0].lower(), matches[0])
            replacement = field + '=' + value
            index = positions[0]
            if len(re.findall(pattern, result[index], re.I)) > 1:
                raise ValueError('Duplicate native template field')
            if re.search(pattern, result[index], re.I):
                result[index] = re.sub(pattern, lambda _: replacement, result[index], flags=re.I)
            else:
                result[index] += ' ' + replacement
            applied.append({'template': name, 'field': field, 'value': value, 'reason': rule['reason']})
    return result, applied


def startup_files(spec, target, source, resources, name_map, rename_refs):
    """Native filenames must exist before static player/inventory initialization."""
    files = {}
    changes = []
    for name, rule in spec.get('native_cog_edits', {}).items():
        _, path, archive = target.get(name)
        original = archive.read(path)
        if hashlib.sha256(original).hexdigest() != rule['sha256']:
            raise ValueError('Unreviewed native COG hash: ' + name)
        value = original.decode('cp1252').replace('\r', '')
        files[path] = apply_cog_edits(value, rule['edits']).encode('cp1252')
        changes.append({'kind': 'native-cog', 'path': path, 'source_sha256': rule['sha256'], 'edits': rule['edits']})
    for requested_path, rule in spec.get('native_text_edits', {}).items():
        _, path, archive = target.get(Path(requested_path).name)
        original = archive.read(path)
        if path != requested_path or hashlib.sha256(original).hexdigest() != rule['sha256']:
            raise ValueError('Unreviewed native text asset: ' + requested_path)
        files[path] = apply_cog_edits(original.decode('cp1252').replace('\r', ''), rule['edits']).encode('cp1252')
        changes.append({'kind': 'native-text', 'path': path, 'source_sha256': rule['sha256'], 'edits': rule['edits']})
    for native_path, rule in spec.get('native_resource_overrides', {}).items():
        _, path, archive = source.get(Path(rule['source_path']).name)
        original = archive.read(path)
        if path != rule['source_path'] or hashlib.sha256(original).hexdigest() != rule['sha256'] or not rule.get('reason'):
            raise ValueError('Unreviewed player model override: ' + native_path)
        # Model material references point to the namespaced copies. Include the
        # namespaced graph in the overlay too: model selection precedes the map.
        files[native_path] = rename_refs(original.decode('cp1252').replace('\r', '')).encode('cp1252')
        changes.append({'kind': 'native-resource', 'path': native_path, **rule})
    if spec.get('native_resource_overrides'):
        for path, data in resources.items():
            if not path.endswith('.jkl') and path not in ('episode.jk', 'misc/cogstrings.uni'):
                files.setdefault(path, data)
    if not files:
        return None
    return {'archive_name': 'bridge-' + spec['tag'] + '-startup.goo',
            'folder_name': 'bridge-' + spec['tag'] + '-startup',
            'data': build_gob(files), 'changes': changes,
            'files': {path: hashlib.sha256(data).hexdigest() for path, data in sorted(files.items())}}

"""Source-only, hash-pinned Ninja Kage 7.0 -> MotS startup-mod prototype.

No source game/mod asset bytes are embedded here. User-owned archives are read
locally. Structural verification is independent of assembly and is not gameplay.
"""
from collections import Counter, deque
from dataclasses import dataclass
import copy
import hashlib
import io
import json
from pathlib import Path
import re
import struct
from force_icon_palette import allocation_menu_palette, derivation_report
import zipfile

import bridge
from gob import ArchiveError, Gob, build_gob, resource_name
import ninja_catalog as catalog


class NinjaError(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def txt(data):
    return data.decode('cp1252').replace('\r\n', '\n').replace('\r', '\n')


def encoded(value):
    return value.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\r\n').encode('cp1252')


def catalog_entry():
    return {'id': 'ninja-kage', 'title': catalog.SPEC['title'], 'kind': 'mod',
            'gameplay': ['mp'], 'author': catalog.SPEC['author'],
            'source_url': catalog.SPEC['source_url'],
            'archive_hint': catalog.SPEC['archive_hint'], 'requires_archive': True,
            'status': catalog.STATUS,
            'summary': 'Original Ninja Kage weapons and movement on a native MotS multiplayer base; runtime gates pending.',
            'startup_overlay': catalog.SPEC['startup_overlay'],
            'runtime_test': copy.deepcopy(catalog.RUNTIME_TEST)}


def original_hashes():
    return {catalog.SPEC['zip_sha256'], catalog.SPEC['gob_sha256']}


def recipe_details():
    return {**copy.deepcopy(catalog.SPEC), 'status': catalog.STATUS,
            'runtime_test': copy.deepcopy(catalog.RUNTIME_TEST),
            'original_cog_edits': copy.deepcopy(catalog.ORIGINAL_COG_EDITS),
            'native_player_sha256': catalog.NATIVE_PLAYER_SHA256,
            'player_cog_edits': copy.deepcopy(catalog.PLAYER_COG_EDITS),
            'script_aliases': dict(catalog.SCRIPT_ALIASES),
            'excluded_sp_scripts': list(catalog.EXCLUDED_SP_SCRIPTS),
            'native_unused_template': dict(catalog.NATIVE_UNUSED_TEMPLATE),
            'optional_force_ui_extension': copy.deepcopy(catalog.FORCE_UI_EXTENSION),
            'original_omissions': [{'referrer': a, 'name': b, 'reason': reason}
                                   for (a, b), reason in sorted(catalog.ORIGINAL_MISSING.items())],
            'known_gaps': list(catalog.KNOWN_GAPS)}


@dataclass(frozen=True)
class Original:
    archive: Gob
    source_sha256: str
    readme: bytes | None


def _normalize_pinned_gob(data):
    # This one historical directory entry is accepted only under the whole-file
    # content pin. Normal Gob validation remains strict for every other input.
    if digest(data) != catalog.SPEC['gob_sha256']:
        raise NinjaError('Unsupported Ninja Kage GOB SHA256')
    raw = bytearray(data)
    magic, version, table = struct.unpack_from('<4sII', raw)
    if magic != b'GOB ' or version != 20:
        raise NinjaError('Unexpected pinned GOB header')
    count = struct.unpack_from('<I', raw, table)[0]
    changed = 0
    for index in range(count):
        start = table + 4 + index * 136 + 8
        name = bytes(raw[start:start+128]).split(b'\x00', 1)[0]
        if name == b'\\patchinfo.txt':
            raw[start:start+128] = b'patchinfo.txt'.ljust(128, b'\x00')
            changed += 1
    if changed != 1:
        raise NinjaError('Pinned legacy directory normalization did not match once')
    result = Gob(raw, 'Ninja Kage 7.0, one pinned virtual-path normalization')
    if len(result.entries) != catalog.SPEC['original_member_count']:
        raise NinjaError('Unexpected original GOB member count')
    for name, expected in catalog.SPEC['cog_sha256'].items():
        if digest(result.read(name)) != expected:
            raise NinjaError('Original COG content pin mismatch: ' + name)
    return result


def _read_zip(data):
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = archive.infolist()
            names = [resource_name(x.filename) for x in members]
            expected = {resource_name(catalog.SPEC['gob_member']),
                        resource_name(catalog.SPEC['readme_member'])}
            if len(names) != 2 or len(set(names)) != 2 or set(names) != expected:
                raise NinjaError('Unexpected/duplicate original ZIP members')
            if any(x.flag_bits & 1 or x.is_dir() or x.file_size > 10_000_000
                   or ((x.external_attr >> 16) & 0o170000) == 0o120000 for x in members):
                raise NinjaError('Unsupported original ZIP member')
            payloads = {resource_name(x.filename): archive.read(x) for x in members}
            readme = payloads[resource_name(catalog.SPEC['readme_member'])]
            if digest(readme) != catalog.SPEC['readme_sha256']:
                raise NinjaError('Original README SHA256 mismatch')
            return payloads[resource_name(catalog.SPEC['gob_member'])], readme
    except (zipfile.BadZipFile, RuntimeError, KeyError) as exc:
        raise NinjaError('Invalid original ZIP or member CRC') from exc


def open_original(path):
    path = Path(path)
    if path.stat().st_size > 10_000_000:
        raise NinjaError('Original exceeds the bounded Ninja Kage archive size')
    data = path.read_bytes()
    sha = digest(data)
    if sha == catalog.SPEC['zip_sha256']:
        gob_data, readme = _read_zip(data)
    elif sha == catalog.SPEC['gob_sha256']:
        gob_data, readme = data, None
    else:
        raise NinjaError('Unsupported Ninja Kage archive; requires the pinned 7.0 original')
    return Original(_normalize_pinned_gob(gob_data), sha, readme)


def validate_sources(archives, original):
    for key, expected in bridge.HASHES.items():
        if key not in archives or archives[key].sha256 != expected:
            raise NinjaError('Unsupported owned source archive: ' + key)
    if not isinstance(original, Original) or original.source_sha256 not in original_hashes():
        raise NinjaError('Expected a pinned Original object')
    if original.archive.sha256 != catalog.NORMALIZED_GOB_SHA256:
        raise NinjaError('Normalized original payload/directory hash changed')
    if original.readme is not None and digest(original.readme) != catalog.SPEC['readme_sha256']:
        raise NinjaError('Original README changed after loading')
    # Normalized directory bytes differ, so validate every original payload
    # against the raw digest pin's strictly parsed copy at the loader boundary.
    for path, sha in catalog.SPEC['cog_sha256'].items():
        if digest(original.archive.read(path)) != sha:
            raise NinjaError('Original script changed after loading: ' + path)
    if digest(archives['motsres'].read('cog/kyle_m.cog')) != catalog.NATIVE_PLAYER_SHA256:
        raise NinjaError('Native player COG SHA256 mismatch')


def apply_edits(value, edits):
    for edit in edits:
        if not edit['old'] or not edit['reason'] or value.count(edit['old']) != edit['count']:
            raise NinjaError('Exact source edit count failed: ' + edit.get('reason', ''))
        value = value.replace(edit['old'], edit['new'])
    return value


ITEM_ROW = re.compile(r'^(\s*)(\S+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(0x[0-9a-f]+)([^\n]*)$', re.I)


def items(value):
    result = {}
    for line in value.splitlines():
        match = ITEM_ROW.fullmatch(line.split('#', 1)[0].rstrip())
        if not match:
            continue
        _, name, number, low, high, flags, extra = match.groups()
        number = int(number)
        if number in result:
            raise NinjaError('Duplicate inventory bin')
        result[number] = {'name': name, 'min': float(low), 'max': float(high),
                          'flags': int(flags, 16), 'extra': extra.strip(), 'line': line}
    if not result:
        raise NinjaError('Empty inventory table')
    return result


def build_items(native, authored, *, force_ui=False):
    old, source = items(native), items(authored)
    if old[124]['max'] != 30 or source[4]['max'] != 200:
        raise NinjaError('Kunai max source pin did not match')
    lines = native.splitlines()
    for index, line in enumerate(lines):
        match = ITEM_ROW.fullmatch(line.split('#', 1)[0].rstrip())
        if not match:
            continue
        number = int(match.group(3))
        if number == 124:
            start, end = match.span(5)
            lines[index] = line[:start] + '200' + line[end:]
        elif number == 27:
            if line.count('cog=force_blinding.cog') != 1:
                raise NinjaError('Native blinding descriptor anchor changed')
            lines[index] = line.replace('cog=force_blinding.cog', 'cog=nk_force_push.cog')
    additions = []
    for number in (30, 32, 116, 117, 118, 119):
        if number in old or number not in source:
            raise NinjaError('Custom inventory bin collision')
        row = source[number]['line']
        if force_ui and number in catalog.FORCE_UI_EXTENSION['descriptors']:
            match = ITEM_ROW.fullmatch(row)
            row = row[:match.start(2)] + catalog.FORCE_UI_EXTENSION['descriptors'][number] + row[match.end(2):]
        additions.append(row)
    end_indices = [i for i, line in enumerate(lines) if line.strip().lower() == 'end']
    if len(end_indices) != 1:
        raise NinjaError('Unexpected inventory terminator')
    lines[end_indices[0]:end_indices[0]] = ['# Ninja Kage original powers and controls.'] + additions
    result = '\n'.join(lines) + '\n'
    if len(action_bins(result)) > 32:
        raise NinjaError('Engine hotkey action capacity exceeded')
    return result


def action_bins(value):
    return sorted(number for number, row in items(value).items() if row['flags'] & 0x100)


# Native stdString_GetQuotedStringContents uses plain quote delimiters; a
# backslash is literal. Treating it as an escape skipped DIK_BACKSLASH and
# undercounted the emitted physical records, dropping the final native key.
UNI_ROW = re.compile(r'^\s*"([^"]*)"\s+(-?\d+)\s+"([^"]*)"\s*(?:#.*)?$')


def uni_rows(value):
    rows = {}
    for line in value.splitlines():
        match = UNI_ROW.fullmatch(line)
        if match:
            key, flag, string = match.groups()
            # Pinned retail MotS repeats GUI_JEDIONLY_HINT. Engine hash insertion
            # keeps the first key; preserve both source lines and that behavior.
            rows.setdefault(key, (int(flag), string))
    if not rows:
        raise NinjaError('Empty UNI string table')
    return rows


def _write_uni(native, changes):
    remaining = dict(changes)
    lines = []
    for line in native.splitlines():
        match = UNI_ROW.fullmatch(line)
        if match and match.group(1) in remaining:
            key = match.group(1); flag, string = remaining.pop(key)
            line = f'   "{key}" {flag} "{string}"'
        lines.append(line)
    ends = [i for i, line in enumerate(lines) if re.match(r'^\s*END\b', line, re.I)]
    if len(ends) != 1:
        raise NinjaError('Unexpected UNI terminator')
    lines[ends[0]:ends[0]] = [f'   "{key}" {flag} "{string}"'
                             for key, (flag, string) in sorted(remaining.items())]
    value = '\n'.join(lines) + '\n'
    count = sum(UNI_ROW.fullmatch(line) is not None for line in value.splitlines())
    value, changed = re.subn(r'(?m)^MSGS\s+\d+', f'MSGS {count}', value)
    if changed != 1:
        raise NinjaError('Unexpected UNI count header')
    return value


def merge_uni(native, jk, authored, native_items=None, authored_items=None, output_items=None):
    base, source = uni_rows(jk), uni_rows(authored)
    changes = {key: row for key, row in source.items() if base.get(key) != row
               and not re.fullmatch(r'ACTIVATE\d+', key)}
    if output_items is not None:
        native_strings = uni_rows(native)
        source_bins = {number: source[f'ACTIVATE{i}']
                       for i, number in enumerate(action_bins(authored_items))}
        native_bins = {number: native_strings[f'ACTIVATE{i}']
                       for i, number in enumerate(action_bins(native_items))}
        for index, number in enumerate(action_bins(output_items)):
            changes[f'ACTIVATE{index}'] = source_bins.get(number, native_bins.get(number))
            if changes[f'ACTIVATE{index}'] is None:
                raise NinjaError('Missing control display label')
        for old, new in catalog.WEAPON_BINS.items():
            key = f'COG_{old:05d}'
            if key in source:
                changes[f'COG_{new:05d}'] = source[key]
    return _write_uni(native, changes)


def build_models(value):
    result = []
    count = 0
    for line in value.splitlines():
        active, sep, comment = line.partition('#')
        tokens = active.split()
        if tokens and re.fullmatch(r'\d+:', tokens[0]):
            if len(tokens) != 3 or not tokens[1].lower().endswith('.3do') or not tokens[2].lower().endswith('.snd'):
                raise NinjaError('Unexpected original model row')
            line = active.rstrip() + '\t1' + ('\t#' + comment if sep else '')
            count += 1
        result.append(line)
    if count != 29:
        raise NinjaError('Original model count is not 29')
    return '\n'.join(result) + '\n'


def _template_rows(value):
    return bridge.records(value, 'templates')


def _append_templates(native, authored):
    if re.search(r'^World templates\b', native, re.I | re.M):
        raise NinjaError('Native static unexpectedly already has templates')
    rows = _template_rows(authored)
    names = {row.split()[0].lower() for row in rows}
    if len(names) != 15 or len(rows) != 15:
        raise NinjaError('Original static template set changed')
    prior = {'none'}
    for row in rows:
        tokens = row.split()
        if tokens[1].lower() not in prior:
            raise NinjaError('Original static template parent is not loaded before child')
        prior.add(tokens[0].lower())
    return native.rstrip() + '\n\nSection: templates\nWorld templates 15\n' + '\n'.join(rows) + '\nend\n'


CAPACITIES = {'sounds': '.wav', 'materials': '.mat', 'soundclasses': '.snd',
              'models': '.3do', 'sprites': '.spr', 'keyframes': '.key',
              'puppets': '.pup', 'scripts': '.cog', 'cogs': '.cog'}


def _grow_capacities(value, files):
    counts = Counter(Path(path).suffix for path in files)
    for label, extension in CAPACITIES.items():
        pattern = re.compile(r'(^World ' + label + r'\s+)(\d+)', re.I | re.M)
        value, n = pattern.subn(lambda m: m.group(1) + str(max(int(m.group(2)), counts[extension])), value)
        if n != 1:
            raise NinjaError('Missing native static capacity: ' + label)
    return value


def _preload_static(value, files):
    # Native rows remain first with their original indices. Loading the closure
    # here makes weapon resources independent of the selected MP level's pools.
    for label, extension in CAPACITIES.items():
        if label == 'cogs':
            continue
        match = bridge.block(value, label)
        rows = bridge.records(value, label)
        existing = set(bridge.references('\n'.join(rows)))
        names = sorted({Path(path).name for path in files if Path(path).suffix == extension} - existing)
        for name in names:
            if label == 'sounds':
                row = name
            elif label == 'materials':
                row = f'{len(rows)}: {name} 1.0 1.0'
            else:
                row = f'{len(rows)}: {name}'
            rows.append(row)
        value = bridge.replace_block(value, label, rows, max(int(match.group(2)), len(rows)))
    # Each inventory descriptor makes a COG instance; template class COGs are
    # another instance. Count these independently from unique script preloads.
    descriptor_count = sum('cog=' in row['extra'].lower() for row in items(txt(files['misc/items.dat'])).values())
    class_count = len(re.findall(r'(?i)\bcog\s*=\s*[^\s]+', '\n'.join(_template_rows(value))))
    match = bridge.block(value, 'cogs')
    value = bridge.replace_block(value, 'cogs', [], max(int(match.group(2)), descriptor_count + class_count))
    if any(path.endswith('.ai') for path in files):
        ai_names = sorted(Path(path).name for path in files if path.endswith('.ai'))
        value = value.replace('Section: templates\n', 'Section: aiclass\nWorld aiclasses ' + str(len(ai_names)) + '\n' +
                              '\n'.join(f'{i}: {name}' for i, name in enumerate(ai_names)) + '\nend\n\nSection: templates\n')
    return value


def allocation_icon(data, source_palette, target_palette):
    """Derive four states in the actual allocation-menu palette."""
    from force_icon_palette import derive_allocation_icon
    try:
        return derive_allocation_icon(data, source_palette, target_palette)
    except ValueError as error:
        raise NinjaError(str(error)) from error


def validate_hud_bitmap(data, depth):
    """Check every declared native HUD frame and optional palette payload."""
    if len(data) < 136 or data[:4] != b'BM  ' or struct.unpack_from('<I', data, 4)[0] != 70:
        raise NinjaError('Invalid HUD bitmap header')
    frames = struct.unpack_from('<I', data, 16)[0]
    if not 1 <= frames <= 64 or struct.unpack_from('<I', data, 36)[0] != depth:
        raise NinjaError('Invalid HUD bitmap frame count/depth')
    offset = 128
    for _ in range(frames):
        if offset + 8 > len(data):
            raise NinjaError('Truncated HUD bitmap frame header')
        width, height = struct.unpack_from('<II', data, offset)
        if not 1 <= width <= 4096 or not 1 <= height <= 4096:
            raise NinjaError('Invalid HUD bitmap frame dimensions')
        offset += 8 + width * height * (depth // 8)
        if offset > len(data):
            raise NinjaError('Truncated HUD bitmap frame pixels')
    palette = 768 if struct.unpack_from('<I', data, 12)[0] & 2 else 0
    if len(data) != offset + palette:
        raise NinjaError('HUD bitmap palette/trailing payload mismatch')
    return frames


def _omission(path, name):
    reverse = {new: old for old, new in catalog.SCRIPT_ALIASES.items()}
    basename = Path(path).name
    original_path = 'cog/' + reverse[basename] if basename in reverse else path
    reason = catalog.ORIGINAL_MISSING.get((original_path, name))
    return {'referrer': path, 'original_referrer': original_path, 'name': name, 'reason': reason} if reason else None


def _resource_refs(path, data):
    if Path(path).suffix in bridge.TEXT_EXTENSIONS | {'.dat'}:
        return bridge.references(txt(data))
    return set()


def _closure(files, modes, archives, original):
    orders = {
        'authored': bridge.Catalog([('original', original.archive)] + [(k, archives[k]) for k in ('jkres', 'jksnd', 'motsres', 'motssnd', 'motsmp')]),
        'native': bridge.Catalog([(k, archives[k]) for k in ('motsres', 'motssnd', 'motsmp', 'jkres', 'jksnd')]),
    }
    queue = deque(sorted(files))
    origins = {path: {'kind': modes[path], 'sha256': digest(data)} for path, data in files.items()}
    omissions = {}
    while queue:
        path = queue.popleft()
        by_name = {Path(key).name: key for key in files}
        for name in sorted(_resource_refs(path, files[path])):
            if name in by_name:
                continue
            try:
                label, dependency, archive = orders[modes[path]].get(name)
            except bridge.RecipeError:
                waiver = _omission(path, name)
                if not waiver:
                    raise NinjaError(f'Unresolved resource {path} -> {name}')
                omissions[path, name] = waiver
                continue
            # Authored Force Push intentionally has a new basename; this lookup
            # should never reintroduce an excluded JK player/campaign script.
            if label == 'original' and (Path(dependency).name in catalog.EXCLUDED_SP_SCRIPTS or dependency == 'cog/kyle.cog'):
                raise NinjaError('MP closure unexpectedly requires excluded SP/player COG: ' + dependency)
            files[dependency] = archive.read(dependency)
            modes[dependency] = 'authored' if label in ('original', 'jkres', 'jksnd') else 'native'
            origins[dependency] = {'kind': label, 'sha256': digest(files[dependency])}
            queue.append(dependency)
    return origins, [omissions[key] for key in sorted(omissions)]


def build(archives, original, *, force_ui=False):
    validate_sources(archives, original)
    original_gob = original.archive
    merged = {'misc/items.dat', 'misc/models.dat', 'jkl/static.jkl',
              'ui/jkstrings.uni', 'misc/sithstrings.uni', 'cog/kyle.cog'}
    files, modes = {}, {}
    for path in sorted(original_gob.entries):
        if path in merged or Path(path).name in catalog.EXCLUDED_SP_SCRIPTS:
            continue
        data = original_gob.read(path)
        target = path
        if Path(path).suffix == '.cog':
            name = Path(path).name
            edits = catalog.ORIGINAL_COG_EDITS.get(name, [])
            if edits:
                data = encoded(apply_edits(txt(data), edits))
            target = 'cog/' + catalog.SCRIPT_ALIASES.get(name, name)
        files[target] = data
        modes[target] = 'authored'
    def add(path, value, mode='native'):
        files[path] = encoded(value); modes[path] = mode
    native_items = txt(archives['motsres'].read('misc/items.dat'))
    authored_items = txt(original_gob.read('misc/items.dat'))
    output_items = build_items(native_items, authored_items, force_ui=force_ui)
    add('misc/items.dat', output_items)
    add('cog/kyle_m.cog', apply_edits(txt(archives['motsres'].read('cog/kyle_m.cog')), catalog.PLAYER_COG_EDITS))
    add('misc/models.dat', build_models(txt(original_gob.read('misc/models.dat'))), 'authored')
    add('ui/jkstrings.uni', merge_uni(txt(archives['motssnd'].read('ui/jkstrings.uni')),
        txt(archives['jksnd'].read('ui/jkstrings.uni')), txt(original_gob.read('ui/jkstrings.uni')),
        native_items, authored_items, output_items))
    add('misc/sithstrings.uni', merge_uni(txt(archives['motsres'].read('misc/sithstrings.uni')),
        txt(archives['jkres'].read('misc/sithstrings.uni')), txt(original_gob.read('misc/sithstrings.uni'))))
    # These descriptors are active in every Ninja build. Native HUD startup
    # requests ic + the first five name characters + 8/16, even headlessly.
    # MotS lacks the original Throw/Lightning images; retain exact JK assets.
    for name in catalog.FORCE_UI_EXTENSION['hud_icons']:
        path = 'ui/bm/' + name
        files[path] = archives['jksnd'].read(path); modes[path] = 'authored'
    allocation_reports = {}
    allocation_backgrounds = None
    if force_ui:
        source_background = archives['jksnd'].read('ui/bm/bkforce.bm')
        target_background = files.get('ui/bm/bkforce.bm', archives['motssnd'].read('ui/bm/bkforce.bm'))
        try:
            source_palette = allocation_menu_palette(source_background)
            target_palette = allocation_menu_palette(target_background)
        except ValueError as error:
            raise NinjaError(str(error)) from error
        allocation_backgrounds = {'source_resource': 'ui/bm/bkforce.bm', 'source_archive': 'jksnd',
            'source_sha256': digest(source_background), 'target_resource': 'ui/bm/bkforce.bm',
            'target_provider': 'output' if 'ui/bm/bkforce.bm' in files else 'motssnd',
            'target_sha256': digest(target_background)}
        for source, target in catalog.FORCE_UI_EXTENSION['allocation_icons'].items():
            path = 'ui/bm/' + target
            original_icon = archives['jksnd'].read('ui/bm/' + source)
            files[path] = allocation_icon(original_icon, source_palette, target_palette); modes[path] = 'native'
            report = derivation_report(original_icon, files[path], source_palette, target_palette)
            if report['weighted_rgb_rmse'] > 30 or report['maximum_pixel_weighted_rgb_error'] > 56 or not all(report['transparent_masks_preserved']):
                raise NinjaError('Allocation icon color quality or transparency gate failed: ' + path)
            allocation_reports[path] = report
        hints = uni_rows(txt(original_gob.read('ui/jkstrings.uni')))
        add('ui/jkstrings.uni', _write_uni(txt(files['ui/jkstrings.uni']), {key:hints[key] for key in ('GUI_HINT_THROW','GUI_HINT_LIGHTNING')}))
    static = _append_templates(txt(archives['motsres'].read('jkl/static.jkl')), txt(original_gob.read('jkl/static.jkl')))
    add('jkl/static.jkl', static)
    origins, omissions = _closure(files, modes, archives, original)
    if force_ui and files.get('ui/bm/bkforce.bm', archives['motssnd'].read('ui/bm/bkforce.bm')) != target_background:
        raise NinjaError('Allocation background changed after icon derivation')
    add('jkl/static.jkl', _preload_static(_grow_capacities(static, files), files))
    for path in merged - {'cog/kyle.cog'} | {'cog/kyle_m.cog'}:
        origins[path] = {'kind': 'derived', 'sha256': digest(files[path])}
    result = build_gob(files)
    manifest = {'schema': 1, 'recipe': 'ninja-kage-7.0-mots-mp-prototype-' + ('5-force-ui-menu-palette' if force_ui else '3-hud-closure'),
                'original': {key: catalog.SPEC[key] for key in ('author', 'title', 'source_url', 'download_url', 'zip_sha256', 'gob_sha256', 'readme_sha256')},
                'native_sources': dict(bridge.HASHES), 'startup_overlay': catalog.SPEC['startup_overlay'],
                'output_sha256': digest(result), 'runtime_test': copy.deepcopy(catalog.RUNTIME_TEST),
                'known_gaps': list(catalog.KNOWN_GAPS), 'original_omissions': omissions,
                'native_unused_template': dict(catalog.NATIVE_UNUSED_TEMPLATE),
                'force_ui_extension': copy.deepcopy(catalog.FORCE_UI_EXTENSION) if force_ui else None,
                'allocation_backgrounds': allocation_backgrounds, 'allocation_icons': allocation_reports,
                'control_bindings': [{'action': f'ACTIVATE{i}', 'bin': number,
                    'label': uni_rows(txt(files['ui/jkstrings.uni']))[f'ACTIVATE{i}'][1]}
                    for i, number in enumerate(action_bins(output_items))],
                'resources': [{'path': path, 'sha256': digest(data), 'bytes': len(data),
                               'origin': origins[path]} for path, data in sorted(files.items())]}
    return result, manifest


def _independent_edits(data, edits):
    value = txt(data)
    for edit in edits:
        pieces = value.split(edit['old'])
        if len(pieces) - 1 != edit['count']:
            raise NinjaError('Verifier source-anchor mismatch')
        value = edit['new'].join(pieces)
    return value


def verify(archives, original, data, manifest=None, *, force_ui=False):
    """Check source semantics and unchanged payloads without invoking build()."""
    validate_sources(archives, original)
    output = Gob(data, 'Ninja Kage converted startup overlay')
    checks = []
    def require(condition, message):
        if not condition:
            raise NinjaError('Independent verification: ' + message)
    source = original.archive
    excluded = set(catalog.EXCLUDED_SP_SCRIPTS) | {'kyle.cog'}
    special = {'misc/items.dat', 'misc/models.dat', 'jkl/static.jkl', 'ui/jkstrings.uni', 'misc/sithstrings.uni'}
    authored_paths = set()
    for path in source.entries:
        if path in special or Path(path).name in excluded:
            continue
        target = 'cog/' + catalog.SCRIPT_ALIASES.get(Path(path).name, Path(path).name) if path.endswith('.cog') else path
        require(target in output.entries, 'missing authored asset ' + target)
        edits = catalog.ORIGINAL_COG_EDITS.get(Path(path).name, [])
        if edits:
            require(txt(output.read(target)) == _independent_edits(source.read(path), edits), 'COG edit/untouched-segment mismatch ' + target)
        else:
            require(output.read(target) == source.read(path), 'original asset bytes changed ' + target)
        authored_paths.add(target)
    require(not any('cog/' + x in output.entries for x in excluded), 'excluded single-player/player script was reintroduced')
    require(txt(output.read('cog/kyle_m.cog')) == _independent_edits(archives['motsres'].read('cog/kyle_m.cog'), catalog.PLAYER_COG_EDITS), 'native player adaptation or untouched native segments changed')
    checks.append('All original MP assets are unchanged except exact counted COG edits; native player edits and untouched segments match.')
    old, now, authored = (items(txt(x)) for x in (archives['motsres'].read('misc/items.dat'), output.read('misc/items.dat'), source.read('misc/items.dat')))
    require(set(now) == set(old) | {30, 32, 116, 117, 118, 119}, 'inventory bin set changed')
    for number in old:
        expected = {k: v for k, v in old[number].items() if k != 'line'}
        actual = {k: v for k, v in now[number].items() if k != 'line'}
        if number == 124:
            expected['max'] = 200.0
        if number == 27:
            expected['extra'] = expected['extra'].replace('force_blinding.cog', 'nk_force_push.cog')
        require(actual == expected, f'native descriptor semantics changed at bin {number}')
    for number in (30, 32, 116, 117, 118, 119):
        expected = {k:v for k,v in authored[number].items() if k!='line'}
        if force_ui and number in catalog.FORCE_UI_EXTENSION['descriptors']:
            expected['name'] = catalog.FORCE_UI_EXTENSION['descriptors'][number]
        require({k:v for k,v in now[number].items() if k!='line'} == expected, f'authored descriptor changed at bin {number}')
    require(output.read('cog/force_push.cog') == archives['motsres'].read('cog/force_push.cog'), 'native Force Push38 overwritten')
    require(output.read('cog/weap_concrifle_m.cog') == archives['motsres'].read('cog/weap_concrifle_m.cog'), 'native concussion129 changed')
    require(action_bins(txt(output.read('misc/items.dat'))) == list(range(21, 40)) + [40, 41, 42, 116, 117, 118], 'hotkey enumeration mismatch')
    checks.append('Native inventory, weapon flags/order, concussion129 and Force Push38 retained; only reviewed rows27/124 plus six additions differ.')
    original_models = [line.split('#',1)[0].split() for line in txt(source.read('misc/models.dat')).splitlines() if re.match(r'^\d+:', line)]
    converted_models = [line.split('#',1)[0].split() for line in txt(output.read('misc/models.dat')).splitlines() if re.match(r'^\d+:', line)]
    require(converted_models == [row + ['1'] for row in original_models] and len(converted_models) == 29, 'authored model selection/personality mapping mismatch')
    for path, jkkey, nativekey in (('ui/jkstrings.uni','jksnd','motssnd'), ('misc/sithstrings.uni','jkres','motsres')):
        jkrows, original_rows, native_rows, rows = (uni_rows(txt(x)) for x in (archives[jkkey].read(path), source.read(path), archives[nativekey].read(path), output.read(path)))
        expected = dict(native_rows)
        for key, row in original_rows.items():
            if jkrows.get(key) != row and not re.fullmatch(r'ACTIVATE\d+', key):
                expected[key] = row
        if path == 'ui/jkstrings.uni':
            native_actions = dict(zip(action_bins(txt(archives['motsres'].read('misc/items.dat'))), [native_rows[f'ACTIVATE{i}'] for i in range(20)]))
            original_actions = dict(zip(action_bins(txt(source.read('misc/items.dat'))), [original_rows[f'ACTIVATE{i}'] for i in range(20)]))
            for index, number in enumerate(sorted(n for n, row in now.items() if row['flags'] & 0x100)):
                expected[f'ACTIVATE{index}'] = original_actions[number] if number in original_actions else native_actions[number]
            for number, new in catalog.WEAPON_BINS.items():
                if f'COG_{number:05d}' in original_rows:
                    expected[f'COG_{new:05d}'] = original_rows[f'COG_{number:05d}']
            if force_ui:
                for key in ('GUI_HINT_THROW','GUI_HINT_LIGHTNING'):
                    expected[key] = original_rows[key]
        require(rows == expected, 'native/authored UI merge mismatch: ' + path)
        header = re.search(r'^MSGS\s+(\d+)', txt(output.read(path)))
        count = sum(UNI_ROW.fullmatch(line) is not None for line in txt(output.read(path)).splitlines())
        require(header and int(header.group(1)) == count, 'UNI record count mismatch')
    checks.append('All 29 authored models have explicit Jedi personality; native UI keys retained and 25 hotkey labels map to actual descriptor order.')
    static = txt(output.read('jkl/static.jkl'))
    require(_template_rows(static) == _template_rows(txt(source.read('jkl/static.jkl'))), 'authored static templates or parent order changed')
    native_static = txt(archives['motsres'].read('jkl/static.jkl'))
    static_prefix = re.split(r'(?mi)^Section: templates\s*$', static)[0].rstrip()
    counts = Counter(Path(path).suffix for path in output.entries)
    for label, extension in CAPACITIES.items():
        count = int(bridge.block(static, label).group(2))
        original_count = int(bridge.block(txt(archives['motsres'].read('jkl/static.jkl')), label).group(2))
        if label == 'cogs':
            instances = sum('cog=' in row['extra'].lower() for row in now.values())
            instances += len(re.findall(r'(?i)\bcog\s*=\s*[^\s]+', '\n'.join(_template_rows(static))))
            require(not bridge.records(static, label), 'unexpected static COG placement')
            require(count == max(original_count, counts[extension], instances), 'COG instance capacity mismatch')
        else:
            native_rows = bridge.records(txt(archives['motsres'].read('jkl/static.jkl')), label)
            rows = bridge.records(static, label)
            require(rows[:len(native_rows)] == native_rows, 'native preload row/index changed: ' + label)
            old_names = set(bridge.references('\n'.join(native_rows)))
            new_names = sorted({Path(path).name for path in output.entries if Path(path).suffix == extension} - old_names)
            expected_rows = list(native_rows)
            for name in new_names:
                expected_rows.append(name if label == 'sounds' else f'{len(expected_rows)}: {name}' + (' 1.0 1.0' if label == 'materials' else ''))
            require(rows == expected_rows, 'full closure preload rows/order mismatch: ' + label)
            require(count == max(original_count, counts[extension], len(rows)), 'static resource capacity does not match actual closure')
        for which in ('output', 'native'):
            value = static_prefix if which == 'output' else native_static
            match = bridge.block(value, label)
            value = value[:match.start()] + f'BLOCK_{label}\n' + value[match.end():]
            if which == 'output':
                static_prefix = value
            else:
                native_static = value
    if re.search(r'^Section: aiclass\b', static_prefix, re.I | re.M):
        ai_names = sorted(Path(path).name for path in output.entries if path.endswith('.ai'))
        require(bridge.records(static, 'aiclasses') == [f'{i}: {name}' for i, name in enumerate(ai_names)], 'AI preload mismatch')
        static_prefix = re.sub(r'(?mis)^Section: aiclass\n.*?^end\s*\n*', '', static_prefix)
    require(static_prefix.rstrip() == native_static.rstrip(), 'native static header/section order changed')
    checks.append('Fifteen original templates retained; native preloads stay first and the complete resource closure is preloaded with computed pools.')
    # Verify every imported dependency against a pinned original archive, then
    # independently resolve every active literal filename and COG template.
    base_names = {}
    for path in output.entries:
        name = Path(path).name
        require(name not in base_names, 'ambiguous output resource basename ' + name)
        require(len(name.encode('cp1252')) <= 31, 'engine resource basename exceeds 31 bytes: ' + name)
        base_names[name] = path
    generated = special | {'cog/kyle_m.cog'}
    for name in catalog.FORCE_UI_EXTENSION['hud_icons']:
        path = 'ui/bm/' + name
        require(path in output.entries and output.read(path) == archives['jksnd'].read(path), 'required Ninja HUD icon absent or changed: ' + path)
        generated.add(path)
    # Independently audit the actual native naming contract for every active
    # item/power, including unchanged MotS icons supplied by its own archives.
    hud_paths = {f"ui/bm/ic{row['name'].lower()[:5]}{depth}.bm"
                 for row in now.values() if row['flags'] & 0x00a for depth in (8, 16)}
    hud_paths |= {f'ui/bm/{name}{depth}.bm' for name in ('icbrack', 'forcebrack', 'icdefau') for depth in (8, 16)}
    for path in hud_paths:
        provider = next((archive for archive in (output, archives['motsres'], archives['motssnd']) if path in archive.entries), None)
        require(provider is not None, 'descriptor HUD bitmap unavailable at native runtime path: ' + path)
        validate_hud_bitmap(provider.read(path), 16 if path.endswith('16.bm') else 8)
    checks.append('Every active item/power and required HUD fallback resolves both bit depths with complete frames/palettes; four missing MotS Throw/Lightning icons retain exact JK bytes in every Ninja build.')
    allocation_reports = {}
    allocation_backgrounds = None
    if force_ui:
        source_background = archives['jksnd'].read('ui/bm/bkforce.bm')
        target_background = output.read('ui/bm/bkforce.bm') if 'ui/bm/bkforce.bm' in output.entries else archives['motssnd'].read('ui/bm/bkforce.bm')
        try:
            source_palette = allocation_menu_palette(source_background)
            target_palette = allocation_menu_palette(target_background)
        except ValueError as error:
            raise NinjaError('Independent verification: allocation background ' + str(error)) from error
        allocation_backgrounds = {'source_resource': 'ui/bm/bkforce.bm', 'source_archive': 'jksnd',
            'source_sha256': digest(source_background), 'target_resource': 'ui/bm/bkforce.bm',
            'target_provider': 'output' if 'ui/bm/bkforce.bm' in output.entries else 'motssnd',
            'target_sha256': digest(target_background)}
        for old, new in catalog.FORCE_UI_EXTENSION['allocation_icons'].items():
            old_data = archives['jksnd'].read('ui/bm/'+old)
            path = 'ui/bm/'+new
            new_data = output.read(path)
            require(new_data == allocation_icon(old_data, source_palette, target_palette), 'allocation icon palette/shape/disabled-state derivation mismatch ' + path)
            report = derivation_report(old_data, new_data, source_palette, target_palette)
            require(report['weighted_rgb_rmse'] <= 30 and report['maximum_pixel_weighted_rgb_error'] <= 56
                    and all(report['transparent_masks_preserved']), 'allocation icon quality/transparency mismatch ' + path)
            allocation_reports[path] = report
            generated.add(path)
        checks.append('Explicit Force UI opt-in; allocation icons remapped into the actual menu palette with retained28x28 shapes, preserved transparency and a derived dark disabled state; no rank grants. Original HUD icon bytes remain unchanged.')
    for path in set(output.entries) - authored_paths - generated:
        require(any(path in archive.entries and output.read(path) == archive.read(path) for archive in archives.values()), 'imported resource lacks exact pinned source ' + path)
    # The static preload table is derived from this closure, so exclude its
    # appended preload names as graph roots. Otherwise an unneeded retail file
    # could justify itself merely by also adding itself to that table.
    reachable = set(authored_paths) | generated
    pending = deque(sorted(reachable))
    original_static_references = bridge.references(txt(archives['motsres'].read('jkl/static.jkl')))
    original_static_references |= bridge.references('\n'.join(_template_rows(txt(source.read('jkl/static.jkl')))))
    while pending:
        path = pending.popleft()
        names = original_static_references if path == 'jkl/static.jkl' else _resource_refs(path, output.read(path))
        for name in names:
            if name in base_names and base_names[name] not in reachable:
                reachable.add(base_names[name]); pending.append(base_names[name])
    require(reachable == set(output.entries), 'unreferenced imported resource outside the authored/native closure')
    omissions = []
    for path in sorted(output.entries):
        for name in sorted(_resource_refs(path, output.read(path))):
            if name not in base_names:
                omission = _omission(path, name)
                require(omission is not None, f'unresolved resource {path} -> {name}')
                omissions.append(omission)
    native_world = next(path for path in archives['motsmp'].entries if path.endswith('/k1.jkl'))
    templates = {line.split()[0].lower() for line in _template_rows(static) + _template_rows(txt(archives['motsmp'].read(native_world)))}
    for path in output.entries:
        if path.endswith('.cog'):
            for symbol, name in re.findall(r'(?mi)^\s*template\s+(\w+)\s*=\s*([^\s#]+)', txt(output.read(path))):
                if name.lower() in templates | {'none', '-1'}:
                    continue
                waiver = catalog.NATIVE_UNUSED_TEMPLATE
                active = bridge.active_lines(txt(output.read(path)))
                require(path == waiver['path'] and name == waiver['name'] and symbol == waiver['symbol']
                        and digest(output.read(path)) == waiver['sha256']
                        and len(re.findall(r'\b' + re.escape(symbol) + r'\b', active)) == 1,
                        f'COG template absent from authored static/native K1: {path} -> {name}')
    checks.append('Every imported payload matches a pinned source; filename closure has four exact original omissions; COG templates resolve against authored static plus native K1 except one pinned unused native default.')
    if manifest is not None:
        require(manifest.get('allocation_backgrounds') == allocation_backgrounds and manifest.get('allocation_icons') == allocation_reports, 'manifest allocation palette/provenance mismatch')
        require(manifest.get('force_ui_extension') == (catalog.FORCE_UI_EXTENSION if force_ui else None), 'manifest Force UI option mismatch')
        require(manifest['native_sources'] == bridge.HASHES, 'manifest native source pins mismatch')
        require(manifest['native_unused_template'] == catalog.NATIVE_UNUSED_TEMPLATE, 'manifest native template waiver mismatch')
        require(manifest['output_sha256'] == digest(data), 'manifest output digest mismatch')
        actual = {path: (digest(output.read(path)), len(output.read(path))) for path in output.entries}
        listed = {row['path']: (row['sha256'], row['bytes']) for row in manifest['resources']}
        require(actual == listed and len(listed) == len(manifest['resources']), 'manifest exact resource set mismatch')
        require(manifest['original_omissions'] == omissions, 'manifest omission edges mismatch')
    return {'status': 'structural-pass', 'gameplay': 'not-run', 'sha256': digest(data),
            'resources': len(output.entries), 'checks': checks, 'original_omissions': omissions,
            'known_gaps': list(catalog.KNOWN_GAPS)}


def build_to_directory(archives, original_path, stage, *, force_ui=False):
    stage = Path(stage).resolve()
    project = Path(__file__).resolve().parent
    if stage == project or project in stage.parents:
        raise NinjaError('Generated game assets must be outside the source project')
    original = open_original(original_path)
    data, manifest = build(archives, original, force_ui=force_ui)
    verification = verify(archives, original, data, manifest, force_ui=force_ui)
    folder = stage / catalog.SPEC['startup_overlay']
    if folder.exists():
        raise NinjaError('Ninja Kage output already exists; select a fresh output directory')
    folder.mkdir(parents=True)
    filename = folder / 'blackwing-ninja-kage.goo'
    manifest_path = folder / 'source.manifest.json'
    with filename.open('xb') as handle:
        handle.write(data)
    manifest['verification'] = verification
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    if original.readme is not None:
        (folder / 'ORIGINAL-NINJA-KAGE.txt').write_bytes(original.readme)
    readme = ('Ninja Kage 7.0 - local MotS multiplayer prototype\n'
              'Original mod: ShadowX and the contributors credited in the original README.\n'
              'Original converter: World Between Worlds / Andrei Pemberton with Coda Lilitari.\n'
              f"Source: {catalog.SPEC['source_url']}\n\n"
              'Install this entire folder beside the runtime resource/ and episode/ folders.\n'
              'Launch OpenMotS with: -motsCompat -path blackwing-ninja-kage\n'
              'Use Multiplayer, a fresh Jedi character, an authored ninja model and green saber.\n'
              'All peers need the same startup mod; restart without -path for other mods.\n'
              'Bind Grappling Hook, Jump/Handspring and Kick in Controls.\n'
              'Also bind F2 Field Light, F3 IR Goggles and F4 Bacta; native defaults use the old action order.\n'
              'This structural prototype has not passed gameplay or visual tests.\n\n'
              + ('This variant requires the optional restored-Force allocation/cycling engine extension; it grants no ranks or stars.\n' if force_ui else '')
              + '\n'.join('- ' + gap for gap in catalog.KNOWN_GAPS) + '\n')
    (folder / 'README.txt').write_text(readme, encoding='utf-8')
    if filename.read_bytes() != data:
        raise NinjaError('Post-write artifact bytes differ')
    return {'filename': filename.relative_to(stage).as_posix(),
            'manifest_filename': manifest_path.relative_to(stage).as_posix(),
            'verification': verification, 'startup_overlay': catalog.SPEC['startup_overlay']}

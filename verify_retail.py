"""Independent scene invariants and repeat-build checks against user-owned inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import re

import bridge
import custom_registry
import blackwing_revisions
from gob import Gob, build_gob


# Kept independently of the recipe table so a recipe selecting the wrong world
# cannot validate itself. These names come from the owned JK episode directory.
STOCK_WORLDS = {
    'nar-shaddaa': ('jkmp', 'jkl/m2.jkl', 'br_narshaddaa'),
    'bespin': ('jkmp', 'jkl/m4.jkl', 'br_bespin'),
    'blades-of-death': ('jkmp', 'jkl/m5.jkl', 'br_blades'),
    'canyon-oasis': ('jkmp', 'jkl/m10.jkl', 'br_canyon'),
    'valley': ('jkmp', 'jkl/m_boss15.jkl', 'br_valley'),
    'battleground': ('jkmp', 'jkl/m_boss17.jkl', 'br_battleground'),
    'ctf-duel': ('jkctf', 'jkl/c1.jkl', 'br_ctf_duel'),
    'ctf-arena': ('jkctf', 'jkl/c2.jkl', 'br_ctf_arena'),
    'ctf-challenge': ('jkctf', 'jkl/c3.jkl', 'br_ctf_challenge'),
}


def game_payload(generated, expected_recipe, *, role='primary'):
    """Validate tracking and expose only the canonical game archive to checks.

    A marker does not establish conversion correctness: the returned payload
    still passes the existing source reconstruction and repeat-build checks.
    """
    allowed = {expected_recipe} if isinstance(expected_recipe, str) else set(expected_recipe)
    marker = blackwing_revisions.validate_archive(generated.data)
    if marker is None:
        return generated, None
    assert marker['id'] in allowed, 'Tracked archive belongs to a different selected recipe'
    assert marker['role'] == role, 'Tracked archive has the wrong primary/startup role'
    payload = Gob(build_gob({name: generated.read(name) for name in generated.entries
                             if name != blackwing_revisions.MARKER_NAME}), generated.label)
    assert payload.sha256 == marker['payload_sha256'], 'Tracked game-payload hash mismatch'
    return payload, marker


def resolve_output(directory, legacy_filename, expected_recipe, *, role='primary'):
    """Select one legacy output or a valid marked output, including renamed ones.

    A suffixed filename without a marker cannot assert identity. Multiple
    matching outputs are rejected instead of choosing whichever loads first.
    """
    directory = Path(directory).absolute()
    allowed = {expected_recipe} if isinstance(expected_recipe, str) else set(expected_recipe)
    catalog = [dict(id=key, title=key, kind='verification',
                    revision=blackwing_revisions.RECIPE_REVISIONS.get(key, 1),
                    legacy_filenames=[legacy_filename]) for key in sorted(allowed)]
    report = blackwing_revisions.scan_installation(directory, catalog)
    assert not report['truncated'], 'Archive lookup was incomplete: ' + '; '.join(report['warnings'])
    candidates = []
    for row in report['results']:
        path = Path(row['path'])
        # A startup/episode lookup refers to this exact directory; do not select
        # a similarly marked archive from another family's nested output folder.
        if path.parent != directory:
            continue
        legacy_name = path.name.lower() == legacy_filename.lower()
        marked_identity = row['id'] in allowed and row['role'] == role
        if not legacy_name and not marked_identity:
            continue
        generated = Gob.open(path)
        _, marker = game_payload(generated, allowed, role=role)
        assert marker is not None or legacy_name, 'Unmarked renamed archive has no verified recipe identity'
        candidates.append(path)
    assert len(candidates) == 1, ('Expected exactly one output for ' + ', '.join(sorted(allowed))
                                  + '; found ' + str(len(candidates)))
    return candidates[0]


def tracked_result(result, original, payload, marker):
    """Report the actual delivered hash separately from its verified payload."""
    if marker is not None:
        result.update(sha256=original.sha256, payload_sha256=payload.sha256,
                      tracking=marker)
    return result


# Independent compatibility contract. Never derive this from the converter's
# tables: a wrong producer binding or edited game script must fail verification.
FORCE_PICKUP_BINDINGS = {
    'pow_mana.cog': 'wbw_forceboost.cog',
    'pow_lightside.cog': 'wbw_forcesurge.cog',
    'pow_darkside.cog': 'wbw_forcesurge.cog',
}
FORCE_PICKUP_SOURCES = {
    'wbw_forceboost.cog': ('cog/pow_mana.cog',
        '8147b03115c1d9e8ff8c883a547c6ffe689751a46d27b84dc6ac7544bf3ace11', 2, 3),
    'wbw_forcesurge.cog': ('cog/pow_darkside.cog',
        'e57ec1e2e0421e303015b97266d4a2c502aeb0f9ed1ca05a8375ba295f650ddf', 1, 1),
}
FORCE_PICKUP_VISUALS = {
    'wbw_forceboost.cog': ('dark.3do', 'manaboost', 'pow_mana.cog',
        '3do/dark.3do', '83710448bde751d04df8b378c7de5f7ef56cd701054dfb72b405c03358561fc0',
        {'mat/00twinkle.mat': '2905c646dd2bf5020e5b0ca666dc43040045aaf7e645be34a6d05bf5a2ca2967'}),
    'wbw_forcesurge.cog': ('mana1.3do', 'darkside', 'pow_darkside.cog',
        '3do/mana1.3do', 'f62e393d4f391000118a33275071217cea3efb019f14992ecd1d9610fb684ed6',
        {'3do/mat/dark.mat': '6ac61efc7e39ca34d1485d528ae06acac556b45db213f8e58cc9dafc3cbbb5c1'}),
}


def native_force_pickup_rows(rows):
    """Independently substitute only each effective Force binding's model field."""
    inherited = {}; converted = {}; result = []
    for row in rows:
        values = {**inherited.get(row[1].lower(), {})}
        values.update(field.lower().split('=', 1) for field in row[2:] if '=' in field)
        inherited[row[0].lower()] = values
        copied = list(row)
        if values.get('cog') in FORCE_PICKUP_VISUALS:
            model = FORCE_PICKUP_VISUALS[values['cog']][0]
            positions = [i for i in range(2, len(row)) if row[i].lower().startswith('model3d=')]
            assert len(positions) <= 1, 'Independent duplicate Force model declaration'
            if positions:
                copied[positions[0]] = 'model3d=' + model
            else:
                copied.append('model3d=' + model)
        actual = dict(converted.get(copied[1].lower(), {}))
        actual.update(field.lower().split('=', 1) for field in copied[2:] if '=' in field)
        if values.get('cog') not in FORCE_PICKUP_VISUALS:
            assert actual.get('model3d') == values.get('model3d'), 'Independent non-Force inherited model changed: ' + row[0]
        converted[row[0].lower()] = actual
        result.append(copied)
    return result


def check_native_force_visual_resources(archives, generated, selected):
    """Check native visual pins and reject archive overrides of those resources."""
    if not selected:
        return []
    raw = archives['motsmp'].read('jkl/k1.jkl')
    assert hashlib.sha256(raw).hexdigest() == '6ff496d6aa2434fc392da0bf1a160e3f48b312cd54c3da677bf5669ff6cfb681', 'Independent native Force template world pin'
    rows = {row.split()[0].lower(): row.split() for row in bridge.records(bridge.text(raw), 'templates')}
    models = []
    for cog in sorted(selected):
        model, template, native_cog, path, digest, materials = FORCE_PICKUP_VISUALS[cog]
        fields = dict(token.lower().split('=', 1) for token in rows[template][2:] if '=' in token)
        assert fields.get('model3d') == model and fields.get('cog') == native_cog, 'Independent native Force visual template binding'
        for member, expected in {path: digest, **materials}.items():
            original = archives['motsres'].read(member)
            assert hashlib.sha256(original).hexdigest() == expected, 'Independent native Force visual source pin: ' + member
            overrides = [name for name in generated.entries if Path(name).name.lower() == Path(member).name.lower()]
            assert all(generated.read(name) == original for name in overrides), 'Independent native Force visual archive override: ' + member
        models.append(model)
    return models


def reconstruct_force_pickup(original, player_assignments, rank_limits):
    """Reconstruct owned native bytes without production transformation code."""
    value = original.decode('cp1252').replace('\r', '')
    for before, after, count in (
        ('symbols\n', 'symbols\n\nflex wbw_maximum local\n', 1),
        ('player = GetSourceRef();',
         'player = GetSourceRef();\n   call wbw_get_maximum;', player_assignments),
        ('GetInv(player, 20) * 50', 'wbw_maximum', rank_limits),
    ):
        pieces = value.split(before)
        assert len(pieces) == count + 1, 'Independent Force pickup anchor count: ' + before
        value = after.join(pieces)
    ends = list(re.finditer(r'\nend', value))
    assert ends and not value[ends[-1].end():].strip(), 'Independent Force pickup final terminator'
    insertion = ('\n\nwbw_get_maximum:\n'
                 '   wbw_maximum = GetInv(player, 20) * 50;\n'
                 '   if(IsMulti())\n'
                 '      wbw_maximum = GetInv(player, 69);\n'
                 '   Return;\n')
    return (value[:ends[-1].start()] + insertion + value[ends[-1].start():]).encode('cp1252')


def check_force_pickup_resources(archives, generated, runtime):
    """Check exact compatibility files, source pins and complete COG contents."""
    bindings = {name: converted for name, converted in FORCE_PICKUP_BINDINGS.items() if name in runtime}
    selected = set(bindings.values())
    present = {path for path in generated.entries if Path(path).name in FORCE_PICKUP_SOURCES}
    assert present == {'cog/' + name for name in selected}, 'Independent Force pickup member set'
    for name in selected:
        path, sha256, players, ranks = FORCE_PICKUP_SOURCES[name]
        original = archives['motsres'].read(path)
        assert hashlib.sha256(original).hexdigest() == sha256, 'Independent native Force pickup source pin: ' + path
        expected = reconstruct_force_pickup(original, players, ranks)
        assert generated.read('cog/' + name) == expected, 'Independent complete Force pickup source reconstruction: ' + name
    return bindings


def shared_force_surge_rows(rows):
    """Independently require one inherited COG instance for all Surge roots."""
    controller = 'wbw_surge_base'
    roots = [index for index, row in enumerate(rows)
             if 'cog=wbw_forcesurge.cog' in [field.lower() for field in row[2:]]]
    if not roots:
        return rows
    assert controller not in {row[0].lower() for row in rows}, 'Independent reserved Surge controller collision'
    parents = {rows[index][1] for index in roots}
    assert len(parents) == 1, 'Independent shared Surge original parent mismatch'
    result = []
    for index, row in enumerate(rows):
        if index == roots[0]:
            result.append([controller, next(iter(parents)), 'cog=wbw_forcesurge.cog'])
        if index in roots:
            assert sum(field.lower().startswith('cog=') for field in row[2:]) == 1, 'Independent duplicate Surge COG declaration'
            result.append([row[0], controller] + [field for field in row[2:]
                                                 if field.lower() != 'cog=wbw_forcesurge.cog'])
        else:
            result.append(row)
    return result


def check_force_pickup_templates(source_rows, output_rows, bindings, resource_names, template_map):
    """Require native Force models; preserve all other inherited template fields."""
    source = {row.split()[0].lower(): row.split() for row in source_rows}
    output = {row.split()[0].lower(): row.split() for row in output_rows}
    templates = {name: template_map.get(name, 'br_' + name) for name in source}
    effective = {}
    for name, row in source.items():
        fields = dict(effective.get(row[1].lower(), {}))
        fields.update(token.lower().split('=', 1) for token in row[2:] if '=' in token)
        effective[name] = fields
    affected = {name: fields for name, fields in effective.items() if fields.get('cog') in bindings}
    required = set(affected)
    for name in list(required):
        parent = source[name][1].lower()
        while parent in source:
            required.add(parent)
            parent = source[parent][1].lower()
    expected_rows = []
    for name in source:
        def renamed(match):
            original = match[1].lower()
            return resource_names.get(original, 'br_' + original)
        tokens = RESOURCE_LITERAL.sub(renamed, ' '.join(source[name])).split()
        tokens[0] = templates[name]
        tokens[1] = templates.get(tokens[1].lower(), tokens[1])
        for index, token in enumerate(tokens[2:], 2):
            if '=' in token:
                field, value = token.split('=', 1)
                tokens[index] = field + '=' + templates.get(value.lower(), value)
        expected_rows.append(tokens)
    expected_rows = shared_force_surge_rows(native_force_pickup_rows(expected_rows))
    expected = {row[0]: row for row in expected_rows}
    for name in required:
        assert output.get(templates[name]) == expected[templates[name]], 'Independent Force pickup template fields: ' + name
    if 'wbw_surge_base' in expected:
        assert output.get('wbw_surge_base') == expected['wbw_surge_base'], 'Independent shared Surge controller fields'
        ordered = [row.split()[0].lower() for row in output_rows]
        first_root = expected_rows[[row[0] for row in expected_rows].index('wbw_surge_base') + 1][0]
        assert ordered.count('wbw_surge_base') == 1, 'Independent shared Surge controller count'
        assert ordered.index('wbw_surge_base') + 1 == ordered.index(first_root), 'Independent shared Surge controller order'
    else:
        assert 'wbw_surge_base' not in output, 'Independent unexpected shared Surge controller'
    return affected


def check_force_pickup_script_indices(source_rows, output_rows, bindings):
    """Original preload indices must still resolve to the intended pickup COG."""
    output = {row.split()[0]: row.split()[1:] for row in output_rows}
    assert len(output) == len(output_rows), 'Independent duplicate script table index'
    for row in source_rows:
        index, name = row.split()
        if name.lower() in bindings:
            assert output.get(index) == [bindings[name.lower()]], 'Independent Force pickup script table index: ' + index


def check_cog_instance_capacity(source_world, output_world, native_rows):
    """Check the instance allocation budget separately from the script table."""
    def declared(value):
        headers = re.findall(r'^World cogs\s+(\d+)\s*$', value, re.M | re.I)
        assert len(headers) == 1, 'Independent unique COG capacity header'
        return int(headers[0])

    def explicit_bindings(rows):
        return sum(sum(token.lower().startswith('cog=') for token in row.split()) for row in rows)

    templates = bridge.records(output_world, 'templates')
    controller_count = sum(row.split()[0].lower() == 'wbw_surge_base' for row in templates)
    assert controller_count in (0, 1), 'Independent shared controller allocation count'
    original_capacity = declared(source_world)
    native_instances = explicit_bindings(native_rows)
    explicit_instances = (explicit_bindings(templates) + len(bridge.records(output_world, 'cogs'))
                          + explicit_bindings(bridge.records(output_world, 'things')))
    expected = max(original_capacity + native_instances + controller_count, explicit_instances)
    actual = declared(output_world)
    assert actual == expected, ('Independent COG instance capacity', actual, expected)
    return {'source_capacity': original_capacity, 'native_template_instances': native_instances,
            'shared_surge_instances': controller_count, 'explicit_instance_floor': explicit_instances,
            'output_capacity': actual}


def source_resource(archives, name, custom=None, *, is_ctf=False):
    """Find an exact source filename without using the converter's scanner."""
    order = (('jkctf',) if is_ctf else ()) + ('jkmp', 'jkres', 'jksnd', 'jksp')
    candidates = ([custom] if custom else []) + [
        archives[key] for key in order
        if key in archives]
    for archive in candidates:
        for path in archive.entries:
            if path.rsplit('/', 1)[-1].lower() == name.lower():
                return path, archive.read(path)
    raise AssertionError('Missing original resource: ' + name)


def source_cog(archives, name, custom=None, *, is_ctf=False):
    return bridge.text(source_resource(archives, name, custom, is_ctf=is_ctf)[1])


def source_graph_references(archives, world, runtime, requested, custom=None, *, is_ctf=False):
    """Trace one original dependency without consulting produced files/metadata."""
    def active_refs(value):
        active = '\n'.join(line.split('#', 1)[0].split('//', 1)[0] for line in value.splitlines())
        return {match[1].lower() for match in RESOURCE_LITERAL.finditer(active)}

    pending = sorted(active_refs(world))
    seen = set()
    for name in pending:
        if name in runtime or name in seen:
            continue
        seen.add(name)
        try:
            path, data = source_resource(archives, name, custom, is_ctf=is_ctf)
        except AssertionError:
            # Existing omission checks separately verify absent authored edges;
            # an absent edge cannot establish a copied material binding.
            continue
        if name == requested:
            return True
        if Path(path).suffix in TEXT_RESOURCES:
            pending.extend(sorted(active_refs(data.decode('cp1252').replace('\r', '')) - seen))
    return False


def cog_argument_symbols(value):
    symbols = segment(value, r'^\s*symbols\s*$', r'^\s*end\s*$')
    kinds = []
    for line in symbols.splitlines():
        line = line.split('#', 1)[0].split('//', 1)[0].strip()
        if not line:
            continue
        tokens = line.lower().split()
        if tokens[0] != 'message' and 'local' not in tokens:
            kinds.append((tokens[0], tokens[1].split('=')[0]))
    return kinds


def cog_argument_types(value):
    return [kind for kind, _ in cog_argument_symbols(value)]


def expected_argument(value, kind, *, resources=None, templates=None):
    # Numeric indices, vectors, masks, timing and other gameplay parameters must
    # remain exact. Resource and template symbols alone gain a namespace.
    if value == '-1':
        return value
    if kind == 'template':
        return (templates or {}).get(value.lower(), 'br_' + value.lower())
    if kind in {'sound', 'material', 'model', 'keyframe', 'cog', 'aiclass'}:
        if re.search(r'\.(wav|mat|3do|key|cog|ai)$', value, re.I):
            return (resources or {}).get(value.lower(), 'br_' + value.lower())
    return value


def check_source_omissions(archives, generated, custom, spec, source_world, output_world, resource_names):
    """Check each original absent edge without trusting a generated manifest."""
    def contains_reference(data, name):
        value = '\n'.join(line.split('#', 1)[0].split('//', 1)[0] for line in bridge.text(data).splitlines())
        return re.search(r'(?<![\w.&~+\-])' + re.escape(name) + r'(?![\w.&~+\-])', value, re.I) is not None

    native = [archives[k] for k in ('motsmp', 'motsres', 'motssnd') if k in archives]
    available = {Path(path).name for archive in [generated] + native for path in archive.entries}
    for rule in spec.get('source_omissions', []):
        name, referrer = rule['name'], rule['referrer']
        path, original = source_resource(archives, Path(referrer).name, custom)
        assert path == referrer and hashlib.sha256(original).hexdigest() == rule['referrer_sha256'], 'Original omission referrer hash'
        assert contains_reference(original, name), 'Original omission reference is absent: ' + name
        try:
            source_resource(archives, name, custom)
        except AssertionError:
            pass
        else:
            raise AssertionError('Reviewed original omission unexpectedly exists: ' + name)
        renamed = resource_names.get(name, 'br_' + name)
        target = (output_world if referrer == source_world else
                  referrer.rsplit('/', 1)[0] + '/' + resource_names.get(Path(referrer).name, 'br_' + Path(referrer).name))
        assert renamed not in available, 'Reviewed output omission unexpectedly exists: ' + renamed
        assert contains_reference(generated.read(target), renamed), ('Missing preserved omission edge', target, renamed)


def segment(value, start, stop):
    a = re.search(start, value, re.M | re.I)
    b = re.search(stop, value[a.end():], re.M | re.I)
    return value[a.end():a.end() + b.start()]


def numeric_rows(value):
    return [line.split() for line in value.splitlines()
            if re.match(r'^\s*\d+:', line)]


# Deliberately separate from bridge.references and its transformation helpers.
RESOURCE_LITERAL = re.compile(r'(?<![\w.~&])([\w+.~&-]+\.(?:mat|cmp|3do|key|pup|snd|cog|wav|spr|par|ai))(?![\w.~&])', re.I)
TEXT_RESOURCES = {'.jkl', '.3do', '.pup', '.snd', '.cog', '.spr', '.par', '.ai'}


def rename_resource_literals(value, names):
    return RESOURCE_LITERAL.sub(lambda match: names.get(match[1].lower(), match[1]), value)


def counted_source_edits(value, edits):
    """Reconstruct exact edited bytes without calling the production editor."""
    for edit in edits:
        assert edit.get('reason') and edit.get('old') and type(edit.get('count')) is int and edit['count'] > 0, 'Unreviewed exact edit'
        pieces = value.split(edit['old'])
        assert len(pieces) - 1 == edit['count'], 'Independent exact edit occurrence count'
        value = edit['new'].join(pieces)
    return value


def community_source_graph(archives, custom, spec, old, runtime_names):
    """Independently enumerate literal source edges, including absent edges."""
    def refs(value):
        active = '\n'.join(line.split('#', 1)[0].split('//', 1)[0] for line in value.splitlines())
        return {match[1].lower() for match in RESOURCE_LITERAL.finditer(active)}

    names = dict(runtime_names)
    pending = [(spec['world'], name) for name in sorted(refs(old))]
    pending += [(spec['world'], Path(rule['source_path']).name) for rule in spec.get('native_resource_overrides', {}).values()]
    graph = {}
    environment = spec['environment'].split() if isinstance(spec['environment'], str) else spec['environment']
    for referrer, name in pending:
        if name in runtime_names:
            continue
        try:
            path, data = source_resource(archives, name, custom)
        except AssertionError:
            rules = [rule for rule in spec.get('source_omissions', []) if rule['name'] == name and rule['referrer'] == referrer]
            assert len(rules) == 1, ('Independent unreviewed missing source edge', referrer, name)
            names[name] = spec.get('resource_aliases', {}).get(name, 'br_' + name)
            continue
        if name in graph:
            continue
        assert not name.endswith('.cog') or name in environment, 'Independent unreviewed environmental COG: ' + name
        names[name] = spec.get('resource_aliases', {}).get(name, 'br_' + name)
        graph[name] = (path, data)
        if Path(name).suffix in TEXT_RESOURCES:
            pending.extend((path, child) for child in sorted(refs(data.decode('cp1252').replace('\r', ''))))
    return names, graph


def check_community_resources(generated, spec, graph, names, templates):
    """Check complete code/text reconstruction and untouched binary payloads."""
    used_edits = set()
    for name, (path, data) in graph.items():
        if Path(name).suffix in TEXT_RESOURCES:
            value = data.decode('cp1252').replace('\r', '')
            edits = spec.get('cog_edits', {}).get(name, [])
            if edits:
                used_edits.add(name)
            value = rename_resource_literals(counted_source_edits(value, edits), names)
            if name.endswith('.cog'):
                # The entire source is compared, so code, flags, comments and
                # unedited spacing cannot silently change with a passing test.
                lines = []
                for line in value.splitlines(keepends=True):
                    match = re.match(r'(\s*template\s+\w+\s*=\s*)(\S+)', line, re.I)
                    if match and match[2].lower() in templates:
                        line = line[:match.start(2)] + templates[match[2].lower()] + line[match.end(2):]
                    lines.append(line)
                value = ''.join(lines)
            expected = value.encode('cp1252')
        else:
            expected = data
        target = path.rsplit('/', 1)[0] + '/' + names[name]
        assert generated.read(target) == expected, 'Independent complete source reconstruction: ' + target
    assert used_edits == set(spec.get('cog_edits', {})), 'Unused reviewed source edits'


def check_community_templates(source_rows, native_rows, output_rows, spec, names, templates):
    """Native parent/other fields and all authored templates remain exact."""
    source = {row.split()[0].lower(): row for row in source_rows}
    native = {row.split()[0].lower(): row for row in native_rows}
    rules = spec.get('native_template_overrides', {})
    assert set(rules) <= set(native), 'Unknown native template override'
    expected_rows = []
    for row in native_rows:
        tokens = row.split()
        rule = rules.get(tokens[0].lower())
        if rule:
            assert rule.get('reason') and rule.get('fields'), 'Unreviewed native template fields'
            original = source[rule.get('source_template', tokens[0].lower())].split()
            for field in rule['fields']:
                selected = [token.split('=', 1)[1] for token in original[2:] if token.lower().startswith(field.lower() + '=')]
                assert len(selected) == 1, 'Ambiguous authored template field'
                value = names.get(selected[0].lower(), selected[0])
                positions = [i for i, token in enumerate(tokens[2:], 2) if token.lower().startswith(field.lower() + '=')]
                assert len(positions) <= 1, 'Duplicate native template field'
                replacement = field + '=' + value
                if positions:
                    tokens[positions[0]] = replacement
                else:
                    tokens.append(replacement)
        expected_rows.append(tokens)
    for row in source_rows:
        tokens = rename_resource_literals(row, names).split()
        tokens[0] = templates[tokens[0].lower()]
        tokens[1] = templates.get(tokens[1].lower(), tokens[1])
        for index in range(2, len(tokens)):
            if '=' in tokens[index]:
                field, value = tokens[index].split('=', 1)
                tokens[index] = field + '=' + templates.get(value.lower(), value)
        expected_rows.append(tokens)
    expected_rows = shared_force_surge_rows(native_force_pickup_rows(expected_rows))
    assert expected_rows == [row.split() for row in output_rows], 'Independent native and authored template fields, parents and order'


def check_community_startup(archives, generated, custom, spec, names, directory):
    """Verify required startup files from original bytes, never a manifest."""
    expected = {}
    for name, rule in spec.get('native_cog_edits', {}).items():
        found = [(path, archive) for key in ('motsmp', 'motsres', 'motssnd')
                 for archive in [archives[key]] for path in archive.entries if Path(path).name == name]
        assert found, 'Missing original native startup COG'
        path, archive = found[0]
        original = archive.read(path)
        assert hashlib.sha256(original).hexdigest() == rule['sha256'], 'Native startup COG source pin'
        expected[path] = counted_source_edits(original.decode('cp1252').replace('\r', ''), rule['edits']).encode('cp1252')
    for requested_path, rule in spec.get('native_text_edits', {}).items():
        found = [(path, archive) for key in ('motsmp', 'motsres', 'motssnd')
                 for archive in [archives[key]] for path in archive.entries if Path(path).name == Path(requested_path).name]
        assert found, 'Missing original native startup text asset'
        path, archive = found[0]
        original = archive.read(path)
        assert path == requested_path and hashlib.sha256(original).hexdigest() == rule['sha256'], 'Native startup text source pin'
        assert path not in expected, 'Duplicate native startup override'
        expected[path] = counted_source_edits(original.decode('cp1252').replace('\r', ''), rule['edits']).encode('cp1252')
    for path, rule in spec.get('native_resource_overrides', {}).items():
        source_path, original = source_resource(archives, Path(rule['source_path']).name, custom)
        assert source_path == rule['source_path'] and rule.get('reason') and hashlib.sha256(original).hexdigest() == rule['sha256'], 'Native resource source pin'
        expected[path] = rename_resource_literals(original.decode('cp1252').replace('\r', ''), names).encode('cp1252')
    if spec.get('native_resource_overrides'):
        for path in generated.entries:
            if not path.endswith('.jkl') and path not in {'episode.jk', 'misc/cogstrings.uni'}:
                expected.setdefault(path, generated.read(path))
    if not expected:
        return None
    assert directory is not None, 'Required community startup directory was not supplied'
    directory = Path(directory)
    filename = 'bridge-' + spec['tag'] + '-startup.goo'
    assert directory.is_dir(), 'Required startup folder is missing or has extra files'
    target = resolve_output(directory, filename, spec.get('key', spec['tag']), role='startup')
    assert {path.name for path in directory.iterdir()} == {target.name, 'README.txt'}, 'Required startup folder is missing or has extra files'
    original_startup = Gob.open(target)
    startup, marker = game_payload(original_startup, spec.get('key', spec['tag']), role='startup')
    assert set(startup.entries) == set(expected), 'Independent startup archive member set'
    for path, data in expected.items():
        assert startup.read(path) == data, 'Independent exact startup source reconstruction: ' + path
    assert startup.data == build_gob(expected), 'Independent deterministic startup archive bytes'
    return tracked_result({'sha256': startup.sha256, 'member_count': len(expected),
            'passed': ['complete startup code/model source reconstruction and exact member set',
                       'required isolated startup folder and deterministic archive bytes'],
            'runtime': 'Startup loading and gameplay are not executed by this verifier'},
            original_startup, startup, marker)


def check_ctf_startup(archives, directory, *, recipe_id=None):
    """Independently verify the mandatory early-loaded CTF inventory overlay."""
    allowed = {recipe_id} if recipe_id is not None else {'ctf-duel', 'ctf-arena', 'ctf-challenge'}
    assert allowed <= {'ctf-duel', 'ctf-arena', 'ctf-challenge'}, 'Select a CTF recipe for its startup overlay'
    directory = Path(directory)
    target = resolve_output(directory, 'bridge-ctf-ui.goo', allowed, role='startup')
    assert len([path for path in directory.iterdir() if path.suffix.lower() == '.goo']) == 1, 'Ambiguous extra GOO in CTF startup folder'
    original = Gob.open(target)
    generated, marker = game_payload(original, allowed, role='startup')
    assert set(generated.entries) == {'misc/items.dat'}, 'Unexpected startup overlay member'
    lines = bridge.text(archives['motsres'].read('misc/items.dat')).splitlines(keepends=True)
    matches = 0
    for index, line in enumerate(lines):
        tokens = line.split()
        if len(tokens) >= 5 and tokens[1] == '81':
            assert tokens == ['ysalamiri', '81', '0', '1', '0x048'], 'Unexpected original descriptor81'
            lines[index] = line.replace('ysalamiri', 'redflag', 1)
            matches += 1
    assert matches == 1
    assert generated.read('misc/items.dat') == ''.join(lines).encode('cp1252'), 'Startup overlay changed unrelated native descriptors'
    return tracked_result({'sha256': generated.sha256, 'passed': ['only misc/items.dat is present in the game payload',
            'only descriptor81 name changes; all native flags, ranges, COGs and other descriptors unchanged'],
            'required_launch_arguments': ['-motsCompat', '-path', 'bridge-ctf-ui'],
            'runtime': 'Packaging verified here; actual startup descriptor loading requires runtime observation'},
            original, generated, marker)


def check(archives, generated, *, dojo=None, caesars=None, stock_map='valley', community=None, community_key=None, community_startup=None, community_spec=None):
    assert sum(value is not None for value in (dojo, caesars, community)) <= 1, 'Select one custom map'
    assert (community is None) == (community_key is None and community_spec is None), 'Supply the archive and one reviewed world specification'
    assert not any(value is not None for value in (dojo, caesars, community)) or stock_map == 'valley', 'Custom and stock selections cannot be combined'
    spec = custom_registry.reviewed_world(community_key, community_spec) if community is not None else {}
    selected_recipe = (spec['key'] if community is not None else 'caesars' if caesars is not None
                       else 'dojo' if dojo is not None else stock_map)
    original_generated = generated
    generated, tracking = game_payload(generated, selected_recipe)
    custom = caesars if caesars else dojo if dojo else community
    custom_tag = spec['tag'] if community is not None else 'caesars' if caesars else 'dojo'
    archive_key, stock_source, target_name = STOCK_WORLDS[stock_map]
    source_world = spec['world'] if community is not None else 'jkl/' + custom_tag + '.jkl' if custom else stock_source
    output_world = 'jkl/br_' + custom_tag + '.jkl' if custom else f'jkl/{target_name}.jkl'
    original_bytes = custom.read(source_world) if custom else archives[archive_key].read(source_world)
    if community is not None:
        assert custom.sha256 == spec['gob_sha256'] and hashlib.sha256(original_bytes).hexdigest() == spec['sha256'], 'Community original hashes'
    old = bridge.text(original_bytes)
    new = bridge.text(generated.read(output_world))
    is_ctf = stock_map.startswith('ctf-') and custom is None
    resource_names = dict(spec.get('resource_aliases', {}))
    if caesars:
        resource_names['00_sectorliteanimflicker2.cog'] = 'br_sectorliteanimflicker2.cog'
    original_scripts = {row.split(None, 1)[1].lower() for row in bridge.records(old, 'scripts')}
    runtime = spec.get('runtime_cogs', {name for name in original_scripts if name.startswith('pow_') or name in
                                      {'kyle.cog', 'class_sequencer.cog', '00_smoketrail.cog', '00_desttrail.cog'}})
    runtime = set(runtime.split()) if isinstance(runtime, str) else set(runtime)
    native_names = {Path(path).name for key in ('motsmp', 'motsres', 'motssnd') for path in archives[key].entries}
    pickup_bindings = {name: target for name, target in FORCE_PICKUP_BINDINGS.items() if name in runtime}
    for name in runtime:
        if name in pickup_bindings:
            resource_names[name] = pickup_bindings[name]
            continue
        alternate = name[:-4] + '_m.cog'
        selected = alternate if alternate in native_names else name
        assert selected in native_names, 'Missing native runtime COG: ' + selected
        resource_names[name] = selected
    template_map = dict(spec.get('template_aliases', {}))
    source_templates = {row.split()[0].lower() for row in bridge.records(old, 'templates')}
    if community is not None:
        script_hash = hashlib.sha256('\n'.join(sorted(original_scripts)).encode()).hexdigest()
        assert script_hash == spec['scripts_sha256'], 'Independent original script set pin'
        for name, expected_hash in spec.get('cog_sha256', {}).items():
            assert hashlib.sha256(source_resource(archives, name, custom)[1]).hexdigest() == expected_hash, 'Independent original COG pin: ' + name
        template_map = {name: template_map.get(name, 'br_' + name) for name in source_templates}
        runtime_names = {name: resource_names[name] for name in runtime}
        resource_names, community_graph = community_source_graph(archives, custom, spec, old, runtime_names)
    check_force_pickup_resources(archives, generated, runtime)
    native_force_models = check_native_force_visual_resources(archives, generated, set(pickup_bindings.values()))
    model_preloads = {row.split()[1].lower() for row in bridge.records(new, 'models')}
    assert set(native_force_models) <= model_preloads, 'Independent native Force model preloads'
    omitted_cogs = {rule['name'] for rule in spec.get('source_omissions', []) if rule['name'].endswith('.cog')}
    verified = []
    for start, stop, label in (
        (r'^World vertices\b[^\n]*', r'^World texture vertices\b', 'vertex positions and indices'),
        (r'^World texture vertices\b[^\n]*', r'^World adjoins\b', 'texture vertices and indices'),
        (r'^World adjoins\b[^\n]*', r'^World surfaces\b', 'adjoin records'),
        (r'^Section:\s*sectors\b[^\n]*', r'^Section:', 'sector boundaries and parameters'),
    ):
        expected = segment(old, start, stop)
        if label.startswith('sector'):
            expected = re.sub(r'(^SOUND\s+)([^\s]+\.wav)',
                              lambda m: m.group(1) + resource_names.get(m.group(2).lower(), 'br_' + m.group(2).lower()),
                              expected, flags=re.M | re.I)
        assert expected == segment(new, start, stop), label
        verified.append(label)
    a = numeric_rows(segment(old, r'^World surfaces\b[^\n]*', r'^World sectors\b'))
    b = numeric_rows(segment(new, r'^World surfaces\b[^\n]*', r'^World sectors\b'))
    # The region includes the separate normals array after the surface array.
    count = int(re.search(r'^World surfaces\s+(\d+)', old, re.I | re.M).group(1))
    assert len(a) == len(b)
    for left, right in zip(a[:count], b[:count]):
        n = int(left[9]); prefix = 10 + n
        assert left[:prefix] == right[:prefix]
        assert right[prefix:] == [x for val in left[prefix:] for x in [val] * 4]
    assert a[count:] == b[count:]
    verified.append('all surface topology, flags, UV references, normals and exact replicated light values')
    a = [line.split() for line in bridge.records(old, 'things')]
    b = [line.split() for line in bridge.records(new, 'things')]
    assert len(a) == len(b)
    for left, right in zip(a, b):
        assert right[0] == left[0] and right[2:10] == left[2:10]
        assert right[10] == '-1' and right[11:] == left[10:]
        assert right[1] == ('walkplayer' if left[1].lower() == 'walkplayer' else template_map.get(left[1].lower(), 'br_' + left[1].lower()))
    verified.append('all scene object indices, names, coordinates, rotations, sectors, frames and flags')
    a = [line.split() for line in bridge.records(old, 'cogs')]
    b = [line.split() for line in bridge.records(new, 'cogs')]
    assert len(a) == len(b)
    used_missing_templates = set()
    missing_templates = spec.get('missing_template_arguments', [])
    for left, right in zip(a, b):
        if caesars and left[1].lower() == 'riverthrust.cog':
            assert left[0] == '56:' and len(left) == 52
            assert [left[0], 'br_riverthrust.cog', *left[2:]] == right
            continue
        if left[1].lower() in omitted_cogs:
            expected = [left[0], resource_names.get(left[1].lower(), 'br_' + left[1].lower()), *left[2:]]
            assert [x.lower() for x in expected] == [x.lower() for x in right], 'Original missing COG placement'
            continue
        symbols = cog_argument_symbols(source_cog(archives, left[1], custom, is_ctf=is_ctf))
        assert len(left) - 2 <= len(symbols), ('COG argument count', left[0], left[1])
        for value, (kind, symbol) in zip(left[2:], symbols):
            if kind == 'template' and value != '-1' and value.lower() not in source_templates:
                matches = [i for i, rule in enumerate(missing_templates) if rule['row'] == left[0]
                           and rule['cog'].lower() == left[1].lower() and rule['symbol'].lower() == symbol
                           and rule['name'].lower() == value.lower() and rule.get('reason')]
                assert len(matches) == 1, ('Unreviewed missing template argument', left[0], symbol, value)
                used_missing_templates.add(matches[0])
        cog_name = resource_names.get(left[1].lower(), 'br_' + left[1].lower())
        expected = [left[0], cog_name] + [
            expected_argument(value, kind, resources=resource_names, templates=template_map) for value, (kind, _) in zip(left[2:], symbols)]
        assert [x.lower() for x in expected] == [x.lower() for x in right]
    assert used_missing_templates == set(range(len(missing_templates))), 'Unused missing template rule'
    verified.append('all environmental COG arguments, with resource and template namespaces checked by declared symbol type')
    template_names = [line.split()[0].lower() for line in bridge.records(new, 'templates')]
    assert len(template_names) == len(set(template_names))
    assert all('br_' + rule['name'].lower() not in template_names for rule in missing_templates), 'Original missing template unexpectedly supplied'
    known = {'none'}
    for row in bridge.records(new, 'templates'):
        name, parent, *_ = row.lower().split()
        assert parent in known, (name, parent)
        known.add(name)
    verified.append('unique template names and ordered inheritance')
    affected_pickups = check_force_pickup_templates(bridge.records(old, 'templates'),
        bridge.records(new, 'templates'), pickup_bindings, resource_names, template_map)
    check_force_pickup_script_indices(bridge.records(old, 'scripts'), bridge.records(new, 'scripts'), pickup_bindings)
    native_template_count = len(bridge.records(bridge.text(archives['motsmp'].read('jkl/k1.jkl')), 'templates'))
    cog_capacity = check_cog_instance_capacity(old, new, bridge.records(new, 'templates')[:native_template_count])
    verified.append('independent COG instance capacity, preserving source budget and covering added template/placed-object allocations')
    for model in {fields['model3d'] for fields in affected_pickups.values() if 'model3d' in fields}:
        path, original = source_resource(archives, model, custom, is_ctf=is_ctf)
        expected = RESOURCE_LITERAL.sub(lambda match: resource_names.get(match[1].lower(), 'br_' + match[1].lower()),
                                        original.decode('cp1252').replace('\r', '')).encode('cp1252')
        target = path.rsplit('/', 1)[0] + '/' + resource_names.get(model, 'br_' + model)
        assert generated.read(target) == expected, 'Independent unchanged Force pickup model: ' + model
    if pickup_bindings:
        verified.append('independent complete Force pickup COG reconstruction, native MotS model/material pins, expected visual replacement and all other inherited fields')
    if community is not None:
        check_source_omissions(archives, generated, custom, spec, source_world, output_world, resource_names)
        verified.append('exact original omission edges, referrer hashes and continued namespaced absence')
        check_community_resources(generated, spec, community_graph, resource_names, template_map)
        verified.append('independent complete source resource reconstruction, counted code edits and untouched script segments')
        check_community_templates(bridge.records(old, 'templates'),
                                  bridge.records(bridge.text(archives['motsmp'].read('jkl/k1.jkl')), 'templates'),
                                  bridge.records(new, 'templates'), spec, resource_names, template_map)
        verified.append('independent native template overrides, preserved parents/unrelated fields and complete authored templates')
        episode = bridge.text(generated.read('episode.jk'))
        assert re.search(r'^TYPE\s+' + str(spec.get('episode_type', 2)) + r'\s*$', episode, re.M)
        assert re.search(r'^SEQ\s+1\s*$', episode, re.M)
        assert Path(output_world).name in episode
        verified.append('community episode type and selected output world')
        startup_result = check_community_startup(archives, generated, custom, spec, resource_names, community_startup)
        if startup_result:
            verified.append('required community startup archive independently reconstructed from pinned source bytes')
    first, manifest = bridge.recipe(archives, dojo=dojo, caesars=caesars, stock_map=stock_map, community=community, community_key=community_key, community_spec=community_spec)
    second, _ = bridge.recipe(archives, dojo=dojo, caesars=caesars, stock_map=stock_map, community=community, community_key=community_key, community_spec=community_spec)
    assert first == second == generated.data
    verified.append('two repeat builds byte-identical to the verified game payload' if tracking is not None
                    else 'two repeat builds byte-identical to delivered archive')
    for item in manifest['source_resource_graph']:
        path = item['source_path'].rsplit('/', 1)[0] + '/' + item['output_name']
        if not any(path.endswith(ext) for ext in bridge.TEXT_EXTENSIONS):
            assert hashlib.sha256(generated.read(path)).hexdigest() == item['source_sha256']
    verified.append('all binary resources byte-identical to hash-pinned JK source payloads')
    result = {'passed': verified, 'sha256': generated.sha256,
            'surface_count': count, 'placed_thing_count': len(bridge.records(new, 'things')),
            'resource_count': len(generated.entries), 'runtime': 'not executed by this verifier'}
    result['cog_instance_capacity'] = cog_capacity
    if pickup_bindings:
        counts = {name: 0 for name in pickup_bindings}
        for row in bridge.records(old, 'things'):
            fields = affected_pickups.get(row.split()[1].lower(), {})
            if fields.get('cog') in counts:
                counts[fields['cog']] += 1
        result['force_pickups'] = {'bindings': pickup_bindings, 'original_placements_preserved': counts,
                                  'native_visual_models': native_force_models}
    if community is not None and startup_result:
        result['community_startup'] = startup_result
    return tracked_result(result, original_generated, generated, tracking)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baselines')
    parser.add_argument('--jk-root')
    parser.add_argument('--mots-root')
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--archive')
    selection.add_argument('--all-stock-dir', type=Path,
                           help='Verify all nine stock outputs in this directory')
    custom_args = parser.add_mutually_exclusive_group()
    custom_args.add_argument('--dojo-archive', help='Original Jedi Dojo ZIP or GOB when verifying that recipe')
    custom_args.add_argument('--caesars-archive', help='Original Caesar ZIP or GOB when verifying that recipe')
    custom_args.add_argument('--community-archive', help='Original reviewed community ZIP or GOB')
    parser.add_argument('--community-key', help='Reviewed community recipe key, tag, or exact title')
    parser.add_argument('--community-startup', type=Path,
                        help='Required community startup folder; defaults to the recipe-specific sibling folder')
    parser.add_argument('--stock-map', choices=tuple(STOCK_WORLDS), default='valley')
    parser.add_argument('--ctf-startup', type=Path,
                        help='CTF startup directory; defaults to bridge-ctf-ui beside the episode(s)')
    args = parser.parse_args()
    if bool(args.community_archive) != bool(args.community_key):
        parser.error('--community-archive and --community-key are required together')
    if args.all_stock_dir and (args.dojo_archive or args.caesars_archive or args.community_archive):
        parser.error('Custom level archives cannot be combined with --all-stock-dir')
    if args.stock_map != 'valley' and (args.dojo_archive or args.caesars_archive or args.community_archive):
        parser.error('Custom level archives cannot be combined with --stock-map')
    community_key = custom_registry.select(args.community_key) if args.community_key else None
    community_spec = custom_registry.entries()[community_key] if community_key else {}
    archives = bridge.pinned_archives(args.baselines, jk_root=args.jk_root, mots_root=args.mots_root,
                                      include_jksp=bool(args.all_stock_dir) or args.stock_map == 'battleground' or community_spec.get('requires_jksp', False),
                                      include_jkctf=bool(args.all_stock_dir) or args.stock_map.startswith('ctf-'))
    if args.all_stock_dir:
        result = {}
        for key, (_, _, target_name) in STOCK_WORLDS.items():
            filename = 'bridge-' + target_name.removeprefix('br_') + ('-v2.goo' if key == 'valley' else '-v1.goo')
            target = resolve_output(args.all_stock_dir, filename, key)
            result[key] = check(archives, Gob.open(target), stock_map=key)
        result['_ctf_startup'] = check_ctf_startup(archives, args.ctf_startup or args.all_stock_dir / 'bridge-ctf-ui')
    else:
        result = check(archives, Gob.open(args.archive),
                       dojo=bridge.open_dojo(args.dojo_archive) if args.dojo_archive else None,
                       caesars=bridge.open_caesars(args.caesars_archive) if args.caesars_archive else None,
                       community=custom_registry.open_original(args.community_archive, community_key) if community_key else None,
                       community_key=community_key,
                       community_startup=(args.community_startup or Path(args.archive).parent / ('bridge-' + community_spec['tag'] + '-startup')) if community_key else None,
                       stock_map=args.stock_map)
        if args.stock_map.startswith('ctf-'):
            result['ctf_startup'] = check_ctf_startup(archives, args.ctf_startup or Path(args.archive).parent / 'bridge-ctf-ui',
                                                    recipe_id=args.stock_map)
    print(json.dumps(result, indent=2))

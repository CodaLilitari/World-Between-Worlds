"""Independent scene invariants and repeat-build checks against user-owned inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import re

import bridge
import custom_registry
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
    assert directory.is_dir() and {path.name for path in directory.iterdir()} == {filename, 'README.txt'}, 'Required startup folder is missing or has extra files'
    startup = Gob.open(directory / filename)
    assert set(startup.entries) == set(expected), 'Independent startup archive member set'
    for path, data in expected.items():
        assert startup.read(path) == data, 'Independent exact startup source reconstruction: ' + path
    assert startup.data == build_gob(expected), 'Independent deterministic startup archive bytes'
    return {'sha256': startup.sha256, 'member_count': len(expected),
            'passed': ['complete startup code/model source reconstruction and exact member set',
                       'required isolated startup folder and deterministic archive bytes'],
            'runtime': 'Startup loading and gameplay are not executed by this verifier'}


def check_ctf_startup(archives, directory):
    """Independently verify the mandatory early-loaded CTF inventory overlay."""
    generated = Gob.open(Path(directory) / 'bridge-ctf-ui.goo')
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
    return {'sha256': generated.sha256, 'passed': ['only misc/items.dat is present',
            'only descriptor81 name changes; all native flags, ranges, COGs and other descriptors unchanged'],
            'required_launch_arguments': ['-motsCompat', '-path', 'bridge-ctf-ui'],
            'runtime': 'Packaging verified here; actual startup descriptor loading requires runtime observation'}


def check(archives, generated, *, dojo=None, caesars=None, stock_map='valley', community=None, community_key=None, community_startup=None):
    assert sum(value is not None for value in (dojo, caesars, community)) <= 1, 'Select one custom map'
    assert (community is None) == (community_key is None), 'Supply both community archive and key'
    assert not any(value is not None for value in (dojo, caesars, community)) or stock_map == 'valley', 'Custom and stock selections cannot be combined'
    spec = custom_registry.entries()[custom_registry.select(community_key)] if community is not None else {}
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
    for name in runtime:
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
    first, manifest = bridge.recipe(archives, dojo=dojo, caesars=caesars, stock_map=stock_map, community=community, community_key=community_key)
    second, _ = bridge.recipe(archives, dojo=dojo, caesars=caesars, stock_map=stock_map, community=community, community_key=community_key)
    assert first == second == generated.data
    verified.append('two repeat builds byte-identical to delivered archive')
    for item in manifest['source_resource_graph']:
        path = item['source_path'].rsplit('/', 1)[0] + '/' + item['output_name']
        if not any(path.endswith(ext) for ext in bridge.TEXT_EXTENSIONS):
            assert hashlib.sha256(generated.read(path)).hexdigest() == item['source_sha256']
    verified.append('all binary resources byte-identical to hash-pinned JK source payloads')
    result = {'passed': verified, 'sha256': generated.sha256,
            'surface_count': count, 'placed_thing_count': len(bridge.records(new, 'things')),
            'resource_count': len(generated.entries), 'runtime': 'not executed by this verifier'}
    if community is not None and startup_result:
        result['community_startup'] = startup_result
    return result


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
            result[key] = check(archives, Gob.open(args.all_stock_dir / filename), stock_map=key)
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
            result['ctf_startup'] = check_ctf_startup(archives, args.ctf_startup or Path(args.archive).parent / 'bridge-ctf-ui')
    print(json.dumps(result, indent=2))

"""Reviewed multiplayer packs: complete episode graphs and exact resource unions.

Original assets are read only from hash-pinned local downloads. Individual worlds
are independently verified before they share one episode archive. A conflicting
full virtual path is a review failure, never an implicit overwrite.
"""
import copy
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import zipfile

import bridge
import mp_pack_catalog
import verify_retail
from gob import Gob, build_gob, resource_name


class PackError(ValueError):
    pass


METADATA = frozenset({'episode.jk', 'misc/cogstrings.uni'})
ROW = re.compile(r'^(\d+):\s+(\d+)\s+(\d+)\s+(LEVEL)\s+(\S+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s*$', re.I)


def require(condition, message):
    if not condition:
        raise PackError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def recipe_details(recipe_id):
    require(recipe_id in mp_pack_catalog.PACKS, 'Unknown reviewed multiplayer pack')
    spec = copy.deepcopy(mp_pack_catalog.PACKS[recipe_id])
    spec['key'] = recipe_id
    for key, world in spec['world_specs'].items():
        world['key'] = recipe_id + '-' + key
    return spec


def original_hashes(recipe_id):
    return {recipe_details(recipe_id)['zip_sha256']}


def catalog_entries():
    return [dict(id=key, title=spec['title'], author=spec['author'], kind='custom',
                 gameplay=['mp'], requires_archive=True, archive_hint='Original Massassi ZIP',
                 source_url=spec['source_url'], download_url=spec['download_url'],
                 status=spec.get('catalog_status', 'prototype'), startup_overlay=None,
                 output_filename='bridge-' + spec['tag'] + '-pack-v1.goo',
                 legacy_filenames=['bridge-' + spec['tag'] + '-pack-v1.goo'],
                 runtime_test=copy.deepcopy(spec['runtime_test']),
                 summary=f"Complete reviewed {len(spec['world_specs'])}-world pack; original episode order and locally extracted dependencies preserved.")
            for key, spec in mp_pack_catalog.PACKS.items()]


def read_original(path, spec):
    path = Path(path)
    require(path.stat().st_size <= 500_000_000, 'Original pack exceeds the reviewed loader limit')
    data = path.read_bytes()
    require(digest(data) == spec['zip_sha256'], 'Select the exact reviewed original ZIP')
    members = {}
    expected = {resource_name(item['path']): item for item in
                next(iter(spec['world_specs'].values()))['readme_provenance']}
    gob_name = resource_name(spec['gob_member'])
    with zipfile.ZipFile(BytesIO(data)) as archive:
        names = set()
        for item in archive.infolist():
            name = resource_name(item.filename.rstrip('/') if item.is_dir() else item.filename)
            if item.is_dir():
                continue
            require(name not in names, 'Duplicate normalized ZIP member')
            names.add(name)
            require(item.file_size <= 500_000_000, 'Oversized original pack member')
            if name == gob_name or name in expected:
                members[name] = archive.read(item)
        require(gob_name in members, 'Missing reviewed original GOB')
    source = Gob(members[gob_name], spec['gob_member'])
    require(source.sha256 == spec['gob_sha256'], 'Original GOB differs from reviewed source')
    for name, item in expected.items():
        require(name in members and len(members[name]) == item['bytes'] and
                digest(members[name]) == item['sha256'], 'Original README differs: ' + name)
    return source, {name: members[name] for name in sorted(expected)}


def episode_rows(data):
    result = []
    for line in data.decode('cp1252').splitlines():
        line = line.split('#', 1)[0].strip()
        if not line or not re.match(r'^\d+:', line):
            continue
        match = ROW.fullmatch(line)
        require(match is not None, 'Unreviewed episode row syntax or non-level transition')
        values = match.groups()
        result.append(dict(line=int(values[0]), disc=int(values[1]), level=int(values[2]),
                           type=values[3].upper(), world=resource_name('jkl/' + values[4]),
                           lightpow=int(values[5]), darkpow=int(values[6]),
                           goto_a=int(values[7]), goto_b=int(values[8])))
    return result


def reviewed_episode(original, spec):
    """Repair only a pinned, unreferenced later duplicate row identifier.

    Episode line identifiers are branch targets, separate from level numbers.
    Renaming a referenced identifier could change which world a branch reaches;
    that case requires a different review and is deliberately rejected here.
    """
    require(digest(original) == spec['episode_sha256'], 'Original episode graph differs')
    expected = [{key: value for key, value in row.items() if key != 'world_spec'}
                for row in spec['episode_rows']]
    require(episode_rows(original) == expected, 'Reviewed episode rows differ from original')
    repairs = spec.get('episode_row_repairs', [])
    require(type(repairs) is list, 'Episode row repairs must be an explicit list')
    lines = original.decode('cp1252').splitlines(keepends=True)
    active_indices = [index for index, line in enumerate(lines) if re.match(r'^\s*\d+:', line)]
    repaired_indices = set()
    for repair in repairs:
        require(type(repair) is dict and set(repair) ==
                {'row_index', 'old_line', 'new_line', 'row_sha256', 'count', 'reason'},
                'Unreviewed episode row repair operation')
        index, old, new = repair['row_index'], repair['old_line'], repair['new_line']
        require(all(type(value) is int for value in (index, old, new, repair['count']))
                and 0 <= index < len(expected) and new >= 0 and repair['count'] == 1,
                'Episode row repair requires one valid counted identifier change')
        require(index not in repaired_indices, 'Episode row cannot be repaired twice')
        require(expected[index]['line'] == old and any(row['line'] == old for row in expected[:index]),
                'Only a later duplicate episode identifier may be repaired')
        require(all(row['line'] != new for row in expected), 'Repaired episode identifier already exists')
        require(all(row[field] not in {old, new} for row in expected for field in ('goto_a', 'goto_b')),
                'Referenced episode identifiers require separate branch review')
        line_index = active_indices[index]
        require(digest(lines[line_index].encode('cp1252')) == repair['row_sha256'],
                'Original episode repair row differs')
        require(isinstance(repair['reason'], str) and repair['reason'].strip(),
                'Episode row repair requires its review reason')
        lines[line_index], count = re.subn(r'^([ \t]*)\d+:',
                                           lambda match: match[1] + str(new) + ':',
                                           lines[line_index], count=1)
        require(count == repair['count'], 'Episode row repair count differs')
        expected[index]['line'] = new
        repaired_indices.add(index)
    repaired = ''.join(lines).encode('cp1252')
    require(episode_rows(repaired) == expected, 'Episode repair changed another row field')
    require(len({row['line'] for row in expected}) == len(expected), 'Duplicate episode row numbers require separate review')
    return repaired, expected


def metadata(source, spec):
    original, expected = reviewed_episode(source.read('episode.jk'), spec)
    require({row['world_spec'] for row in spec['episode_rows']} == set(spec['world_specs']),
            'Every pack component must have an active reviewed episode row')
    names = {}
    for row in spec['episode_rows']:
        world = spec['world_specs'][row['world_spec']]
        require(row['world'] == world['world'], 'Episode row selects the wrong reviewed world')
        old, new = Path(row['world']).name.lower(), 'br_' + world['tag'] + '.jkl'
        require(old not in names or names[old] == new, 'Inconsistent world mapping')
        names[old] = new
    require(len(set(names.values())) == len(names), 'Converted world names collide')
    value = original.decode('cp1252')
    pattern = re.compile(r'(\bLEVEL\s+)([^\s#]+)', re.I)
    def replace_world(match):
        old = match[2].lower()
        require(old in names, 'Unreviewed active episode world')
        return match[1] + names[old]
    # Match active rows only; comments and all other original bytes remain intact.
    lines = value.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if re.match(r'^\s*\d+:', line):
            active, marker, comment = line.partition('#')
            lines[index] = pattern.sub(replace_world, active) + marker + comment
    output_episode = ''.join(lines).encode('cp1252')
    output_expected = [dict(row, world='jkl/' + names[Path(row['world']).name]) for row in expected]
    require(episode_rows(output_episode) == output_expected, 'Converted episode graph changed beyond world names')
    require('misc/cogstrings.uni' in source.entries, 'Pack lacks reviewed original level strings')
    strings = source.read('misc/cogstrings.uni').decode('cp1252')
    stems = {Path(old).stem: Path(new).stem.upper() for old, new in names.items()}
    # Level title and loading-text keys share a world-name prefix. Rewrite keys
    # once across the original table, retaining every value and unrelated key.
    def replace_key(match):
        key = match[2]
        for old in sorted(stems, key=len, reverse=True):
            if key.lower() == old or key.lower().startswith(old + '_text_'):
                return match[1] + stems[old] + key[len(old):] + match[3]
        return match[0]
    strings = re.sub(r'(^[ \t]*")([^"\r\n]+)(")', replace_key, strings, flags=re.M)
    return {'episode.jk': output_episode, 'misc/cogstrings.uni': strings.encode('cp1252')}


def resource_union(components):
    resources, providers = {}, {}
    for key, output in components:
        for path in sorted(output.entries):
            if path in METADATA:
                continue
            data = output.read(path)
            require(path not in resources or resources[path] == data,
                    'Different bytes at shared full virtual path ' + path + ': ' + ', '.join(providers.get(path, []) + [key]))
            resources[path] = data
            providers.setdefault(path, []).append(key)
    return resources, providers


def reference_count(data, name):
    active = '\n'.join(line.split('#', 1)[0].split('//', 1)[0]
                       for line in data.decode('cp1252').splitlines())
    return sum(match[1].lower() == name for match in verify_retail.RESOURCE_LITERAL.finditer(active))


def component_omissions(archives, source, world, output, manifest):
    """Bind absence to original and output edges, never to a filename alone.

    The independent world verifier has already reconstructed the component.
    Recheck omission sources here and compare its report to those sources so a
    generated manifest cannot grant an exception to the final pack resolver.
    """
    rules = world.get('source_omissions', [])
    names = world.get('resource_aliases', {})
    output_world = 'jkl/br_' + world['tag'] + '.jkl'
    verify_retail.check_source_omissions(archives, output, source, world,
                                       world['world'], output_world, names)
    edges = {}
    for rule in rules:
        original_path, original = verify_retail.source_resource(
            archives, Path(rule['referrer']).name, source)
        name = names.get(rule['name'], 'br_' + rule['name'])
        path = (output_world if original_path == world['world'] else
                original_path.rsplit('/', 1)[0] + '/' +
                names.get(Path(original_path).name, 'br_' + Path(original_path).name))
        require(path not in METADATA and path in output.entries,
                'Omission must belong to a component resource')
        edge = (path, name)
        require(edge not in edges, 'Duplicate reviewed component omission edge')
        count = reference_count(original, rule['name'])
        require(count > 0 and reference_count(output.read(path), name) == count,
                'Reviewed omission reference count changed: ' + path)
        require(isinstance(rule.get('reason'), str) and rule['reason'].strip(),
                'Reviewed omission requires its source-impact explanation')
        edges[edge] = dict(source_referrer=original_path,
                           source_referrer_sha256=digest(original),
                           source_name=rule['name'], output_referrer=path,
                           output_referrer_sha256=digest(output.read(path)),
                           output_name=name, reference_count=count, reason=rule['reason'])
    expected = [dict(source=path, reference=name, reviewed_original_omission=True)
                for path, name in sorted(edges)]
    reported = manifest.get('literal_dependencies_unresolved')
    require(isinstance(reported, list) and all(type(item) is dict for item in reported),
            'Missing component dependency report')
    require(sorted(reported, key=lambda item: (item.get('source', ''), item.get('reference', ''))) == expected
            and all(item.get('reviewed_original_omission') is True for item in reported),
            'Component unresolved dependencies differ from exact reviewed omissions')
    return [edges[edge] for edge in sorted(edges)]


def validate_union(archives, output, components, expected_metadata, *, omissions=()):
    expected, providers = resource_union(components)
    expected.update(expected_metadata)
    require(set(output.entries) == set(expected), 'Final pack member set differs from complete world union')
    for path, data in expected.items():
        require(output.read(path) == data, 'Final pack changed component bytes: ' + path)
    # JKM_MP is a separate episode, not a provider mounted beside this pack.
    # Per-world conversion must have copied any native episode-only resources.
    available = bridge.Catalog([('pack', output)] + [(key, archives[key]) for key in ('motsres', 'motssnd')])
    allowed = {}
    for item in omissions:
        edge = (item['output_referrer'], item['output_name'])
        path, name = edge
        require(path in output.entries and path not in METADATA,
                'Reviewed omission referrer missing from final pack')
        require(name not in available.by_name,
                'Pack union unexpectedly fills reviewed original omission: ' + name)
        require(digest(output.read(path)) == item['output_referrer_sha256']
                and reference_count(output.read(path), name) == item['reference_count'] > 0,
                'Pack omission referrer bytes or count differ: ' + path)
        if edge in allowed:
            require(allowed[edge] == item, 'Conflicting component omission reviews')
        allowed[edge] = item
    seen = set()
    for path in sorted(output.entries):
        if Path(path).suffix in bridge.TEXT_EXTENSIONS:
            for name in sorted(bridge.references(bridge.text(output.read(path)))):
                if (path, name) in allowed:
                    seen.add((path, name))
                    continue
                available.get(name)
    require(seen == set(allowed), 'Final pack did not retain every reviewed omission edge')
    for row in episode_rows(output.read('episode.jk')):
        require(row['world'] in output.entries, 'An active episode world is absent')
    return providers


def build_payload(archives, source, spec):
    require(source.sha256 == spec['gob_sha256'], 'Original pack GOB differs')
    expected_metadata = metadata(source, spec)
    components, manifests, checks, omissions = [], {}, {}, []
    for key, world in spec['world_specs'].items():
        require(not any(world.get(field) for field in
                        ('native_cog_edits', 'native_resource_overrides', 'native_text_edits', 'native_template_overrides')),
                'This pack family does not merge native gameplay or startup overrides')
        data, manifest = bridge.recipe(archives, community=source, community_spec=world)
        require('_startup_data' not in manifest and not manifest.get('required_startup_overlay'),
                'Pack requires a separately reviewed startup profile')
        output = Gob(data, key)
        checks[key] = verify_retail.check(archives, output, community=source, community_spec=world)
        omissions.extend(component_omissions(archives, source, world, output, manifest))
        components.append((key, output))
        manifests[key] = manifest
    resources, _ = resource_union(components)
    resources.update(expected_metadata)
    payload = build_gob(resources)
    output = Gob(payload)
    providers = validate_union(archives, output, components, expected_metadata, omissions=omissions)
    manifest = dict(schema=1, recipe_id=spec['key'], recipe='reviewed-multiplayer-pack-v1',
                    title=spec['title'], author=spec['author'], source_url=spec['source_url'],
                    original_zip_sha256=spec['zip_sha256'], original_gob_sha256=source.sha256,
                    original_episode_sha256=spec['episode_sha256'], output_sha256=digest(payload),
                    episode_rows=episode_rows(output.read('episode.jk')),
                    world_manifests=manifests, shared_resource_providers=providers,
                    resources=output.inventory()['entries'],
                    verification=dict(status='structural-pass', world_checks=checks,
                                      full_gameplay=False, runtime='not-run-on-this-output',
                                      checks=['Every active original episode row retained, only reviewed world names changed.',
                                              'Every component independently reconstructed and verified before union.',
                                              'Shared complete virtual paths require identical bytes.',
                                              'Final archive is the exact component union plus combined source metadata.',
                                              'Final literal resource closure resolves against the exact MotS profile.']))
    if spec.get('episode_row_repairs'):
        repaired_episode, _ = reviewed_episode(source.read('episode.jk'), spec)
        manifest['episode_row_repairs'] = copy.deepcopy(spec['episode_row_repairs'])
        manifest['repaired_original_episode_sha256'] = digest(repaired_episode)
        manifest['verification']['checks'][0] = (
            'Every active original episode row retained; only reviewed world names and '
            'explicitly pinned unreferenced duplicate identifiers changed.')
    if omissions:
        # Shared referrers may occur in multiple independently verified worlds.
        # Record each edge once, without turning it into a pack-wide name waiver.
        manifest['reviewed_source_omissions'] = list({
            (item['output_referrer'], item['output_name']): item for item in omissions}.values())
        manifest['verification']['checks'][-1] = (
            'Final literal closure resolves against the exact MotS profile except '
            'listed, hash- and count-bound original omissions; their absence is preserved.')
    return payload, manifest


def build_to_directory(archives, original_path, stage, recipe_id):
    spec = recipe_details(recipe_id)
    stage = Path(stage).resolve()
    project = Path(__file__).resolve().parent
    require(stage != project and project not in stage.parents, 'Generated assets must remain outside the source repository')
    source, readmes = read_original(original_path, spec)
    payload, manifest = build_payload(archives, source, spec)
    filename = 'bridge-' + spec['tag'] + '-pack-v1.goo'
    target = stage / filename
    require(not target.exists() and not target.with_suffix('.manifest.json').exists(), 'Pack output already exists; choose a fresh output directory')
    stage.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as handle:
        handle.write(payload)
    manifest_path = target.with_suffix('.manifest.json')
    with manifest_path.open('x', encoding='utf-8') as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write('\n')
    for index, (name, data) in enumerate(readmes.items(), 1):
        with (stage / f'ORIGINAL-{index:02d}-{Path(name).name}').open('xb') as handle:
            handle.write(data)
    (stage / 'README.txt').write_text(
        f"{spec['title']} - local MotS multiplayer pack conversion\n"
        f"Original level author: {spec['author']}. Source: {spec['source_url']}\n"
        "Converter: World Between Worlds / Andrei Pemberton with Coda Lilitari.\n"
        "Original readme retained unchanged beside this file. No redistribution rights are granted.\n\n"
        "Place the generated GOO in your MotS episode folder and launch OpenJKDF2 with -motsCompat.\n"
        "Select this multiplayer episode; all its reviewed original maps are included in their original order.\n"
        "No startup overlay is required. Use matching generated files on all peers.\n"
        "Structural verification does not establish rendering, authored mechanics or multiplayer synchronization.\n",
        encoding='utf-8')
    require(target.read_bytes() == payload, 'Post-write pack verification failed')
    return dict(filename=filename, manifest_filename=manifest_path.name,
                verification=manifest['verification'], startup_overlay=None)

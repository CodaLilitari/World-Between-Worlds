"""Experimental, source-locked whole-episode JK single-player conversion.

This module emits local candidates, never ships game bytes or claims gameplay
parity. Its explicit catalog is separate from multiplayer recipes and mods.
"""
from collections import Counter, deque
from pathlib import Path
import hashlib
import io
import json
import re
import zipfile

import bridge
import custom_registry
from gob import Gob, ArchiveError, build_gob, resource_name
import sp_catalog


class SingleplayerError(ValueError):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def catalog_entries():
    return [dict(spec['entry']) for spec in sp_catalog.RECIPES.values()]


def recipe_details(recipe_id):
    return sp_catalog.RECIPES[recipe_id]


def original_hashes(recipe_id):
    spec = recipe_details(recipe_id)
    return [spec['zip_sha256']]


def open_original(path, recipe_id):
    spec = recipe_details(recipe_id)
    path = Path(path)
    if path.stat().st_size > 128 * 1024**2:
        raise SingleplayerError('Source package exceeds reviewed size limit')
    data = path.read_bytes()
    if sha(data) != spec['zip_sha256']:
        raise SingleplayerError('Select the exact reviewed original ZIP, including its notices')
    result, notices = {}, {}
    reserved = {'readme.txt', 'manifest.json', spec['output_filename'].lower()}
    notice_names = [item['path'] for item in spec['readmes']]
    if (any(resource_name(name) != name.lower() or '/' in name or '\\' in name
            or Path(name).name != name for name in notice_names)
            or len({name.lower() for name in notice_names}) != len(notice_names)
            or reserved.intersection(name.lower() for name in notice_names)):
        raise SingleplayerError('Original notice output names need explicit safe aliases')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = [resource_name(x.filename) for x in z.infolist() if not x.is_dir()]
        if len(names) != len(set(names)) or z.testzip() is not None:
            raise SingleplayerError('Invalid or ambiguous source ZIP')
        for expected in spec['archives']:
            content = z.read(expected['member'])
            if sha(content) != expected['sha256']:
                raise SingleplayerError('Embedded source archive hash differs')
            result[expected['role']] = Gob(content, expected['member'])
        for item in spec['readmes']:
            content = z.read(item['path'])
            if sha(content) != item['sha256'] or len(content) != item['bytes']:
                raise SingleplayerError('Original notice hash differs')
            notices[item['path']] = content
    return result, notices


def episode_rows(data):
    text = bridge.text(data)
    type_match = re.search(r'^\s*TYPE\s+(\d+)\b', text, re.I | re.M)
    if not type_match or type_match[1] != '1':
        raise SingleplayerError('Expected original single-player episode')
    rows = []
    for line in text.splitlines():
        tokens = line.split('#', 1)[0].split()
        if not tokens or not re.fullmatch(r'\d+:', tokens[0]):
            continue
        if len(tokens) != 9:
            raise SingleplayerError('Unreviewed episode row shape')
        for index in (0, 1, 2, 5, 6, 7, 8):
            int(tokens[index].rstrip(':'))
        if tokens[3].upper() not in {'LEVEL', 'CUT'}:
            raise SingleplayerError('Unreviewed episode entry kind')
        rows.append(tokens)
    ids = {int(row[0][:-1]) for row in rows}
    if len(ids) != len(rows) or not rows:
        raise SingleplayerError('Duplicate or missing episode entries')
    if any(int(r[i]) != -1 and int(r[i]) not in ids for r in rows for i in (7, 8)):
        raise SingleplayerError('Missing episode branch destination')
    return rows


def template_refs(text):
    return {x.lower() for x in re.findall(r'^\s*template\s+\w+\s*=\s*([^\s]+)',
                                         bridge.active_lines(text), re.I | re.M) if x != '-1'}


LOADER_DIRECTORIES = {
    '.mat': ('mat', '3do/mat'), '.wav': ('sound', 'voice'),
    '.3do': ('3do',), '.key': ('3do/key',), '.cog': ('cog',),
    '.pup': ('misc/pup',), '.snd': ('misc/snd',), '.ai': ('misc/ai',),
    '.cmp': ('misc/cmp',), '.spr': ('misc/spr',), '.par': ('misc/par',),
}
TYPED_TOKEN = re.compile(r'(?<![\w.~&/\\])([\w+.~&/\\-]+\.(?:' +
                         bridge.EXTENSIONS + r'))(?![\w.~&/\\])', re.I)


def literal_counts(data):
    """Count active, whole typed tokens, retaining qualification for rejection."""
    return Counter(match[1].lower() for match in TYPED_TOKEN.finditer(
        bridge.active_lines(bridge.text(data))))


def omission_lines(data, name):
    """Asset-free multiset of the exact active lines containing one token."""
    lines = Counter()
    for line in bridge.active_lines(bridge.text(data)).splitlines():
        count = sum(match[1].lower() == name for match in TYPED_TOKEN.finditer(line))
        if count:
            lines[(sha(line.encode('cp1252')), count)] += 1
    return [{'sha256': digest, 'occurrences': count, 'repetitions': repetitions}
            for (digest, count), repetitions in sorted(lines.items())]


class SourceOmissions:
    """Recipe-local missing MAT/WAV edges, never a global name exemption.

    Both graph traversals call this with their own original referrer bytes.
    The verifier supplies independently reconstructed bytes to contracts();
    neither rules nor output hashes are read from the builder manifest.
    """
    def __init__(self, spec):
        self.spec, self.rules, self.used = spec, {}, set()
        aliases = {}
        for rule in spec.get('source_omissions', []):
            required = {'name', 'owner', 'referrer', 'referrer_sha256', 'occurrences',
                        'output_name', 'output_referrer', 'active_lines', 'usage', 'reason'}
            if not isinstance(rule, dict) or set(rule) != required:
                raise SingleplayerError('Source omission rule shape differs')
            name, alias = rule['name'], rule['output_name']
            if (not isinstance(name, str) or not re.fullmatch(r'[a-z0-9_+.-]+\.(mat|wav)', name)
                    or not isinstance(alias, str) or not re.fullmatch(r'bs_[a-z0-9_+.-]+', alias)
                    or len(alias.encode('ascii')) > 31 or Path(alias).suffix != Path(name).suffix
                    or alias != spec.get('resource_aliases', {}).get(name, 'bs_' + name)):
                raise SingleplayerError('Source omission needs an exact isolated MAT/WAV alias')
            if (rule['owner'] not in {'authored', 'jkres', 'jksnd', 'jksp'}
                    or not re.fullmatch(r'[0-9a-f]{64}', rule['referrer_sha256'])
                    or type(rule['occurrences']) is not int or rule['occurrences'] < 1
                    or rule['usage'] not in {'literal', 'untextured-one-face-material'}
                    or not isinstance(rule['reason'], str) or not rule['reason'].strip()):
                raise SingleplayerError('Source omission authority is incomplete')
            for key in ('referrer', 'output_referrer'):
                path = rule[key]
                if (not isinstance(path, str) or resource_name(path) != path or '/' not in path
                        or Path(path).suffix not in bridge.TEXT_EXTENSIONS):
                    raise SingleplayerError('Source omission needs a canonical full referrer path')
            anchors = rule['active_lines']
            if (not isinstance(anchors, list) or not anchors or any(
                    not isinstance(a, dict) or set(a) != {'sha256', 'occurrences', 'repetitions'}
                    or not re.fullmatch(r'[0-9a-f]{64}', a['sha256'])
                    or type(a['occurrences']) is not int or a['occurrences'] < 1
                    or type(a['repetitions']) is not int or a['repetitions'] < 1 for a in anchors)):
                raise SingleplayerError('Source omission active-line anchors differ')
            edge = (rule['owner'], rule['referrer'], name)
            if edge in self.rules or (alias in aliases and aliases[alias] != name):
                raise SingleplayerError('Duplicate source omission edge or alias')
            if alias in spec['native_cog_bindings'].values():
                raise SingleplayerError('Source omission namespace collision')
            self.rules[edge], aliases[alias] = rule, name

    def inspect(self, owner, path, raw, target, catalog, names):
        if not self.rules:
            return
        for name, count in literal_counts(raw).items():
            if '/' in name or '\\' in name:
                raise SingleplayerError('Qualified resource token needs contextual review: ' + name)
            edge = (owner, path, name)
            rule = self.rules.get(edge)
            # Never turn an ambiguous lookup failure into a missing-resource waiver.
            if name in catalog.ambiguous:
                catalog.get(name)
            if name in catalog.by_name:
                if rule:
                    raise SingleplayerError('Reviewed source omission unexpectedly resolves: ' + name)
                continue
            if rule is None:
                raise SingleplayerError('Unreviewed source omission edge: ' + path + ' -> ' + name)
            if (sha(raw) != rule['referrer_sha256'] or count != rule['occurrences']
                    or omission_lines(raw, name) != rule['active_lines']
                    or target != rule['output_referrer']):
                raise SingleplayerError('Source omission referrer hash, count, lines or target differs: ' + path)
            if rule['usage'] == 'untextured-one-face-material':
                value = bridge.active_lines(bridge.text(raw))
                face = re.search(r'^\s*FACES\s+1\s*$(.*?)^\s*FACE NORMALS', value, re.M | re.I | re.S)
                row = face[1].split() if face else []
                single_blocks = {'MATERIALS': '1', 'GEOSETS': '1', 'GEOSET': '0',
                                 'MESHES': '1', 'MESH': '0', 'TEXTURE VERTICES': '0', 'FACES': '1'}
                if (not path.endswith('.3do') or not name.endswith('.mat')
                        or face is None
                        or any(re.findall(r'^\s*' + label + r'\s+(\d+)\s*$', value, re.M | re.I)
                               != [expected] for label, expected in single_blocks.items())
                        or len(re.findall(r'^\s*\d+:', face[1], re.M)) != 1
                        or len(row) < 8 or row[1] != '0' or row[3] != '3'):
                    raise SingleplayerError('Reviewed untextured material usage changed')
            alias = rule['output_name']
            if ((name in names and names[name] != alias)
                    or any(other != name and value == alias for other, value in names.items())):
                raise SingleplayerError('Source omission namespace collision')
            names[name] = alias
            self.used.add(edge)

    def contracts(self, expected_files):
        if self.used != self.rules.keys():
            raise SingleplayerError('Unused source omission rule')
        records = []
        for edge in sorted(self.rules):
            rule = self.rules[edge]
            raw = expected_files[rule['output_referrer']]
            if literal_counts(raw)[rule['output_name']] != rule['occurrences']:
                raise SingleplayerError('Source-derived omission output count differs')
            records.append({**rule, 'output_referrer_sha256': sha(raw)})
        return records


class SourceTemplateOmissions:
    """Exact local COG defaults that must remain absent in one pinned world.

    This is separate from file omissions: the engine resolves template symbols
    from the loaded template tables, not resource paths. No template is added,
    no statement is removed, and no exposed COG argument is waived.
    """
    def __init__(self, spec):
        self.spec, self.rules, self.used, self.aliases = spec, {}, set(), {}
        required = {'world', 'world_sha256', 'owner', 'referrer', 'referrer_sha256',
                    'symbol', 'default', 'output_name', 'output_referrer',
                    'declaration_sha256', 'declaration_count', 'symbol_use_count', 'reason'}
        for rule in spec.get('source_template_omissions', []):
            if not isinstance(rule, dict) or set(rule) != required:
                raise SingleplayerError('Source template omission rule shape differs')
            if (rule['world'] not in spec['worlds'] or rule['world_sha256'] != spec['worlds'][rule['world']]
                    or rule['owner'] not in {'authored', 'jkres', 'jksnd', 'jksp'}
                    or not re.fullmatch(r'[a-z_][a-z0-9_]*', rule['symbol'])
                    or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', rule['default'])
                    or rule['output_name'] != 'bs_' + rule['default'].lower()
                    or len(rule['output_name']) > 31
                    or type(rule['declaration_count']) is not int or rule['declaration_count'] != 1
                    or type(rule['symbol_use_count']) is not int or rule['symbol_use_count'] < 1
                    or not isinstance(rule['reason'], str) or not rule['reason'].strip()):
                raise SingleplayerError('Source template omission authority differs')
            for field in ('world_sha256', 'referrer_sha256', 'declaration_sha256'):
                if not re.fullmatch(r'[0-9a-f]{64}', rule[field]):
                    raise SingleplayerError('Source template omission hash differs')
            for field in ('referrer', 'output_referrer'):
                path = rule[field]
                if resource_name(path) != path or not re.fullmatch(r'cog/[^/]+\.cog', path):
                    raise SingleplayerError('Source template omission needs an exact COG path')
            if spec.get('cog_edits', {}).get(Path(rule['referrer']).name):
                raise SingleplayerError('Source template omission COG cannot have behavior edits')
            edge = (rule['world'], rule['owner'], rule['referrer'], rule['symbol'])
            if edge in self.rules:
                raise SingleplayerError('Duplicate source template omission edge')
            self.rules[edge] = rule

    @staticmethod
    def occurrences(value, token):
        return len(re.findall(r'(?<![\w+.-])' + re.escape(token) + r'(?![\w+.-])', value, re.I))

    @staticmethod
    def definitions(raw):
        value = bridge.text(raw)
        return ({row.split()[0].lower() for row in bridge.records(value, 'templates')}
                if re.search(r'^World templates\b', value, re.M | re.I) else set())

    def check_world(self, world_path, raw, archives, native_definitions):
        rules = [r for r in self.rules.values() if r['world'] == world_path]
        if not rules:
            return
        definitions = self.definitions(raw) | set(native_definitions)
        for owner in ('jkres', 'motsres'):
            if 'jkl/static.jkl' in archives[owner].entries:
                definitions |= self.definitions(archives[owner].read('jkl/static.jkl'))
        for rule in rules:
            if sha(raw) != rule['world_sha256']:
                raise SingleplayerError('Source template omission world hash differs')
            names = {rule['default'].lower(), rule['output_name']}
            if definitions & names:
                raise SingleplayerError('Reviewed source/native template unexpectedly resolves')
            if any(self.occurrences(bridge.active_lines(bridge.text(raw)), name) for name in names):
                raise SingleplayerError('Missing template has an unreviewed world or placed reference')

    def inspect(self, world, owner, path, raw, target):
        if not self.rules:
            return
        value = bridge.active_lines(bridge.text(raw))
        for rule in self.rules.values():
            name = rule['default'].lower()
            if self.occurrences(value, rule['output_name']):
                raise SingleplayerError('Missing template alias already occurs in source')
            if not self.occurrences(value, name):
                continue
            edge = (world, owner, path, rule['symbol'])
            if self.rules.get(edge) != rule:
                raise SingleplayerError('Unreviewed missing template referrer or world scope')
            blocks = re.findall(r'^\s*symbols\s*$(.*?)^\s*end\s*$', value, re.I | re.M | re.S)
            if len(blocks) != 1:
                raise SingleplayerError('Source template omission symbols block differs')
            declarations = [line for line in blocks[0].splitlines()
                            if re.search(r'^\s*\w+\s+' + re.escape(rule['symbol']) + r'(?=\s|=|$)', line, re.I)]
            declaration = declarations[0] if len(declarations) == 1 else ''
            match = re.fullmatch(r'\s*template\s+' + re.escape(rule['symbol']) +
                                 r'\s*=\s*(\S+)\s+local\s*', declaration, re.I)
            if (not match or match[1] != rule['default']
                    or sha(raw) != rule['referrer_sha256'] or target != rule['output_referrer']
                    or sha(declaration.encode('cp1252')) != rule['declaration_sha256']
                    or self.occurrences(value, name) != rule['declaration_count']
                    or self.occurrences(value, rule['symbol']) != rule['symbol_use_count'] + 1):
                raise SingleplayerError('Source template omission declaration, local flag, hash or use count differs')
            self.aliases.setdefault((world, owner, path), {})[name] = rule['output_name']
            self.used.add(edge)

    def names(self, world, owner, path):
        return self.aliases.get((world, owner, path), {})

    def contracts(self, expected_files):
        if self.used != self.rules.keys():
            raise SingleplayerError('Unused source template omission rule')
        records = []
        for edge, rule in sorted(self.rules.items()):
            path = rule['output_referrer']
            expected = expected_files[path]
            value = bridge.active_lines(bridge.text(expected))
            if (self.occurrences(value, rule['output_name']) != 1
                    or self.occurrences(value, rule['default'])
                    or self.occurrences(value, rule['symbol']) != rule['symbol_use_count'] + 1):
                raise SingleplayerError('Source-derived missing template output contract differs')
            for referrer, raw in expected_files.items():
                if referrer.endswith('.jkl') and self.definitions(raw) & {rule['default'].lower(), rule['output_name']}:
                    raise SingleplayerError('Reviewed omitted output template unexpectedly resolves')
                if (referrer != path and Path(referrer).suffix in bridge.TEXT_EXTENSIONS
                        and any(self.occurrences(bridge.active_lines(bridge.text(raw)), token)
                                for token in (rule['default'], rule['output_name']))):
                    raise SingleplayerError('Unreviewed missing template output referrer')
            records.append({**rule, 'output_referrer_sha256': sha(expected),
                            'status': 'active-original-missing-template-preserved',
                            'runtime_verified': False})
        return records


def verify_typed_literal_closure(output, archives, omissions=()):
    """Check exact loader paths; a matching basename elsewhere is insufficient.

    These directories come from the audited OpenJKDF2 loaders. Material and
    sound directory fallback happens before moving to the next directory,
    regardless of which archive supplies the candidate. Qualified tokens need
    contextual review before this bounded SP adapter accepts them.
    """
    approved = {(rule['output_referrer'], rule['output_name']): rule for rule in omissions}
    if len(approved) != len(omissions):
        raise SingleplayerError('Duplicate typed omission edge')
    used = set()
    sources = [('output', output)] + [(key, archives[key]) for key in ('motsres', 'motssnd')]
    checked, distinct, provider_counts, directory_counts = 0, set(), {}, {}
    for source_path in sorted(output.entries):
        if Path(source_path).suffix not in bridge.TEXT_EXTENSIONS:
            continue
        raw = output.read(source_path)
        counts = literal_counts(raw)
        for token in sorted(counts):
            if '/' in token or '\\' in token:
                raise SingleplayerError('Qualified resource token needs contextual review: ' +
                                        source_path + ' -> ' + token)
            candidates = [directory + '/' + token for directory in LOADER_DIRECTORIES[Path(token).suffix]]
            selected = next(((owner, candidate) for candidate in candidates
                             for owner, archive in sources if candidate in archive.entries), None)
            edge = (source_path, token)
            if edge in approved:
                rule = approved[edge]
                if selected is not None:
                    raise SingleplayerError('Reviewed omitted output unexpectedly resolves: ' + str(selected))
                if counts[token] != rule['occurrences'] or sha(raw) != rule['output_referrer_sha256']:
                    raise SingleplayerError('Typed omission output referrer hash or count differs')
                used.add(edge)
                continue
            if selected is None:
                raise SingleplayerError('Unresolved typed resource path: ' + source_path + ' -> ' +
                                        token + '; tried ' + ', '.join(candidates))
            owner, path = selected
            checked += 1
            distinct.add(token)
            provider_counts[owner] = provider_counts.get(owner, 0) + 1
            directory = path.rsplit('/', 1)[0]
            directory_counts[directory] = directory_counts.get(directory, 0) + 1
    if used != approved.keys():
        raise SingleplayerError('Unused typed omission edge')
    report = {'schema': 'wbw.sp-typed-literal-closure.v1', 'checked_literals': checked,
            'distinct_literals': len(distinct), 'provider_counts': dict(sorted(provider_counts.items())),
            'loader_directory_counts': dict(sorted(directory_counts.items())),
            'scope': 'Recognized literal extensions in output text resolve through exact ordered loader paths in the selected episode and pinned native resource archives.',
            'qualified_tokens': 'rejected-until-contextually-reviewed',
            'limitations': 'Does not validate computed/extensionless references, cache state, loose files, external startup overlays or runtime behavior.'}
    if omissions:
        report.update(schema='wbw.sp-typed-literal-closure.v2', status='partial-reviewed-source-omissions',
                      retained_omission_edges=len(omissions),
                      retained_omission_occurrences=sum(r['occurrences'] for r in omissions),
                      retained_omissions=list(omissions),
                      scope='Resolved literals use exact ordered loader paths; only source-derived hash/count-pinned edges remain absent. This is partial resource closure.')
    return report


def build(archives, originals, recipe_id):
    """Build every hash-pinned episode world; keep progression table unchanged."""
    spec = recipe_details(recipe_id)
    omissions = SourceOmissions(spec)
    template_omissions = SourceTemplateOmissions(spec)
    for key, expected in spec['owned_hashes'].items():
        if key not in archives or archives[key].sha256 != expected:
            raise SingleplayerError('Unreviewed owned source: ' + key)
    if set(originals) != {'episode'}:
        raise SingleplayerError('This pilot does not yet support authored startup archives')
    original = originals['episode']
    if original.sha256 != spec['archives'][0]['sha256']:
        raise SingleplayerError('Original episode hash differs')
    rows = episode_rows(original.read('episode.jk'))
    if rows != spec['episode_rows']:
        raise SingleplayerError('Episode progression differs from reviewed original')
    worlds = {path for path in original.entries if path.endswith('.jkl')}
    if worlds != set(spec['worlds']):
        raise SingleplayerError('Every original JKL must be explicitly reviewed')
    for row in rows:
        if row[3].upper() == 'CUT':
            raise SingleplayerError('External cinematic format needs a reviewed SP recipe')
        if 'jkl/' + row[4].lower() not in worlds:
            raise SingleplayerError('Episode refers to a missing world')
    source = bridge.Catalog([('authored', original)] + [(k, archives[k]) for k in ('jkres', 'jksnd', 'jksp')])
    native = bridge.Catalog([(k, archives[k]) for k in ('motsres', 'motssnd', 'motssp')])
    native_world = bridge.text(archives['motssp'].read(spec['native_world']))
    native_templates = {row.split()[0].lower(): row for row in bridge.records(native_world, 'templates')}
    native_order = list(native_templates)
    static = bridge.text(archives['motsres'].read('jkl/static.jkl'))
    static_templates = ({row.split()[0].lower(): row for row in bridge.records(static, 'templates')}
                        if re.search(r'^World templates\b', static, re.I | re.M) else {})
    native_templates = {**static_templates, **native_templates}
    files = {'episode.jk': original.read('episode.jk')}
    # Preserve authored strings used by objectives and cutscene messages verbatim.
    for path in spec.get('verbatim_paths', []):
        files[path] = original.read(path)
    manifest = {'recipe': recipe_id, 'status': 'structural-candidate-gameplay-unverified',
                'episode_rows': rows, 'worlds': [], 'sources': [],
                'original_episode_sha256': original.sha256, 'owned_sources': dict(spec['owned_hashes']),
                'native_cog_bindings': dict(spec['native_cog_bindings']),
                'cog_edits': spec.get('cog_edits', {}), 'native_copies': [],
                'native_template_basis': {'path': spec['native_world'], 'sha256': sha(archives['motssp'].read(spec['native_world']))},
                'limitations': ['Literal references only; dynamic references require runtime checks.',
                                'No gameplay, cutscene completion, AI parity or save/load claim.']}
    for world_path, expected_world in spec['worlds'].items():
        raw = original.read(world_path)
        if sha(raw) != expected_world:
            raise SingleplayerError('Source world hash differs')
        world = bridge.text(raw)
        template_omissions.check_world(world_path, raw, archives, native_templates)
        template_omissions.inspect(world_path, 'authored', world_path, raw, world_path)
        template_map = {r.split()[0].lower(): ('walkplayer' if r.split()[0].lower() == 'walkplayer' else 'bs_' + r.split()[0].lower())
                        for r in bridge.records(world, 'templates')}
        if any(len(n.encode('cp1252')) > 31 for n in template_map.values()):
            raise SingleplayerError('Source template needs explicit short alias')
        substitutions = dict(spec['native_cog_bindings'])
        for name, expected in spec['native_binding_source_sha256'].items():
            _, source_path, source_archive = source.get(name)
            if sha(source_archive.read(source_path)) != expected:
                raise SingleplayerError('Native substitution source identity differs: ' + name)
        name_map = dict(substitutions)
        omissions.inspect('authored', world_path, raw, world_path, source, name_map)
        source_files, source_records = {}, []
        root_references = bridge.references(world)
        dependency_parents = {name: {world_path} for name in root_references}
        queue = deque(sorted(root_references))
        seen = set()
        while queue:
            name = queue.popleft()
            if name in seen or name in substitutions:
                continue
            seen.add(name)
            if name not in source.by_name and name in name_map:
                continue  # Each missing edge was checked at its original referrer.
            label, path, archive = source.get(name)
            data = archive.read(path)
            if name.endswith('.cog') and name not in spec['source_cog_sha256']:
                raise SingleplayerError('Unreviewed source COG: ' + name)
            if name.endswith('.cog') and sha(data) != spec['source_cog_sha256'][name]:
                raise SingleplayerError('Source COG hash differs: ' + name)
            alias = spec.get('resource_aliases', {}).get(name, 'bs_' + name)
            if len(alias.encode('cp1252')) > 31:
                raise SingleplayerError('Source resource needs explicit short alias: ' + name)
            if alias in name_map.values():
                raise SingleplayerError('Source namespace collision')
            name_map[name] = alias
            output_path = path.rsplit('/', 1)[0] + '/' + alias
            source_files[output_path] = data
            source_records.append({'owner': label, 'path': path, 'sha256': sha(data), 'output_path': output_path})
            if Path(path).suffix in bridge.TEXT_EXTENSIONS:
                omissions.inspect(label, path, data, output_path, source, name_map)
                template_omissions.inspect(world_path, label, path, data, output_path)
                references = bridge.references(bridge.text(data))
                for reference in references:
                    dependency_parents.setdefault(reference, set()).add(path)
                queue.extend(sorted(references - seen))
        def rename(value):
            return bridge.FILE_REF.sub(lambda m: name_map.get(m[1].lower(), m[1]), value)
        for path, data in source_files.items():
            source_record = next(r for r in source_records if r['output_path'] == path)
            original_name = Path(source_record['path']).name
            if Path(path).suffix in bridge.TEXT_EXTENSIONS:
                value = custom_registry.apply_cog_edits(bridge.text(data), spec.get('cog_edits', {}).get(original_name, []))
                missing_defaults = template_omissions.names(world_path, source_record['owner'], source_record['path'])
                unknown = template_refs(value) - template_map.keys() - missing_defaults.keys()
                if unknown:
                    raise SingleplayerError('Unreviewed source template defaults: ' + str(sorted(unknown)))
                value = bridge.template_defaults(rename(value), {**template_map, **missing_defaults})
                data = value.encode('cp1252')
            if path in files and files[path] != data:
                raise SingleplayerError('Cross-world resource differs under shared episode path')
            files[path] = data
            record = next(record for record in source_records if record['output_path'] == path)
            record['output_sha256'] = sha(data)
            record['referrers'] = sorted(dependency_parents[original_name])
            record['operation'] = ('preserve-binary-bytes-and-namespace-path' if Path(path).suffix not in bridge.TEXT_EXTENSIONS
                                   else 'namespace-literal-references-and-template-defaults-with-explicit-counted-cog-edits')
        # Native inventory and replacement scripts contribute only the template
        # definitions they actually reference, including recursive parents.
        native_resources, native_used_templates = set(), set()
        pending_resources = deque(sorted(set(substitutions.values()) | bridge.references(bridge.text(archives['motsres'].read('misc/items.dat')))))
        pending_templates = deque()
        while pending_resources or pending_templates:
            while pending_resources:
                name = pending_resources.popleft()
                if name in native_resources:
                    continue
                native_resources.add(name)
                label, path, archive = native.get(name)
                data = archive.read(path)
                if label == 'motssp':
                    if path in files and files[path] != data:
                        raise SingleplayerError('Unexpected native episode resource collision')
                    files[path] = data
                    if not any(record['path'] == path for record in manifest['native_copies']):
                        manifest['native_copies'].append({'owner': label, 'path': path, 'sha256': sha(data),
                            'operation': 'copy-exact-native-episode-dependency-not-mounted-with-selected-world'})
                if Path(path).suffix in bridge.TEXT_EXTENSIONS:
                    value = bridge.text(data)
                    pending_resources.extend(sorted(bridge.references(value) - native_resources))
                    if path.endswith('.cog'):
                        refs = template_refs(value)
                        rule = spec.get('native_template_omissions', {}).get(path)
                        if rule:
                            if sha(data) != rule['sha256'] or rule['name'] not in refs:
                                raise SingleplayerError('Native omission anchor differs')
                            refs.remove(rule['name'])
                        pending_templates.extend(sorted(refs))
            while pending_templates:
                name = pending_templates.popleft()
                if name in native_used_templates or name == 'none':
                    continue
                if name not in native_templates:
                    raise SingleplayerError('Native SP template unresolved: ' + name)
                native_used_templates.add(name)
                row = native_templates[name]
                parts = row.split()
                pending_templates.append(parts[1].lower())
                for ref in re.findall(r'(?<==)([^\s()]+)', row):
                    if ref.lower() in native_templates:
                        pending_templates.append(ref.lower())
                pending_resources.extend(sorted(bridge.references(row) - native_resources))
        converted = rename(bridge.rewrite_cog_template_arguments(world, source, template_map))
        converted, surfaces = bridge.expand_surface_lighting(converted)
        authored_rows = []
        for row in bridge.records(converted, 'templates'):
            parts = row.split(None, 2)
            parts[0] = template_map[parts[0].lower()]
            parts[1] = template_map.get(parts[1].lower(), parts[1])
            if len(parts) == 3:
                parts[2] = re.sub(r'(?<==)([^\s()]+)', lambda m: template_map.get(m[1].lower(), m[1]), parts[2])
            authored_rows.append(' '.join(parts))
        # Native template order is retained, preserving inherited definitions.
        imported_templates = [native_templates[n] for n in native_order if n in native_used_templates and n not in static_templates]
        if any(r.split()[0].lower() == 'walkplayer' for r in imported_templates):
            raise SingleplayerError('Native player must not replace authored SP player')
        converted = bridge.replace_block(converted, 'templates', imported_templates + authored_rows)
        converted, things = bridge.convert_things(converted, template_map)
        for label, ext in zip(bridge.TABLES, ('.wav', '.mat', '.cmp', '.ai', '.3do', '.spr', '.key', '.pup', '.snd', '.cog')):
            old = bridge.records(converted, label)
            existing = {re.sub(r'^\d+:\s*', '', row).split()[0].lower() for row in old}
            needed = [n for n in sorted(native_resources) if Path(n).suffix == ext and n not in existing]
            indexed = label != 'sounds'
            start = max((int(r.split(':')[0]) + 1 for r in old), default=0) if indexed else len(old)
            extra = [n + (' 1 1' if label == 'materials' else '') for n in needed]
            extra = [f'{start+i}: {n}' for i, n in enumerate(extra)] if indexed else extra
            converted = bridge.replace_block(converted, label, old + extra, start + len(extra))
        # Budget for template-attached COG instances in addition to authored rows.
        attached = sum('cog=' in row.lower() for row in imported_templates + authored_rows)
        converted = bridge.replace_block(converted, 'cogs', bridge.records(converted, 'cogs'),
                                         max(int(bridge.block(world, 'cogs')[2]), len(bridge.records(converted, 'cogs')) + attached + 8))
        if re.search(r'^Section:\s*ARCHLIGHTING', converted, re.I | re.M):
            raise SingleplayerError('Already converted world')
        converted += '\nSection: ARCHLIGHTING\nNum ArchObjects 0\nend\n'
        files[world_path] = converted.encode('cp1252')
        manifest['worlds'].append({'path': world_path, 'source_sha256': expected_world, 'surfaces': surfaces, 'things': things,
                                   'authored_templates': len(authored_rows), 'native_templates': len(imported_templates),
                                   'native_resource_names': sorted(native_resources)})
        manifest['sources'].extend(source_records)
    data = build_gob(files)
    omission_records = omissions.contracts(files)
    template_omission_records = template_omissions.contracts(files)
    if omission_records:
        # The builder checks mount collisions too; the verifier re-derives its
        # own contracts from original bytes without consuming this manifest.
        verify_typed_literal_closure(Gob(data), archives, omission_records)
        manifest['source_omissions'] = omission_records
        manifest['status'] = 'structural-candidate-reviewed-source-omissions-gameplay-unverified'
    if template_omission_records:
        manifest['source_template_omissions'] = template_omission_records
        manifest['status'] = 'structural-candidate-reviewed-source-omissions-gameplay-unverified'
    manifest['output_sha256'] = sha(data)
    manifest['output'] = Gob(data).inventory()
    return data, manifest


def verify(archives, originals, recipe_id, data):
    """Independent preservation checks; no runtime equivalence inference."""
    output, source = Gob(data), originals['episode']
    if output.read('episode.jk') != source.read('episode.jk'):
        raise SingleplayerError('Episode progression was changed')
    spec = recipe_details(recipe_id)
    omissions = SourceOmissions(spec)
    template_omissions = SourceTemplateOmissions(spec)
    expected_files = {}
    for key, expected in spec['owned_hashes'].items():
        if archives[key].sha256 != expected:
            raise SingleplayerError('Verifier owned source hash differs')
    if source.sha256 != spec['archives'][0]['sha256']:
        raise SingleplayerError('Verifier original source hash differs')
    original_catalog = bridge.Catalog([('authored', source)] + [(k, archives[k]) for k in ('jkres', 'jksnd', 'jksp')])
    native_catalog = bridge.Catalog([(k, archives[k]) for k in ('motsres', 'motssnd', 'motssp')])
    # Independently derive the exact native dependency and template sets from
    # the pinned original scripts, inventory and SP templates, never from output.
    native_rows = bridge.records(bridge.text(archives['motssp'].read(spec['native_world'])), 'templates')
    static_text = bridge.text(archives['motsres'].read('jkl/static.jkl'))
    static_rows = (bridge.records(static_text, 'templates')
                   if re.search(r'^World templates\b', static_text, re.I | re.M) else [])
    definitions = {row.split()[0].lower(): row for row in static_rows + native_rows}
    static_names = {row.split()[0].lower() for row in static_rows}
    expected_native_names = (set(spec['native_cog_bindings'].values()) |
                             bridge.references(bridge.text(archives['motsres'].read('misc/items.dat'))))
    checked_names, expected_template_names, checked_templates = set(), set(), set()
    expected_native_copies = {}
    while checked_names != expected_native_names or checked_templates != expected_template_names:
        for name in sorted(expected_native_names - checked_names):
            owner, resource_path, archive = native_catalog.get(name)
            raw = archive.read(resource_path)
            checked_names.add(name)
            if owner == 'motssp':
                expected_native_copies[resource_path] = raw
            if Path(resource_path).suffix in bridge.TEXT_EXTENSIONS:
                value = bridge.text(raw)
                expected_native_names.update(bridge.references(value))
                if resource_path.endswith('.cog'):
                    templates = template_refs(value)
                    omission = spec.get('native_template_omissions', {}).get(resource_path)
                    if omission:
                        if sha(raw) != omission['sha256'] or omission['name'] not in templates:
                            raise SingleplayerError('Verifier native omission source differs')
                        templates.remove(omission['name'])
                    expected_template_names.update(templates - {'none'})
        for name in sorted(expected_template_names - checked_templates):
            if name not in definitions:
                raise SingleplayerError('Verifier native template unresolved: ' + name)
            row = definitions[name]
            checked_templates.add(name)
            if row.split()[1].lower() != 'none':
                expected_template_names.add(row.split()[1].lower())
            expected_template_names.update(ref.lower() for ref in re.findall(r'(?<==)([^\s()]+)', row)
                                           if ref.lower() in definitions)
            expected_native_names.update(bridge.references(row))
    expected_native_templates = [row for row in native_rows
                                 if row.split()[0].lower() in expected_template_names - static_names]
    accounted = {'episode.jk', *spec.get('verbatim_paths', []), *spec['worlds']}
    if {p for p in output.entries if p.endswith('.jkl')} != set(spec['worlds']):
        raise SingleplayerError('World set differs')
    for path in spec['worlds']:
        before, after = bridge.text(source.read(path)), bridge.text(output.read(path))
        template_omissions.check_world(path, source.read(path), archives, definitions)
        template_omissions.inspect(path, 'authored', path, source.read(path), path)
        template_map = {r.split()[0].lower(): ('walkplayer' if r.split()[0].lower() == 'walkplayer' else 'bs_' + r.split()[0].lower())
                        for r in bridge.records(before, 'templates')}
        names = dict(spec['native_cog_bindings'])
        omissions.inspect('authored', path, source.read(path), path, original_catalog, names)
        queue = list(bridge.references(before))
        dependencies = {}
        while queue:
            name = queue.pop()
            if name in names:
                continue
            owner, original_path, archive = original_catalog.get(name)
            raw = archive.read(original_path)
            alias = spec.get('resource_aliases', {}).get(name, 'bs_' + name)
            names[name] = alias
            target_path = original_path.rsplit('/', 1)[0] + '/' + alias
            dependencies[target_path] = (name, raw, owner, original_path)
            if Path(name).suffix in bridge.TEXT_EXTENSIONS:
                omissions.inspect(owner, original_path, raw, target_path, original_catalog, names)
                template_omissions.inspect(path, owner, original_path, raw, target_path)
                queue.extend(bridge.references(bridge.text(raw)))
        for target_path, (name, raw, owner, original_path) in dependencies.items():
            expected = raw
            if Path(name).suffix in bridge.TEXT_EXTENSIONS:
                value = bridge.text(raw)
                missing_defaults = template_omissions.names(path, owner, original_path)
                unknown = template_refs(value) - template_map.keys() - missing_defaults.keys()
                if unknown:
                    raise SingleplayerError('Verifier unreviewed source template defaults: ' + str(sorted(unknown)))
                for edit in spec.get('cog_edits', {}).get(name, []):
                    if value.count(edit['old']) != edit['count']:
                        raise SingleplayerError('Verifier edit anchor mismatch')
                    value = value.replace(edit['old'], edit['new'])
                value = bridge.FILE_REF.sub(lambda m: names.get(m[1].lower(), m[1]), value)
                value = re.sub(r'(^\s*template\s+\w+\s*=\s*)([^\s]+)',
                               lambda m: m[1] + {**template_map, **missing_defaults}.get(m[2].lower(), m[2]),
                               value, flags=re.I | re.M)
                expected = value.encode('cp1252')
            if target_path not in output.entries or output.read(target_path) != expected:
                raise SingleplayerError('Source resource transformation differs: ' + target_path)
            accounted.add(target_path)
            expected_files[target_path] = expected
        extensions = dict(zip(bridge.TABLES, ('.wav', '.mat', '.cmp', '.ai', '.3do', '.spr', '.key', '.pup', '.snd', '.cog')))
        expected_tables = {}
        for label in bridge.TABLES:
            expected_rows = [bridge.FILE_REF.sub(lambda m: names.get(m[1].lower(), m[1]), row)
                             for row in bridge.records(before, label)]
            present_names = {re.sub(r'^\d+:\s*', '', row).split()[0].lower() for row in expected_rows}
            added_names = sorted(name for name in expected_native_names
                                 if Path(name).suffix == extensions[label] and name not in present_names)
            next_index = (len(expected_rows) if label == 'sounds'
                          else max((int(row.split(':')[0]) + 1 for row in expected_rows), default=0))
            for index, name in enumerate(added_names, next_index):
                row = name + (' 1 1' if label == 'materials' else '')
                expected_rows.append(row if label == 'sounds' else f'{index}: {row}')
            if bridge.records(after, label) != expected_rows:
                raise SingleplayerError('Resource table differs from exact reviewed closure: ' + label)
            if int(bridge.block(after, label)[2]) != next_index + len(added_names):
                raise SingleplayerError('Resource table capacity differs: ' + label)
            expected_tables[label] = (expected_rows, next_index + len(added_names))
        expected_templates = []
        for row in bridge.records(before, 'templates'):
            row = bridge.FILE_REF.sub(lambda m: names.get(m[1].lower(), m[1]), row)
            parts = row.split(None, 2)
            parts[0] = template_map[parts[0].lower()]
            parts[1] = template_map.get(parts[1].lower(), parts[1])
            if len(parts) > 2:
                parts[2] = re.sub(r'(?<==)([^\s()]+)', lambda m: template_map.get(m[1].lower(), m[1]), parts[2])
            expected_templates.append(' '.join(parts))
        output_templates = bridge.records(after, 'templates')
        if output_templates[-len(expected_templates):] != expected_templates:
            raise SingleplayerError('Authored template physics, AI or behavior changed')
        if output_templates[:-len(expected_templates)] != expected_native_templates:
            raise SingleplayerError('Native template set, order or content differs from needed SP closure')
        expected_cog_capacity = max(int(bridge.block(before, 'cogs')[2]),
            len(bridge.records(before, 'cogs')) + sum('cog=' in row.lower() for row in output_templates) + 8)
        for label, capacity in (('templates', len(output_templates)),
                                ('things', int(bridge.block(before, 'things')[2])),
                                ('cogs', expected_cog_capacity)):
            if int(bridge.block(after, label)[2]) != capacity:
                raise SingleplayerError('Gameplay table capacity differs: ' + label)
        for section in ('vertices', 'adjoins', 'sectors'):
            expected_geometry = [bridge.FILE_REF.sub(lambda m: names.get(m[1].lower(), m[1]), row)
                                 for row in bridge.records(before, section)]
            if expected_geometry != bridge.records(after, section):
                raise SingleplayerError('Unexpected geometry/topology change: ' + section)
        bthings, athings = bridge.records(before, 'things'), bridge.records(after, 'things')
        if len(bthings) != len(athings):
            raise SingleplayerError('Placed things lost')
        for left, right in zip(bthings, athings):
            a, b = left.split(), right.split()
            if (a[0] != b[0] or template_map.get(a[1].lower(), a[1]) != b[1]
                    or a[2:10] != b[2:10] or a[10:] != b[11:] or b[10] != '-1'):
                raise SingleplayerError('Placed thing parameters changed')
        if len(bridge.records(before, 'cogs')) != len(bridge.records(after, 'cogs')):
            raise SingleplayerError('Authored COG placement lost')
        expected_cog_rows = []
        for before_row, after_row in zip(bridge.records(before, 'cogs'), bridge.records(after, 'cogs')):
            original_tokens, converted_tokens = before_row.split(), after_row.split()
            if original_tokens[0] != converted_tokens[0] or names.get(original_tokens[1].lower(), original_tokens[1]) != converted_tokens[1]:
                raise SingleplayerError('COG instance identity differs')
            _, cog_path, cog_source = original_catalog.get(original_tokens[1])
            symbols = bridge.exposed_symbols(bridge.text(cog_source.read(cog_path)))
            expected_args = []
            for index, token in enumerate(original_tokens[2:]):
                expected_args.append(template_map.get(token.lower(), token) if symbols[index] == 'template'
                                     else bridge.FILE_REF.sub(lambda m: names.get(m[1].lower(), m[1]), token))
            if converted_tokens[2:] != expected_args:
                raise SingleplayerError('Authored COG argument changed')
            expected_cog_rows.append(' '.join([original_tokens[0], names.get(original_tokens[1].lower(),
                                            original_tokens[1]), *expected_args]))
        def surfaces(value):
            found = re.search(r'^World surfaces\s+(\d+)\s*$', value, re.I | re.M)
            return [row.split() for row in value[found.end():].splitlines()
                    if re.match(r'^\s*\d+:', row)][:int(found[1])]
        for left, right in zip(surfaces(before), surfaces(after)):
            count = int(left[9]); split = 10 + count
            if left[:split] != right[:split] or [x for v in left[split:] for x in (v, v, v, v)] != right[split:]:
                raise SingleplayerError('Surface topology or scalar-to-RGB expansion differs')
        def skeleton(value):
            for label in (*bridge.TABLES, 'templates', 'cogs', 'things'):
                match = bridge.block(value, label)
                value = value[:match.start()] + f'<REVIEWED {label}>\n' + value[match.end():]
            return value
        expected_skeleton = bridge.FILE_REF.sub(lambda m: names.get(m[1].lower(), m[1]), before)
        expected_skeleton = bridge.expand_surface_lighting(expected_skeleton)[0]
        archlighting = '\nSection: ARCHLIGHTING\nNum ArchObjects 0\nend\n'
        if not after.endswith(archlighting) or skeleton(after[:-len(archlighting)]) != skeleton(expected_skeleton):
            raise SingleplayerError('Unapproved world header, normals, physics or opaque section change')
        if omissions.rules or template_omissions.rules:
            # Reconstruct the complete referrer from source-derived rows; an
            # output hash must not grant authority to the output it checks.
            expected_world = expected_skeleton
            for label, (expected_rows, capacity) in expected_tables.items():
                expected_world = bridge.replace_block(expected_world, label, expected_rows, capacity)
            expected_world = bridge.replace_block(expected_world, 'templates',
                                                   expected_native_templates + expected_templates)
            expected_things = []
            for row in bthings:
                row = bridge.FILE_REF.sub(lambda m: names.get(m[1].lower(), m[1]), row)
                parts = row.split()
                parts[1] = template_map.get(parts[1].lower(), parts[1])
                parts.insert(10, '-1')
                expected_things.append(' '.join(parts))
            expected_world = bridge.replace_block(expected_world, 'things', expected_things,
                                                   int(bridge.block(before, 'things')[2]))
            expected_world = bridge.replace_block(expected_world, 'cogs', expected_cog_rows,
                                                   expected_cog_capacity) + archlighting
            expected_files[path] = expected_world.encode('cp1252')
            if output.read(path) != expected_files[path]:
                raise SingleplayerError('Source-derived omission world transformation differs')
    for path in spec.get('verbatim_paths', []):
        if output.read(path) != source.read(path):
            raise SingleplayerError('Authored strings changed')
    if output.entries.keys() - accounted != expected_native_copies.keys() - accounted:
        raise SingleplayerError('Native copied resource set differs from exact needed closure')
    for path, raw in expected_native_copies.items():
        if path not in output.entries or output.read(path) != raw:
            raise SingleplayerError('Native resource override or missing required copy: ' + path)
    # Only resources actually available in the installed MotS base are allowed
    # to fill a dependency. JKM.GOO is not the selected converted episode.
    omission_records = omissions.contracts(expected_files)
    template_omission_records = template_omissions.contracts(expected_files)
    typed_closure = verify_typed_literal_closure(output, archives, omission_records)
    report = {'status': ('structural-preservation-with-reviewed-source-omissions' if omission_records or template_omission_records
                       else 'structural-preservation-pass'), 'world_count': len(spec['worlds']),
            'episode_rows': len(episode_rows(source.read('episode.jk'))),
            'source_resource_exact_transforms': True, 'literal_resource_closure': not (omission_records or template_omission_records),
            'typed_resource_closure': typed_closure,
            'native_copy_identity': True, 'runtime_verified': False}
    if template_omission_records:
        report['template_resource_closure'] = False
        report['source_template_omissions'] = template_omission_records
        report['template_omission_limitations'] = 'Exact active missing local defaults retained under isolated names. Predicted missing-template behavior only; branch execution and retail parity untested.'
    return report


def readme_text(spec):
    """Append only explicitly reviewed behavior caveats to the existing text."""
    value = ('Experimental whole-episode SP conversion. Full gameplay remains unverified.\n'
        'Use OpenJKDF2 in MotS single-player mode (-motsCompat -sp), with only the declared startup profile.\n'
        'Copy the generated GOO to a private test installation episode folder; retain all original notices.\n'
        'No retail/custom assets or this converted output may be committed to the WBW repository.\n')
    if 'source_behavior_caveats' not in spec:
        return value
    caveats = spec['source_behavior_caveats']
    if (not isinstance(caveats, list) or not caveats or any(
            not isinstance(item, str) or not item.strip() or item != item.strip()
            or '\n' in item or '\r' in item for item in caveats)):
        raise SingleplayerError('Source behavior caveats must be a nonempty list of nonempty single-line strings')
    return value + '\nSource behavior caveats:\n' + ''.join('- ' + item + '\n' for item in caveats)


def build_to_directory(archives, original_path, stage, recipe_id):
    stage = Path(stage).resolve()
    project = Path(__file__).resolve().parent
    if stage == project or project in stage.parents:
        raise SingleplayerError('Generated SP assets must remain outside the source repository')
    if not stage.is_dir() or any(stage.iterdir()):
        raise SingleplayerError('Use an existing empty staging directory')
    readme = readme_text(recipe_details(recipe_id))
    originals, notices = open_original(original_path, recipe_id)
    data, manifest = build(archives, originals, recipe_id)
    verification = verify(archives, originals, recipe_id, data)
    manifest['verification'] = verification
    output = stage / recipe_details(recipe_id)['output_filename']
    with output.open('xb') as handle:
        handle.write(data)
    for name, content in notices.items():
        with (stage / name).open('xb') as handle:
            handle.write(content)
    manifest_filename = 'manifest.json'
    (stage / manifest_filename).write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf8')
    (stage / 'README.txt').write_text(readme, encoding='utf8')
    if output.read_bytes() != data:
        raise SingleplayerError('Post-write artifact verification failed')
    return {'filename': output.name, 'manifest_filename': manifest_filename,
            'verification': verification, 'startup_overlay': None}

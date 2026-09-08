"""Source-only forensic audit of the reviewed Caesar's Palace archive.

Reads user-owned resources; emits metadata only. It never extracts game assets,
changes an archive, supplies placeholders, starts a game, or certifies gameplay.
The waiver is deliberately restricted to exact source hashes and referrers.
"""
import argparse
from collections import deque
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import zipfile

from gob import Gob, ArchiveError, resource_name

CAESARS_GOB_SHA256 = '56393dc8b9c855e06799650d08dfe24268344d1fe3f6972140e2525ac3a4e3f0'
CAESARS_ZIP_SHA256 = 'b7a9f16b9141a4ef56c97784ef5a49914655a87ad6db59a2014429ee6ffe5fbd'
JK_HASHES = {
    'jkmp': '27a4b3642e0965753232f35b1e8e846c91df1eca1da77398b5efda66ca369a2e',
    'jkres': 'c75f7d5211bdd2e07a3af6a987c718037e8f0fd6909018ddb4327137bf3a7ebf',
    'jksnd': '6c6d51eca9c85dffe7dce9b449642a052f055352e3f817abf03b465da861aafd',
}
EXPECTED_REFERRERS = {
    'none.wav': ['jkl/caesars.jkl'],
    'windowout.mat': ['jkl/caesars.jkl'],
    'tv.mat': ['jkl/caesars.jkl'],
    '00_glass.mat': ['3do/shard0.3do', 'jkl/caesars.jkl'],
    'floor1.mat': ['jkl/caesars.jkl'],
    'kk60008.wav': ['cog/textvoice.cog', 'jkl/caesars.jkl'],
    'trap.wav': ['cog/destruct.cog', 'cog/grenade.cog', 'cog/raildet.cog',
                 'cog/seqcharge.cog', 'jkl/caesars.jkl'],
    'riverthrust.cog': ['jkl/caesars.jkl'],
    'window2.mat': ['jkl/caesars.jkl'],
    'discofloor.mat': ['jkl/caesars.jkl'],
    'disco.mat': ['jkl/caesars.jkl'],
}
CLASSIFICATIONS = {
    'windowout.mat': '19 total missing-material world surfaces: this material has 15, all geo=0.',
    'floor1.mat': 'Two world surfaces, both geo=0.',
    'window2.mat': 'Two world surfaces, both geo=0.',
    'tv.mat': 'No world surfaces; material table and 00_MATANIM instance 48 only.',
    'disco.mat': 'No world surfaces; material table and 00_MATANIM instance 108 only.',
    'discofloor.mat': 'No world surfaces; material table and 00_MATANIM instance 110 only.',
    '00_glass.mat': 'No world surfaces; owned JK shard0.3do has one solid geo=3, tex=0 face. Breaking-glass COGs instantiate its shard00 template.',
    'kk60008.wav': 'Sound preload plus textvoice.cog exposed default; sole instance 241 overrides voice with none.wav.',
    'none.wav': 'Explicit missing sound on instances 241 and 242. Intended silence is plausible but remains an inference.',
    'trap.wav': 'Missing activation sound in 15 placed trap scripts; projectile creation follows sound playback and does not depend on its return value.',
    'riverthrust.cog': 'Script table 54 and instance 56. Authentic separately recovered candidate has matching 50 fields but all sector/surface values -1; historical revision is unverified. Preserve absence; do not bundle or stub.',
}
FILE_REF = re.compile(r'(?<![\w.~])([\w+.~-]+\.(?:mat|cmp|3do|key|pup|snd|cog|wav|spr|par|ai))(?![\w.~])', re.I)
TEXT_EXTENSIONS = {'.jkl', '.3do', '.pup', '.snd', '.cog', '.spr', '.par', '.ai'}
SOURCES = [
    {'url': 'https://www.massassi.net/levels/files/1400.shtml', 'claim': 'Original author/catalogue context; no optional Caesar texture pack established.'},
    {'url': 'https://www.massassi.net/levels/files/2542.shtml', 'claim': 'SM Nesseight, 2003-09-07, first-person former-host testimony explicitly describes replacing Purgatory dflt.mat using resource/mat. This is another map, not evidence of Caesar image contents or an official optional pack.'},
    {'url': 'https://www.massassi.net/cog/both.html', 'claim': 'River Thrust catalogue credits Gandalv the Gray in JK Only subsection.'},
    {'url': 'https://www.massassi.net/cogfiles/both/riverthrust.cog', 'claim': 'Authentic candidate SHA256 0476afe206a9a529804b30473fa7b23ce0b3c5ea21cc09bb2b4898c0aba1169b; not proven exact Caesar revision.'},
]
ENGINE_EVIDENCE = [
    {'path': 'src/World/sithWorld.c:642', 'function': 'sithWorld_CalcWorldChecksum', 'claim': 'Hashes world/static compiled COG bytecode, vertices and selected thing-template fields; MAT/WAV bytes are not hashed. MotS additionally invokes its PER callback.'},
    {'path': 'src/World/sithThing.c:1945', 'function': 'sithThing_CalcThingChecksum', 'claim': 'Flags/type/movement/control plus selected physics, actor and weapon fields; no material or sound byte hashing.'},
    {'path': 'src/World/jkPlayer.c:2056', 'function': 'jkPlayer_ChecksumExtra', 'claim': 'MotS class PER parameters enter its additional checksum.'},
    {'path': 'src/World/sithMaterial.c:141', 'function': 'sithMaterial_Load', 'claim': 'Missing materials fall back to dflt.mat; if fallback also fails, loading can fail.'},
    {'path': 'src/Cog/sithCog.c:533', 'function': 'sithCog_ReadCogsListText', 'claim': 'A missing COG instance is skipped. Missing script loads also do not abort ReadCogScriptsListText at line1559.'},
    {'path': 'src/Cog/sithCogFunctionSound.c:22', 'function': 'sithCogFunctionSound_PlaySoundThing', 'claim': 'Missing sound pushes -1 and returns; caller COG continues.'},
    {'path': 'src/Main/jkRes.c:476', 'function': 'jkRes_FileOpen', 'claim': 'Supports loose resource paths as well as archives. Lookup order can allow a later loose directory to win; use an isolated installation and verify resolution.'},
]
for _item in ENGINE_EVIDENCE:
    _path, _line = _item['path'].rsplit(':', 1)
    _item['source_url'] = ('https://github.com/andreipemberton/OpenJKDF2-MotS-Fixes/blob/'
                          'f40e965bbe4133aef9e9b9eccabb2fbf0a34a9fb/' + _path + '#L' + _line)


def open_original(path):
    path = Path(path)
    if path.stat().st_size > 20_000_000:
        raise ValueError('Unsupported Caesar archive size')
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest == CAESARS_GOB_SHA256:
        return Gob(data, str(path))
    if digest != CAESARS_ZIP_SHA256:
        raise ValueError('Unsupported Caesar archive hash; requires a separate audit')
    with zipfile.ZipFile(BytesIO(data)) as archive:
        entries = [(item, resource_name(item.filename)) for item in archive.infolist()]
        names = [name for _, name in entries]
        if len(names) != 4 or set(names) != {'caesars.gob', 'readme.txt', 'credits.txt', 'credits.doc'}:
            raise ValueError('Unexpected Caesar ZIP directory')
        if archive.testzip() is not None:
            raise ValueError('Caesar ZIP CRC failure')
        entry = next(item for item, name in entries if name == 'caesars.gob')
        data = archive.read(entry)
    if hashlib.sha256(data).hexdigest() != CAESARS_GOB_SHA256:
        raise ValueError('Unexpected embedded Caesar GOB hash')
    return Gob(data, str(path) + ':caesars.gob')


def normalize_missing(missing):
    return {name.lower(): sorted(set(resource_name(ref) for ref in
            (details['referrers'] if isinstance(details, dict) else details)))
            for name, details in missing.items()}


def literal_references(data):
    value = data.decode('cp1252')
    active = '\n'.join(line.split('#', 1)[0].split('//', 1)[0] for line in value.splitlines())
    return {name.lower() for name in FILE_REF.findall(active)}


def legacy_omission_waiver(caesars, archives, missing):
    """Return exact reviewed missing references and reserved output names.

    Integration: add name_map before graph traversal; skip copying these names;
    keep missing COG placement arguments unchanged; waive only output references
    from the corresponding transformed referrers. Require every reserved name
    to remain absent from the output/native catalogue. No assets are supplied.
    """
    if caesars.sha256 != CAESARS_GOB_SHA256:
        raise ValueError('Caesar waiver requires the reviewed original archive')
    for role, expected in JK_HASHES.items():
        if role not in archives or archives[role].sha256 != expected:
            raise ValueError('Caesar waiver requires pinned JK archive: ' + role)
    if normalize_missing(missing) != EXPECTED_REFERRERS:
        raise ValueError('Missing dependency set/referrers differ from the reviewed eleven omissions')
    return {
        'policy': 'preserve-reviewed-original-omissions-v1',
        'source_sha256': caesars.sha256,
        'name_map': {name: 'br_' + name for name in sorted(EXPECTED_REFERRERS)},
        'original_referrers': EXPECTED_REFERRERS,
        'classifications': CLASSIFICATIONS,
        'intentionally_absent_names': ['br_' + name for name in sorted(EXPECTED_REFERRERS)],
        'substitute_assets': [],
        'omitted_original_behavior': [],
        'note': 'Original missing-loader behavior is preserved; no claim that authored intended assets were recovered or gameplay parity was established.',
    }


def waived_output_reference(reference, referrer, waiver, world_name='br_caesars.jkl'):
    """Exact name AND transformed referrer check, not a broad extension waiver."""
    referrer = resource_name(referrer)
    for old, new in waiver['name_map'].items():
        if reference.lower() != new:
            continue
        allowed = {'/'.join([str(Path(p).parent).replace('\\', '/'),
                   world_name if p == 'jkl/caesars.jkl' else 'br_' + Path(p).name])
                   for p in waiver['original_referrers'][old]}
        return referrer in allowed
    return False


def section(lines, start, end='end'):
    first = next(i for i, line in enumerate(lines) if line.lower().startswith(start.lower()))
    last = next((i for i in range(first + 1, len(lines)) if lines[i].lower().startswith(end.lower())), len(lines))
    return [(i + 1, lines[i]) for i in range(first + 1, last)]


def static_usage(caesars):
    lines = caesars.read('jkl/caesars.jkl').decode('cp1252').splitlines()
    materials = {int(m[1]): m[2].lower() for _, line in section(lines, 'World materials')
                 if (m := re.match(r'\s*(\d+):\s+(\S+)', line))}
    surfaces = {}
    for no, line in section(lines, 'World surfaces', 'World sectors'):
        m = re.match(r'\s*(\d+):\s+(.*)', line)
        if not m or len(t := m[2].split()) < 10:
            continue
        surfaces[int(m[1])] = {'line': no, 'material_index': int(t[0]), 'surface_flags': int(t[1], 0),
                              'face_flags': int(t[2], 0), 'geo': int(t[3]), 'adjoin': int(t[6])}
        if len(surfaces) == 6773:
            break
    adjoins = {int(m[1]): (int(m[2], 0), int(m[3]))
               for _, line in section(lines, 'World adjoins', 'World surfaces')
               if (m := re.match(r'\s*(\d+):\s+(\S+)\s+(\d+)', line))}
    sectors = set()
    current = None
    for _, line in section(lines, 'World sectors', 'Section: AIClass'):
        if m := re.match(r'SECTOR (\d+)', line, re.I):
            current = int(m[1]); sectors.add(current)
        elif m := re.match(r'SURFACES (\d+) (\d+)', line, re.I):
            first, count = map(int, m.groups())
            for sid in range(first, first + count):
                surfaces[sid]['sector'] = current
    spawns = []
    for no, line in section(lines, 'World things'):
        if m := re.match(r'\s*(\d+):\s+walkplayer\s+(.*)', line, re.I):
            spawns.append({'id': int(m[1]), 'line': no, 'sector': int(m[2].split()[7])})
    mirror_surface = {s['adjoin']: sid for sid, s in surfaces.items() if s['adjoin'] >= 0}
    graphs = [{s: set() for s in sectors} for _ in range(2)]
    for aid, (flags, mirror) in adjoins.items():
        src = surfaces[mirror_surface[aid]]['sector']
        dst = surfaces[mirror_surface[mirror]]['sector']
        graphs[0][src].add(dst)
        if flags & 2:
            graphs[1][src].add(dst)
    reached = []
    for graph in graphs:
        seen = {s['sector'] for s in spawns}; todo = list(seen)
        while todo:
            for nxt in graph[todo.pop()] - seen:
                seen.add(nxt); todo.append(nxt)
        reached.append(seen)
    placements = []
    for no, line in section(lines, 'World cogs'):
        if m := re.match(r'\s*(\d+):\s+(\S+)\s*(.*)', line):
            placements.append({'id': int(m[1]), 'line': no, 'script': m[2].lower(), 'args': m[3].split()})
    usage = {}
    for name in EXPECTED_REFERRERS:
        indices = [i for i, value in materials.items() if value == name]
        matched = [{'id': sid, **s, 'topological_path_from_spawn': s['sector'] in reached[0],
                    'passflag_path_from_spawn': s['sector'] in reached[1]}
                   for sid, s in surfaces.items() if s['material_index'] in indices]
        usage[name] = {'classification': CLASSIFICATIONS[name], 'material_indices': indices,
                       'surfaces': matched, 'placements_naming_asset': [p for p in placements if name == p['script'] or name in [a.lower() for a in p['args']]]}
    if len(surfaces) != 6773 or len(sectors) != 667 or len(placements) != 243 or len(spawns) != 6:
        raise ValueError('Static parser count disagreement')
    return {'resources': usage, 'counts': {'surfaces': len(surfaces), 'sectors': len(sectors), 'placements': len(placements), 'spawns': len(spawns)},
            'spawns': spawns, 'topological_reachable_sectors': len(reached[0]), 'passflag_reachable_sectors': len(reached[1]),
            'scope': 'Static adjacency only. This does not simulate collisions, doors, secrets, player movement, COG execution or rendered visibility.'}


def audit(caesars, jk_roots, resource_dir=None):
    paths = []
    for root in jk_roots:
        root = Path(root).resolve(strict=True)
        paths.extend(p for p in root.rglob('*') if p.is_file() and p.suffix.lower() == '.gob' and p.resolve().is_relative_to(root))
    archives = [Gob.open(p) for p in sorted(set(paths))]
    catalog = {}
    for arc in [caesars] + archives:
        for name in arc.entries:
            catalog.setdefault(name.split('/')[-1], (arc, name))
    pending = deque([('jkl/caesars.jkl', name) for name in literal_references(caesars.read('jkl/caesars.jkl'))])
    missing = {}; seen = set()
    while pending:
        referrer, name = pending.popleft()
        if name not in catalog:
            missing.setdefault(name, set()).add(referrer); continue
        if name in seen:
            continue
        seen.add(name)
        arc, path = catalog[name]
        if Path(path).suffix in TEXT_EXTENSIONS:
            pending.extend((path, ref) for ref in literal_references(arc.read(path)))
    missing = {name: sorted(refs) for name, refs in sorted(missing.items())}
    expected_archives = {'res1hi.gob', 'res2.gob', 'jk1.gob', 'jk1ctf.gob', 'jk1mp.gob'}
    have = {Path(a.label).name.lower() for a in archives}
    by_hash = {a.sha256: a for a in archives}
    pinned = {role: by_hash[digest] for role, digest in JK_HASHES.items() if digest in by_hash}
    waiver = None
    if expected_archives <= have and len(pinned) == 3 and missing == EXPECTED_REFERRERS:
        waiver = legacy_omission_waiver(caesars, pinned, missing)
    user_candidates = []
    if resource_dir is not None:
        root = Path(resource_dir).resolve(strict=True)
        for name in sorted(EXPECTED_REFERRERS):
            folders = ('', 'mat', '3do/mat') if name.endswith('.mat') else ('', 'sound') if name.endswith('.wav') else ('', 'cog')
            for folder in folders:
                p = root / folder / name
                if p.is_file():
                    if not p.resolve().is_relative_to(root):
                        raise ValueError('User resource resolves outside the selected directory')
                    user_candidates.append({'requested_name': name, 'path': str(p), 'bytes': p.stat().st_size,
                                            'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'status': 'candidate-only; not applied; authenticity and compatibility unverified'})
    return {'schema': 1, 'source_sha256': caesars.sha256, 'status': 'static-audit-only',
            'all_five_owned_jk_archive_names_present': expected_archives <= have,
            'jk_archives': [{'path': a.label, 'sha256': a.sha256, 'entries': len(a.entries),
                             'matches_for_reviewed_names': {n: [p for p in a.entries if p.split('/')[-1] == n] for n in EXPECTED_REFERRERS}} for a in archives],
            'missing_original_dependencies': missing, 'reviewed_legacy_omission_waiver': waiver,
            'static_usage': static_usage(caesars), 'user_resource_candidates': user_candidates,
            'resource_policy': 'Optional user resource directories are explicit candidate inputs. Never silently copy or replace absent files. Cosmetic MAT/WAV bytes do not enter the inspected port world checksum, but checksum acceptance does not prove matching gameplay, sound IDs, rendering or retail-peer compatibility. Adding COG code can change checksums and behavior. Keep executable resource repairs separate and synchronize reviewed packages across peers.',
            'engine_evidence': ENGINE_EVIDENCE, 'primary_sources': SOURCES,
            'limits': ['The retail executable checksum was not disassembled or tested here; engine facts describe the current OpenJKDF2/OpenMotS source.',
                       'No missing file content, optional Caesar pack or restoration intent is inferred from a filename.',
                       'No hosting, gameplay, visual or full compatibility claim follows from this audit.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--caesars', required=True, type=Path)
    parser.add_argument('--jk-root', required=True, action='append', type=Path)
    parser.add_argument('--resource-dir', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = audit(open_original(args.caesars), args.jk_root, args.resource_dir)
        payload = json.dumps(result, indent=2) + '\n'
        if args.output:
            with args.output.open('x', encoding='utf-8') as stream:
                stream.write(payload)
        else:
            print(payload, end='')
    except (OSError, ValueError, ArchiveError, zipfile.BadZipFile) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()

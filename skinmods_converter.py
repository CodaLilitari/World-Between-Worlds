"""Exact optional skin recipes: preserve native registrations and animation bindings.

No assets are embedded. This adapter accepts only catalogued source ZIPs and
owned archives. Static skeleton/resource checks are not animation/render parity.
"""
import copy
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import zipfile

import bridge
from gob import Gob, build_gob, resource_name
import skinmods_catalog as catalog


class SkinError(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise SkinError(message)


def recipe_details(recipe_id):
    require(recipe_id in catalog.SPECS, 'Unknown reviewed skin recipe')
    return copy.deepcopy(catalog.SPECS[recipe_id])


def original_hashes(recipe_id):
    return {recipe_details(recipe_id)['zip_sha256']}


def catalog_entries():
    return [{'id': key, 'title': spec['title'], 'author': spec['author'], 'kind': 'mod',
             'gameplay': ['mp'], 'requires_archive': True, 'archive_hint': spec['archive_hint'],
             'source_url': spec['source_url'], 'download_url': spec['download_url'],
             'status': 'prototype', 'startup_overlay': spec['startup_overlay'],
             'legacy_filenames': [spec['filename']], 'output_filename': spec['filename'],
             'runtime_test': copy.deepcopy(spec['runtime_test']),
             'summary': spec.get('summary', 'Optional additional MP skin; native model list retained, private assets isolated. Appearance and peer checks are separate.')}
            for key, spec in catalog.SPECS.items()]


def read_original(path, spec):
    path = Path(path)
    require(path.stat().st_size == spec['zip_bytes'] and path.stat().st_size < 16*1024**2,
            'Choose the reviewed original skin ZIP')
    raw = path.read_bytes()
    require(digest(raw) == spec['zip_sha256'], 'Original ZIP hash differs')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        expected = {x['path']: x for x in spec['zip_members']}
        files = z.infolist()
        require(len(files) == len(expected) and {x.filename for x in files} == set(expected), 'Original ZIP members differ')
        members = {}
        for item in files:
            require(item.file_size == expected[item.filename]['bytes'] and item.file_size < 32*1024**2, 'ZIP member size differs')
            members[item.filename] = z.read(item)
            require(digest(members[item.filename]) == expected[item.filename]['sha256'], 'ZIP member hash differs')
    if spec.get('source_format') == 'loose-zip':
        original = map_loose_source(members, spec)
        return original, members[spec['readme_member']]
    payload = bytearray(members[spec['gob_member']])
    require(digest(payload) == spec['gob_sha256'], 'Original GOB hash differs')
    if spec.get('identical_duplicate_repair'):
        payload = bytearray(repair_identical_duplicates(payload, spec['identical_duplicate_repair']))
    # A reviewed legacy metadata path normalization, gated by the entire GOB.
    table = struct.unpack_from('<I', payload, 8)[0]
    count = struct.unpack_from('<I', payload, table)[0]
    for old, new in spec.get('directory_repairs', []):
        changed = 0
        for i in range(count):
            offset = table + 4 + i * 136 + 8
            name = bytes(payload[offset:offset+128]).split(b'\0', 1)[0]
            if name == old.encode('cp1252'):
                payload[offset:offset+128] = new.encode('cp1252').ljust(128, b'\0')
                changed += 1
        require(changed == 1, 'Pinned legacy directory repair no longer matches once')
    original = Gob(payload)
    require(original.sha256 == spec['normalized_gob_sha256'], 'Normalized GOB hash differs')
    actual = {p:(e.size, digest(original.read(p))) for p,e in original.entries.items()}
    require(actual == {p:(r['bytes'],r['sha256']) for p,r in spec['resources'].items()}, 'Source resource inventory differs')
    return original, members[spec['readme_member']]


def repair_identical_duplicates(payload, plan):
    """Remove only pinned, byte-identical directory copies; keep strict Gob parsing."""
    require(len(payload) == plan['archive_bytes'] and digest(payload) == plan['archive_sha256'],
            'Duplicate repair archive pin differs')
    require(len(payload) >= 16 and payload[:8] == b'GOB \x14\x00\x00\x00', 'Duplicate repair header differs')
    table = struct.unpack_from('<I', payload, 8)[0]
    require(table == plan['table_offset'] and 12 <= table <= len(payload)-4, 'Duplicate repair table differs')
    count = struct.unpack_from('<I', payload, table)[0]
    end = table + 4 + count * 136
    require(count == plan['entry_count'] and end <= len(payload), 'Duplicate repair entry count differs')
    entries, grouped = [], {}
    for index in range(count):
        off, size, raw = struct.unpack_from('<II128s', payload, table+4+index*136)
        require(b'\0' in raw, 'Duplicate repair filename is unterminated')
        name = resource_name(raw.split(b'\0', 1)[0].decode('cp1252'))
        require(off >= 12 and off+size <= len(payload) and not (size and off < end and off+size > table),
                'Duplicate repair resource bounds differ')
        row = {'index':index, 'offset':off, 'bytes':size, 'sha256':digest(payload[off:off+size])}
        entries.append(row)
        grouped.setdefault(name, []).append(row)
    extents = sorted((row['offset'],row['offset']+row['bytes']) for row in entries if row['bytes'])
    require(all(left[1] <= right[0] for left,right in zip(extents,extents[1:])),
            'Duplicate repair source payloads overlap')
    actual = {name:rows for name,rows in grouped.items() if len(rows)>1}
    expected = {row['path']:row['entries'] for row in plan['duplicates']}
    require(len(expected) == len(plan['duplicates']) and actual == expected, 'Pinned duplicate membership differs')
    removed = set()
    for name, rows in actual.items():
        require(len(rows) == 2, 'Duplicate repair requires exactly two copies')
        first, second = rows
        left = payload[first['offset']:first['offset']+first['bytes']]
        right = payload[second['offset']:second['offset']+second['bytes']]
        require(left == right, 'Duplicate resources have different bytes: '+name)
        removed.add(second['index'])
    require(len(removed) == plan['removed_count'] and bool(removed), 'Duplicate repair removal count differs')
    # Preserve offsets and every payload byte. Vacated directory slots become padding.
    result = bytearray(payload)
    kept = b''.join(payload[table+4+i*136:table+4+(i+1)*136] for i in range(count) if i not in removed)
    struct.pack_into('<I', result, table, count-len(removed))
    result[table+4:end] = kept + b'\0'*(136*len(removed))
    Gob(result)  # Still rejects unsafe paths, unreviewed duplicates and overlapping payloads.
    return bytes(result)


def map_loose_source(members, spec):
    """Apply one exact catalogued readme layout; never infer directories by suffix."""
    layout = spec['source_layout']
    require(set(layout) == set(members), 'Loose ZIP layout does not cover every pinned member')
    files = {}
    for source, target in layout.items():
        require(resource_name(target) == target, 'Loose layout path is not normalized')
        require(target not in files, 'Loose source layout has a duplicate virtual path')
        files[target] = members[source]
    # This private in-memory index is not represented as a GOB from the author.
    original = Gob(build_gob(files))
    require(original.sha256 == spec['mapped_source_sha256'], 'Readme-mapped source inventory differs')
    actual = {p: (e.size, digest(original.read(p))) for p, e in original.entries.items()}
    require(actual == {p: (r['bytes'], r['sha256']) for p, r in spec['resources'].items()},
            'Loose source resource inventory differs')
    return original


def source_registration_paths(spec):
    return set(spec.get('registration_source_paths', ['misc/models.dat']))


def hierarchy(data):
    text = bridge.text(data)
    match = re.search(r'(?im)^HIERARCHY NODES\s+(\d+)\s*$', text)
    require(match is not None, 'Model has no hierarchy')
    rows = [line.split() for line in text[match.end():].splitlines()
            if re.match(r'^\s*\d+:', line)]
    count = int(match.group(1))
    require(len(rows) == count and all(len(row) == 18 for row in rows), 'Malformed hierarchy rows')
    require([int(row[0][:-1]) for row in rows] == list(range(count)), 'Hierarchy node indices differ')
    # Skin meshes/translations vary, but animation node identities and topology must match.
    return [(int(row[1],16), int(row[2],16), *map(int,row[4:8]), row[17].lower()) for row in rows]


def validate_native(archives, spec, original):
    expected = spec['mapped_source_sha256'] if spec.get('source_format') == 'loose-zip' else spec['normalized_gob_sha256']
    require(original.sha256 == expected, 'Original object changed after source loading')
    for key, expected in spec['owned_hashes'].items():
        require(key in archives and archives[key].sha256 == expected, 'Owned archive changed: '+key)
    for row in spec['native_dependencies']:
        require(digest(archives[row['archive']].read(row['path'])) == row['sha256'], 'Native dependency changed: '+row['path'])
    for row in spec.get('source_omissions', []):
        source = row['source_path']
        require(source in spec['resources'] and source.endswith('.snd')
                and spec['resources'][source]['output_path'] == row['output_path'], 'Omission referrer differs')
        data = original.read(source)
        require(digest(data) == row['source_sha256'] == spec['resources'][source]['sha256'], 'Omission source hash differs')
        require(row['source_gob_sha256'] == spec['gob_sha256'], 'Omission source archive pin differs')
        require(row['count'] == 1 and row['candidate_paths'] == ['sound/'+row['token'],'voice/'+row['token']],
                'Omission path/count contract differs')
        pairs = [line.split()[:2] for line in bridge.active_lines(bridge.text(data)).splitlines() if line.split()]
        require(pairs.count([row['event'],row['token']]) == row['count'], 'Omission event/token count differs')
        require(all(p not in original.entries and all(p not in g.entries for g in archives.values())
                    for p in row['candidate_paths']), 'Previously missing sound now has a provider')
    native = hierarchy(archives['motsres'].read('3do/ky.3do'))
    for row in spec['models_added']:
        require(hierarchy(original.read('3do/'+row['model'])) == native, 'Skin node identities/topology differ from native Kyle')
    for row in spec['animation_checks']:
        data = archives['motsres'].read(row['path'])
        require(digest(data) == row['sha256'], 'Native animation source changed')
        nodes = [int(x) for x in re.findall(r'(?im)^node\s+(\d+)', bridge.text(data))]
        require(nodes == row['nodes'], 'Native animation node list changed')
    if spec.get('source_registration_review'):
        review = spec['source_registration_review']
        rows = model_rows(original.read('misc/models.dat'))
        require(rows == review['source_rows'], 'Original skin registrations differ')
        stock = model_rows(archives[review['stock_source_archive']].read('misc/models.dat'))
        require(rows[:review['stock_row_count']] == stock, 'Authored prefix differs from owned JK registrations')
        added = [[r['source_index'], r['model'], r['soundclass']] for r in spec['models_added']]
        require(rows[review['stock_row_count']:] == added, 'Added skins differ from authored registration tail')
        labels = {}
        for key, value in re.findall(r'(?m)^\s*"([^"]+)"\s+-?\d+\s+"([^"]*)"',
                                     original.read('ui/jkstrings.uni').decode('cp1252')):
            labels.setdefault(key.lower(), set()).add(value)
        for row in spec['models_added']:
            require(labels.get(Path(row['model']).stem.lower()) == {row['display_name']},
                    'Skin label differs from the exact authored UI entry')


def model_rows(data):
    text = data.decode('cp1252')
    rows = []
    for line in bridge.active_lines(text).splitlines():
        match = re.match(r'^\s*(\d+):\s+(\S+)\s+(\S+)(?:\s+\d+)?\s*$', line)
        if match:
            rows.append([int(match[1]), match[2].lower(), match[3].lower()])
    headers = re.findall(r'(?im)^\s*numModels:\s*(\d+)\s*$', text)
    require(len(headers) == 1 and int(headers[0]) == len(rows), 'Model registration count differs')
    require([r[0] for r in rows] == list(range(len(rows))), 'Model registration indices differ')
    return rows


def transform(data, edits):
    for edit in edits:
        old, new = edit['old'].encode('cp1252'), edit['new'].encode('cp1252')
        # Exact resource-token anchors prevent hand.mat from changing bhand.mat.
        pattern = re.compile(rb'(?<![\w.~&-])'+re.escape(old)+rb'(?![\w.~&-])',0 if edit.get('case_sensitive') else re.I)
        require(len(pattern.findall(data)) == edit['count'], 'Resource-token edit count differs')
        data = pattern.sub(lambda _:new,data)
    return data


def models_table(native, spec):
    count = spec['native_model_count']
    existing = model_rows(native)
    require(len(existing) == count, 'Native model registration count differs')
    new_names = [row['output_model'].lower() for row in spec['models_added']]
    require(len(set(new_names)) == len(new_names) and not set(new_names) & {row[1] for row in existing},
            'Added model names duplicate another registration')
    old = f'numModels: {count}'.encode('ascii')
    require(native.count(old) == 1, 'Native model count anchor changed')
    rows = []
    for i,row in enumerate(spec['models_added'],count):
        rows.append(f"{i}: {row['output_model']} {row['output_soundclass']} {row['personality']}\r\n".encode('ascii'))
    return native.replace(old, f'numModels: {count+len(rows)}'.encode('ascii'),1)+b'\r\n'+b''.join(rows)


def ui_table(native, spec):
    text = native.decode('cp1252')
    additions = ''.join(f'"{row["output_model"].split(".")[0].upper()}" 0 "{row["display_name"]}"\r\n'
                        for row in spec['models_added'])
    for row in spec['models_added']:
        require('"'+row['output_model'].split('.')[0].upper()+'"' not in text.upper(), 'UI label already exists')
    match = re.search(r'(?im)^END\b',text)
    require(match is not None and len(re.findall(r'(?im)^END\b',text))==1, 'Native UI terminator differs')
    text = text[:match.start()]+additions+text[match.start():]
    count = len(re.findall(r'(?m)^\s*"[^"]*"\s+-?\d+\s+"[^"]*"',text))
    text, n = re.subn(r'(?m)^MSGS\s+\d+',f'MSGS {count}',text)
    require(n == 1, 'Native UI header differs')
    return text.encode('cp1252')


def verify_references(files, spec):
    native={row['path'] for row in spec['native_dependencies']}
    omissions = {}
    for row in spec.get('source_omissions', []):
        key = (row['output_path'],row['event'],row['token'])
        require(key not in omissions and row['output_path'] in files and row['count'] == 1,
                'Omission declaration is duplicated or incomplete')
        require(digest(files[row['output_path']]) == row['output_sha256'], 'Omission output referrer hash differs')
        require(row['candidate_paths'] == ['sound/'+row['token'],'voice/'+row['token']], 'Omission resolver paths differ')
        omissions[key] = row['count']
    observed = {}
    for row in spec['models_added']:
        require('3do/'+row['output_model'] in files and 'misc/snd/'+row['output_soundclass'] in files,
                'Added model or authored soundclass is absent')
    for path,data in files.items():
        if path.endswith('.3do'):
            require(not re.search(r'[\w.~&+/-]+[/\\][\w.~&+-]+\.mat\b', bridge.active_lines(bridge.text(data)), re.I),
                    'Qualified model material requires an explicitly reviewed resolver context')
            refs=bridge.references(bridge.text(data))
            require(all(name.endswith('.mat') for name in refs),'Unexpected model resource type')
            groups=[(None,name,('mat/'+name,'3do/mat/'+name)) for name in refs]
        elif path.endswith('.snd'):
            rows=[line.split() for line in bridge.active_lines(bridge.text(data)).splitlines() if line.split()]
            require(all(len(row)>=2 and row[1].lower().endswith('.wav') and '/' not in row[1] and '\\' not in row[1] for row in rows),'Soundclass contains an unresolved/unsupported sound token')
            groups=[(row[0],row[1].lower(),('sound/'+row[1].lower(),'voice/'+row[1].lower())) for row in rows]
        else:
            continue
        for event,token,candidates in groups:
            if any(name in files or name in native for name in candidates):
                continue
            key = (path,event,token)
            require(key in omissions,'Unresolved typed resource: '+path+' -> '+str(candidates))
            observed[key] = observed.get(key,0)+1
    require(observed == omissions, 'Declared original omission was changed, duplicated or filled')


def build(archives, original, spec):
    validate_native(archives,spec,original)
    files, provenance = {}, {}
    for source_path,row in spec['resources'].items():
        if source_path in source_registration_paths(spec):
            continue
        target = row['output_path']
        data = transform(original.read(source_path),row.get('edits',[]))
        require(target not in files, 'Duplicate output resource')
        files[target] = data
        if spec.get('source_format') == 'loose-zip':
            provenance[target] = {'archive':'original_zip','archive_sha256':spec['zip_sha256'],
                                  'path':row['source_zip_path'],'virtual_path':source_path,
                                  'layout_reason':row.get('layout_reason','Exact original readme installation directory'),
                                  'sha256':row['sha256'],'edits':row.get('edits',[])}
        else:
            provenance[target] = {'archive':'original','archive_sha256':spec['gob_sha256'],
                                  'path':source_path,'sha256':row['sha256'],'edits':row.get('edits',[])}
    for row in spec['retail_dependencies']:
        data = archives[row['archive']].read(row['path'])
        require(digest(data)==row['sha256'],'Owned dependency differs')
        require(row['output_path'] not in files, 'Dependency output collision')
        files[row['output_path']]=transform(data,row.get('edits',[]));provenance[row['output_path']]=copy.deepcopy(row)
    files['misc/models.dat']=models_table(archives['motsres'].read('misc/models.dat'),spec)
    files['ui/jkstrings.uni']=ui_table(archives['motssnd'].read('ui/jkstrings.uni'),spec)
    for path,key in [('misc/models.dat','motsres'),('ui/jkstrings.uni','motssnd')]:
        provenance[path]={'archive':key,'path':path,'sha256':digest(archives[key].read(path)),
                          'operation':'preserve native table and append declared skin records only'}
    overlaps={path for path in files if any(path in archives[k].entries for k in ('motsres','motssnd'))}
    require(overlaps=={'misc/models.dat','ui/jkstrings.uni'},'Unexpected native resource override')
    native_leaves={Path(p).name for k in ('motsres','motssnd') for p in archives[k].entries}
    require(not any(Path(p).name in native_leaves for p in files if Path(p).suffix in {'.3do','.mat','.snd','.wav'}),
            'New skin asset aliases a native loader/cache basename')
    verify_references(files,spec)
    payload=build_gob(files)
    manifest={'schema':1,'recipe':spec['recipe'],'startup_overlay':spec['startup_overlay'],
              'source_zip_sha256':spec['zip_sha256'],'output_sha256':digest(payload),
              'models_added':copy.deepcopy(spec['models_added']),
              'native_overrides':sorted(overlaps),'skeleton_check':'Native Kyle node identity/topology match; geometry and rest transforms preserved from source.',
              'animation_limit':'Native ky.pup references 63 keys. Three native keys include node18 beyond the 18-node stock Kyle too; no new mismatch introduced. This is not animated pose/weapon attachment validation.',
              'runtime_test':copy.deepcopy(spec['runtime_test']),
              'resources':[{'path':p,'bytes':len(data),'sha256':digest(data),'origin':provenance[p]}
                           for p,data in sorted(files.items())],
              'native_dependencies':copy.deepcopy(spec['native_dependencies'])}
    if spec.get('source_format') == 'loose-zip':
        manifest['source_format'] = 'loose-zip'
        manifest['source_layout'] = copy.deepcopy(spec['source_layout'])
    if spec.get('source_registration_review'):
        manifest['source_registration_review'] = copy.deepcopy(spec['source_registration_review'])
    if spec.get('identical_duplicate_repair'):
        manifest['identical_duplicate_repair'] = copy.deepcopy(spec['identical_duplicate_repair'])
    if spec.get('source_omissions'):
        manifest['source_omissions'] = copy.deepcopy(spec['source_omissions'])
    if spec.get('native_reference_differences'):
        manifest['native_reference_differences'] = copy.deepcopy(spec['native_reference_differences'])
    return payload,manifest


def reverse_edits(data, edits, source_path):
    for edit in reversed(edits):
        pattern=re.compile(rb'(?<![\w.~&-])'+re.escape(edit['new'].encode('cp1252'))+rb'(?![\w.~&-])',0 if edit.get('case_sensitive') else re.I)
        require(len(pattern.findall(data))==edit['count'],'Output rewrite multiplicity differs: '+source_path+' '+edit['new'])
        data=pattern.sub(lambda _:edit['old'].encode('cp1252'),data)
    return data


def verify(archives, original, payload, spec):
    validate_native(archives,spec,original)
    out=Gob(payload)
    expected={row['output_path'] for p,row in spec['resources'].items() if p not in source_registration_paths(spec)}
    expected|={row['output_path'] for row in spec['retail_dependencies']}|{'misc/models.dat','ui/jkstrings.uni'}
    require(set(out.entries)==expected,'Output resource set differs')
    for source_path,row in spec['resources'].items():
        if source_path in source_registration_paths(spec):continue
        data=out.read(row['output_path'])
        # Reverse every declared replacement independently to recover exact source bytes.
        data=reverse_edits(data,row.get('edits',[]),source_path)
        require(data==original.read(source_path),'Reversing declared edits did not recover exact authored bytes: '+source_path)
    for row in spec['retail_dependencies']:
        recovered=reverse_edits(out.read(row['output_path']),row.get('edits',[]),row['path'])
        require(recovered==archives[row['archive']].read(row['path']),'Owned dependency bytes changed outside declared edits')
    require(out.read('misc/models.dat')==models_table(archives['motsres'].read('misc/models.dat'),spec),'Native model table differs outside declared additions')
    require(out.read('ui/jkstrings.uni')==ui_table(archives['motssnd'].read('ui/jkstrings.uni'),spec),'Native UI table differs outside declared additions')
    require(not any(Path(p).suffix in {'.cog','.jkl','.key','.pup'} for p in out.entries),'Unexpected gameplay or animation override')
    verify_references({p:out.read(p) for p in out.entries},spec)
    return {'ok':True,'resource_count':len(out.entries),'native_model_count_preserved':spec['native_model_count'],
            'added_models':len(spec['models_added']),'scope':'Exact source/path/table and static skeleton checks; runtime, appearance and peers separate.'}


def build_to_directory(archives, original_path, stage, recipe_id):
    spec=recipe_details(recipe_id);stage=Path(stage)
    require(not stage.resolve().is_relative_to(Path(bridge.__file__).resolve().parent),'Keep conversions outside the source repository')
    root=stage/spec['startup_overlay'];require(not root.exists(),'Output directory already exists')
    original,readme=read_original(original_path,spec)
    payload,manifest=build(archives,original,spec);verification=verify(archives,original,payload,spec)
    notices = {}
    if spec.get('additional_notice_members'):
        raw = Path(original_path).read_bytes()
        require(digest(raw) == spec['zip_sha256'], 'Original ZIP changed before notice preservation')
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for row in spec['additional_notice_members']:
                target = row['output_filename']
                require(resource_name(target) == target.lower() and '/' not in target and '\\' not in target
                        and target.lower() not in {'readme.txt','original-readme.txt',spec['filename'].lower(),
                                                  (spec['filename']+'.manifest.json').lower()}, 'Unsafe notice target')
                require(target.lower() not in {n.lower() for n in notices}, 'Duplicate notice target')
                data = z.read(row['member'])
                require(len(data) == row['bytes'] and digest(data) == row['sha256'], 'Original notice differs')
                notices[target] = data
    root.mkdir(parents=True);(root/spec['filename']).write_bytes(payload)
    manifest_name=spec['filename']+'.manifest.json';(root/manifest_name).write_text(json.dumps(manifest,indent=2)+'\n')
    (root/'ORIGINAL-README.txt').write_bytes(readme)
    for target,data in notices.items():
        (root/target).write_bytes(data)
    (root/'README.txt').write_text(spec['title']+' for MotS - optional skin prototype\n\n'+
        'Author: '+spec['author']+'\nKeep the original readme and credits with this local conversion.\n'+
        'Launch OpenJKDF2 in MotS multiplayer with one startup overlay only: -motsCompat -path '+spec['startup_overlay']+'\n'+
        'Choose '+', '.join(x['display_name'] for x in spec['models_added'])+' in multiplayer character setup. Native characters remain.\n'+
        'All peers need the exact same recipe/output. Restart when changing overlays.\n'+
        'Do not upload this conversion or its game/mod assets. Animated poses, appearance and peer synchronization require separate tests.\n'+
        ''.join('\nOpen finding: '+finding+'\n' for finding in spec.get('review_findings', [])))
    verification=verify(archives,original,(root/spec['filename']).read_bytes(),spec)
    require((root/'ORIGINAL-README.txt').read_bytes()==readme,'Written original readme differs')
    require(all((root/target).read_bytes()==data for target,data in notices.items()), 'Written original notice differs')
    return {'filename':(root/spec['filename']).relative_to(stage).as_posix(),
            'manifest_filename':(root/manifest_name).relative_to(stage).as_posix(),
            'verification':verification,'startup_overlay':spec['startup_overlay']}

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
from gob import Gob, build_gob
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
             'summary': 'Optional additional MP skin; native model list retained, private assets isolated. Appearance and peer checks are separate.'}
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
    payload = bytearray(members[spec['gob_member']])
    require(digest(payload) == spec['gob_sha256'], 'Original GOB hash differs')
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
    require(original.sha256 == spec['normalized_gob_sha256'], 'Original object changed after source loading')
    for key, expected in spec['owned_hashes'].items():
        require(key in archives and archives[key].sha256 == expected, 'Owned archive changed: '+key)
    for row in spec['native_dependencies']:
        require(digest(archives[row['archive']].read(row['path'])) == row['sha256'], 'Native dependency changed: '+row['path'])
    native = hierarchy(archives['motsres'].read('3do/ky.3do'))
    for row in spec['models_added']:
        require(hierarchy(original.read('3do/'+row['model'])) == native, 'Skin node identities/topology differ from native Kyle')
    for row in spec['animation_checks']:
        data = archives['motsres'].read(row['path'])
        require(digest(data) == row['sha256'], 'Native animation source changed')
        nodes = [int(x) for x in re.findall(r'(?im)^node\s+(\d+)', bridge.text(data))]
        require(nodes == row['nodes'], 'Native animation node list changed')


def transform(data, edits):
    for edit in edits:
        old, new = edit['old'].encode('cp1252'), edit['new'].encode('cp1252')
        # Exact resource-token anchors prevent hand.mat from changing bhand.mat.
        pattern = re.compile(rb'(?<![\w.~&-])'+re.escape(old)+rb'(?![\w.~&-])',re.I)
        require(len(pattern.findall(data)) == edit['count'], 'Resource-token edit count differs')
        data = pattern.sub(lambda _:new,data)
    return data


def models_table(native, spec):
    count = spec['native_model_count']
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
        require('"'+row['output_model'].split('.')[0].upper()+'"' not in text, 'UI label already exists')
    match = re.search(r'(?im)^END\b',text)
    require(match is not None and len(re.findall(r'(?im)^END\b',text))==1, 'Native UI terminator differs')
    text = text[:match.start()]+additions+text[match.start():]
    count = len(re.findall(r'(?m)^\s*"[^"]*"\s+-?\d+\s+"[^"]*"',text))
    text, n = re.subn(r'(?m)^MSGS\s+\d+',f'MSGS {count}',text)
    require(n == 1, 'Native UI header differs')
    return text.encode('cp1252')


def verify_references(files, spec):
    native={row['path'] for row in spec['native_dependencies']}
    for row in spec['models_added']:
        require('3do/'+row['output_model'] in files and 'misc/snd/'+row['output_soundclass'] in files,
                'Added model or authored soundclass is absent')
    for path,data in files.items():
        if path.endswith('.3do'):
            refs=bridge.references(bridge.text(data))
            require(all(name.endswith('.mat') for name in refs),'Unexpected model resource type')
            groups=[('mat/'+name,'3do/mat/'+name) for name in refs]
        elif path.endswith('.snd'):
            rows=[line.split() for line in bridge.active_lines(bridge.text(data)).splitlines() if line.split()]
            require(all(len(row)>=2 and row[1].lower().endswith('.wav') for row in rows),'Soundclass contains an unresolved/unsupported sound token')
            groups=[('sound/'+row[1].lower(),'voice/'+row[1].lower()) for row in rows]
        else:
            continue
        for candidates in groups:
            require(any(name in files or name in native for name in candidates),'Unresolved typed resource: '+path+' -> '+str(candidates))


def build(archives, original, spec):
    validate_native(archives,spec,original)
    files, provenance = {}, {}
    for source_path,row in spec['resources'].items():
        if source_path == 'misc/models.dat':
            continue
        target = row['output_path']
        data = transform(original.read(source_path),row.get('edits',[]))
        require(target not in files, 'Duplicate output resource')
        files[target] = data
        provenance[target] = {'archive':'original','archive_sha256':spec['gob_sha256'],
                              'path':source_path,'sha256':row['sha256'],'edits':row.get('edits',[])}
    for row in spec['retail_dependencies']:
        data = archives[row['archive']].read(row['path'])
        require(digest(data)==row['sha256'],'Owned dependency differs')
        require(row['output_path'] not in files, 'Dependency output collision')
        files[row['output_path']]=data;provenance[row['output_path']]=copy.deepcopy(row)
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
    return payload,manifest


def verify(archives, original, payload, spec):
    validate_native(archives,spec,original)
    out=Gob(payload)
    expected={row['output_path'] for p,row in spec['resources'].items() if p!='misc/models.dat'}
    expected|={row['output_path'] for row in spec['retail_dependencies']}|{'misc/models.dat','ui/jkstrings.uni'}
    require(set(out.entries)==expected,'Output resource set differs')
    for source_path,row in spec['resources'].items():
        if source_path=='misc/models.dat':continue
        data=out.read(row['output_path'])
        # Reverse every declared replacement independently to recover exact source bytes.
        for edit in reversed(row.get('edits',[])):
            pattern=re.compile(rb'(?<![\w.~&-])'+re.escape(edit['new'].encode('cp1252'))+rb'(?![\w.~&-])',re.I)
            require(len(pattern.findall(data))==edit['count'],'Output rewrite multiplicity differs: '+source_path+' '+edit['new'])
            # Each accepted source token spelling is pinned; inverse edits recover it.
            data=pattern.sub(lambda _:edit['old'].encode('cp1252'),data)
        require(data==original.read(source_path),'Reversing declared edits did not recover exact authored bytes: '+source_path)
    for row in spec['retail_dependencies']:
        require(out.read(row['output_path'])==archives[row['archive']].read(row['path']),'Owned dependency bytes changed')
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
    root.mkdir(parents=True);(root/spec['filename']).write_bytes(payload)
    manifest_name=spec['filename']+'.manifest.json';(root/manifest_name).write_text(json.dumps(manifest,indent=2)+'\n')
    (root/'ORIGINAL-README.txt').write_bytes(readme)
    (root/'README.txt').write_text(spec['title']+' for MotS - optional skin prototype\n\n'+
        'Author: '+spec['author']+'\nKeep the original readme and credits with this local conversion.\n'+
        'Launch OpenJKDF2 in MotS multiplayer with one startup overlay only: -motsCompat -path '+spec['startup_overlay']+'\n'+
        'Choose '+', '.join(x['display_name'] for x in spec['models_added'])+' in multiplayer character setup. Native characters remain.\n'+
        'All peers need the exact same recipe/output. Restart when changing overlays.\n'+
        'Do not upload this conversion or its game/mod assets. Animated poses, appearance and peer synchronization require separate tests.\n')
    verification=verify(archives,original,(root/spec['filename']).read_bytes(),spec)
    require((root/'ORIGINAL-README.txt').read_bytes()==readme,'Written original readme differs')
    return {'filename':(root/spec['filename']).relative_to(stage).as_posix(),
            'manifest_filename':(root/manifest_name).relative_to(stage).as_posix(),
            'verification':verification,'startup_overlay':spec['startup_overlay']}

"""Synthetic assets only; no game/mod files are test inputs."""
import io
import copy
import json
from pathlib import Path
import tempfile
import struct
import unittest
from unittest.mock import patch
import zipfile

from gob import Gob, build_gob
import skinmods_converter as c


def model(parent=0):
    return ('HIERARCHY NODES 2\n'
            '0: 0x0 0x10 -1 -1 1 -1 1 0 0 0 0 0 0 0 0 0 root\n'
            f'1: 0x0 0x4 0 {parent} -1 -1 0 0 0 0 0 0 0 0 0 0 hand\n').encode()


class SkinConverterTests(unittest.TestCase):
    def fixture(self):
        native = {
            'motsres': Gob(build_gob({'3do/ky.3do': model(),
                'misc/models.dat': b'numModels: 2\r\n0: old.3do old.snd 3 # native\r\n1: team.3do old.snd 0\r\n'})),
            'motssnd': Gob(build_gob({'ui/jkstrings.uni': b'MSGS 2\r\n"NATIVE" 0 "Native"\r\n"DUP" 0 "First"\r\nEND\r\n'})),
        }
        files = {'3do/skin.3do': b'MATERIALS 1\n0: panel.mat\n'+model(), 'mat/panel.mat': b'synthetic material bytes',
                 'misc/snd/skin.snd':b'walk ping.wav\n','sound/ping.wav':b'synthetic sound bytes',
                 'misc/models.dat': b'numModels: 1\n0: skin.3do ky.snd\n', 'readme.txt': b'fictional readme'}
        original = Gob(build_gob(files))
        resources = {p:{'bytes':len(data),'sha256':c.digest(data),
                       'output_path': 'wbw/readme.txt' if p=='readme.txt' else p.replace('skin.3do','sk_skin.3do').replace('panel.mat','sk_panel.mat').replace('skin.snd','sk_skin.snd').replace('ping.wav','sk_ping.wav'),
                       'edits':[]} for p,data in files.items()}
        resources['3do/skin.3do']['edits']=[{'old':'panel.mat','new':'sk_panel.mat','count':1,'reason':'isolation'}]
        resources['misc/snd/skin.snd']['edits']=[{'old':'ping.wav','new':'sk_ping.wav','count':1,'reason':'isolation'}]
        spec={'resources':resources,'owned_hashes':{k:a.sha256 for k,a in native.items()},
              'normalized_gob_sha256':original.sha256,'gob_sha256':original.sha256,
              'native_dependencies':[],'retail_dependencies':[],'animation_checks':[],
              'native_model_count':2,'models_added':[{'model':'skin.3do','output_model':'sk_skin.3do',
                'output_soundclass':'sk_skin.snd','personality':1,'display_name':'Synthetic Skin'}],
              'recipe':'synthetic','startup_overlay':'synthetic','zip_sha256':'0'*64,'runtime_test':{'status':'not-run'}}
        return native,original,spec

    def test_rebuild_preserves_native_rows_and_only_appends_skin(self):
        native,original,spec=self.fixture()
        first,manifest=c.build(native,original,spec);second,_=c.build(native,original,spec)
        self.assertEqual(first,second)
        self.assertTrue(c.verify(native,original,first,spec)['ok'])
        out=Gob(first)
        expected=native['motsres'].read('misc/models.dat').replace(b'numModels: 2',b'numModels: 3')
        self.assertEqual(out.read('misc/models.dat'),expected+b'\r\n2: sk_skin.3do sk_skin.snd 1\r\n')
        self.assertEqual(out.read('mat/sk_panel.mat'),original.read('mat/panel.mat'))
        self.assertEqual(manifest['native_overrides'],['misc/models.dat','ui/jkstrings.uni'])

    def test_written_output_contract_and_exact_original_readme(self):
        native,original,spec=self.fixture()
        readme=b'Synthetic original contributor notice.\r\nPreserve exactly.\r\n'
        notice=b'Second exact original installation notice.\r\n'
        members={'fixture.gob':original.data,'readme.txt':readme,'notice.txt':notice}
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
            for name,data in members.items():z.writestr(name,data)
        spec.update(title='Synthetic Skin',author='Synthetic Author',filename='skin.goo',
                    zip_bytes=len(stream.getvalue()),zip_sha256=c.digest(stream.getvalue()),
                    gob_member='fixture.gob',readme_member='readme.txt',
                    additional_notice_members=[{'member':'notice.txt','output_filename':'ORIGINAL-NOTICE.txt',
                        'bytes':len(notice),'sha256':c.digest(notice)}],
                    zip_members=[{'path':p,'bytes':len(data),'sha256':c.digest(data)} for p,data in members.items()])
        with tempfile.TemporaryDirectory() as folder,patch.dict(c.catalog.SPECS,{'fixture':spec},clear=True):
            base=Path(folder);source=base/'original.zip';source.write_bytes(stream.getvalue())
            trees=[]
            for name in ('first','second'):
                stage=base/name
                result=c.build_to_directory(native,source,stage,'fixture')
                self.assertEqual(result['filename'],'synthetic/skin.goo')
                self.assertEqual(result['manifest_filename'],'synthetic/skin.goo.manifest.json')
                self.assertFalse(Path(result['filename']).is_absolute())
                payload=(stage/result['filename']).read_bytes()
                self.assertTrue(c.verify(native,original,payload,spec)['ok'])
                self.assertEqual((stage/'synthetic/ORIGINAL-README.txt').read_bytes(),readme)
                self.assertEqual((stage/'synthetic/ORIGINAL-NOTICE.txt').read_bytes(),notice)
                manifest=json.loads((stage/result['manifest_filename']).read_text())
                self.assertEqual(manifest['output_sha256'],c.digest(payload))
                trees.append({p.relative_to(stage).as_posix():p.read_bytes() for p in stage.rglob('*') if p.is_file()})
            self.assertEqual(trees[0],trees[1])
            with self.assertRaises(c.SkinError):c.build_to_directory(native,source,base/'first','fixture')
            self.assertEqual((base/'first/synthetic/skin.goo').read_bytes(),payload)
            for i,(key,value) in enumerate([('output_filename','../escaped.txt'),('output_filename','README.txt'),
                                            ('bytes',len(notice)+1),('sha256','0'*64)]):
                bad=copy.deepcopy(spec);bad['additional_notice_members'][0][key]=value
                with self.subTest(notice_pin=key,value=value),patch.dict(c.catalog.SPECS,{'fixture':bad},clear=True):
                    with self.assertRaises(ValueError):c.build_to_directory(native,source,base/f'bad-{i}','fixture')
                self.assertFalse((base/f'bad-{i}').exists())

    def test_descriptor_or_authored_payload_tamper_is_rejected(self):
        native,original,spec=self.fixture();payload,_=c.build(native,original,spec);out=Gob(payload)
        for path,replacement in [('misc/models.dat',out.read('misc/models.dat').replace(b'old.3do',b'bad.3do')),
                                 ('mat/sk_panel.mat',b'changed'),('3do/sk_skin.3do',model(parent=1)+b'# sk_panel.mat\r\n')]:
            files={p:out.read(p) for p in out.entries};files[path]=replacement
            with self.assertRaises(c.SkinError):c.verify(native,original,build_gob(files),spec)

    def test_additional_graphical_or_gameplay_provider_is_rejected(self):
        native,original,spec=self.fixture();payload,_=c.build(native,original,spec);out=Gob(payload)
        for path in ('cog/native.cog','mat/extra.mat'):
            files={p:out.read(p) for p in out.entries};files[path]=b'synthetic'
            with self.assertRaises(c.SkinError):c.verify(native,original,build_gob(files),spec)

    def test_changed_owned_and_original_archives_fail(self):
        native,original,spec=self.fixture()
        changed=dict(native);changed['motsres']=Gob(build_gob({'x.txt':b'bad'}))
        with self.assertRaises(c.SkinError):c.build(changed,original,spec)
        with self.assertRaises(c.SkinError):c.build(native,Gob(build_gob({'x.txt':b'bad'})),spec)

    def test_skeleton_parent_topology_is_not_assumed_compatible(self):
        self.assertNotEqual(c.hierarchy(model()),c.hierarchy(model(parent=1)))
        with self.assertRaises(c.SkinError):c.hierarchy(b'HIERARCHY NODES 2\n')

    def test_resource_token_rewrite_keeps_parent_paths_and_other_names(self):
        data=b'hand.mat bhand.mat\r\n3do/mat/hand.mat'
        edits=[{'old':'hand.mat','new':'sk_hand.mat','count':2}]
        self.assertEqual(c.transform(data,edits),b'sk_hand.mat bhand.mat\r\n3do/mat/sk_hand.mat')
        with self.assertRaises(c.SkinError):c.transform(data,[{**edits[0],'count':3}])

    def test_filename_scanner_cannot_hide_bare_sound_reference(self):
        with self.assertRaises(c.SkinError):
            c.verify_references({'misc/snd/skin.snd':b'hurt missing\n'},{'native_dependencies':[],'models_added':[]})
        with self.assertRaises(c.SkinError):
            c.verify_references({'misc/snd/skin.snd':b'hurt absent.wav\n'},{'native_dependencies':[],'models_added':[]})


class LooseSkinSourceTests(unittest.TestCase):
    """Synthetic fixtures exercise reviewed loose layout and multi-skin additions."""
    fixture = SkinConverterTests.fixture

    def loose_fixture(self):
        native,_,_=self.fixture()
        stock=native['motsres'].read('misc/models.dat')
        native['jkres']=Gob(build_gob({'misc/models.dat':stock}))
        source_models=stock.replace(b'numModels: 2',b'numModels: 4')+b'2: skin.3do skin.snd\r\n3: second.3do skin.snd\r\n'
        members={'Skin.3do':b'MATERIALS 1\n0: panel.mat\n'+model(),
                 'Second.3do':b'MATERIALS 1\n0: panel.mat\n'+model(),
                 'panel.mat':b'synthetic material', 'skin.snd':b'walk ping.wav\n',
                 'ping.wav':b'synthetic audio', 'models.dat':source_models,
                 'jkstrings.uni':b'MSGS 2\n"SKIN" 0 "First Skin"\n"SECOND" 0 "Second Skin"\nEND\n',
                 'Readme.txt':b'Original fictional notices.\r\n'}
        layout={'Skin.3do':'3do/skin.3do','Second.3do':'3do/second.3do','panel.mat':'3do/mat/panel.mat',
                'skin.snd':'misc/snd/skin.snd','ping.wav':'sound/ping.wav',
                'models.dat':'misc/models.dat','jkstrings.uni':'ui/jkstrings.uni','Readme.txt':'readme.txt'}
        files={v:members[k] for k,v in layout.items()};original=Gob(build_gob(files))
        rows={}
        for source,path in layout.items():
            target='wbw/original-readme.txt' if path=='readme.txt' else str(Path(path).with_name('ls_'+Path(path).name)).replace('\\','/')
            edits=[]
            if path.endswith('.3do'):edits=[{'old':'panel.mat','new':'ls_panel.mat','count':1}]
            if path.endswith('.snd'):edits=[{'old':'ping.wav','new':'ls_ping.wav','count':1}]
            rows[path]={'source_zip_path':source,'bytes':len(files[path]),'sha256':c.digest(files[path]),'output_path':target,'edits':edits}
        spec={'source_format':'loose-zip','source_layout':layout,'mapped_source_sha256':original.sha256,
            'readme_member':'Readme.txt','registration_source_paths':['misc/models.dat','ui/jkstrings.uni'],
            'source_registration_review':{'stock_row_count':2,'stock_source_archive':'jkres','source_rows':c.model_rows(source_models)},
            'resources':rows,'owned_hashes':{k:g.sha256 for k,g in native.items()},
            'native_dependencies':[],'retail_dependencies':[],'animation_checks':[],'native_model_count':2,
            'models_added':[{'source_index':2,'model':'skin.3do','soundclass':'skin.snd','output_model':'ls_skin.3do',
                'output_soundclass':'ls_skin.snd','personality':1,'display_name':'First Skin'},
                {'source_index':3,'model':'second.3do','soundclass':'skin.snd','output_model':'ls_second.3do',
                'output_soundclass':'ls_skin.snd','personality':1,'display_name':'Second Skin'}],
            'recipe':'synthetic-loose-v1','startup_overlay':'synthetic-loose','filename':'synthetic-loose.goo',
            'title':'Synthetic loose skins','author':'Synthetic Author','runtime_test':{'status':'not-run'}}
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
            for name,data in members.items():z.writestr(name,data)
        raw=stream.getvalue();spec.update(zip_bytes=len(raw),zip_sha256=c.digest(raw),
            zip_members=[{'path':n,'bytes':len(b),'sha256':c.digest(b)} for n,b in members.items()])
        return native,original,spec,members,raw

    def test_exact_loose_zip_layout_preserves_parents_and_adds_two_skins(self):
        native,_,spec,members,raw=self.loose_fixture()
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.zip';source.write_bytes(raw)
            original,notice=c.read_original(source,spec)
        self.assertEqual(notice,members['Readme.txt'])
        payload,manifest=c.build(native,original,spec);out=Gob(payload)
        self.assertTrue(c.verify(native,original,payload,spec)['ok'])
        self.assertIn('3do/mat/ls_panel.mat',out.entries)
        self.assertNotIn('mat/ls_panel.mat',out.entries)
        self.assertNotIn('ui/ls_jkstrings.uni',out.entries)
        self.assertEqual(c.model_rows(out.read('misc/models.dat'))[:2],c.model_rows(native['motsres'].read('misc/models.dat')))
        self.assertEqual(c.model_rows(out.read('misc/models.dat'))[2:],[[2,'ls_skin.3do','ls_skin.snd'],[3,'ls_second.3do','ls_skin.snd']])
        self.assertEqual(manifest['source_format'],'loose-zip')
        origins={r['path']:r['origin'] for r in manifest['resources']}
        self.assertEqual(origins['3do/mat/ls_panel.mat']['path'],'panel.mat')
        self.assertEqual(origins['3do/mat/ls_panel.mat']['virtual_path'],'3do/mat/panel.mat')

    def test_unreviewed_layout_moved_parent_duplicate_and_omission_fail(self):
        _,_,spec,members,_=self.loose_fixture()
        changes=[{'panel.mat':'mat/panel.mat'}, {'panel.mat':'../panel.mat'},
                 {'Second.3do':'3do/skin.3do'}, {'panel.mat':'3do/MAT/panel.mat'}]
        for change in changes:
            changed=copy.deepcopy(spec);changed['source_layout'].update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):c.map_loose_source(members,changed)
        changed=copy.deepcopy(spec);del changed['source_layout']['panel.mat']
        with self.assertRaises(c.SkinError):c.map_loose_source(members,changed)

    def test_source_readme_and_any_loose_member_tamper_rejected(self):
        _,_,spec,members,_=self.loose_fixture()
        for name in ('Readme.txt','panel.mat'):
            changed=dict(members);changed[name]+=b'x'
            with self.subTest(name=name),self.assertRaises(c.SkinError):c.map_loose_source(changed,spec)

    def test_authored_registration_tail_and_ui_labels_cannot_silently_change(self):
        native,original,spec,_,_=self.loose_fixture()
        for operation in ('label','model','order','remove','duplicate-output'):
            changed=copy.deepcopy(spec)
            if operation=='label':changed['models_added'][0]['display_name']='Wrong name'
            elif operation=='model':changed['models_added'][0]['model']='second.3do'
            elif operation=='order':changed['models_added'].reverse()
            elif operation=='remove':changed['models_added'].pop()
            else:changed['models_added'][1]['output_model']='LS_SKIN.3DO'
            with self.subTest(operation=operation),self.assertRaises(c.SkinError):c.build(native,original,changed)

    def test_native_row_count_or_ui_case_alias_rejected(self):
        native,_,spec,_,_=self.loose_fixture()
        malformed=native['motsres'].read('misc/models.dat').replace(b'numModels: 2',b'numModels: 20')
        with self.assertRaises(c.SkinError):c.models_table(malformed,spec)
        with self.assertRaises(c.SkinError):c.ui_table(b'MSGS 1\n"ls_skin" 0 "Existing"\nEND\n',spec)

    def test_qualified_reference_is_not_mistaken_for_valid_basename(self):
        for files in ({'3do/test.3do':b'MATERIALS 1\n0: elsewhere/panel.mat\n','mat/panel.mat':b'x'},
                      {'misc/snd/test.snd':b'walk elsewhere/ping.wav\n','sound/ping.wav':b'x'}):
            with self.subTest(files=files),self.assertRaises(c.SkinError):c.verify_references(files,{'native_dependencies':[],'models_added':[]})

    def test_case_preserving_owned_text_edits_are_independently_reversible(self):
        data=b'walk Ping.wav\nrun ping.wav\n'
        edits=[{'old':'Ping.wav','new':'ls_Ping.wav','count':1,'case_sensitive':True},
               {'old':'ping.wav','new':'ls_ping.wav','count':1,'case_sensitive':True}]
        changed=c.transform(data,edits)
        self.assertEqual(changed,b'walk ls_Ping.wav\nrun ls_ping.wav\n')
        self.assertEqual(c.reverse_edits(changed,edits,'synthetic.snd'),data)
        with self.assertRaises(c.SkinError):c.reverse_edits(changed.replace(b'ls_Ping',b'ls_ping'),edits,'synthetic.snd')


class IdenticalDuplicateSkinTests(unittest.TestCase):
    def fixture(self, duplicate=b'first'):
        entries=[('mat/panel.mat',b'first'),('readme.txt',b'notice'),('mat/panel.mat',duplicate)]
        offset=16+len(entries)*136;directory=[];payload=[];pins=[]
        for index,(name,data) in enumerate(entries):
            directory.append(struct.pack('<II128s',offset,len(data),name.encode()))
            if name=='mat/panel.mat':
                pins.append({'index':index,'offset':offset,'bytes':len(data),'sha256':c.digest(data)})
            payload.append(data);offset+=len(data)
        raw=struct.pack('<4sIII',b'GOB ',20,12,len(entries))+b''.join(directory)+b''.join(payload)
        plan={'archive_bytes':len(raw),'archive_sha256':c.digest(raw),'table_offset':12,
              'entry_count':3,'removed_count':1,'duplicates':[{'path':'mat/panel.mat','entries':pins}]}
        return raw,plan

    def test_exact_duplicate_repair_preserves_payloads_and_strict_general_reader(self):
        raw,plan=self.fixture()
        with self.assertRaisesRegex(ValueError,'Duplicate resource'):Gob(raw)
        repaired=c.repair_identical_duplicates(raw,plan);out=Gob(repaired)
        self.assertEqual(set(out.entries),{'mat/panel.mat','readme.txt'})
        self.assertEqual(out.read('mat/panel.mat'),b'first')
        self.assertEqual(out.read('readme.txt'),b'notice')
        self.assertEqual(raw[16+3*136:],repaired[16+3*136:])
        self.assertEqual(repaired,c.repair_identical_duplicates(raw,plan))
        with self.assertRaises(ValueError):Gob(raw)

    def test_different_duplicate_payloads_fail_even_with_matching_archive_pins(self):
        raw,plan=self.fixture(b'other')
        with self.assertRaisesRegex(c.SkinError,'different bytes'):c.repair_identical_duplicates(raw,plan)

    def test_every_repair_pin_and_full_duplicate_membership_are_required(self):
        raw,plan=self.fixture()
        changes=[('archive_bytes',len(raw)+1),('archive_sha256','0'*64),('table_offset',13),
                 ('entry_count',4),('removed_count',0),('duplicates',[])]
        for key,value in changes:
            changed=copy.deepcopy(plan);changed[key]=value
            with self.subTest(key=key),self.assertRaises(c.SkinError):c.repair_identical_duplicates(raw,changed)
        for key,value in [('index',1),('offset',0),('bytes',4),('sha256','0'*64)]:
            changed=copy.deepcopy(plan);changed['duplicates'][0]['entries'][1][key]=value
            with self.subTest(pin=key),self.assertRaises(c.SkinError):c.repair_identical_duplicates(raw,changed)
        changed=copy.deepcopy(plan);changed['duplicates'][0]['path']='mat/other.mat'
        with self.assertRaises(c.SkinError):c.repair_identical_duplicates(raw,changed)
        changed=copy.deepcopy(plan);changed['duplicates'].append(copy.deepcopy(changed['duplicates'][0]))
        with self.assertRaises(c.SkinError):c.repair_identical_duplicates(raw,changed)

    def test_duplicate_repair_rejects_changed_source_and_undeclared_third_member(self):
        raw,plan=self.fixture()
        with self.assertRaises(c.SkinError):c.repair_identical_duplicates(raw[:-1]+b'x',plan)
        changed=bytearray(raw);changed[16+136+8:16+136+136]=b'mat/panel.mat'.ljust(128,b'\0')
        repinned=copy.deepcopy(plan);repinned['archive_sha256']=c.digest(changed)
        with self.assertRaisesRegex(c.SkinError,'membership'):c.repair_identical_duplicates(changed,repinned)

    def test_gob_registration_review_preserves_all_authored_rows(self):
        native,original,spec,_,_=LooseSkinSourceTests().loose_fixture()
        spec.pop('source_format');spec['normalized_gob_sha256']=original.sha256
        spec['gob_sha256']=original.sha256
        c.validate_native(native,spec,original)
        for operation in ('drop','label','order'):
            changed=copy.deepcopy(spec)
            if operation=='drop':changed['models_added'].pop()
            elif operation=='label':changed['models_added'][0]['display_name']='Wrong'
            else:changed['models_added'].reverse()
            with self.subTest(operation=operation),self.assertRaises(c.SkinError):c.validate_native(native,changed,original)


class OriginalSoundOmissionTests(unittest.TestCase):
    def fixture(self):
        native,original,spec=SkinConverterTests().fixture()
        files={p:original.read(p) for p in original.entries}
        files['misc/snd/skin.snd']+=b'falling absent.wav\n'
        original=Gob(build_gob(files));spec['normalized_gob_sha256']=original.sha256
        spec['gob_sha256']=original.sha256
        row=spec['resources']['misc/snd/skin.snd']
        row['bytes']=len(files['misc/snd/skin.snd']);row['sha256']=c.digest(files['misc/snd/skin.snd'])
        spec['source_omissions']=[{'source_path':'misc/snd/skin.snd','source_sha256':row['sha256'],
            'source_gob_sha256':original.sha256,
            'output_path':row['output_path'],'output_sha256':c.digest(c.transform(files['misc/snd/skin.snd'],row['edits'])),
            'event':'falling','token':'absent.wav','count':1,'candidate_paths':['sound/absent.wav','voice/absent.wav']}]
        return native,original,spec

    def test_exact_original_omission_preserves_event_and_other_sound_events(self):
        native,original,spec=self.fixture();payload,manifest=c.build(native,original,spec)
        self.assertTrue(c.verify(native,original,payload,spec)['ok'])
        self.assertEqual(Gob(payload).read('misc/snd/sk_skin.snd'),b'walk sk_ping.wav\nfalling absent.wav\n')
        self.assertEqual(manifest['source_omissions'],spec['source_omissions'])

    def test_mutated_referrer_source_hash_event_token_count_or_candidates_fail(self):
        native,original,spec=self.fixture()
        for key,value in [('source_path','misc/models.dat'),('source_sha256','0'*64),('source_gob_sha256','0'*64),
                          ('output_path','misc/snd/other.snd'),('output_sha256','0'*64),
                          ('event','death'),('token','other.wav'),('count',2),
                          ('candidate_paths',['sound/other.wav','voice/other.wav'])]:
            changed=copy.deepcopy(spec);changed['source_omissions'][0][key]=value
            with self.subTest(key=key),self.assertRaises(c.SkinError):c.build(native,original,changed)

    def test_new_missing_sound_cannot_reuse_the_original_omission(self):
        native,original,spec=self.fixture();payload,_=c.build(native,original,spec);out=Gob(payload)
        files={p:out.read(p) for p in out.entries};del files['sound/sk_ping.wav']
        with self.assertRaisesRegex(c.SkinError,'Unresolved typed resource'):c.verify_references(files,spec)
        files['sound/sk_ping.wav']=b'synthetic';files['misc/snd/other.snd']=b'falling absent.wav\n'
        with self.assertRaisesRegex(c.SkinError,'Unresolved typed resource'):c.verify_references(files,spec)

    def test_omission_cannot_be_silently_filled_or_removed(self):
        native,original,spec=self.fixture();payload,_=c.build(native,original,spec);out=Gob(payload)
        files={p:out.read(p) for p in out.entries};files['sound/absent.wav']=b'wrong invented voice'
        with self.assertRaisesRegex(c.SkinError,'changed, duplicated or filled'):c.verify_references(files,spec)
        changed=copy.deepcopy(spec);changed['source_omissions']*=2
        with self.assertRaises(c.SkinError):c.verify_references({p:out.read(p) for p in out.entries},changed)
        changed=copy.deepcopy(spec);changed.pop('source_omissions')
        with self.assertRaisesRegex(c.SkinError,'Unresolved typed resource'):c.build(native,original,changed)


if __name__=='__main__':unittest.main()

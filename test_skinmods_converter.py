"""Synthetic assets only; no game/mod files are test inputs."""
import io
import json
from pathlib import Path
import tempfile
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
        members={'fixture.gob':original.data,'readme.txt':readme}
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
            for name,data in members.items():z.writestr(name,data)
        spec.update(title='Synthetic Skin',author='Synthetic Author',filename='skin.goo',
                    zip_bytes=len(stream.getvalue()),zip_sha256=c.digest(stream.getvalue()),
                    gob_member='fixture.gob',readme_member='readme.txt',
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
                manifest=json.loads((stage/result['manifest_filename']).read_text())
                self.assertEqual(manifest['output_sha256'],c.digest(payload))
                trees.append({p.relative_to(stage).as_posix():p.read_bytes() for p in stage.rglob('*') if p.is_file()})
            self.assertEqual(trees[0],trees[1])
            with self.assertRaises(c.SkinError):c.build_to_directory(native,source,base/'first','fixture')
            self.assertEqual((base/'first/synthetic/skin.goo').read_bytes(),payload)

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


if __name__=='__main__':unittest.main()

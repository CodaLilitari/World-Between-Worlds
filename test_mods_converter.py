"""Original synthetic fixtures for the exact material-mod adapter."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from gob import Gob, build_gob
import mods_catalog
import mods_converter as converter


class MaterialModTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.resources = {'mat/synthetic0.mat': b'authored synthetic material',
                          'patchinfo.txt': b'Synthetic contributor notice'}
        self.source = Gob(build_gob(self.resources))
        readme = b'Synthetic original documentation; preserve exactly.\r\n'
        members = {'fixture.gob': self.source.data, 'Readme.txt': readme}
        transport = io.BytesIO()
        with zipfile.ZipFile(transport, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, data in members.items():
                archive.writestr(name, data)
        self.original = self.root / 'original.zip'
        self.original.write_bytes(transport.getvalue())
        sabers = b'numSabers: 1\n0: synthetic.bm synthetic0.mat synthetic0.mat\n'
        self.archives = {'jkres': Gob(build_gob({'misc/owned.txt': b'owned synthetic source'})),
                         'motsres': Gob(build_gob({'misc/sabers.dat': sabers,
                                                  'mat/synthetic0.mat': b'native synthetic material'}))}
        self.spec = {'id': 'fixture', 'title': 'Synthetic material mod', 'author': 'Fixture Author',
                     'source_url': 'https://example.invalid/fixture', 'download_url': 'https://example.invalid/fixture.zip',
                     'archive_hint': 'fixture.zip', 'zip_sha256': converter.digest(transport.getvalue()),
                     'zip_bytes': len(transport.getvalue()), 'gob_member': 'fixture.gob',
                     'gob_sha256': self.source.sha256, 'filename': 'wbw-fixture.goo',
                     'startup_overlay': 'wbw-fixture', 'mode': 'exact-material-repack-v1',
                     'revision': 1, 'selected_saber': 'synthetic', 'runtime_test': {'status': 'not-run'},
                     'zip_members': [{'path': name, 'bytes': len(data), 'sha256': converter.digest(data)}
                                     for name, data in members.items()],
                     'resources': [{'path': name, 'bytes': len(data), 'sha256': converter.digest(data)}
                                   for name, data in self.resources.items()],
                     'native_overrides': {'mat/synthetic0.mat': converter.digest(b'native synthetic material')},
                     'readmes': [{'path': 'Readme.txt', 'bytes': len(readme), 'sha256': converter.digest(readme)}]}
        self.patches = [patch.dict(mods_catalog.SPECS, {'fixture': self.spec}, clear=True),
                        patch.dict(mods_catalog.NATIVE_HASHES, {key: value.sha256 for key, value in self.archives.items()}, clear=True),
                        patch.object(mods_catalog, 'NATIVE_SABERS_SHA256', converter.digest(sabers))]
        for context in self.patches:
            context.start()
            self.addCleanup(context.stop)

    def build(self, stage='result'):
        return converter.build_to_directory(self.archives, self.original, self.root/stage, 'fixture')

    def test_exact_paths_payloads_and_readme_survive_two_fresh_builds(self):
        result = self.build('one')
        self.build('two')
        first = {p.relative_to(self.root/'one').as_posix():p.read_bytes()
                 for p in (self.root/'one').rglob('*') if p.is_file()}
        second = {p.relative_to(self.root/'two').as_posix():p.read_bytes()
                  for p in (self.root/'two').rglob('*') if p.is_file()}
        self.assertEqual(first, second)
        output = Gob(first[result['filename']])
        self.assertEqual(set(output.entries), set(self.resources))
        self.assertEqual({path:output.read(path) for path in output.entries}, self.resources)
        self.assertEqual(first['wbw-fixture/ORIGINAL-01-Readme.txt'], b'Synthetic original documentation; preserve exactly.\r\n')
        self.assertEqual(result['verification']['gameplay'], 'not-run')
        self.assertEqual(json.loads(first[result['manifest_filename']])['scope'], 'explicit-isolated-startup-mod')

    def test_catalogue_does_not_select_or_alias_ninja(self):
        rows = converter.catalog_entries()
        self.assertEqual([item['id'] for item in rows], ['fixture'])
        self.assertEqual(rows[0]['kind'], 'mod')
        self.assertTrue(rows[0]['requires_archive'])
        self.assertEqual(converter.original_hashes('fixture'), {self.spec['zip_sha256']})

    def test_unknown_recipe_and_altered_zip_fail_before_output(self):
        with self.assertRaises(converter.ModError):
            converter.recipe_details('unknown')
        data = bytearray(self.original.read_bytes())
        data[-1] ^= 1
        self.original.write_bytes(data)
        with self.assertRaises(converter.ModError):
            self.build()
        self.assertFalse((self.root/'result').exists())

    def test_wrong_native_source_or_unregistered_target_is_rejected(self):
        good = self.archives['motsres']
        self.archives['motsres'] = Gob(build_gob({'misc/sabers.dat':b'changed'}))
        with self.assertRaises(converter.ModError):
            self.build()
        self.archives['motsres'] = good
        self.spec['native_overrides']['mat/unregistered.mat'] = '0' * 64
        with self.assertRaises(converter.ModError):
            self.build()

    def test_output_resource_rename_or_byte_change_is_rejected_independently(self):
        for changed in ({'mat/synthetic0.mat':b'changed','patchinfo.txt':self.resources['patchinfo.txt']},
                        {'mat/renamed.mat':self.resources['mat/synthetic0.mat'],'patchinfo.txt':self.resources['patchinfo.txt']}):
            with self.subTest(changed=changed):
                with self.assertRaises(converter.ModError):
                    converter.verify(self.archives,self.source,build_gob(changed),self.spec)

    def test_foreign_original_and_gameplay_resources_cannot_pass_verifier(self):
        foreign = Gob(build_gob({'cog/weap_saber_m.cog':b'authored synthetic code'}))
        with self.assertRaises(converter.ModError):
            converter.verify(self.archives,foreign,foreign.data,self.spec)
        modified_spec = copy.deepcopy(self.spec)
        modified_spec['gob_sha256'] = foreign.sha256
        with self.assertRaises(converter.ModError):
            converter.verify(self.archives,foreign,foreign.data,modified_spec)

    def test_no_output_overwrite_and_no_output_inside_repository(self):
        first = self.build()
        path = self.root/'result'/first['filename']
        original = path.read_bytes()
        with self.assertRaises(converter.ModError):
            self.build()
        self.assertEqual(path.read_bytes(),original)
        with self.assertRaises(converter.ModError):
            converter.build_to_directory(self.archives,self.original,Path(converter.__file__).parent/'forbidden-fixture','fixture')


if __name__ == '__main__':
    unittest.main()

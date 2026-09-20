"""Synthetic community-package, targeted-edit, and independent omission gates."""
from io import BytesIO
from pathlib import Path
import hashlib
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import bridge
import custom_registry
from gob import ArchiveError, Gob, build_gob
import verify_retail


def digest(value):
    return hashlib.sha256(value).hexdigest()


def make_zip(members):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, value in members:
            archive.writestr(name, value)
    return buffer.getvalue()


class CommunityPackageTests(unittest.TestCase):
    def setUp(self):
        self.gob = build_gob({'jkl/fixture.jkl': b'Synthetic fixture\n'})
        self.package = make_zip([('fixture.gob', self.gob), ('readme.txt', b'Original test data\n')])
        self.spec = {'title': 'Synthetic fixture', 'gob_sha256': digest(self.gob),
                     'zip_sha256': digest(self.package), 'gob_member': 'fixture.gob'}

    def load(self, data, *, pin_zip=False, spec_changes=None):
        spec = dict(self.spec)
        if pin_zip:
            spec['zip_sha256'] = digest(data)
        spec.update(spec_changes or {})
        with tempfile.TemporaryDirectory() as directory, patch.object(custom_registry, 'entries', return_value={'fixture': spec}):
            path = Path(directory) / 'original.zip'
            path.write_bytes(data)
            return custom_registry.open_original(path, 'fixture')

    def test_zip_and_gob_originals_load_identical_payloads(self):
        self.assertEqual(self.load(self.package).data, self.gob)
        self.assertEqual(self.load(self.gob).data, self.gob)

    def test_unreviewed_package_bytes_are_rejected(self):
        with self.assertRaisesRegex(ArchiveError, 'Unreviewed original package hash'):
            self.load(self.package + b'tampered')

    def test_pinned_zip_with_wrong_embedded_gob_is_rejected(self):
        other = build_gob({'jkl/fixture.jkl': b'Wrong source revision\n'})
        package = make_zip([('fixture.gob', other)])
        with self.assertRaisesRegex(ArchiveError, 'Unexpected embedded GOB'):
            self.load(package, pin_zip=True)

    def test_missing_expected_gob_is_rejected(self):
        package = make_zip([('different.gob', self.gob)])
        with self.assertRaisesRegex(ArchiveError, 'missing reviewed GOB'):
            self.load(package, pin_zip=True)

    def test_unsafe_paths_rejected_even_with_known_zip_digest(self):
        for name in ('../outside.txt', '/absolute.txt', 'C:/drive.txt', 'dir/CON.txt', 'dir/trailing. '):
            with self.subTest(name=name):
                package = make_zip([('fixture.gob', self.gob), (name, b'no extraction')])
                with self.assertRaises(ArchiveError):
                    self.load(package, pin_zip=True)

    def test_case_colliding_members_are_rejected(self):
        package = make_zip([('fixture.gob', self.gob), ('FIXTURE.GOB', self.gob)])
        with self.assertRaisesRegex(ArchiveError, 'Duplicate ZIP member'):
            self.load(package, pin_zip=True)

    def test_crc_is_checked_for_non_gob_members(self):
        damaged = bytearray(self.package)
        with zipfile.ZipFile(BytesIO(self.package)) as archive:
            info = archive.getinfo('readme.txt')
            name_length, extra_length = struct.unpack_from('<HH', damaged, info.header_offset + 26)
            offset = info.header_offset + 30 + name_length + extra_length
        damaged[offset] ^= 1
        with self.assertRaisesRegex(ArchiveError, 'CRC'):
            self.load(bytes(damaged), pin_zip=True)


class CountedCogEditTests(unittest.TestCase):
    def test_exact_edit_preserves_other_numbers_and_calls(self):
        source = 'SetInv(player, 10, 1);\nSetInv(player, 11, 100);\nSetTimer(10);\n'
        edit = {'old': 'SetInv(player, 10, 1);', 'new': 'SetInv(player, 131, 1);',
                'count': 1, 'reason': 'Translate the specifically reviewed saber grant'}
        result = custom_registry.apply_cog_edits(source, [edit])
        self.assertEqual(result, 'SetInv(player, 131, 1);\nSetInv(player, 11, 100);\nSetTimer(10);\n')

    def test_changed_occurrence_count_rejects_source_drift(self):
        edit = {'old': 'SetInv(p, 10, 1);', 'new': 'SetInv(p, 131, 1);', 'count': 1, 'reason': 'Reviewed grant'}
        for source in ('SetInv(p, 9, 1);', 'SetInv(p, 10, 1);\nSetInv(p, 10, 1);'):
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, 'Unexpected COG source'):
                custom_registry.apply_cog_edits(source, [edit])

    def test_edits_require_nonempty_source_reason_and_positive_count(self):
        valid = {'old': 'a', 'new': 'b', 'count': 1, 'reason': 'Reviewed edit'}
        for change in ({'old': ''}, {'reason': ''}, {'count': 0}, {'count': -1}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                custom_registry.apply_cog_edits('a', [{**valid, **change}])


class FilenameAndTypedArgumentTests(unittest.TestCase):
    def test_ampersand_filename_is_one_dependency(self):
        value = '0: rock&stone.mat\n1: m&n~1.3do\n# ignored&comment.wav\n'
        self.assertEqual(bridge.references(value), {'rock&stone.mat', 'm&n~1.3do'})
        self.assertNotIn('stone.mat', bridge.references(value))

    def test_resource_and_template_aliases_do_not_rewrite_numeric_parameters(self):
        resources = {'long&name.wav': 'br_short.wav', 'kyle.cog': 'kyle_m.cog'}
        templates = {'long_template': 'br_short_template'}
        expected = verify_retail.expected_argument
        self.assertEqual(expected('LONG&NAME.WAV', 'sound', resources=resources), 'br_short.wav')
        self.assertEqual(expected('kyle.cog', 'cog', resources=resources), 'kyle_m.cog')
        self.assertEqual(expected('long_template', 'template', templates=templates), 'br_short_template')
        for value, kind in (('31', 'int'), ('1.25', 'flex'), ('(1/2/3)', 'vector'), ('-1', 'template')):
            self.assertEqual(expected(value, kind, resources=resources, templates=templates), value)

    def test_missing_template_waiver_is_specific_to_row_cog_symbol_and_name(self):
        cog = b'symbols\nthing first\nthing second\ntemplate enemy_tpl\nend\ncode\nend\n'
        catalog = bridge.Catalog([('fixture', Gob(build_gob({'cog/eye_actor1.cog': cog})))])
        world = 'World cogs 1\n2: EYE_ACTOR1.COG 72 116 MAX\nend\n'
        rule = {'row': '2:', 'cog': 'eye_actor1.cog', 'symbol': 'enemy_tpl', 'name': 'max', 'reason': 'Original undefined generator template'}
        result = bridge.rewrite_cog_template_arguments(world, catalog, {}, missing_templates=[rule])
        self.assertIn('2: EYE_ACTOR1.COG 72 116 br_max', result)
        for change in ({'row': '3:'}, {'cog': 'other.cog'}, {'symbol': 'other_tpl'}, {'name': 'other'}):
            with self.subTest(change=change), self.assertRaises(bridge.RecipeError):
                bridge.rewrite_cog_template_arguments(world, catalog, {}, missing_templates=[{**rule, **change}])
        with self.assertRaises(bridge.RecipeError):
            bridge.rewrite_cog_template_arguments(world, catalog, {'max': 'br_max'}, missing_templates=[rule])


class IndependentOmissionTests(unittest.TestCase):
    def setUp(self):
        self.original = b'World scripts 1\n0: missing.cog\nend\nWorld cogs 1\n17: missing.cog\nend\n'
        self.output = self.original.replace(b'missing.cog', b'br_missing.cog')
        self.rule = {'name': 'missing.cog', 'referrer': 'jkl/fixture.jkl',
                     'referrer_sha256': digest(self.original), 'reason': 'Original missing script'}

    def verify(self, *, original=None, output=None, additions=None, rule=None, archives=None):
        custom = Gob(build_gob({'jkl/fixture.jkl': self.original if original is None else original}))
        resources = {'jkl/br_fixture.jkl': self.output if output is None else output, **(additions or {})}
        generated = Gob(build_gob(resources))
        verify_retail.check_source_omissions(archives or {}, generated, custom,
                                             {'source_omissions': [rule or self.rule]},
                                             'jkl/fixture.jkl', 'jkl/br_fixture.jkl', {})

    def test_exact_missing_cog_declaration_and_placement_are_preserved(self):
        self.verify()

    def test_changed_source_referrer_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'referrer hash'):
            self.verify(original=self.original + b'changed')

    def test_missing_or_comment_only_output_edge_rejected(self):
        for output in (b'no reference\n', b'# br_missing.cog\n', b'prefixbr_missing.cog\n'):
            with self.subTest(output=output), self.assertRaisesRegex(AssertionError, 'Missing preserved omission edge'):
                self.verify(output=output)

    def test_false_original_edge_rejected_even_if_output_contains_it(self):
        rule = {**self.rule, 'name': 'invented.cog'}
        with self.assertRaisesRegex(AssertionError, 'Original omission reference is absent'):
            self.verify(rule=rule, output=b'br_invented.cog\n')

    def test_supplying_a_fake_script_rejects_preserved_omission_claim(self):
        with self.assertRaisesRegex(AssertionError, 'unexpectedly exists'):
            self.verify(additions={'cog/br_missing.cog': b'Fake implementation'})

    def test_native_namespaced_resource_collision_rejected(self):
        native = Gob(build_gob({'cog/br_missing.cog': b'Unrelated native override'}))
        with self.assertRaisesRegex(AssertionError, 'unexpectedly exists'):
            self.verify(archives={'motsres': native})


class CanyonOmissionScopeTests(unittest.TestCase):
    """Missing turret audio must remain limited to the reviewed source edges."""

    def setUp(self):
        self.world = b'World sounds 1\n0: df_machine2.wav\nend\nturret.snd\n'
        self.soundclass = b'moving df_machine2.wav 0x0 1.0\n'
        self.rules = [
            {'name': 'df_machine2.wav', 'referrer': path,
             'referrer_sha256': digest(data), 'reason': 'Synthetic original absent edge'}
            for path, data in [('jkl/canyon.jkl', self.world),
                               ('misc/snd/turret.snd', self.soundclass)]
        ]

    def fixture(self, *, world=None, additions=None):
        return Gob(build_gob({'jkl/canyon.jkl': self.world if world is None else world,
                              'misc/snd/turret.snd': self.soundclass, **(additions or {})}))

    def test_reviewed_canyon_has_only_four_exact_original_edges(self):
        spec = custom_registry.entries()['canyon-stream']
        self.assertEqual(spec['catalog_status'], 'prototype')
        self.assertFalse(spec['runtime_test']['full_gameplay'])
        rules = spec['source_omissions']
        expected = {
            ('00_glass.mat', 'jkl/canyon.jkl', 'dda3972d40ac9b1478f6de1e5599f8d27a475931c7bc3dea66da7464610a7cb6'),
            ('00_glass.mat', '3do/shard0.3do', 'f0b4102b3ba378913b6d16ee585baab2d14f46f9ae4ae293a1c24b9f2369f44d'),
            ('df_machine2.wav', 'jkl/canyon.jkl', 'dda3972d40ac9b1478f6de1e5599f8d27a475931c7bc3dea66da7464610a7cb6'),
            ('df_machine2.wav', 'misc/snd/turret.snd', 'dd7a2af6fded0e8fa2500cc67d1316e5817f98081ac3839d038d948b4a91b95b'),
        }
        self.assertEqual(len(rules), 4)
        self.assertEqual({(r['name'], r['referrer'], r['referrer_sha256']) for r in rules}, expected)
        self.assertTrue(next(r for r in rules if r['referrer'] == '3do/shard0.3do')['untextured_3do'])

    def test_exact_absent_sound_edges_are_accepted(self):
        original = self.fixture()
        catalog = bridge.Catalog([('fixture', original)])
        for rule in self.rules:
            accepted = bridge.reviewed_source_omission(rule['name'], rule['referrer'], catalog, self.rules)
            self.assertEqual(accepted['output_name'], 'br_df_machine2.wav')
        names, graph = verify_retail.community_source_graph({}, original,
            {'world': 'jkl/canyon.jkl', 'environment': [], 'source_omissions': self.rules},
            self.world.decode(), {})
        self.assertEqual(names['df_machine2.wav'], 'br_df_machine2.wav')
        self.assertEqual(set(graph), {'turret.snd'})

    def test_changed_omission_referrer_path_is_rejected(self):
        catalog = bridge.Catalog([('fixture', self.fixture())])
        with self.assertRaisesRegex(bridge.RecipeError, 'Unresolved literal dependency'):
            bridge.reviewed_source_omission('df_machine2.wav', 'misc/snd/other.snd', catalog, self.rules)
        with self.assertRaisesRegex(AssertionError, 'Independent unreviewed missing source edge'):
            verify_retail.community_source_graph({}, self.fixture(),
                {'world': 'jkl/other.jkl', 'environment': [], 'source_omissions': self.rules},
                self.world.decode(), {})

    def test_changed_referrer_bytes_are_rejected_by_both_checks(self):
        original = self.fixture(world=self.world + b'# changed source\n')
        catalog = bridge.Catalog([('fixture', original)])
        with self.assertRaisesRegex(bridge.RecipeError, 'referrer hash mismatch'):
            bridge.reviewed_source_omission('df_machine2.wav', 'jkl/canyon.jkl', catalog, self.rules)
        output = Gob(build_gob({'jkl/br_canyonstream.jkl': self.world.replace(b'df_machine2', b'br_df_machine2'),
                               'misc/snd/br_turret.snd': self.soundclass.replace(b'df_machine2', b'br_df_machine2')}))
        with self.assertRaisesRegex(AssertionError, 'Original omission referrer hash'):
            verify_retail.check_source_omissions({}, output, original,
                {'source_omissions': self.rules}, 'jkl/canyon.jkl', 'jkl/br_canyonstream.jkl', {})

    def test_unreviewed_missing_name_is_rejected_by_both_graphs(self):
        original = self.fixture()
        catalog = bridge.Catalog([('fixture', original)])
        with self.assertRaisesRegex(bridge.RecipeError, 'Unresolved literal dependency'):
            bridge.reviewed_source_omission('unreviewed.wav', 'jkl/canyon.jkl', catalog, self.rules)
        with self.assertRaisesRegex(AssertionError, 'Independent unreviewed missing source edge'):
            verify_retail.community_source_graph({}, original,
                {'world': 'jkl/canyon.jkl', 'environment': [], 'source_omissions': self.rules},
                self.world.decode() + 'unreviewed.wav\n', {})

    def test_reviewed_missing_name_at_additional_referrer_is_rejected(self):
        world = self.world + b'other.snd\n'
        original = self.fixture(world=world, additions={'misc/snd/other.snd': self.soundclass})
        with self.assertRaisesRegex(AssertionError, 'Independent unreviewed missing source edge'):
            verify_retail.community_source_graph({}, original,
                {'world': 'jkl/canyon.jkl', 'environment': [], 'source_omissions': self.rules},
                world.decode(), {})


class IndependentCommunityAdaptationTests(unittest.TestCase):
    def setUp(self):
        self.source = ['+bolt none damage=45 model3d=authored.3do', 'walkplayer none health=100']
        self.native = ['+bolt none damage=20 model3d=native.3do timer=3']
        self.spec = {'tag': 'fixture', 'native_template_overrides': {
            '+bolt': {'fields': ['damage'], 'reason': 'Reviewed authored damage'}}}
        self.names = {'authored.3do': 'br_authored.3do'}
        self.templates = {'+bolt': 'br_+bolt', 'walkplayer': 'br_walkplayer'}
        self.expected = ['+bolt none damage=45 model3d=native.3do timer=3',
                         'br_+bolt none damage=45 model3d=br_authored.3do',
                         'br_walkplayer none health=100']

    def test_native_reviewed_field_changes_and_unrelated_fields_stay_native(self):
        verify_retail.check_community_templates(self.source, self.native, self.expected,
                                                self.spec, self.names, self.templates)

    def test_native_unreviewed_field_or_parent_change_is_rejected(self):
        for row in ('+bolt none damage=45 model3d=br_authored.3do timer=3',
                    '+bolt different damage=45 model3d=native.3do timer=3',
                    '+bolt none damage=45 model3d=native.3do timer=4'):
            with self.subTest(row=row), self.assertRaisesRegex(AssertionError, 'native and authored template'):
                verify_retail.check_community_templates(self.source, self.native,
                    [row, *self.expected[1:]], self.spec, self.names, self.templates)

    def test_authored_template_gameplay_field_change_is_rejected(self):
        rows = self.expected[:-1] + ['br_walkplayer none health=500']
        with self.assertRaises(AssertionError):
            verify_retail.check_community_templates(self.source, self.native, rows,
                                                    self.spec, self.names, self.templates)

    def test_full_cog_reconstruction_rejects_untargeted_code_and_flag_changes(self):
        original = b'flags=0x240\nsymbols\ntemplate shot=+bolt\nsound noise=shot.wav\nend\ncode\nSetInv(p, 10, 1);\nReturn;\nend\n'
        edit = {'old': 'SetInv(p, 10, 1);', 'new': 'SetInv(p, 131, 1);', 'count': 1, 'reason': 'Reviewed saber grant'}
        spec = {'cog_edits': {'fixture.cog': [edit]}}
        expected = original.replace(b'+bolt', b'br_+bolt').replace(b'shot.wav', b'br_shot.wav').replace(b', 10,', b', 131,')
        graph = {'fixture.cog': ('cog/fixture.cog', original)}
        names = {'fixture.cog': 'br_fixture.cog', 'shot.wav': 'br_shot.wav'}
        for output, valid in ((expected, True), (expected.replace(b'0x240', b'0x040'), False),
                              (expected.replace(b'Return;', b'Sleep(10);'), False)):
            generated = Gob(build_gob({'cog/br_fixture.cog': output}))
            if valid:
                verify_retail.check_community_resources(generated, spec, graph, names, self.templates)
            else:
                with self.assertRaisesRegex(AssertionError, 'complete source reconstruction'):
                    verify_retail.check_community_resources(generated, spec, graph, names, self.templates)

    def startup_fixture(self, *, output=None, extra=None, directory_present=True):
        original = b'flags=0x240\ncode\nSetInv(p, 10, 1);\nReturn;\nend\n'
        edit = {'old': 'SetInv(p, 10, 1);', 'new': 'SetInv(p, 131, 1);', 'count': 1, 'reason': 'Reviewed fixture grant'}
        spec = {'tag': 'fixture', 'native_cog_edits': {'native.cog': {'sha256': digest(original), 'edits': [edit]}}}
        empty = Gob(build_gob({}))
        native = Gob(build_gob({'cog/native.cog': original}))
        archives = {'motsmp': empty, 'motsres': native, 'motssnd': empty}
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            payload = original.replace(b', 10,', b', 131,') if output is None else output
            (directory / 'bridge-fixture-startup.goo').write_bytes(build_gob({'cog/native.cog': payload, **(extra or {})}))
            (directory / 'README.txt').write_text('Synthetic fixture instructions')
            return verify_retail.check_community_startup(archives, empty, empty, spec, {}, directory if directory_present else None)

    def test_startup_exact_source_edit_and_archive_bytes_pass(self):
        self.assertEqual(self.startup_fixture()['member_count'], 1)

    def test_startup_missing_explicit_folder_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'directory was not supplied'):
            self.startup_fixture(directory_present=False)

    def test_startup_untargeted_code_change_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'exact startup source reconstruction'):
            self.startup_fixture(output=b'Fake alternative implementation')

    def test_startup_extra_archive_member_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'archive member set'):
            self.startup_fixture(extra={'cog/extra.cog': b'Unreviewed override'})

    def test_native_inventory_edit_preserves_all_other_descriptor_bytes(self):
        original = b'fieldlight 42 0 1 0x100\nysalamiri 81 0 1 0x048\nredflag2 82 0 1 0x049\n'
        expected = original.replace(b'ysalamiri 81', b'redflag 81')
        rule = {'sha256': digest(original), 'edits': [{'old': 'ysalamiri 81', 'new': 'redflag 81',
                 'count': 1, 'reason': 'Reviewed original map requires red flag name at native bin81'}]}
        empty = Gob(build_gob({}))
        native = Gob(build_gob({'misc/items.dat': original}))
        archives = {'motsmp': empty, 'motsres': native, 'motssnd': empty}
        spec = {'tag': 'fixture', 'native_text_edits': {'misc/items.dat': rule}}
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / 'README.txt').write_text('Synthetic fixture instructions')
            for payload, valid in ((expected, True), (expected.replace(b'0x048', b'0x049'), False),
                                   (expected.replace(b'fieldlight 42', b'fieldlight 43'), False)):
                (directory / 'bridge-fixture-startup.goo').write_bytes(build_gob({'misc/items.dat': payload}))
                if valid:
                    verify_retail.check_community_startup(archives, empty, empty, spec, {}, directory)
                else:
                    with self.assertRaisesRegex(AssertionError, 'exact startup source reconstruction'):
                        verify_retail.check_community_startup(archives, empty, empty, spec, {}, directory)


if __name__ == '__main__':
    unittest.main()

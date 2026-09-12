"""Asset-free SP episode and original-source contract checks."""
from pathlib import Path
import os
import re
import tempfile
import unittest

import bridge
import blackwing_revisions
from gob import Gob, build_gob
import sp_converter


class SingleplayerContracts(unittest.TestCase):
    def test_pumping_station_versioned_name_fits_engine_episode_stem(self):
        spec = sp_converter.recipe_details('sp-imperial-pumping-station')
        legacy, = spec['entry']['legacy_filenames']
        self.assertEqual(legacy, spec['output_filename'])
        name = blackwing_revisions.versioned_name(legacy, spec['entry']['revision'])
        self.assertEqual(name, 'wbw-sp-pumping-station_wbw_v1.goo')
        self.assertLessEqual(len(Path(name).stem.encode('cp1252')), 31)
        with self.assertRaisesRegex(ValueError, '31-byte episode-name limit'):
            blackwing_revisions.versioned_name('wbw-sp-imperial-pumping-station.goo', 1)

    def typed_closure(self, output_files, native_files=None):
        archives = {'motsres': Gob(build_gob(native_files or {'native.txt': b'synthetic'})),
                    'motssnd': Gob(build_gob({'native.txt': b'synthetic'}))}
        return sp_converter.verify_typed_literal_closure(Gob(build_gob(output_files)), archives)

    def test_matching_basename_in_wrong_directory_does_not_satisfy_loader(self):
        for name, wrong_path in (('gate.cog', 'misc/gate.cog'),
                                 ('panel.mat', 'misc/panel.mat'),
                                 ('idle.key', 'misc/key/idle.key')):
            with self.subTest(name=name), self.assertRaisesRegex(
                    sp_converter.SingleplayerError, 'Unresolved typed resource path'):
                self.typed_closure({'jkl/test.jkl': name.encode(), wrong_path: b'synthetic'})

    def test_material_and_sound_fallback_use_exact_directories(self):
        report = self.typed_closure({'jkl/test.jkl': b'panel.mat chirp.wav',
                                    '3do/mat/panel.mat': b'synthetic',
                                    'voice/chirp.wav': b'synthetic'})
        self.assertEqual(report['checked_literals'], 2)
        self.assertEqual(report['distinct_literals'], 2)
        self.assertEqual(report['loader_directory_counts'], {'3do/mat': 1, 'voice': 1})

    def test_loader_directory_precedence_precedes_archive_precedence(self):
        # The engine finds native mat/sound before trying episode 3do/mat/voice.
        report = self.typed_closure({'jkl/test.jkl': b'panel.mat chirp.wav',
                                    '3do/mat/panel.mat': b'second material candidate',
                                    'voice/chirp.wav': b'second sound candidate'},
                                   {'mat/panel.mat': b'first material candidate',
                                    'sound/chirp.wav': b'first sound candidate'})
        self.assertEqual(report['provider_counts'], {'motsres': 2})
        self.assertEqual(report['loader_directory_counts'], {'mat': 1, 'sound': 1})

    def test_qualified_token_is_not_silently_stripped_to_basename(self):
        for token in (b'custom/panel.mat', b'custom\\panel.mat', b'../panel.mat'):
            with self.subTest(token=token), self.assertRaisesRegex(
                    sp_converter.SingleplayerError, 'Qualified resource token'):
                self.typed_closure({'jkl/test.jkl': token, 'mat/panel.mat': b'synthetic'})

    def test_branching_episode_retains_exact_rows_and_progression(self):
        data = (b'"Synthetic"\nTYPE 1\nSEQ 3\n'
                b'10: 1 1 LEVEL first.jkl 24 0 20 30\n'
                b'20: 1 2 LEVEL light.jkl 25 0 -1 -1\n'
                b'30: 2 2 LEVEL dark.jkl 0 29 20 -1\nend\n')
        rows = sp_converter.episode_rows(data)
        self.assertEqual(rows[0], ['10:', '1', '1', 'LEVEL', 'first.jkl', '24', '0', '20', '30'])
        self.assertEqual(rows[2][1:], ['2', '2', 'LEVEL', 'dark.jkl', '0', '29', '20', '-1'])

    def test_missing_branch_target_is_rejected(self):
        with self.assertRaisesRegex(sp_converter.SingleplayerError, 'branch'):
            sp_converter.episode_rows(b'TYPE 1\n10: 1 1 LEVEL a.jkl 0 0 30 -1\n')

    def test_duplicate_entry_and_non_sp_type_are_rejected(self):
        for data in (b'TYPE 1\n10: 1 1 LEVEL a.jkl 0 0 -1 -1\n10: 1 1 LEVEL b.jkl 0 0 -1 -1\n',
                     b'TYPE 2\n10: 1 1 LEVEL a.jkl 0 0 -1 -1\n'):
            with self.assertRaises(sp_converter.SingleplayerError):
                sp_converter.episode_rows(data)

    def test_original_contract_offers_zip_only_and_rejects_unpinned_bytes(self):
        entry = sp_converter.catalog_entries()[0]
        spec = sp_converter.recipe_details(entry['id'])
        self.assertEqual(sp_converter.original_hashes(entry['id']), [spec['zip_sha256']])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'unreviewed.zip'
            path.write_bytes(b'synthetic unrelated input')
            before = path.read_bytes()
            with self.assertRaisesRegex(sp_converter.SingleplayerError, 'reviewed original ZIP'):
                sp_converter.open_original(path, entry['id'])
            self.assertEqual(path.read_bytes(), before)


@unittest.skipUnless(os.environ.get('WBW_SP_TEST_BASELINES') and os.environ.get('WBW_SP_TEST_ORIGINAL'),
                     'Set explicit owned baselines and original ZIP paths to run private payload controls')
class SingleplayerPayloadControls(unittest.TestCase):
    """Code-only tests: retail and authored fixture bytes are supplied locally."""
    @classmethod
    def setUpClass(cls):
        cls.recipe_id = 'sp-phantom-menace-final-battle'
        cls.archives = bridge.pinned_archives(Path(os.environ['WBW_SP_TEST_BASELINES']),
                                              include_jksp=True, include_motssp=True)
        cls.originals, _ = sp_converter.open_original(Path(os.environ['WBW_SP_TEST_ORIGINAL']), cls.recipe_id)
        cls.payload, cls.manifest = sp_converter.build(cls.archives, cls.originals, cls.recipe_id)
        cls.output = Gob(cls.payload)
        cls.world_path = next(iter(sp_converter.recipe_details(cls.recipe_id)['worlds']))

    def mutated_files(self):
        return {path: self.output.read(path) for path in self.output.entries}

    def rejects(self, files, expected):
        with self.assertRaisesRegex(sp_converter.SingleplayerError, expected):
            sp_converter.verify(self.archives, self.originals, self.recipe_id, build_gob(files))

    def test_valid_payload_and_manifest_repeat_exactly(self):
        repeat, manifest = sp_converter.build(self.archives, self.originals, self.recipe_id)
        self.assertEqual(self.payload, repeat)
        self.assertEqual(self.manifest, manifest)
        self.assertEqual(sp_converter.verify(self.archives, self.originals, self.recipe_id,
                                             self.payload)['status'], 'structural-preservation-pass')

    def test_missing_source_cog_and_model_are_rejected(self):
        for path in ('cog/bs_untitled_start.cog', '3do/bs_obiduel.3do'):
            with self.subTest(path=path):
                files = self.mutated_files(); del files[path]
                self.rejects(files, 'Source resource transformation')

    def test_changed_authored_cog_is_rejected(self):
        files = self.mutated_files()
        files['cog/bs_untitled_start.cog'] += b'\n'
        self.rejects(files, 'Source resource transformation')

    def test_progression_change_is_rejected(self):
        files = self.mutated_files(); files['episode.jk'] += b'\n'
        self.rejects(files, 'Episode progression')

    def test_header_and_physics_change_is_rejected(self):
        files = self.mutated_files()
        world = bridge.text(files[self.world_path])
        changed, count = re.subn(r'(?im)^(World gravity\s+)\S+', r'\g<1>123', world, count=1)
        self.assertEqual(count, 1)
        files[self.world_path] = changed.encode('cp1252')
        self.rejects(files, 'header, normals, physics')

    def test_authored_template_parameter_change_is_rejected(self):
        files = self.mutated_files(); world = bridge.text(files[self.world_path])
        rows = bridge.records(world, 'templates')
        index = next(i for i,row in enumerate(rows) if row.startswith('bs_') and 'health=' in row)
        rows[index] = re.sub(r'health=\S+', 'health=123456', rows[index], count=1)
        files[self.world_path] = bridge.replace_block(world, 'templates', rows).encode('cp1252')
        self.rejects(files, 'Authored template physics')

    def test_placed_thing_template_change_is_rejected(self):
        files = self.mutated_files(); world = bridge.text(files[self.world_path])
        rows = bridge.records(world, 'things'); parts = rows[0].split(); parts[1] = 'bs_unreviewed'
        rows[0] = ' '.join(parts)
        files[self.world_path] = bridge.replace_block(world, 'things', rows,
            int(bridge.block(world, 'things')[2])).encode('cp1252')
        self.rejects(files, 'Placed thing parameters')

    def test_missing_native_preload_is_rejected(self):
        files = self.mutated_files(); world = bridge.text(files[self.world_path])
        rows = bridge.records(world, 'scripts'); del rows[-1]
        files[self.world_path] = bridge.replace_block(world, 'scripts', rows,
            int(bridge.block(world, 'scripts')[2])).encode('cp1252')
        self.rejects(files, 'Resource table differs')

    def test_arbitrary_identical_native_asset_and_native_override_are_rejected(self):
        path = next(path for path in self.archives['motsres'].entries
                    if path.endswith('.wav') and path not in self.output.entries)
        for raw in (self.archives['motsres'].read(path), b'unreviewed override'):
            with self.subTest(identical=raw == self.archives['motsres'].read(path)):
                files = self.mutated_files(); files[path] = raw
                self.rejects(files, 'Native copied resource set')

    def test_native_player_controller_override_is_rejected(self):
        path = 'cog/kyle_m.cog'
        files = self.mutated_files(); files[path] = self.archives['motsres'].read(path) + b'\n'
        self.rejects(files, 'Native copied resource set')

    def test_gameplay_capacity_change_is_rejected(self):
        files = self.mutated_files(); world = bridge.text(files[self.world_path])
        files[self.world_path] = bridge.replace_block(world, 'cogs', bridge.records(world, 'cogs'), 0).encode('cp1252')
        self.rejects(files, 'Gameplay table capacity')

    def test_adapter_writes_exact_notices_and_refuses_repository_or_nonempty_stage(self):
        original = Path(os.environ['WBW_SP_TEST_ORIGINAL'])
        with tempfile.TemporaryDirectory() as directory:
            result = sp_converter.build_to_directory(self.archives, original, directory, self.recipe_id)
            self.assertEqual(set(result), {'filename', 'manifest_filename', 'verification', 'startup_overlay'})
            self.assertIsNone(result['startup_overlay'])
            self.assertEqual((Path(directory) / result['filename']).read_bytes(), self.payload)
            _, notices = sp_converter.open_original(original, self.recipe_id)
            for name, data in notices.items():
                self.assertEqual((Path(directory) / name).read_bytes(), data)
            with self.assertRaisesRegex(sp_converter.SingleplayerError, 'empty staging'):
                sp_converter.build_to_directory(self.archives, original, directory, self.recipe_id)
        with self.assertRaisesRegex(sp_converter.SingleplayerError, 'outside the source'):
            sp_converter.build_to_directory(self.archives, original, Path(__file__).parent, self.recipe_id)


@unittest.skipUnless(os.environ.get('WBW_SP_TEST_BASELINES') and os.environ.get('WBW_SP_TEST_MAUL_ORIGINAL'),
                     'Set explicit owned baselines and Maul/Jinn source ZIP to run private payload controls')
class MaulJinnPayloadControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe_id = 'sp-maul-vs-qui-gon'
        cls.archives = bridge.pinned_archives(Path(os.environ['WBW_SP_TEST_BASELINES']),
                                              include_jksp=True, include_motssp=True)
        cls.originals, _ = sp_converter.open_original(Path(os.environ['WBW_SP_TEST_MAUL_ORIGINAL']), cls.recipe_id)
        cls.payload, cls.manifest = sp_converter.build(cls.archives, cls.originals, cls.recipe_id)
        cls.output = Gob(cls.payload)

    def test_full_episode_rebuild_and_original_force_setup_preserved(self):
        repeat, manifest = sp_converter.build(self.archives, self.originals, self.recipe_id)
        self.assertEqual(repeat, self.payload); self.assertEqual(manifest, self.manifest)
        self.assertEqual(self.output.read('episode.jk'), self.originals['episode'].read('episode.jk'))
        self.assertEqual(sp_converter.verify(self.archives, self.originals, self.recipe_id,
            self.payload)['status'], 'structural-preservation-pass')
        self.assertEqual(sp_converter.recipe_details(self.recipe_id)['entry']['massassi_id'], 26)

    def test_changed_authored_force_rank_is_rejected(self):
        files = {path: self.output.read(path) for path in self.output.entries}
        path = 'cog/bs_duel_start.cog'
        changed = files[path].replace(b'SetInv(player, 20, 7)', b'SetInv(player, 20, 8)')
        self.assertNotEqual(changed, files[path]); files[path] = changed
        with self.assertRaisesRegex(sp_converter.SingleplayerError, 'Source resource transformation'):
            sp_converter.verify(self.archives, self.originals, self.recipe_id, build_gob(files))

    def test_sector_sound_rewrite_is_verified_without_allowing_arbitrary_change(self):
        files = {path: self.output.read(path) for path in self.output.entries}
        path = 'jkl/zela_duel.jkl'
        world = bridge.text(files[path])
        changed, count = re.subn(r'(?m)^(SOUND\s+)\S+', r'\g<1>unreviewed.wav', world, count=1)
        self.assertEqual(count, 1)
        files[path] = changed.encode('cp1252')
        with self.assertRaisesRegex(sp_converter.SingleplayerError, 'geometry/topology change: sectors'):
            sp_converter.verify(self.archives, self.originals, self.recipe_id, build_gob(files))

    def test_native_pickup_controller_cannot_be_overridden(self):
        files = {path: self.output.read(path) for path in self.output.entries}
        files['cog/pow_mana.cog'] = self.archives['jkres'].read('cog/pow_mana.cog')
        with self.assertRaisesRegex(sp_converter.SingleplayerError, 'Native copied resource set'):
            sp_converter.verify(self.archives, self.originals, self.recipe_id, build_gob(files))


@unittest.skipUnless(os.environ.get('WBW_SP_TEST_BASELINES') and os.environ.get('WBW_SP_TEST_PUMPING_ORIGINAL'),
                     'Set explicit owned baselines and Pumping Station source ZIP to run private payload controls')
class PumpingStationPayloadControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe_id = 'sp-imperial-pumping-station'
        cls.archives = bridge.pinned_archives(Path(os.environ['WBW_SP_TEST_BASELINES']),
                                              include_jksp=True, include_motssp=True)
        cls.originals, cls.notices = sp_converter.open_original(
            Path(os.environ['WBW_SP_TEST_PUMPING_ORIGINAL']), cls.recipe_id)
        cls.payload, cls.manifest = sp_converter.build(cls.archives, cls.originals, cls.recipe_id)
        cls.output = Gob(cls.payload)

    def files(self):
        return {path: self.output.read(path) for path in self.output.entries}

    def rejects(self, files, expected):
        with self.assertRaisesRegex(sp_converter.SingleplayerError, expected):
            sp_converter.verify(self.archives, self.originals, self.recipe_id, build_gob(files))

    def test_repeat_build_preserves_episode_and_non_jedi_inventory(self):
        repeat, manifest = sp_converter.build(self.archives, self.originals, self.recipe_id)
        self.assertEqual((repeat, manifest), (self.payload, self.manifest))
        self.assertEqual(self.output.read('episode.jk'), self.originals['episode'].read('episode.jk'))
        report = sp_converter.verify(self.archives, self.originals, self.recipe_id, self.payload)
        self.assertEqual(report['status'], 'structural-preservation-pass')
        self.assertFalse(report['runtime_verified'])
        source = bridge.text(self.originals['episode'].read('cog/installation_start.cog'))
        converted = bridge.text(self.output.read('cog/bs_installation_start.cog'))
        self.assertEqual(source, converted)  # No filename/default-template substitutions in this COG.
        self.assertIn('SetInv(player, 20, 0);', converted)
        for ordinal, amount in ((1, 1), (2, 1), (3, 1), (4, 12), (8, 3), (11, 300)):
            self.assertIn(f'SetInv(player, {ordinal}, {amount});', converted)
        self.assertNotIn('SetInv(player, 131,', converted)

    def test_adding_force_rank_or_rewriting_original_weapon_ordinal_is_rejected(self):
        path = 'cog/bs_installation_start.cog'
        for old, new in ((b'SetInv(player, 20, 0);', b'SetInv(player, 20, 8);'),
                         (b'SetInv(player, 8, 3);', b'SetInv(player, 128, 3);')):
            with self.subTest(change=new):
                files = self.files()
                self.assertIn(old, files[path])
                files[path] = files[path].replace(old, new)
                self.rejects(files, 'Source resource transformation')

    def test_corbit_player_model_and_reactor_model_are_retained(self):
        world = bridge.text(self.output.read('jkl/mk_ips.jkl'))
        rows = bridge.records(world, 'templates')
        player = next(row for row in rows if row.startswith('bs_walkplayer2 '))
        self.assertIn('type=player', player)
        self.assertIn('model3d=bs_rebcom.3do', player)
        self.assertIn('cog=kyle_m.cog', player)
        self.assertNotIn('model3d=ky.3do', player)
        reactor = next(row for row in rows if row.startswith('bs_reactorbomb '))
        self.assertIn('model3d=bs_bomb.3do', reactor)
        self.assertNotIn('cog=pow_', reactor)
        files = self.files()
        del files['3do/bs_rebcom.3do']
        self.rejects(files, 'Source resource transformation')

    def test_native_ordinary_pickups_do_not_ship_jk_controller_replacements(self):
        world = bridge.text(self.output.read('jkl/mk_ips.jkl'))
        for name in ('pow_drailgun', 'pow_drepeater', 'pow_dstrifle', 'pow_energy',
                     'pow_railcharges', 'pow_sequencer', 'pow_smbkpk', 'pow_thermal'):
            with self.subTest(controller=name):
                self.assertIn(name + '_m.cog', world)
                self.assertNotIn('cog/bs_' + name + '.cog', self.output.entries)
                self.assertNotIn('cog/' + name + '_m.cog', self.output.entries)
        files = self.files()
        files['cog/pow_energy_m.cog'] = self.archives['jkres'].read('cog/pow_energy.cog')
        self.rejects(files, 'Native copied resource set')

    def test_original_wrench_logic_stays_isolated_from_mots_story_dialogue(self):
        for color, bin_number in (('blue', 49), ('yellow', 50)):
            path = 'cog/bs_pow_wrench' + color + '.cog'
            value = bridge.text(self.output.read(path))
            self.assertRegex(value, rf'\bbin\s*=\s*{bin_number}\b')
            self.assertNotIn('PlayVoiceLocal', value)
            self.assertNotIn('Duncansnd', value)
            self.assertNotIn('cog/pow_wrench' + color + '.cog', self.output.entries)
            files = self.files()
            native = 'cog/pow_wrench' + color + '.cog'
            files[path] = self.archives['motsres'].read(native)
            self.rejects(files, 'Source resource transformation')

    def test_no_speculative_camera_repair_and_no_removed_goal_sequence(self):
        start = bridge.text(self.output.read('cog/bs_installation_start.cog'))
        self.assertEqual(start.count('stopbrief'), 1)
        self.assertEqual(start.count('briefstop'), 3)
        files = self.files()
        path = 'cog/bs_installation_goals.cog'
        self.assertIn(b'jkEndLevel(1);', files[path])
        files[path] = files[path].replace(b'jkEndLevel(1);', b'return;')
        self.rejects(files, 'Source resource transformation')

    def test_key_gate_and_pump_control_changes_are_rejected(self):
        for path, old, new in (
                ('cog/bs_watergate.cog', b'GetInv(GetSourceRef(), 49)', b'GetInv(GetSourceRef(), 50)'),
                ('cog/bs_movepipes.cog', b'GetInv(GetSourceRef(), 50)', b'GetInv(GetSourceRef(), 49)'),
                ('cog/bs_pumpcontrol.cog', b'pathmovepause', b'pathmoveresume')):
            with self.subTest(path=path):
                files = self.files()
                self.assertIn(old, files[path])
                files[path] = files[path].replace(old, new)
                self.rejects(files, 'Source resource transformation')


if __name__ == '__main__':
    unittest.main()

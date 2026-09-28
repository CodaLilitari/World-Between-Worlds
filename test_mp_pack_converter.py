"""Synthetic failures for multi-world graph preservation and archive unions."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import blackwing_revisions
from gob import Gob, build_gob
import mp_pack_converter as converter
import verify_retail


class ChaosStartupProfileTests(unittest.TestCase):
    """Synthetic source bytes exercise the narrow contract and independent verifier."""
    def setUp(self):
        self.original = ('symbols\nend\ncode\npulse:\n' + converter.FORCE_PULSE_OLD
                         + '\n   Return;\nend\n').encode('cp1252')
        self.expected = ('symbols\nend\ncode\npulse:\n'
                         '   maximum = GetInv(player, 20) * 50;\n'
                         '   if (IsMulti())\n      SetInv(player, 69, maximum);\n'
                         '   Return;\nend\n').encode('cp1252')
        self.payload = build_gob({'cog/force_well.cog': self.expected})
        self.empty = Gob(build_gob({}))
        self.archives = dict(motsmp=self.empty, motssnd=self.empty,
                             motsres=Gob(build_gob({'cog/force_well.cog': self.original})))
        rules = {'force_well.cog': dict(sha256=converter.digest(self.original), edits=[
            dict(old=converter.FORCE_PULSE_OLD, new=converter.FORCE_PULSE_NEW,
                 count=1, reason='Synthetic reviewed pulse operation.')])}
        worlds = {}
        for path, (name, rank) in converter.CHAOS_RANKS.items():
            key = Path(path).stem
            anchor = f'SetInv(player, 20, {rank});'
            worlds[key] = dict(key='fixture-' + key, tag=key, world=path,
                gob_sha256='a' * 64, episode_type=2, native_cog_edits=copy.deepcopy(rules),
                runtime_cogs='kyle.cog', environment=('pow_mana.cog ' if key != 'academy' else '') + name,
                cog_sha256={name: 'b' * 64}, cog_edits={name: [
                    dict(old=anchor, new=anchor + '\n  if (IsMulti())\n    SetInv(player, 69, GetInv(player, 20) * 50);',
                         count=1, reason='Synthetic reviewed rank synchronization.'),
                    dict(old='SetInv(player, 10, 1);', new='SetInv(player, 131, 1);',
                         count=1, reason='Synthetic reviewed saber operation.')]})
        self.spec = dict(key='fixture', tag='fixture', title='Synthetic campaign',
                         author='Fixture', source_url='https://example.test/fixture',
                         gob_sha256='a' * 64, world_specs=worlds,
                         startup_profile=dict(profile_id='chaos-force-ranks-v1',
                             source_gob_sha256='a' * 64, runtime_mode='mots-multiplayer',
                             expected_native_members=['cog/force_well.cog'],
                             native_cog_edits=rules, required_world_paths=list(converter.CHAOS_RANKS)))

    def check_bytes(self, payload=None, spec=None, archives=None):
        return verify_retail.check_community_startup_payload(
            self.archives if archives is None else archives, self.empty, self.empty,
            self.spec['world_specs']['academy'] if spec is None else spec, {},
            self.payload if payload is None else payload)

    def test_exact_profile_and_source_reconstruction_pass(self):
        self.assertEqual(converter.startup_contract(self.spec)['folder_name'], 'bridge-fixture-startup')
        self.assertEqual(self.check_bytes()['sha256'], converter.digest(self.payload))

    def test_no_profile_rejects_every_native_override_field(self):
        for field in converter.NATIVE_OVERRIDE_FIELDS:
            spec = dict(world_specs={'fixture': {field: {'unreviewed': {}}}})
            with self.subTest(field=field), self.assertRaisesRegex(converter.PackError, 'does not merge'):
                converter.startup_contract(spec)
        self.assertIsNone(converter.startup_contract(dict(world_specs={'fixture': {}})))

    def test_profile_rejects_extra_override_and_extra_metadata(self):
        for field in converter.NATIVE_OVERRIDE_FIELDS[1:]:
            spec = copy.deepcopy(self.spec)
            spec['world_specs']['club'][field] = {'unreviewed': {}}
            with self.subTest(field=field), self.assertRaisesRegex(converter.PackError, 'sole native'):
                converter.startup_contract(spec)
        self.spec['startup_profile']['native_template_overrides'] = {}
        with self.assertRaisesRegex(converter.PackError, 'profile fields'):
            converter.startup_contract(self.spec)

    def test_profile_rejects_added_or_replaced_native_member(self):
        for members in (['cog/force_well.cog', 'cog/kyle_m.cog'], ['cog/kyle_m.cog']):
            self.spec['startup_profile']['expected_native_members'] = members
            with self.subTest(members=members), self.assertRaisesRegex(converter.PackError, 'member set'):
                converter.startup_contract(self.spec)

    def test_every_world_must_share_the_same_rule(self):
        self.spec['world_specs']['club']['native_cog_edits']['force_well.cog']['sha256'] = 'c' * 64
        with self.assertRaisesRegex(converter.PackError, 'components must agree'):
            converter.startup_contract(self.spec)

    def test_missing_world_wrong_mode_or_pack_pin_is_rejected(self):
        for change in ('world', 'mode', 'pin'):
            spec = copy.deepcopy(self.spec)
            if change == 'world':
                del spec['world_specs']['club']
            elif change == 'mode':
                spec['world_specs']['club']['episode_type'] = 16
            else:
                spec['startup_profile']['source_gob_sha256'] = 'd' * 64
            with self.subTest(change=change), self.assertRaises(converter.PackError):
                converter.startup_contract(spec)

    def test_source_operation_anchor_count_and_sp_policy_are_exact(self):
        for field, value in (('old', 'if (!IsMulti())'), ('count', 2), ('count', True),
                              ('new', 'SetInv(player, 69, maximum);')):
            spec = copy.deepcopy(self.spec)
            spec['startup_profile']['native_cog_edits']['force_well.cog']['edits'][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaisesRegex(converter.PackError, 'source operation'):
                converter.startup_contract(spec)

    def test_world_rank_saber_and_no_timer_reset_are_exact(self):
        for field, value in (('new', 'SetTimer(0);'), ('count', 0), ('old', 'SetInv(player, 20, 4);')):
            spec = copy.deepcopy(self.spec)
            spec['world_specs']['academy']['cog_edits']['academy_start.cog'][0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(converter.PackError, 'rank synchronization'):
                converter.startup_contract(spec)
        self.spec['world_specs']['club']['cog_edits']['club_start.cog'].pop()
        with self.assertRaisesRegex(converter.PackError, 'rank synchronization'):
            converter.startup_contract(self.spec)

    def test_authored_mana_cannot_be_reclassified_as_native_runtime(self):
        self.spec['world_specs']['club']['runtime_cogs'] += ' pow_mana.cog'
        with self.assertRaisesRegex(converter.PackError, 'authored mana'):
            converter.startup_contract(self.spec)

    def test_independent_verifier_rejects_forged_output_and_extra_member(self):
        for files in ({'cog/force_well.cog': self.expected + b' changed'},
                      {'cog/force_well.cog': self.expected, 'cog/kyle_m.cog': b'extra'}):
            with self.subTest(files=list(files)), self.assertRaises(AssertionError):
                self.check_bytes(build_gob(files))

    def test_independent_verifier_rejects_wrong_provider_path_or_hash(self):
        for path, data in (('other/force_well.cog', self.original),
                           ('cog/force_well.cog', self.original + b' changed')):
            archives = dict(self.archives, motsres=Gob(build_gob({path: data})))
            with self.subTest(path=path), self.assertRaises(AssertionError):
                self.check_bytes(archives=archives)

    def test_independent_verifier_requires_actual_anchor_count_even_if_repinned(self):
        for original in (self.original.replace(converter.FORCE_PULSE_OLD.encode(), b'no anchor'),
                         self.original + converter.FORCE_PULSE_OLD.encode()):
            spec = copy.deepcopy(self.spec['world_specs']['academy'])
            spec['native_cog_edits']['force_well.cog']['sha256'] = converter.digest(original)
            archives = dict(self.archives, motsres=Gob(build_gob({'cog/force_well.cog': original})))
            with self.subTest(sha256=converter.digest(original)), self.assertRaises(AssertionError):
                self.check_bytes(spec=spec, archives=archives)

    def test_independent_verifier_rejects_startup_without_source_rule(self):
        with self.assertRaisesRegex(AssertionError, 'without reviewed source'):
            self.check_bytes(spec=dict(tag='fixture'))

    def test_existing_filesystem_checker_keeps_exact_folder_and_byte_checks(self):
        spec = self.spec['world_specs']['academy']
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            (folder / 'bridge-academy-startup.goo').write_bytes(self.payload)
            (folder / 'README.txt').write_text('Synthetic startup instructions.')
            args = (self.archives, self.empty, self.empty, spec, {}, folder)
            result = verify_retail.check_community_startup(*args)
            self.assertIn('required isolated startup folder and deterministic archive bytes', result['passed'])
            (folder / 'extra.txt').write_text('Unexpected loose resource.')
            with self.assertRaisesRegex(AssertionError, 'extra files'):
                verify_retail.check_community_startup(*args)

    def test_profile_writer_delivers_paired_startup_and_retains_notice(self):
        episode = build_gob({'episode.jk': b'Synthetic episode'})
        startup = dict(converter.startup_contract(self.spec), sha256=converter.digest(self.payload))
        manifest = dict(verification={'status': 'fixture'}, required_startup_overlay=startup,
                        _startup_data=self.payload)
        with tempfile.TemporaryDirectory() as root:
            stage = Path(root) / 'fresh'
            with patch.object(converter, 'recipe_details', return_value=self.spec), \
                    patch.object(converter, 'read_original', return_value=(self.empty, {'notice.txt': b'Original notice\r\n'})), \
                    patch.object(converter, 'build_payload', return_value=(episode, manifest)):
                result = converter.build_to_directory({}, 'unused.zip', stage, 'fixture')
            folder = stage / result['startup_overlay']
            self.assertEqual((folder / startup['archive_name']).read_bytes(), self.payload)
            self.assertEqual((stage / 'ORIGINAL-01-notice.txt').read_bytes(), b'Original notice\r\n')
            saved = json.loads((stage / result['manifest_filename']).read_text())
            self.assertNotIn('_startup_data', saved)
            self.assertEqual(saved['required_startup_overlay']['sha256'], converter.digest(self.payload))
            text = (stage / 'README.txt').read_text()
            for required in ('-motsCompat -path bridge-fixture-startup', 'restart', 'Every peer'):
                self.assertIn(required, text)
            self.assertNotIn('No startup overlay is required', text)
            self.assertEqual((folder / 'README.txt').read_text(), text)

    def component_build(self, change=None):
        """Isolate pack aggregation; startup checks and union checks remain real."""
        spec = copy.deepcopy(self.spec)
        episode = b'"Synthetic campaign"\nTYPE 2\nSEQ 3\n'
        for i, name in enumerate(spec['world_specs']):
            episode += f'{10+i}: 0 {i+1} LEVEL {name}.jkl 0 0 {11+i if i<2 else -1} -1\n'.encode()
        episode += b'end\n'
        source = Gob(build_gob({'episode.jk': episode, 'misc/cogstrings.uni': b'MSGS 0\nEND\n'}))
        spec.update(gob_sha256=source.sha256, zip_sha256='a'*64,
                    episode_sha256=converter.digest(episode), episode_rows=converter.episode_rows(episode))
        spec['startup_profile']['source_gob_sha256'] = source.sha256
        candidates = []
        for row, (name, world) in zip(spec['episode_rows'], spec['world_specs'].items()):
            row['world_spec'] = name
            world['gob_sha256'] = source.sha256
            files = {'jkl/br_' + world['tag'] + '.jkl': b'', 'episode.jk': b''}
            if change == 'episode-copy':
                files['cog/force_well.cog'] = self.expected
            manifest = dict(_startup_data=self.payload, literal_dependencies_unresolved=[])
            if name == 'club':
                if change == 'missing':
                    del manifest['_startup_data']
                elif change == 'different':
                    manifest['_startup_data'] = build_gob({'cog/force_well.cog': self.expected + b' changed'})
                elif change == 'extra':
                    manifest['_startup_data'] = build_gob({'cog/force_well.cog': self.expected, 'cog/extra.cog': b'extra'})
                elif change == 'new-omission':
                    files['cog/extra.cog'] = b'sound missing=new_missing.wav\n'
            candidates.append((build_gob(files), manifest))
        def component_check(archives, generated, *, community, community_spec, community_startup_payload):
            return verify_retail.check_community_startup_payload(
                archives, generated, community, community_spec, {}, community_startup_payload)
        with patch.object(converter.bridge, 'recipe', side_effect=candidates), \
                patch.object(converter.verify_retail, 'check', side_effect=component_check) as checker:
            result = converter.build_payload(self.archives, source, spec)
        self.assertEqual(checker.call_count, 3)
        return result

    def test_pack_aggregation_binds_all_three_independent_startup_checks(self):
        payload, manifest = self.component_build()
        self.assertEqual(manifest['_startup_data'], self.payload)
        self.assertEqual(manifest['schema'], 1)
        self.assertNotIn('cog/force_well.cog', Gob(payload).entries)
        self.assertEqual(len(manifest['verification']['world_checks']), 3)
        for world in manifest['world_manifests'].values():
            self.assertEqual(world['required_startup_overlay']['folder_name'], 'bridge-fixture-startup')
            self.assertNotIn('_startup_data', world)

    def test_pack_aggregation_rejects_missing_different_or_extra_startup(self):
        for change, message in [('missing', 'startup payload is missing'), ('different', 'Different startup bytes'),
                                 ('extra', 'member set'), ('episode-copy', 'must not be copied')]:
            with self.subTest(change=change), self.assertRaisesRegex(converter.PackError, message):
                self.component_build(change)

    def test_pack_profile_does_not_waive_a_new_missing_resource(self):
        with self.assertRaises(converter.bridge.RecipeError):
            self.component_build('new-omission')


class MultiplayerPackTests(unittest.TestCase):
    def setUp(self):
        self.episode = (b'"Synthetic pack"\r\nTYPE 2\r\nSEQ 2\r\n'
                        b'# LEVEL one.jkl is documentation\r\n'
                        b'10: 1 1 LEVEL one.jkl 0 0 11 -1\r\n'
                        b'11: 0 2 LEVEL two.jkl 0 0 10 -1 # LEVEL one.jkl is documentation\r\nend\r\n')
        self.strings = (b'MSGS 4\r\n"ONE" 0 "Original one"\r\n'
                        b'"ONE_TEXT_00" 0 "Created by Fixture"\r\n'
                        b'"TWO" 0 "Original two"\r\n'
                        b'"OTHER" 0 "ONE is a value"\r\nEND\r\n')
        self.source = Gob(build_gob({'episode.jk': self.episode,
                                     'misc/cogstrings.uni': self.strings}))
        self.spec = dict(episode_sha256=converter.digest(self.episode),
                         episode_rows=[dict(line=10, disc=1, level=1, type='LEVEL',
                                            world='jkl/one.jkl', lightpow=0, darkpow=0,
                                            goto_a=11, goto_b=-1, world_spec='one'),
                                       dict(line=11, disc=0, level=2, type='LEVEL',
                                            world='jkl/two.jkl', lightpow=0, darkpow=0,
                                            goto_a=10, goto_b=-1, world_spec='two')],
                         world_specs={'one': dict(world='jkl/one.jkl', tag='first'),
                                      'two': dict(world='jkl/two.jkl', tag='second')})

    def test_preserves_graph_comments_values_and_line_endings(self):
        result = converter.metadata(self.source, self.spec)
        self.assertEqual(result['episode.jk'], self.episode.replace(
            b'LEVEL one.jkl 0', b'LEVEL br_first.jkl 0').replace(
            b'LEVEL two.jkl 0', b'LEVEL br_second.jkl 0'))
        self.assertEqual(result['misc/cogstrings.uni'], self.strings.replace(
            b'"ONE"', b'"BR_FIRST"').replace(b'"ONE_TEXT_00"', b'"BR_FIRST_TEXT_00"').replace(
            b'"TWO"', b'"BR_SECOND"'))

    def test_omitted_second_world_is_not_a_complete_pack(self):
        del self.spec['world_specs']['two']
        with self.assertRaisesRegex(converter.PackError, 'Every pack component'):
            converter.metadata(self.source, self.spec)

    def test_world_rename_does_not_permit_altered_transition(self):
        self.spec['episode_rows'][1]['goto_a'] = 11
        with self.assertRaisesRegex(converter.PackError, 'rows differ'):
            converter.metadata(self.source, self.spec)

    def test_unlisted_component_requires_graph_review(self):
        self.spec['world_specs']['orphan'] = dict(world='jkl/orphan.jkl', tag='orphan')
        with self.assertRaisesRegex(converter.PackError, 'Every pack component'):
            converter.metadata(self.source, self.spec)

    def test_duplicate_output_world_names_fail(self):
        self.spec['world_specs']['two']['tag'] = 'first'
        with self.assertRaisesRegex(converter.PackError, 'world names collide'):
            converter.metadata(self.source, self.spec)

    def test_conflict_is_based_on_complete_normalized_virtual_path(self):
        left = Gob(build_gob({'mat/example.mat': b'one'}))
        right = Gob(build_gob({'3do/mat/example.mat': b'two'}))
        result, providers = converter.resource_union([('one', left), ('two', right)])
        self.assertEqual(result, {'mat/example.mat': b'one', '3do/mat/example.mat': b'two'})

    def test_shared_equal_bytes_are_kept_once_with_both_providers(self):
        left = Gob(build_gob({'cog/shared.cog': b'same', 'episode.jk': b'one'}))
        right = Gob(build_gob({'COG\\SHARED.COG': b'same', 'episode.jk': b'two'}))
        result, providers = converter.resource_union([('one', left), ('two', right)])
        self.assertEqual(result, {'cog/shared.cog': b'same'})
        self.assertEqual(providers['cog/shared.cog'], ['one', 'two'])

    def test_shared_different_bytes_fail_instead_of_last_writer_winning(self):
        left = Gob(build_gob({'cog/shared.cog': b'one'}))
        right = Gob(build_gob({'COG\\SHARED.COG': b'two'}))
        with self.assertRaisesRegex(converter.PackError, 'cog/shared.cog: one, two'):
            converter.resource_union([('one', left), ('two', right)])

    def test_separate_native_episode_is_not_a_runtime_dependency_provider(self):
        output = Gob(build_gob({'cog/example.cog': b'material value=ghost.mat\n',
                                 'episode.jk': b'', 'misc/cogstrings.uni': b''}))
        archives = {'motsmp': Gob(build_gob({'mat/ghost.mat': b'not mounted'})),
                    'motsres': Gob(build_gob({})), 'motssnd': Gob(build_gob({}))}
        with self.assertRaises(converter.bridge.RecipeError):
            converter.validate_union(archives, output, [('one', output)],
                                     {'episode.jk': b'', 'misc/cogstrings.uni': b''})

    def test_pack_components_remain_outside_selectable_catalog(self):
        rows = converter.catalog_entries()
        self.assertIn('mp-6000-block', [row['id'] for row in rows])
        self.assertNotIn('mp-6000-block-sabers', [row['id'] for row in rows])
        details = converter.recipe_details('mp-6000-block')
        self.assertEqual(details['world_specs']['sabers']['key'], 'mp-6000-block-sabers')


class EpisodeIdentifierRepairTests(unittest.TestCase):
    def setUp(self):
        self.episode = (b'"Synthetic duplicate"\r\nTYPE 2\r\nSEQ 3\r\n'
                        b'# 11: is retained documentation\r\n'
                        b'10: 1 1 LEVEL one.jkl 0 0 -1 -1\r\n'
                        b'11: 0 2 LEVEL two.jkl 0 0 -1 -1\r\n'
                        b'11:\t0\t2\tLEVEL\tthree.jkl\t0\t0\t-1\t-1 # keep 11: here\r\nend\r\n')
        self.row = self.episode.splitlines(keepends=True)[6]
        self.spec = {
            'episode_sha256': converter.digest(self.episode),
            'episode_rows': converter.episode_rows(self.episode),
            'episode_row_repairs': [{
                'row_index': 2, 'old_line': 11, 'new_line': 12,
                'row_sha256': converter.digest(self.row), 'count': 1,
                'reason': 'Synthetic terminal third row has an unreferenced duplicate ID.',
            }],
        }

    def test_exact_repair_keeps_level_column_branches_comments_and_order(self):
        result, rows = converter.reviewed_episode(self.episode, self.spec)
        self.assertEqual(result, self.episode.replace(self.row, b'12:' + self.row[3:]))
        self.assertEqual([row['line'] for row in rows], [10, 11, 12])
        self.assertEqual([row['level'] for row in rows], [1, 2, 2])
        self.assertTrue(all(row['goto_a'] == row['goto_b'] == -1 for row in rows))
        self.assertEqual([row['line'] for row in self.spec['episode_rows']], [10, 11, 11])

    def test_duplicate_without_explicit_repair_remains_rejected(self):
        del self.spec['episode_row_repairs']
        with self.assertRaisesRegex(converter.PackError, 'Duplicate episode row'):
            converter.reviewed_episode(self.episode, self.spec)

    def test_changed_episode_or_row_hash_fails(self):
        with self.assertRaisesRegex(converter.PackError, 'Original episode graph'):
            converter.reviewed_episode(self.episode.replace(b'Synthetic', b'Changed'), self.spec)
        self.spec['episode_row_repairs'][0]['row_sha256'] = '0' * 64
        with self.assertRaisesRegex(converter.PackError, 'repair row differs'):
            converter.reviewed_episode(self.episode, self.spec)

    def test_incoming_branch_to_either_identifier_requires_separate_review(self):
        for target in (11, 12):
            with self.subTest(target=target):
                episode = self.episode.replace(b'one.jkl 0 0 -1 -1',
                                               f'one.jkl 0 0 {target} -1'.encode())
                spec = copy.deepcopy(self.spec)
                spec['episode_sha256'] = converter.digest(episode)
                spec['episode_rows'] = converter.episode_rows(episode)
                with self.assertRaisesRegex(converter.PackError, 'Referenced episode identifiers'):
                    converter.reviewed_episode(episode, spec)

    def test_first_occurrence_or_existing_destination_is_not_repaired(self):
        self.spec['episode_row_repairs'][0]['row_index'] = 1
        with self.assertRaisesRegex(converter.PackError, 'Only a later duplicate'):
            converter.reviewed_episode(self.episode, self.spec)
        self.spec['episode_row_repairs'][0]['row_index'] = 2
        self.spec['episode_row_repairs'][0]['new_line'] = 10
        with self.assertRaisesRegex(converter.PackError, 'already exists'):
            converter.reviewed_episode(self.episode, self.spec)

    def test_unreviewed_repair_field_and_wrong_count_fail(self):
        self.spec['episode_row_repairs'][0]['new_level'] = 3
        with self.assertRaisesRegex(converter.PackError, 'Unreviewed episode row repair'):
            converter.reviewed_episode(self.episode, self.spec)
        del self.spec['episode_row_repairs'][0]['new_level']
        self.spec['episode_row_repairs'][0]['count'] = 2
        with self.assertRaisesRegex(converter.PackError, 'one valid counted'):
            converter.reviewed_episode(self.episode, self.spec)

    def test_recipe_row_mismatch_cannot_be_used_to_repair_another_field(self):
        self.spec['episode_rows'][2]['level'] = 3
        with self.assertRaisesRegex(converter.PackError, 'rows differ from original'):
            converter.reviewed_episode(self.episode, self.spec)

    def test_metadata_keeps_all_three_world_labels_with_identifier_repair(self):
        strings = b'MSGS 3\r\n"ONE" 0 "First"\r\n"TWO" 0 "Second"\r\n"THREE" 0 "Third"\r\nEND\r\n'
        source = Gob(build_gob({'episode.jk': self.episode, 'misc/cogstrings.uni': strings}))
        spec = copy.deepcopy(self.spec)
        spec['world_specs'] = {key: {'world': f'jkl/{key}.jkl', 'tag': 'test_' + key}
                               for key in ('one', 'two', 'three')}
        for key, row in zip(spec['world_specs'], spec['episode_rows']):
            row['world_spec'] = key
        output = converter.metadata(source, spec)
        rows = converter.episode_rows(output['episode.jk'])
        self.assertEqual([row['line'] for row in rows], [10, 11, 12])
        self.assertEqual([row['world'] for row in rows],
                         ['jkl/br_test_one.jkl', 'jkl/br_test_two.jkl', 'jkl/br_test_three.jkl'])
        self.assertEqual(output['misc/cogstrings.uni'], strings.replace(b'"ONE"', b'"BR_TEST_ONE"')
                         .replace(b'"TWO"', b'"BR_TEST_TWO"').replace(b'"THREE"', b'"BR_TEST_THREE"'))


class PackOmissionTests(unittest.TestCase):
    def setUp(self):
        self.original = b'World scripts 1\n0: lost_start.cog\nWorld cogs 1\n0: lost_start.cog\n'
        self.converted = self.original.replace(b'lost_start.cog', b'br_lost_start.cog')
        self.source = Gob(build_gob({'jkl/one.jkl': self.original}))
        self.metadata = {'episode.jk': b'', 'misc/cogstrings.uni': b''}
        self.output = Gob(build_gob({'jkl/br_first.jkl': self.converted, **self.metadata}))
        self.archives = {key: Gob(build_gob({})) for key in ('motsres', 'motssnd')}
        self.rule = dict(name='lost_start.cog', referrer='jkl/one.jkl',
                         referrer_sha256=converter.digest(self.original),
                         reason='Synthetic original active startup controller is absent; behavior unknown.')
        self.world = dict(world='jkl/one.jkl', tag='first', source_omissions=[self.rule])
        self.manifest = dict(literal_dependencies_unresolved=[
            dict(source='jkl/br_first.jkl', reference='br_lost_start.cog', reviewed_original_omission=True)])

    def review(self, output=None):
        return converter.component_omissions(self.archives, self.source, self.world,
                                              output or self.output, self.manifest)

    def validate(self, components, omissions):
        resources, _ = converter.resource_union(components)
        result = Gob(build_gob({**resources, **self.metadata}))
        return converter.validate_union(self.archives, result, components, self.metadata,
                                        omissions=omissions)

    def test_retains_two_original_references_and_records_exact_output_bytes(self):
        omissions = self.review()
        self.assertEqual(omissions[0]['reference_count'], 2)
        self.assertEqual(omissions[0]['output_referrer_sha256'], converter.digest(self.converted))
        self.validate([('one', self.output)], omissions)

    def test_original_referrer_hash_mismatch_rejects_review(self):
        self.rule['referrer_sha256'] = '0' * 64
        with self.assertRaisesRegex(AssertionError, 'Original omission referrer hash'):
            self.review()

    def test_reference_occurrence_change_fails_even_when_edge_still_exists(self):
        output = Gob(build_gob({'jkl/br_first.jkl': self.converted + b'2: br_lost_start.cog\n'}))
        with self.assertRaisesRegex(converter.PackError, 'reference count changed'):
            self.review(output)

    def test_comment_reference_does_not_inflate_count(self):
        output = Gob(build_gob({'jkl/br_first.jkl': self.converted + b'# br_lost_start.cog\n'}))
        self.assertEqual(self.review(output)[0]['reference_count'], 2)

    def test_missing_or_forged_manifest_approval_cannot_waive_other_edges(self):
        for report in ([], [dict(self.manifest['literal_dependencies_unresolved'][0],
                                 reviewed_original_omission=False)],
                       [dict(self.manifest['literal_dependencies_unresolved'][0],
                             reviewed_original_omission=1)],
                       self.manifest['literal_dependencies_unresolved'] * 2,
                       [dict(source='jkl/other.jkl', reference='br_lost_start.cog',
                             reviewed_original_omission=True)]):
            with self.subTest(report=report):
                manifest = dict(literal_dependencies_unresolved=report)
                with self.assertRaisesRegex(converter.PackError, 'differ from exact reviewed'):
                    converter.component_omissions(self.archives, self.source, self.world,
                                                   self.output, manifest)

    def test_duplicate_source_review_rejected(self):
        self.world['source_omissions'].append(dict(self.rule))
        with self.assertRaisesRegex(converter.PackError, 'Duplicate reviewed'):
            self.review()

    def test_review_requires_impact_explanation(self):
        self.rule['reason'] = ''
        with self.assertRaisesRegex(converter.PackError, 'source-impact explanation'):
            self.review()

    def test_resolved_original_cannot_be_marked_missing(self):
        self.source = Gob(build_gob({'jkl/one.jkl': self.original, 'cog/lost_start.cog': b'original'}))
        with self.assertRaisesRegex(AssertionError, 'original omission unexpectedly exists'):
            self.review()

    def test_other_component_cannot_fill_the_missing_name(self):
        omissions = self.review()
        for path in ('cog/br_lost_start.cog', 'different/br_lost_start.cog'):
            with self.subTest(path=path):
                other = Gob(build_gob({path: b'made-up replacement'}))
                with self.assertRaisesRegex(converter.PackError, 'union unexpectedly fills'):
                    self.validate([('one', self.output), ('two', other)], omissions)

    def test_native_provider_cannot_fill_the_missing_name(self):
        omissions = self.review()
        self.archives['motsres'] = Gob(build_gob({'cog/br_lost_start.cog': b'native'}))
        with self.assertRaisesRegex(converter.PackError, 'union unexpectedly fills'):
            self.validate([('one', self.output)], omissions)

    def test_review_does_not_waive_same_name_from_another_world(self):
        other = Gob(build_gob({'jkl/other.jkl': b'0: br_lost_start.cog\n'}))
        with self.assertRaises(converter.bridge.RecipeError):
            self.validate([('one', self.output), ('two', other)], self.review())

    def test_unrelated_absent_name_still_fails(self):
        other = Gob(build_gob({'cog/other.cog': b'sound snd=another.wav\n'}))
        with self.assertRaises(converter.bridge.RecipeError):
            self.validate([('one', self.output), ('two', other)], self.review())

    def test_final_referrer_bytes_must_match_reviewed_component(self):
        changed = Gob(build_gob({'jkl/br_first.jkl': self.converted + b'# unrelated edit\n'}))
        with self.assertRaisesRegex(converter.PackError, 'referrer bytes or count differ'):
            self.validate([('one', changed)], self.review())

    def test_final_union_rejects_deleted_omission_referrer(self):
        with self.assertRaisesRegex(converter.PackError, 'referrer missing'):
            self.validate([('empty', Gob(build_gob({})))], self.review())

    def test_identical_shared_omission_remains_valid_in_multiple_components(self):
        omissions = self.review()
        self.validate([('one', self.output), ('two', self.output)], omissions * 2)
        conflict = dict(omissions[0], reason='A different review')
        with self.assertRaisesRegex(converter.PackError, 'Conflicting component omission'):
            self.validate([('one', self.output)], omissions + [conflict])


class PackCatalogAndReadmeTests(unittest.TestCase):
    PRIOR_README_SHA256 = {
        'mp-6000-block': '32059ddd198a3deadb547fe42a3f5c9d0d9d0af353bdb979f51a8135e47cd032',
        'mp-gladiator': 'f73c21f35d2e70353003edbd1ec567c6c68dbb88b7c0dc7d5dd87d70b98d7047',
        'mp-the-matrix': '24bcb3893c4e86df6794316bd7ebf926e93699865434a28dd5472c82b3d88edd',
        'mp-dbz-tdir-tournament': '0e0a0ff1287603a05633801d643120d5d744e20e7ca2963f9a75d2de0baaadf4',
    }

    def synthetic_delivery(self, recipe_id, spec=None):
        payload = build_gob({'episode.jk': b'"Synthetic writer fixture"\nend\n'})
        notice = b'Original synthetic notice\r\nRetain exact bytes.\r\n'
        original = Gob(build_gob({}))
        with tempfile.TemporaryDirectory() as root:
            stage = Path(root) / 'output'
            with patch.object(converter, 'read_original', return_value=(original, {'notice.txt': notice})), \
                    patch.object(converter, 'build_payload', return_value=(payload, {'verification': {'status': 'fixture'}})):
                if spec is None:
                    converter.build_to_directory({}, 'unused-original.zip', stage, recipe_id)
                else:
                    with patch.object(converter, 'recipe_details', return_value=spec):
                        converter.build_to_directory({}, 'unused-original.zip', stage, recipe_id)
            self.assertEqual(next(stage.glob('*.goo')).read_bytes(), payload)
            self.assertEqual((stage / 'ORIGINAL-01-notice.txt').read_bytes(), notice)
            return (stage / 'README.txt').read_bytes()

    def test_prior_four_pack_readmes_retain_exact_text_and_platform_bytes(self):
        for recipe_id, expected in self.PRIOR_README_SHA256.items():
            with self.subTest(recipe_id=recipe_id):
                spec = converter.recipe_details(recipe_id)
                self.assertNotIn('summary', spec)
                self.assertNotIn('source_behavior_caveats', spec)
                text = converter.readme_text(spec)
                self.assertEqual(converter.digest(text.encode('utf-8')), expected)
                self.assertEqual(self.synthetic_delivery(recipe_id),
                                 text.replace('\n', os.linesep).encode('utf-8'))

    def test_optional_summary_replaces_only_that_catalog_description(self):
        rows = {row['id']: row for row in converter.catalog_entries()}
        for recipe_id in self.PRIOR_README_SHA256:
            count = len(converter.recipe_details(recipe_id)['world_specs'])
            self.assertEqual(rows[recipe_id]['summary'],
                             f'Complete reviewed {count}-world pack; original episode order and locally extracted dependencies preserved.')
        spec = converter.recipe_details('mp-mlp3')
        self.assertEqual(rows['mp-mlp3']['summary'], spec['summary'])
        self.assertIn('active startup script', rows['mp-mlp3']['summary'])

    def test_mlp3_is_one_revision_one_prototype_with_all_authored_worlds(self):
        spec = converter.recipe_details('mp-mlp3')
        expected = [
            ('jkl/hoodwink.jkl', 'Stress'), ('jkl/dryheatnc.jkl', 'NorthChaos'),
            ('jkl/wartriangle2.jkl', 'Posse and Naythn of AE'),
            ('jkl/contest.jkl', 'Justin "Juz" Stocks'), ('jkl/warehouse.jkl', 'Home_Sliced'),
            ("jkl/oy'glah'th.jkl", 'Freelancer'), ('jkl/subway.jkl', 'Jepman'),
            ('jkl/castle.jkl', 'bug')]
        self.assertEqual([(row['world'], spec['world_specs'][row['world_spec']]['author'])
                          for row in spec['episode_rows']], expected)
        self.assertEqual([r['line'] for r in spec['episode_rows']], list(range(10, 81, 10)))
        self.assertEqual([r['goto_a'] for r in spec['episode_rows']], [20, 30, 40, 50, 60, 70, 80, 10])
        self.assertTrue(all(r['goto_b'] == -1 for r in spec['episode_rows']))
        self.assertEqual(len(spec['world_specs']), 8)
        self.assertEqual(blackwing_revisions.revision('mp-mlp3'), 1)
        self.assertEqual(spec['catalog_status'], 'prototype')
        self.assertIs(spec['runtime_test']['full_gameplay'], False)
        self.assertEqual([row['id'] for row in converter.catalog_entries() if row['id'].startswith('mp-mlp3')], ['mp-mlp3'])

    def test_mlp3_keeps_exact_source_omissions_without_repairs_or_overrides(self):
        spec = converter.recipe_details('mp-mlp3')
        self.assertEqual(spec['gob_sha256'], '0f2110813ec56f0bc6a6c3816930ae0f4097efacc861d88481af9131a4fefe7b')
        rules = [rule for world in spec['world_specs'].values() for rule in world['source_omissions']]
        self.assertEqual({(r['referrer'], r['name'], r['referrer_sha256']) for r in rules}, {
            ('jkl/hoodwink.jkl', '00electrexplo3.wav', '039bd934c7dd175f5448518f5ed0fa184025aabc758d39c57197c189322ecfc5'),
            ('cog/mpsimplesparks.cog', '00electrexplo3.wav', '5c7aef2e4a356a17f19e180dd3a3de6b567779912e7b99d745ff47b5524cb077'),
            ('jkl/subway.jkl', 'subway_start.cog', '6fa80f14e23532c7a99a3fba96a69eede38f448988b81c0b2d0bcef40e3b5fea')})
        self.assertEqual(len(rules), 3)
        for world in spec['world_specs'].values():
            for field in ('cog_edits', 'native_cog_edits', 'native_template_overrides', 'native_resource_overrides'):
                self.assertFalse(world[field])

    def test_mlp3_delivery_includes_each_declared_caveat_and_summary(self):
        spec = converter.recipe_details('mp-mlp3')
        readme = self.synthetic_delivery('mp-mlp3').decode('utf-8')
        self.assertIn(spec['summary'], readme)
        self.assertEqual(len(spec['source_behavior_caveats']), 4)
        for caveat in spec['source_behavior_caveats']:
            self.assertIn('- ' + caveat, readme)
        for token in ('active subway_start.cog', 'intended startup behavior remains unknown',
                      '00electrexplo3.wav', '00rumbleamb01.wav', '(0,00/0,00/1,00)',
                      'undeclared dummy', 'audible emitter behavior is not established'):
            self.assertIn(token, readme)

    def test_summary_and_caveats_are_independently_optional(self):
        spec = converter.recipe_details('mp-6000-block')
        original = converter.readme_text(spec)
        spec['summary'] = 'Synthetic reviewed summary.'
        self.assertEqual(converter.readme_text(spec), original + '\nSynthetic reviewed summary.\n')
        del spec['summary']
        spec['source_behavior_caveats'] = []
        self.assertEqual(converter.readme_text(spec), original)
        spec['source_behavior_caveats'] = ['Synthetic unresolved source behavior.']
        self.assertTrue(converter.readme_text(spec).startswith(original))
        self.assertIn('- Synthetic unresolved source behavior.', converter.readme_text(spec))

    def test_malformed_delivery_metadata_fails_before_writing(self):
        for field, values in (('summary', ('', 7, None)),
                              ('source_behavior_caveats', ('not a list', [''], [None]))):
            for value in values:
                with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as root:
                    spec = converter.recipe_details('mp-6000-block')
                    spec[field] = value
                    stage = Path(root) / 'output'
                    with patch.object(converter, 'recipe_details', return_value=spec), \
                            patch.object(converter, 'read_original') as read_original:
                        with self.assertRaises(converter.PackError):
                            converter.build_to_directory({}, 'unused-original.zip', stage, 'mp-6000-block')
                    self.assertFalse(stage.exists())
                    read_original.assert_not_called()


if __name__ == '__main__':
    unittest.main()

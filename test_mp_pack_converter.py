"""Synthetic failures for multi-world graph preservation and archive unions."""
import copy
import unittest

from gob import Gob, build_gob
import mp_pack_converter as converter


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


if __name__ == '__main__':
    unittest.main()

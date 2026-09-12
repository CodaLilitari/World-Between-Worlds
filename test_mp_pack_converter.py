"""Synthetic failures for multi-world graph preservation and archive unions."""
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


if __name__ == '__main__':
    unittest.main()

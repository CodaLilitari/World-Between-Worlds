"""Authored synthetic COG fragments; no retail or mod assets are fixtures."""
import hashlib
import unittest
from unittest.mock import patch

import bridge
from gob import Gob, build_gob
import verify_retail


def synthetic_source(players, limits):
    # Deliberately tiny, invented text exercises only the reviewed edit anchors.
    return ('# Synthetic pickup fixture, not a game asset.\n'
            'symbols\nthing player local\nend\ncode\n'
            + 'player = GetSourceRef();\n' * players
            + 'synthetic_value = GetInv(player, 20) * 50;\n' * limits
            + 'synthetic_unchanged = 12345;\nReturn;\nend\n').encode('cp1252')


def synthetic_world(capacity, templates, cogs=(), things=()):
    return ('World cogs ' + str(capacity) + '\n' + '\n'.join(cogs) + '\nend\n'
            'World templates ' + str(len(templates)) + '\n' + '\n'.join(templates) + '\nend\n'
            'World things ' + str(len(things)) + '\n' + '\n'.join(things) + '\nend\n'
            'World scripts 500\n0: unrelated.cog\nend\n')


class ForcePickupTransforms(unittest.TestCase):
    def test_selected_source_surge_names_share_native_behavior_and_visual(self):
        self.assertEqual(bridge.FORCE_PICKUP_BINDINGS, {
            'pow_mana.cog': 'wbw_forceboost.cog',
            'pow_lightside.cog': 'wbw_forcesurge.cog',
            'pow_darkside.cog': 'wbw_forcesurge.cog',
        })
        self.assertEqual(bridge.FORCE_PICKUP_VISUALS['wbw_forceboost.cog']['model'], 'dark.3do')
        self.assertEqual(bridge.FORCE_PICKUP_VISUALS['wbw_forcesurge.cog']['model'], 'mana1.3do')

    def test_edit_uses_active_mp_capacity_and_leaves_unrelated_code_exact(self):
        for output, rule in bridge.FORCE_PICKUP_SOURCES.items():
            with self.subTest(output=output):
                source = synthetic_source(rule['player_assignments'], rule['rank_limits'])
                actual = bridge.adapt_force_pickup(source.decode('cp1252'), rule)
                self.assertIn('synthetic_unchanged = 12345;\nReturn;', actual)
                self.assertEqual(actual.count('call wbw_get_maximum;'), rule['player_assignments'])
                self.assertEqual(actual.count('synthetic_value = wbw_maximum;'), rule['rank_limits'])
                self.assertIn('wbw_maximum = GetInv(player, 20) * 50;\n'
                              '   if(IsMulti())\n'
                              '      wbw_maximum = GetInv(player, 69);', actual)
                self.assertEqual(actual.encode('cp1252'), verify_retail.reconstruct_force_pickup(
                    source, rule['player_assignments'], rule['rank_limits']))

    def test_missing_and_duplicate_edit_anchors_fail_closed(self):
        rule = bridge.FORCE_PICKUP_SOURCES['wbw_forcesurge.cog']
        source = synthetic_source(1, 1).decode('cp1252')
        for anchor in ('symbols\n', 'player = GetSourceRef();', 'GetInv(player, 20) * 50'):
            for altered in (source.replace(anchor, '', 1), anchor + source):
                with self.subTest(anchor=anchor, altered=altered), self.assertRaises(bridge.RecipeError):
                    bridge.adapt_force_pickup(altered, rule)
                with self.assertRaises(AssertionError):
                    verify_retail.reconstruct_force_pickup(altered.encode('cp1252'), 1, 1)

    def test_nonfinal_code_terminator_fails_closed(self):
        source = synthetic_source(1, 1) + b'unreviewed extra code'
        with self.assertRaises(bridge.RecipeError):
            bridge.adapt_force_pickup(source.decode('cp1252'), bridge.FORCE_PICKUP_SOURCES['wbw_forcesurge.cog'])
        with self.assertRaises(AssertionError):
            verify_retail.reconstruct_force_pickup(source, 1, 1)

    def test_unreviewed_owned_source_is_rejected_before_conversion(self):
        archives = {'motsres': Gob(build_gob({'cog/pow_mana.cog': synthetic_source(2, 3)}))}
        with self.assertRaisesRegex(bridge.RecipeError, 'Unreviewed native Force pickup hash'):
            bridge.force_pickup_resources(archives, {'pow_mana.cog'})

    def test_unrelated_selection_reads_no_force_sources(self):
        resources, provenance = bridge.force_pickup_resources({}, {'pow_shield.cog', 'kyle.cog'})
        self.assertEqual(resources, {})
        self.assertEqual(provenance['bindings'], {})
        self.assertEqual(provenance['resources'], [])

    def test_shared_controller_inherits_one_instance_without_changing_other_fields(self):
        rows = ['br__pickup none type=item',
                'br_light br__pickup model3d=br_light.3do cog=wbw_forcesurge.cog respawn=30',
                'br_dark br__pickup model3d=br_dark.3do cog=wbw_forcesurge.cog respawn=30',
                'br_child br_light size=0.05']
        transformed, metadata = bridge.share_force_surge_controller(rows)
        expected = ['br__pickup none type=item',
                    'wbw_surge_base br__pickup cog=wbw_forcesurge.cog',
                    'br_light wbw_surge_base model3d=br_light.3do respawn=30',
                    'br_dark wbw_surge_base model3d=br_dark.3do respawn=30',
                    'br_child br_light size=0.05']
        self.assertEqual(transformed, expected)
        self.assertEqual(metadata, {'name': 'wbw_surge_base', 'parent': 'br__pickup',
                                    'children': ['br_light', 'br_dark']})
        self.assertEqual([row.split() for row in transformed],
                         verify_retail.shared_force_surge_rows([row.split() for row in rows]))
        self.assertEqual(bridge.share_force_surge_controller(['br_other none type=item']),
                         (['br_other none type=item'], None))

    def test_shared_controller_rejects_unreviewed_inheritance_or_ambiguous_cog(self):
        rows = ['br_light br__pickup cog=wbw_forcesurge.cog',
                'br_dark br__pickup cog=wbw_forcesurge.cog']
        for changed in ([rows[0], rows[1].replace('br__pickup', 'different')],
                        ['wbw_surge_base none', *rows],
                        [rows[0] + ' cog=wbw_forcesurge.cog', rows[1]],
                        [rows[0] + ' cog=other.cog', rows[1]]):
            with self.subTest(changed=changed), self.assertRaises(bridge.RecipeError):
                bridge.share_force_surge_controller(changed)


class CogInstanceCapacity(unittest.TestCase):
    def test_original_instance_budget_is_preserved_and_new_allocations_are_added(self):
        native = ['native_a none cog=a.cog', 'native_b none cog=b.cog']
        templates = native + ['wbw_surge_base none cog=wbw_forcesurge.cog',
                              'br_light wbw_surge_base', 'br_dark wbw_surge_base']
        original = synthetic_world(32, [])
        actual = verify_retail.check_cog_instance_capacity(original, synthetic_world(35, templates), native)
        self.assertEqual(actual['source_capacity'], 32)
        self.assertEqual(actual['native_template_instances'], 2)
        self.assertEqual(actual['shared_surge_instances'], 1)
        self.assertEqual(actual['output_capacity'], 35)
        for capacity in (32, 34, 36):
            with self.subTest(capacity=capacity), self.assertRaisesRegex(AssertionError, 'COG instance capacity'):
                verify_retail.check_cog_instance_capacity(original, synthetic_world(capacity, templates), native)

    def test_instance_floor_counts_environment_templates_and_direct_thing_cogs(self):
        native = ['native none cog=native.cog']
        templates = native + ['wbw_surge_base none cog=wbw_forcesurge.cog',
                              'br_light wbw_surge_base', 'br_dark wbw_surge_base',
                              'extra none cog=extra.cog']
        cogs = ['0: first.cog', '1: second.cog']
        things = ['0: br_light cog=placed.cog']
        original = synthetic_world(2, [])
        actual = verify_retail.check_cog_instance_capacity(original, synthetic_world(6, templates, cogs, things), native)
        self.assertEqual(actual['explicit_instance_floor'], 6)
        self.assertEqual(actual['output_capacity'], 6)
        with self.assertRaisesRegex(AssertionError, 'COG instance capacity'):
            verify_retail.check_cog_instance_capacity(original, synthetic_world(4, templates, cogs, things), native)


class IndependentForcePickupVerifier(unittest.TestCase):
    def setUp(self):
        self.source = synthetic_source(1, 1)
        self.sha = hashlib.sha256(self.source).hexdigest()
        self.pin = {'wbw_forcesurge.cog': ('cog/pow_darkside.cog', self.sha, 1, 1)}
        self.archives = {'motsres': Gob(build_gob({'cog/pow_darkside.cog': self.source}))}
        self.valid = verify_retail.reconstruct_force_pickup(self.source, 1, 1)

    def verify(self, members):
        with patch.dict(verify_retail.FORCE_PICKUP_SOURCES, self.pin, clear=True):
            return verify_retail.check_force_pickup_resources(self.archives, Gob(build_gob(members)),
                                                              {'pow_lightside.cog', 'pow_darkside.cog'})

    def test_verifier_does_not_use_producer_helpers_or_binding_table(self):
        with patch.object(bridge, 'adapt_force_pickup', side_effect=AssertionError('producer must not be called')), \
             patch.object(bridge, 'force_pickup_resources', side_effect=AssertionError('producer must not be called')), \
             patch.dict(bridge.FORCE_PICKUP_BINDINGS, {'pow_lightside.cog': 'pow_lightside.cog'}, clear=True):
            self.assertEqual(self.verify({'cog/wbw_forcesurge.cog': self.valid}), {
                'pow_lightside.cog': 'wbw_forcesurge.cog', 'pow_darkside.cog': 'wbw_forcesurge.cog'})

    def test_code_tampering_fails_even_with_valid_rebuilt_archive(self):
        for before, after in ((b'GetInv(player, 69)', b'GetInv(player, 14)'),
                              (b'call wbw_get_maximum;', b'call other_helper;'),
                              (b'synthetic_unchanged = 12345;', b'synthetic_unchanged = 0;')):
            with self.subTest(before=before), self.assertRaisesRegex(AssertionError, 'complete Force pickup source'):
                self.verify({'cog/wbw_forcesurge.cog': self.valid.replace(before, after)})

    def test_missing_or_wrong_directory_pickup_is_rejected(self):
        for members in ({}, {'misplaced/wbw_forcesurge.cog': self.valid}):
            with self.subTest(members=list(members)), self.assertRaisesRegex(AssertionError, 'member set'):
                self.verify(members)

    def test_independent_source_hash_is_checked(self):
        self.archives = {'motsres': Gob(build_gob({'cog/pow_darkside.cog': self.source + b'\n'}))}
        with self.assertRaisesRegex(AssertionError, 'source pin'):
            self.verify({'cog/wbw_forcesurge.cog': self.valid})

    def test_boost_animation_retains_native_material_and_rejects_old_namespace(self):
        source = synthetic_source(2, 3).replace(b'thing player local\n',
                                               b'thing player local\nmaterial twinkle_mat=00twinkle.mat local\n')
        pin = {'wbw_forceboost.cog': ('cog/pow_mana.cog', hashlib.sha256(source).hexdigest(), 2, 3)}
        archives = {'motsres': Gob(build_gob({'cog/pow_mana.cog': source}))}
        expected = verify_retail.reconstruct_force_pickup(source, 2, 3)
        with patch.dict(verify_retail.FORCE_PICKUP_SOURCES, pin, clear=True):
            verify_retail.check_force_pickup_resources(archives,
                Gob(build_gob({'cog/wbw_forceboost.cog': expected})), {'pow_mana.cog'})
            with self.assertRaisesRegex(AssertionError, 'complete Force pickup source'):
                verify_retail.check_force_pickup_resources(archives,
                    Gob(build_gob({'cog/wbw_forceboost.cog': expected.replace(b'00twinkle.mat', b'br_00twinkle.mat')})),
                    {'pow_mana.cog'})
        producer_pin = {'wbw_forceboost.cog': dict(source_path='cog/pow_mana.cog',
            source_sha256=hashlib.sha256(source).hexdigest(), player_assignments=2, rank_limits=3)}
        with patch.dict(bridge.FORCE_PICKUP_SOURCES, producer_pin, clear=True):
            resources, metadata = bridge.force_pickup_resources(archives, {'pow_mana.cog'})
        self.assertEqual(resources['cog/wbw_forceboost.cog'], expected)
        self.assertEqual(metadata['resources'][0]['material_bindings'], {})

    def test_native_visual_override_includes_inheritors_and_changes_only_model_field(self):
        original = ['base none type=item',
                    'boost base cog=wbw_forceboost.cog model3d=br_original.3do respawn=23',
                    'child boost size=0.05',
                    'surge base cog=wbw_forcesurge.cog model3d=br_light.3do thingflags=0x400',
                    'other base model3d=br_other.3do']
        expected = ['base none type=item',
                    'boost base cog=wbw_forceboost.cog model3d=dark.3do respawn=23',
                    'child boost size=0.05 model3d=dark.3do',
                    'surge base cog=wbw_forcesurge.cog model3d=mana1.3do thingflags=0x400',
                    'other base model3d=br_other.3do']
        actual, metadata = bridge.native_force_pickup_visuals(original)
        self.assertEqual(actual, expected)
        self.assertEqual([row['template'] for row in metadata], ['boost', 'child', 'surge'])
        with patch.object(bridge, 'native_force_pickup_visuals', side_effect=AssertionError('producer must not run')):
            self.assertEqual(verify_retail.native_force_pickup_rows([row.split() for row in original]),
                             [row.split() for row in expected])
        for checker in (bridge.native_force_pickup_visuals,
                        lambda rows: verify_retail.native_force_pickup_rows([row.split() for row in rows])):
            with self.assertRaises((bridge.RecipeError, AssertionError)):
                checker(original + ['duplicate boost model3d=a.3do model3d=b.3do'])

    def test_non_force_child_cannot_inherit_changed_force_model(self):
        base = ['base none type=item',
                'boost base cog=wbw_forceboost.cog model3d=br_boost.3do']
        cases = [base + ['health boost cog=pow_health.cog'],
                 base + ['intermediate boost size=0.04', 'health intermediate cog=pow_health.cog'],
                 ['base none type=item', 'surge base cog=wbw_forcesurge.cog',
                  'health surge cog=pow_health.cog']]
        for rows in cases:
            with self.subTest(rows=rows):
                with self.assertRaisesRegex(bridge.RecipeError, 'Non-Force template inherits changed Force model'):
                    bridge.native_force_pickup_visuals(rows)
                with patch.object(bridge, 'native_force_pickup_visuals', side_effect=AssertionError('producer must not run')):
                    with self.assertRaisesRegex(AssertionError, 'Independent non-Force inherited model changed'):
                        verify_retail.native_force_pickup_rows([row.split() for row in rows])
        # An explicit source model on the non-Force child prevents leakage and
        # remains untouched; an already-native parent also requires no rejection.
        for rows in (base + ['health boost cog=pow_health.cog model3d=br_health.3do'],
                     [base[0], base[1].replace('br_boost.3do', 'dark.3do'), 'health boost cog=pow_health.cog']):
            actual, _ = bridge.native_force_pickup_visuals(rows)
            self.assertEqual(actual[-1], rows[-1])
            self.assertEqual([row.split() for row in actual],
                             verify_retail.native_force_pickup_rows([row.split() for row in rows]))

    def test_original_script_indices_keep_both_color_bindings(self):
        source = ['10: pow_lightside.cog', '12: pow_darkside.cog']
        output = ['10: wbw_forcesurge.cog', '12: wbw_forcesurge.cog', '13: another.cog']
        bindings = {'pow_lightside.cog': 'wbw_forcesurge.cog', 'pow_darkside.cog': 'wbw_forcesurge.cog'}
        verify_retail.check_force_pickup_script_indices(source, output, bindings)
        for damaged in (output[1:], [output[0], '12: pow_darkside.cog'], output + [output[0]]):
            with self.subTest(damaged=damaged), self.assertRaises(AssertionError):
                verify_retail.check_force_pickup_script_indices(source, damaged, bindings)

    def test_native_pickup_models_preserve_parent_flags_respawn_and_other_fields(self):
        source = ['_pickup none type=item thingflags=0x400',
                  'light _pickup model3d=light.3do cog=pow_lightside.cog respawn=30',
                  'dark _pickup model3d=dark.3do cog=pow_darkside.cog respawn=30',
                  'anotherlight light size=0.05']
        output = ['br__pickup none type=item thingflags=0x400',
                  'wbw_surge_base br__pickup cog=wbw_forcesurge.cog',
                  'br_light wbw_surge_base model3d=mana1.3do respawn=30',
                  'br_dark wbw_surge_base model3d=mana1.3do respawn=30',
                  'br_anotherlight br_light size=0.05 model3d=mana1.3do']
        bindings = {'pow_lightside.cog': 'wbw_forcesurge.cog', 'pow_darkside.cog': 'wbw_forcesurge.cog'}
        affected = verify_retail.check_force_pickup_templates(source, output, bindings, bindings, {})
        self.assertEqual(affected['light']['model3d'], 'light.3do')
        self.assertEqual(affected['dark']['model3d'], 'dark.3do')
        self.assertEqual(affected['anotherlight']['model3d'], 'light.3do')
        for index, before, after in ((0, '0x400', '0'), (2, 'mana1.3do', 'br_light.3do'),
                                     (3, 'mana1.3do', 'dark.3do'), (4, 'mana1.3do', 'br_light.3do'),
                                     (2, 'wbw_surge_base', 'br__pickup'),
                                     (3, 'respawn=30', 'respawn=0'), (4, '0.05', '0.5')):
            damaged = list(output)
            damaged[index] = damaged[index].replace(before, after)
            with self.subTest(before=before), self.assertRaisesRegex(AssertionError, 'template fields'):
                verify_retail.check_force_pickup_templates(source, damaged, bindings, bindings, {})
        for damaged in ([row for row in output if not row.startswith('wbw_surge_base ')],
                        output + [output[1]], [output[1], output[0], *output[2:]],
                        [output[0], output[1].replace('br__pickup', 'none'), *output[2:]],
                        [*output[:2], output[2] + ' cog=wbw_forcesurge.cog', *output[3:]]):
            with self.subTest(damaged=damaged), self.assertRaises(AssertionError):
                verify_retail.check_force_pickup_templates(source, damaged, bindings, bindings, {})

    def test_shared_controller_rejects_different_parents_duplicate_cogs_and_name_collision(self):
        original = [['br_light', 'br__pickup', 'cog=wbw_forcesurge.cog'],
                    ['br_dark', 'br__pickup', 'cog=wbw_forcesurge.cog']]
        for rows in ([original[0], ['br_dark', 'another_parent', 'cog=wbw_forcesurge.cog']],
                     [['wbw_surge_base', 'none'], *original],
                     [original[0] + ['cog=other.cog'], original[1]]):
            with self.subTest(rows=rows), self.assertRaises(AssertionError):
                verify_retail.shared_force_surge_rows(rows)

    def test_community_full_template_check_requires_shared_instance_layer(self):
        source = ['_pickup none type=item',
                  'light _pickup cog=pow_lightside.cog model3d=light.3do',
                  'dark _pickup cog=pow_darkside.cog model3d=dark.3do']
        native = ['native_pickup none type=item']
        output = [native[0], 'br__pickup none type=item',
                  'wbw_surge_base br__pickup cog=wbw_forcesurge.cog',
                  'br_light wbw_surge_base model3d=mana1.3do',
                  'br_dark wbw_surge_base model3d=mana1.3do']
        names = {'pow_lightside.cog': 'wbw_forcesurge.cog', 'pow_darkside.cog': 'wbw_forcesurge.cog',
                 'light.3do': 'br_light.3do', 'dark.3do': 'br_dark.3do'}
        templates = {'_pickup': 'br__pickup', 'light': 'br_light', 'dark': 'br_dark'}
        verify_retail.check_community_templates(source, native, output, {}, names, templates)
        # The former separate-instance layout must fail even though both roots
        # refer to exactly the same COG filename.
        old_layout = [native[0], output[1],
                      'br_light br__pickup cog=wbw_forcesurge.cog model3d=br_light.3do',
                      'br_dark br__pickup cog=wbw_forcesurge.cog model3d=br_dark.3do']
        with self.assertRaisesRegex(AssertionError, 'template fields, parents and order'):
            verify_retail.check_community_templates(source, native, old_layout, {}, names, templates)


if __name__ == '__main__':
    unittest.main()

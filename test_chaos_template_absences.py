"""Asset-free Chaos omission regression tests; owned inputs are optional.

Set WBW_RETAIL_BASELINES (or BLACKWING_BASELINES) and WBW_CHAOS_ORIGINAL to
explicit local paths to run the original-source controls. The unregistered
candidate metadata comes from docs/top50/candidates/chaos-eternal.json, with
an optional WBW_CHAOS_TEST_SPEC override for private review. Original bytes and
temporary component conversions remain in memory; no full pack is built.
"""
from contextlib import ExitStack
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import unittest
from unittest.mock import patch

import bridge
from gob import Gob, build_gob
import mp_pack_converter
import verify_retail


EXPECTED_DEFAULTS = {'ais_basic_jk.cog': {
    'ais_st2': 'br_ais_st2', '+ais_laser': 'br_+ais_laser'}}
BASELINES = os.environ.get('WBW_RETAIL_BASELINES') or os.environ.get('BLACKWING_BASELINES')
ORIGINAL = os.environ.get('WBW_CHAOS_ORIGINAL')


class _ArchiveView:
    """Test-only changed reads retaining the original outer archive identity.

    This deliberately bypasses the outer GOB hash gate to exercise downstream
    source and provider checks. It is never written or used as a game archive.
    """
    def __init__(self, original, replacements):
        self.original = original
        self.replacements = replacements
        self.entries = {**original.entries, **dict.fromkeys(replacements)}
        self.sha256 = original.sha256
        self.label = 'test-only archive view'

    def read(self, path):
        return self.replacements[path] if path in self.replacements else self.original.read(path)


class ChaosOmissionDispatchTests(unittest.TestCase):
    def test_no_profile_does_not_open_sources_or_relax_other_recipes(self):
        self.assertEqual(bridge.reviewed_template_absences({}, None, {}, ''), {})
        self.assertEqual(verify_retail.check_chaos_template_omissions({}, None, {}, None), {})

    def test_unknown_profile_is_rejected_before_source_access(self):
        spec = {'template_omission_profile': 'unreviewed-template-waiver'}
        with self.assertRaisesRegex(bridge.RecipeError, 'unknown profile'):
            bridge.reviewed_template_absences({}, None, spec, '')
        with self.assertRaisesRegex(AssertionError, 'Unreviewed template omission profile'):
            verify_retail.check_chaos_template_omissions({}, None, spec, None)


@unittest.skipUnless(BASELINES and ORIGINAL,
    'Set explicit owned baselines and original Chaos archive paths')
class ChaosPinnedOriginalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec_path = Path(os.environ.get('WBW_CHAOS_TEST_SPEC',
            Path(__file__).resolve().parent / 'docs/top50/candidates/chaos-eternal.json'))
        cls.pack = json.loads(spec_path.read_text(encoding='utf-8'))
        cls.archives = bridge.pinned_archives(Path(BASELINES))
        cls.original, _ = mp_pack_converter.read_original(
            Path(ORIGINAL), cls.pack)
        cls.outputs = {}
        for key, spec in cls.pack['world_specs'].items():
            payload, _ = bridge.recipe(cls.archives, community=cls.original, community_spec=spec)
            cls.outputs[key] = Gob(payload, 'private in-memory Chaos component')

    def spec(self, key='club'):
        return copy.deepcopy(self.pack['world_specs'][key])

    def producer(self, *, spec=None, original=None, archives=None):
        spec = self.spec() if spec is None else spec
        original = self.original if original is None else original
        return bridge.reviewed_template_absences(
            self.archives if archives is None else archives, original, spec,
            bridge.text(original.read(spec['world'])))

    def verifier(self, *, spec=None, original=None, archives=None, generated=None, key='club'):
        return verify_retail.check_chaos_template_omissions(
            self.archives if archives is None else archives,
            self.original if original is None else original,
            self.spec(key) if spec is None else spec,
            self.outputs[key] if generated is None else generated)

    def output_changed(self, replacements, key='club'):
        output = self.outputs[key]
        files = {path: output.read(path) for path in output.entries}
        files.update(replacements)
        return Gob(build_gob(files))

    def rejected_by_both(self, **kwargs):
        with self.assertRaises(bridge.RecipeError):
            self.producer(**kwargs)
        with self.assertRaises(AssertionError):
            self.verifier(**kwargs)

    def test_all_three_original_worlds_pass_both_independent_contracts(self):
        for key in ('academy', 'club', 'catacombs'):
            with self.subTest(world=key):
                self.assertEqual(self.producer(spec=self.spec(key)), EXPECTED_DEFAULTS)
                self.assertEqual(self.verifier(key=key), EXPECTED_DEFAULTS)

    def test_verifier_succeeds_without_builder_or_builder_omission_helper(self):
        with patch.object(bridge, 'recipe', side_effect=RuntimeError('builder disabled')), \
                patch.object(bridge, 'reviewed_template_absences', side_effect=RuntimeError('producer helper disabled')):
            for key in ('academy', 'club', 'catacombs'):
                with self.subTest(world=key):
                    self.assertEqual(self.verifier(key=key), EXPECTED_DEFAULTS)

    def test_changed_original_archive_cannot_be_approved_by_a_repinned_recipe(self):
        files = {path: self.original.read(path) for path in self.original.entries}
        files['test-only-unreviewed.txt'] = b'Synthetic extra member'
        changed = Gob(build_gob(files))
        spec = self.spec()
        spec['gob_sha256'] = changed.sha256
        self.rejected_by_both(spec=spec, original=changed)

    def test_changed_ai_code_rejected_beyond_the_outer_archive_gate(self):
        path = 'cog/ais_basic_jk.cog'
        source = self.original.read(path)
        for changed in (source + b'\n', source.replace(b'weapon=+ais_laser', b'weapon=+ais_punch', 1)):
            with self.subTest(sha256=hashlib.sha256(changed).hexdigest()):
                self.assertNotEqual(changed, source)
                self.rejected_by_both(original=_ArchiveView(self.original, {path: changed}))

    def test_world_pin_rejects_a_changed_club_range(self):
        spec = self.spec()
        value = bridge.text(self.original.read(spec['world']))
        row = next(row for row in bridge.records(value, 'cogs')
                   if row.split()[:2] == ['48:', 'ais_basic_jk.cog'])
        changed = row.split()
        changed[15] = '1'
        data = value.replace(row, ' '.join(changed), 1).encode('cp1252')
        self.rejected_by_both(original=_ArchiveView(self.original, {spec['world']: data}))

    def test_independent_row_digest_rejects_changed_range_even_after_world_repin(self):
        spec = self.spec()
        value = bridge.text(self.original.read(spec['world']))
        row = next(row for row in bridge.records(value, 'cogs')
                   if row.split()[:2] == ['48:', 'ais_basic_jk.cog'])
        changed = row.split()
        changed[15] = '1'
        data = value.replace(row, ' '.join(changed), 1).encode('cp1252')
        new_hash = hashlib.sha256(data).hexdigest()
        pins = dict(verify_retail.CHAOS_TEMPLATE_WORLDS)
        pins[spec['world']] = (new_hash, *pins[spec['world']][1:])
        spec['sha256'] = new_hash
        with patch.object(verify_retail, 'CHAOS_TEMPLATE_WORLDS', pins), \
                self.assertRaisesRegex(AssertionError, 'complete placed AI rows'):
            self.verifier(spec=spec, original=_ArchiveView(self.original, {spec['world']: data}))

    def test_exact_club_rule_rejects_missing_extra_and_changed_fields(self):
        baseline = self.spec()
        original_rule = baseline['missing_template_arguments'][0]
        variants = [[], [original_rule, original_rule]]
        for key, value in (('row', '49:'), ('symbol', 'aitpl'), ('name', 'ais_st2'),
                           ('reason', ''), ('unexpected_waiver', True)):
            rule = dict(original_rule)
            rule[key] = value
            variants.append([rule])
        for rules in variants:
            with self.subTest(rules=rules):
                spec = self.spec()
                spec['missing_template_arguments'] = rules
                self.rejected_by_both(spec=spec)

    def test_other_worlds_cannot_inherit_clubs_missing_argument_rule(self):
        for key in ('academy', 'catacombs'):
            with self.subTest(world=key):
                spec = self.spec(key)
                spec['missing_template_arguments'] = self.spec()['missing_template_arguments']
                self.rejected_by_both(spec=spec)

    def test_missing_alias_cannot_replace_a_real_template_name(self):
        spec = self.spec()
        for alias in ('br_ais_st2', 'br_+ais_laser'):
            with self.subTest(alias=alias):
                changed = copy.deepcopy(spec)
                changed.setdefault('template_aliases', {})['a_reeyeesbhfist'] = alias
                self.rejected_by_both(spec=changed)

    def test_static_and_native_basis_providers_cannot_fill_original_or_isolated_names(self):
        for owner, path in (('jkres', 'jkl/wbw_test_static.jkl'),
                             ('motsres', 'jkl/wbw_test_static.jkl'), ('motsmp', 'jkl/k1.jkl')):
            for name in ('ais_st2', '+ais_laser', 'br_ais_st2', 'br_+ais_laser'):
                with self.subTest(owner=owner, name=name):
                    data = f'World templates 1\n{name} none\nend\n'.encode('ascii')
                    archives = dict(self.archives)
                    archives[owner] = _ArchiveView(archives[owner], {path: data})
                    self.rejected_by_both(archives=archives)

    def test_every_generated_world_is_checked_for_absent_template_providers(self):
        for name in ('ais_st2', '+ais_laser', 'br_ais_st2', 'br_+ais_laser'):
            with self.subTest(name=name):
                data = f'World templates 1\n{name} none\nend\n'.encode('ascii')
                output = self.output_changed({'jkl/wbw_test_extra_world.jkl': data})
                with self.assertRaisesRegex(AssertionError, 'absence filled by provider'):
                    self.verifier(generated=output)

    def test_changed_generated_ai_rejected_without_builder(self):
        path = 'cog/br_ais_basic_jk.cog'
        original = self.outputs['club'].read(path)
        variants = [original + b'\n', original.replace(b'br_+ais_laser', b'+ais_laser', 1)]
        value = original.decode('cp1252')
        duplicate = re.search(r'^\s*int\s+weapon\s+local[^\n]*$', value, re.M)
        self.assertIsNotNone(duplicate)
        variants.append((value[:duplicate.start()] + value[duplicate.end():]).encode('cp1252'))
        with ExitStack() as stack:
            stack.enter_context(patch.object(bridge, 'recipe', side_effect=RuntimeError('builder disabled')))
            stack.enter_context(patch.object(bridge, 'reviewed_template_absences', side_effect=RuntimeError('producer helper disabled')))
            for changed in variants:
                with self.subTest(sha256=hashlib.sha256(changed).hexdigest()):
                    self.assertNotEqual(changed, original)
                    with self.assertRaisesRegex(AssertionError, 'complete Chaos AI reconstruction'):
                        self.verifier(generated=self.output_changed({path: changed}))

    def test_changed_generated_club_placement_is_not_hidden_by_preserved_source(self):
        path = 'jkl/br_' + self.spec()['tag'] + '.jkl'
        original = self.outputs['club'].read(path).decode('cp1252')
        row = next(row for row in bridge.records(original, 'cogs')
                   if row.split()[:2] == ['48:', 'br_ais_basic_jk.cog'])
        for index, value in ((15, '1'), (40, '-1'), (28, 'walkplayer')):
            with self.subTest(index=index):
                changed = row.split()
                changed[index] = value
                output = self.output_changed({path: original.replace(row, ' '.join(changed), 1).encode('cp1252')})
                with self.assertRaisesRegex(AssertionError, 'complete Chaos placed AI reconstruction'):
                    self.verifier(generated=output)


if __name__ == '__main__':
    unittest.main()

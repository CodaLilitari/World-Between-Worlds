"""Portable policy tests using synthetic metadata/text, without game assets.

These test the waiver boundary, not source-archive authenticity or gameplay.
The CLI separately validates the actual ZIP/GOB bytes and records owned assets.
"""
import copy
from types import SimpleNamespace
import unittest

from caesars_audit import (CAESARS_GOB_SHA256, JK_HASHES, EXPECTED_REFERRERS,
                          legacy_omission_waiver, waived_output_reference,
                          literal_references)
from bridge import RecipeError, rewrite_cog_template_arguments, adapt_caesars_start
from gob import ArchiveError


class CaesarOmissionPolicy(unittest.TestCase):
    def setUp(self):
        self.source = SimpleNamespace(sha256=CAESARS_GOB_SHA256)
        self.archives = {key: SimpleNamespace(sha256=value) for key, value in JK_HASHES.items()}
        self.missing = copy.deepcopy(EXPECTED_REFERRERS)

    def waiver(self):
        return legacy_omission_waiver(self.source, self.archives, self.missing)

    def test_exact_set_records_absence_without_replacements(self):
        value = self.waiver()
        self.assertEqual(len(value['name_map']), 11)
        self.assertEqual(value['substitute_assets'], [])
        self.assertEqual(value['omitted_original_behavior'], [])

    def test_unreviewed_source_rejected(self):
        self.source.sha256 = '0' * 64
        with self.assertRaises(ValueError):
            self.waiver()

    def test_unreviewed_jk_archive_rejected(self):
        self.archives['jkres'].sha256 = '0' * 64
        with self.assertRaises(ValueError):
            self.waiver()

    def test_missing_jk_archive_rejected(self):
        del self.archives['jksnd']
        with self.assertRaises(ValueError):
            self.waiver()

    def test_new_missing_file_rejected(self):
        self.missing['newmissing.mat'] = ['jkl/caesars.jkl']
        with self.assertRaises(ValueError):
            self.waiver()

    def test_removed_omission_rejected(self):
        del self.missing['trap.wav']
        with self.assertRaises(ValueError):
            self.waiver()

    def test_new_referrer_rejected(self):
        self.missing['none.wav'].append('cog/new.cog')
        with self.assertRaises(ValueError):
            self.waiver()

    def test_missing_referrer_rejected(self):
        self.missing['trap.wav'].remove('cog/seqcharge.cog')
        with self.assertRaises(ValueError):
            self.waiver()

    def test_existing_bridge_report_shape_accepted(self):
        shaped = {name: {'referrers': refs, 'owned_mots_candidate': True}
                  for name, refs in self.missing.items()}
        actual = legacy_omission_waiver(self.source, self.archives, shaped)
        self.assertEqual(actual, self.waiver())

    def test_exact_transformed_referrer_accepted(self):
        self.assertTrue(waived_output_reference('br_trap.wav', 'cog/br_seqcharge.cog', self.waiver()))
        self.assertTrue(waived_output_reference('br_window2.mat', 'jkl/br_caesars.jkl', self.waiver()))

    def test_unreviewed_transformed_referrer_rejected(self):
        self.assertFalse(waived_output_reference('br_trap.wav', 'cog/br_textvoice.cog', self.waiver()))

    def test_unreviewed_output_filename_rejected(self):
        self.assertFalse(waived_output_reference('br_unlisted.wav', 'jkl/br_caesars.jkl', self.waiver()))

    def test_unprefixed_name_rejected(self):
        self.assertFalse(waived_output_reference('trap.wav', 'cog/br_seqcharge.cog', self.waiver()))

    def test_unsafe_output_referrer_rejected(self):
        with self.assertRaises(ArchiveError):
            waived_output_reference('br_trap.wav', 'cog/../br_seqcharge.cog', self.waiver())

    def test_reserved_names_obey_legacy_length_and_are_unique(self):
        names = self.waiver()['intentionally_absent_names']
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all(len(name.encode('cp1252')) <= 31 for name in names))

    def test_header_comments_are_not_dependencies(self):
        synthetic = b'# OLD_NAME.COG\n// older.wav\nsound cue=real.wav local\n'
        self.assertEqual(literal_references(synthetic), {'real.wav'})

    def test_absent_script_arguments_are_preserved(self):
        synthetic = 'World cogs 1\n0: absent.cog -1 (0/0/0) 0.5\nend\n'
        value = rewrite_cog_template_arguments(synthetic, SimpleNamespace(by_name={}), {}, missing_cogs={'absent.cog'})
        self.assertIn('0: absent.cog -1 (0/0/0) 0.5', value)

    def test_listed_absent_script_must_not_resolve(self):
        synthetic = 'World cogs 1\n0: absent.cog -1\nend\n'
        with self.assertRaisesRegex(RecipeError, 'unexpectedly resolved'):
            rewrite_cog_template_arguments(synthetic, SimpleNamespace(by_name={'absent.cog': object()}), {}, missing_cogs={'absent.cog'})

    def test_caesar_saber_remap_preserves_other_operations(self):
        synthetic = ('SetInv(player, 1, 1);\nSetInv(player, 2, 1);\n'
                     'SetInv(player, 10, 1);\nSetInv(player, 11, 100);\n'
                     'SetInv(player, 99, 1000);\nSetInv(player, 20, 7);\n'
                     'SetCurInvWeapon(player, 0);\n'
                     'SelectWeapon(player, AutoSelectWeapon(player, 1));\n')
        expected = synthetic.replace('SetInv(player, 10, 1);', 'SetInv(player, 131, 1);')
        self.assertEqual(adapt_caesars_start(synthetic), expected)

    def test_caesar_saber_remap_rejects_missing_call(self):
        with self.assertRaises(RecipeError):
            adapt_caesars_start('SetInv(player, 11, 100);\n')

    def test_caesar_saber_remap_rejects_duplicate_call(self):
        with self.assertRaises(RecipeError):
            adapt_caesars_start('SetInv(player, 10, 1);\nSetInv(player, 10, 1);\n')


if __name__ == '__main__':
    unittest.main()

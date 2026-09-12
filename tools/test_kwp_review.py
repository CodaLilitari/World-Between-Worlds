import unittest
from tools.kwp_review import apply, weapon_edits


class WeaponReviewTests(unittest.TestCase):
    def test_descriptors_do_not_rewrite_network_ordinals_or_arbitrary_numbers(self):
        source = 'GetInv(player, 5); SetCurWeapon(player, 10); damage=5;\nID=GetCurWeapon(player)*10;'
        result = apply(source, weapon_edits(source))
        self.assertEqual(result, 'GetInv(player, 135); SetCurWeapon(player, 131); damage=5;\nID=GetCurWeapon(player)*10;')

    def test_saber_predicate_and_autoselect_are_distinct_ordinal_uses(self):
        source = 'SelectWeapon(player, 1); if(GetCurWeapon(player) == 10) foo=1; SelectWeapon(player, AutoSelectWeapon(player, 1));'
        result = apply(source, weapon_edits(source))
        self.assertEqual(result, 'SelectWeapon(player, 121); if(GetWeaponBin(GetCurWeapon(player)) == 131) foo=1; SelectWeapon(player, GetWeaponBin(AutoSelectWeapon(player, 1)));')

    def test_ammo_and_other_native_inventory_are_unchanged(self):
        source = 'ChangeInv(player, 12, -5); SetInv(player, 60, 200); GetInv(player, 121);'
        self.assertEqual(apply(source, weapon_edits(source)), source)

    def test_count_mismatch_fails(self):
        edits = weapon_edits('GetInv(player, 5); GetInv(player, 5);')
        with self.assertRaises(ValueError):
            apply('GetInv(player, 5);', edits)

    def test_exact_numeric_boundary_preserves_fractional_inputs(self):
        source = 'GetInv(player, 5); GetInv(player, 5.0); GetInv(player, 50); GetInv(player, 1); GetInv(player, 12);'
        result = apply(source, weapon_edits(source))
        self.assertEqual(result, 'GetInv(player, 135); GetInv(player, 5.0); GetInv(player, 50); GetInv(player, 121); GetInv(player, 12);')


if __name__ == '__main__':
    unittest.main()

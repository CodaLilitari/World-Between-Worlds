"""Synthetic Ninja Kage loader, inventory, UI and preload regression gates.

These fixtures contain no original game or mod assets. Optional integration
tests read owned originals only when both BLACKWING_NINJA_ORIGINAL and
BLACKWING_BASELINES are supplied by the caller.
"""
from io import BytesIO
import hashlib
import os
from pathlib import Path
import re
import stat
import struct
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

import bridge
from gob import ArchiveError, Gob, build_gob
import ninja_catalog
import ninja_converter as ninja


def sha(data):
    return hashlib.sha256(data).hexdigest()


def zip_bytes(members, compression=zipfile.ZIP_STORED):
    buffer = BytesIO()
    with warnings.catch_warnings(), zipfile.ZipFile(buffer, 'w', compression=compression) as archive:
        warnings.simplefilter('ignore', UserWarning)  # Deliberate duplicate-member fixture.
        for name, payload in members:
            archive.writestr(name, payload)
    return buffer.getvalue()


def renamed_gob_directory(data, old, new):
    result = bytearray(data)
    table = struct.unpack_from('<I', result, 8)[0]
    count = struct.unpack_from('<I', result, table)[0]
    matches = 0
    for index in range(count):
        start = table + 4 + index * 136 + 8
        name = bytes(result[start:start + 128]).split(b'\0', 1)[0]
        if name.replace(b'\\', b'/') == old.replace(b'\\', b'/'):
            result[start:start + 128] = new.ljust(128, b'\0')
            matches += 1
    if matches != 1:
        raise AssertionError('Synthetic GOB member was not unique')
    return bytes(result)


class OriginalArchiveTests(unittest.TestCase):
    def setUp(self):
        self.payloads = {'patchinfo.txt': b'Synthetic patch metadata\n',
                         'cog/fixture.cog': b'symbols\nend\ncode\nreturn;\nend\n'}
        self.canonical = build_gob(self.payloads)
        self.legacy = renamed_gob_directory(self.canonical, b'patchinfo.txt', b'\\patchinfo.txt')
        self.readme = b'Synthetic original attribution\n'
        self.package = zip_bytes([('Fixture.gob', self.legacy), ('Fixture.txt', self.readme)])
        self.spec = {'gob_sha256': sha(self.legacy), 'zip_sha256': sha(self.package),
                     'gob_member': 'Fixture.gob', 'readme_member': 'Fixture.txt',
                     'readme_sha256': sha(self.readme), 'original_member_count': 2,
                     'cog_sha256': {'cog/fixture.cog': sha(self.payloads['cog/fixture.cog'])}}

    def load(self, data, *, pin_package=False, changes=None):
        spec = dict(self.spec)
        if pin_package:
            spec['zip_sha256'] = sha(data)
        spec.update(changes or {})
        with tempfile.TemporaryDirectory() as directory, patch.dict(ninja_catalog.SPEC, spec):
            path = Path(directory) / 'original.bin'
            path.write_bytes(data)
            return ninja.open_original(path)

    def test_zip_and_gob_preserve_every_payload_under_exact_legacy_normalization(self):
        for data, expected_readme in ((self.package, self.readme), (self.legacy, None)):
            with self.subTest(kind='ZIP' if expected_readme else 'GOB'):
                original = self.load(data)
                self.assertEqual(original.archive.data, self.canonical)
                self.assertEqual(original.source_sha256, sha(data))
                self.assertEqual(original.readme, expected_readme)
                self.assertEqual({p: original.archive.read(p) for p in original.archive.entries}, self.payloads)

    def test_normalization_is_not_available_to_an_unpinned_gob(self):
        with self.assertRaisesRegex(ninja.NinjaError, 'Unsupported Ninja Kage archive'):
            self.load(self.legacy + b'drift')
        with patch.dict(ninja_catalog.SPEC, self.spec):
            with self.assertRaisesRegex(ninja.NinjaError, 'GOB SHA256'):
                ninja._normalize_pinned_gob(self.canonical)

    def test_pinned_gob_must_contain_exactly_one_reviewed_legacy_path(self):
        with self.assertRaisesRegex(ninja.NinjaError, 'normalization did not match once'):
            self.load(self.canonical, changes={'gob_sha256': sha(self.canonical)})
        duplicate = renamed_gob_directory(self.legacy, b'cog/fixture.cog', b'\\patchinfo.txt')
        with self.assertRaisesRegex(ninja.NinjaError, 'normalization did not match once'):
            self.load(duplicate, changes={'gob_sha256': sha(duplicate)})

    def test_normalization_does_not_relax_other_gob_paths_or_payload_pins(self):
        unsafe = renamed_gob_directory(self.legacy, b'cog/fixture.cog', b'../fixture.cog')
        with self.assertRaises(ArchiveError):
            self.load(unsafe, changes={'gob_sha256': sha(unsafe)})
        with self.assertRaisesRegex(ninja.NinjaError, 'COG content pin'):
            self.load(self.legacy, changes={'cog_sha256': {'cog/fixture.cog': '0' * 64}})
        with self.assertRaisesRegex(ninja.NinjaError, 'member count'):
            self.load(self.legacy, changes={'original_member_count': 3})

    def test_unknown_zip_bytes_and_wrong_embedded_gob_are_rejected(self):
        with self.assertRaisesRegex(ninja.NinjaError, 'Unsupported Ninja Kage archive'):
            self.load(self.package + b'drift')
        package = zip_bytes([('Fixture.gob', self.canonical), ('Fixture.txt', self.readme)])
        with self.assertRaisesRegex(ninja.NinjaError, 'GOB SHA256'):
            self.load(package, pin_package=True)

    def test_unsafe_zip_paths_are_rejected_even_with_matching_outer_digest(self):
        for name in ('../Fixture.gob', '/Fixture.gob', 'C:/Fixture.gob', 'dir/CON.gob', 'dir/trailing. '):
            with self.subTest(name=name):
                package = zip_bytes([(name, self.legacy), ('Fixture.txt', self.readme)])
                with self.assertRaises((ArchiveError, ninja.NinjaError)):
                    self.load(package, pin_package=True)

    def test_zip_rejects_duplicate_unexpected_and_directory_members(self):
        for members in (
            [('Fixture.gob', self.legacy), ('FIXTURE.GOB', self.legacy)],
            [('Fixture.gob', self.legacy), ('other.txt', self.readme)],
            [('Fixture.gob', self.legacy), ('Fixture.txt', self.readme), ('extra.txt', b'extra')],
            [('Fixture.gob', self.legacy), ('Fixture.txt/', b'')],
        ):
            with self.subTest(names=[name for name, _ in members]):
                with self.assertRaises((ArchiveError, ninja.NinjaError)):
                    self.load(zip_bytes(members), pin_package=True)

    def test_zip_crc_covers_non_gob_readme(self):
        damaged = bytearray(self.package)
        with zipfile.ZipFile(BytesIO(self.package)) as archive:
            info = archive.getinfo('Fixture.txt')
            name_len, extra_len = struct.unpack_from('<HH', damaged, info.header_offset + 26)
            damaged[info.header_offset + 30 + name_len + extra_len] ^= 1
        with self.assertRaisesRegex(ninja.NinjaError, 'CRC'):
            self.load(bytes(damaged), pin_package=True)

    def test_zip_readme_provenance_pin_is_independent_of_crc(self):
        package = zip_bytes([('Fixture.gob', self.legacy), ('Fixture.txt', b'Wrong attribution')])
        with self.assertRaisesRegex(ninja.NinjaError, 'README SHA256'):
            self.load(package, pin_package=True)

    def test_zip_symlink_and_encrypted_member_metadata_are_rejected(self):
        symlink = zipfile.ZipInfo('Fixture.txt')
        symlink.create_system = 3
        symlink.external_attr = (stat.S_IFLNK | 0o777) << 16
        package = zip_bytes([('Fixture.gob', self.legacy), (symlink, self.readme)])
        with self.assertRaisesRegex(ninja.NinjaError, 'Unsupported original ZIP member'):
            self.load(package, pin_package=True)
        encrypted = bytearray(self.package)
        central = encrypted.index(b'PK\x01\x02')
        flags = struct.unpack_from('<H', encrypted, central + 8)[0]
        struct.pack_into('<H', encrypted, central + 8, flags | 1)
        with self.assertRaisesRegex(ninja.NinjaError, 'Unsupported original ZIP member'):
            self.load(bytes(encrypted), pin_package=True)

    def test_member_expansion_limit_and_outer_file_limit_are_independent(self):
        package = zip_bytes([('Fixture.gob', self.legacy), ('Fixture.txt', b'0' * 10_000_001)],
                            compression=zipfile.ZIP_DEFLATED)
        self.assertLess(len(package), 100_000)
        with self.assertRaisesRegex(ninja.NinjaError, 'Unsupported original ZIP member'):
            self.load(package, pin_package=True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'too-large.bin'
            with path.open('wb') as handle:
                handle.seek(10_000_000)
                handle.write(b'0')
            with self.assertRaisesRegex(ninja.NinjaError, 'bounded Ninja Kage archive size'):
                ninja.open_original(path)


class ExactSourceEditTests(unittest.TestCase):
    def test_maxmana_anchor_rejects_missing_or_duplicate_startup(self):
        edits = ninja_catalog.ORIGINAL_COG_EDITS['force_well.cog']
        anchor = 'startup:\n   player = GetLocalPlayerThing();\n'
        added = '   SetInv(player, 69, GetInv(player, 20) * 50);\n'
        # Synthetic surrounding handlers are intentionally different from retail.
        source = 'code\n' + anchor + '   Return;\npulse:\n   Print("synthetic");\n   Return;\nend\n'
        converted = ninja.apply_edits(source, edits)
        self.assertEqual(converted.replace(added, '', 1), source)
        for changed in (source.replace(anchor, 'startup:\n'), source + anchor):
            with self.subTest(changed=changed), self.assertRaises(ninja.NinjaError):
                ninja.apply_edits(changed, edits)

    def test_surgical_inventory_edit_preserves_ammo_timer_and_comments(self):
        source = '# Preserve provenance\nSetInv(player, 10, 1);\nSetInv(player, 11, 75);\nSetTimer(10);\n'
        edits = [{'old': 'SetInv(player, 10, 1);', 'new': 'SetInv(player, 131, 1);',
                  'count': 1, 'reason': 'Only this reviewed sword grant changes'}]
        self.assertEqual(ninja.apply_edits(source, edits),
                         '# Preserve provenance\nSetInv(player, 131, 1);\nSetInv(player, 11, 75);\nSetTimer(10);\n')

    def test_edit_rejects_missing_repeated_or_unexplained_anchor(self):
        edit = {'old': 'old();', 'new': 'new();', 'count': 1, 'reason': 'Reviewed source anchor'}
        for source, changes in [('different();', {}), ('old();old();', {}), ('old();', {'old': ''}),
                                ('old();', {'reason': ''}), ('old();', {'count': -1})]:
            with self.subTest(source=source, changes=changes):
                with self.assertRaisesRegex(ninja.NinjaError, 'source edit count'):
                    ninja.apply_edits(source, [{**edit, **changes}])

    def test_edits_run_sequentially_and_independent_reconstruction_matches(self):
        edits = [{'old': 'alpha', 'new': 'beta', 'count': 1, 'reason': 'First step'},
                 {'old': 'beta!', 'new': 'gamma!', 'count': 1, 'reason': 'Dependent second step'}]
        self.assertEqual(ninja.apply_edits('alpha!', edits), 'gamma!')
        self.assertEqual(ninja._independent_edits(b'alpha!\r\n', edits), 'gamma!\n')


def synthetic_item_tables():
    native_actions = [n for n in range(21, 40) if n not in (30, 32)] + [40, 41, 42]
    original_actions = list(range(21, 35)) + [40, 41, 42, 116, 117, 118]
    native = ['# Synthetic native inventory']
    for number in range(120, 141):
        script = 'weap_concrifle_m.cog' if number == 129 else f'native_weapon_{number}.cog'
        native.append(f'native_weapon_{number} {number} 0 {30 if number == 124 else 1} 0x0a4 cog={script}')
    for number in native_actions:
        script = {27: 'force_blinding.cog', 38: 'force_push.cog'}.get(number, f'native_action_{number}.cog')
        native.append(f'native_action_{number} {number} 0 4 0x108 cog={script}')
    native += ['ammo 11 0 500 0x080', 'end']
    original = ['kunai 4 0 200 0x0a4 cog=weap_thermdet.cog']
    for number in original_actions:
        script = {30: 'force_throw.cog', 32: 'force_lightning.cog',
                  116: 'item_hook.cog', 117: 'jattack.cog', 118: 'kick.cog'}.get(number, f'original_action_{number}.cog')
        original.append(f'original_action_{number} {number} 0 4 0x108 cog={script}')
    original += ['client 119 1 1 0x000 cog=client_weapons.cog', 'end']
    return '\n'.join(native) + '\n', '\n'.join(original) + '\n'


class InventoryMergeTests(unittest.TestCase):
    def setUp(self):
        self.native, self.original = synthetic_item_tables()

    def test_authored_loadout_capacity_and_extra_powers_preserve_native_weapon_semantics(self):
        result = ninja.items(ninja.build_items(self.native, self.original))
        before = ninja.items(self.native)
        self.assertEqual(set(result), set(before) | {30, 32, 116, 117, 118, 119})
        self.assertEqual(result[124]['max'], 200)
        self.assertEqual(result[27]['extra'], 'cog=nk_force_push.cog')
        for number in set(before) - {27, 124}:
            self.assertEqual(result[number], before[number], f'Native bin {number} changed')
        self.assertEqual(result[129]['extra'], 'cog=weap_concrifle_m.cog')
        self.assertEqual(result[38]['extra'], 'cog=force_push.cog')
        self.assertEqual(ninja.action_bins(ninja.build_items(self.native, self.original)),
                         list(range(21, 40)) + [40, 41, 42, 116, 117, 118])

    def test_all_six_authored_additions_reject_existing_native_bin_collision(self):
        for number in (30, 32, 116, 117, 118, 119):
            with self.subTest(number=number), self.assertRaisesRegex(ninja.NinjaError, 'bin collision'):
                ninja.build_items(self.native.replace('end', f'collision {number} 0 1 0x000\nend'), self.original)

    def test_source_capacity_and_native_push_anchor_must_match(self):
        variants = [(self.native.replace(' 124 0 30 ', ' 124 0 31 '), self.original),
                    (self.native, self.original.replace('kunai 4 0 200 ', 'kunai 4 0 201 ')),
                    (self.native.replace('cog=force_blinding.cog', 'cog=different.cog'), self.original)]
        for native, original in variants:
            with self.subTest(native=native[:25], original=original[:25]), self.assertRaises(ninja.NinjaError):
                ninja.build_items(native, original)

    def test_duplicate_bins_and_oversubscribed_hotkeys_are_rejected(self):
        with self.assertRaisesRegex(ninja.NinjaError, 'Duplicate inventory bin'):
            ninja.items(self.native.replace('end', 'duplicate 129 0 1 0x004\nend'))
        extras = '\n'.join(f'extra_{n} {n} 0 1 0x100' for n in range(160, 168))
        with self.assertRaisesRegex(ninja.NinjaError, 'hotkey action capacity'):
            ninja.build_items(self.native.replace('end', extras + '\nend'), self.original)


def uni(pairs):
    return f'MSGS {len(pairs)}\n' + ''.join(f'"{key}" {flag} "{value}"\n' for key, flag, value in pairs) + 'END\n'


class SourceDeltaUiTests(unittest.TestCase):
    def test_literal_backslash_uses_native_quote_delimiters_and_counts_final_row(self):
        native = uni([('DIK_BACKSLASH', 0, '\\'), ('LAST', 0, 'Final native entry')])
        result = ninja._write_uni(native, {'ADDED': (0, 'Added')})
        self.assertEqual(ninja.uni_rows(result)['DIK_BACKSLASH'], (0, '\\'))
        self.assertEqual(ninja.uni_rows(result)['LAST'], (0, 'Final native entry'))
        self.assertEqual(int(re.search(r'^MSGS (\d+)', result).group(1)), 3)

    def test_unchanged_jk_text_keeps_native_text_and_authored_delta_wins(self):
        native = uni([('KEEP', 0, 'Native wording'), ('CHANGE', 1, 'Native action'), ('NATIVE_ONLY', 0, 'Retained')])
        jk = uni([('KEEP', 0, 'Old JK wording'), ('CHANGE', 1, 'Old action')])
        authored = uni([('KEEP', 0, 'Old JK wording'), ('CHANGE', 1, 'Authored action'), ('NEW', 0, 'New control')])
        result = ninja.uni_rows(ninja.merge_uni(native, jk, authored))
        self.assertEqual(result, {'KEEP': (0, 'Native wording'), 'CHANGE': (1, 'Authored action'),
                                  'NATIVE_ONLY': (0, 'Retained'), 'NEW': (0, 'New control')})

    def test_duplicate_native_keys_keep_first_value_and_physical_row_count(self):
        native = uni([('DUP', 0, 'First native'), ('DUP', 1, 'Second native'), ('OTHER', 0, 'Retained')])
        result = ninja.merge_uni(native, uni([('DUP', 0, 'Old')]), uni([('DUP', 0, 'Authored')]))
        self.assertEqual(ninja.uni_rows(result)['DUP'], (0, 'Authored'))
        self.assertIn('"DUP" 1 "Second native"', result)
        self.assertEqual(len(re.findall(r'^"DUP"|^\s+"DUP"', result, re.M)), 2)
        self.assertEqual(int(re.search(r'^MSGS (\d+)', result).group(1)), 3)
        self.assertEqual(ninja.uni_rows(native)['DUP'], (0, 'First native'))

    def test_hotkeys_follow_actual_25_bin_order_without_erasing_native_additional_powers(self):
        native_items, original_items = synthetic_item_tables()
        output_items = ninja.build_items(native_items, original_items)
        native_actions = ninja.action_bins(native_items)
        original_actions = ninja.action_bins(original_items)
        native = uni([(f'ACTIVATE{i}', 0, f'Native bin {number}') for i, number in enumerate(native_actions)] +
                     [('COG_00131', 0, 'Native sword'), ('NATIVE_ONLY', 0, 'Native content')])
        jk = uni([(f'ACTIVATE{i}', 0, f'JK bin {number}') for i, number in enumerate(original_actions)] +
                 [('COG_00010', 0, 'Old sword')])
        authored = uni([(f'ACTIVATE{i}', 0, f'Authored bin {number}') for i, number in enumerate(original_actions)] +
                       [('COG_00010', 0, 'Authored sword')])
        result = ninja.uni_rows(ninja.merge_uni(native, jk, authored, native_items, original_items, output_items))
        for index, number in enumerate(ninja.action_bins(output_items)):
            owner = 'Authored' if number in original_actions else 'Native'
            self.assertEqual(result[f'ACTIVATE{index}'], (0, f'{owner} bin {number}'))
        self.assertEqual(len([key for key in result if re.fullmatch(r'ACTIVATE\d+', key)]), 25)
        self.assertEqual(result['COG_00131'], (0, 'Authored sword'))
        self.assertEqual(result['NATIVE_ONLY'], (0, 'Native content'))

    def test_uni_terminator_and_count_header_must_be_unambiguous(self):
        valid = uni([('A', 0, 'A')])
        for value in (valid.replace('END', ''), valid + 'END\n', valid.replace('MSGS 1', 'wrong 1')):
            with self.subTest(value=value), self.assertRaises(ninja.NinjaError):
                ninja._write_uni(value, {'B': (0, 'B')})


def static_fixture():
    return ('Section: sounds\nWorld sounds 1\nbase.wav\nend\n'
            'Section: materials\nWorld materials 1\n0: base.mat 1.0 1.0\nend\n'
            'Section: soundclass\nWorld soundclasses 1\n0: base.snd\nend\n'
            'Section: models\nWorld models 1\n0: base.3do\nend\n'
            'Section: sprites\nWorld sprites 1\n0: base.spr\nend\n'
            'Section: keyframes\nWorld keyframes 1\n0: base.key\nend\n'
            'Section: animclass\nWorld puppets 1\n0: base.pup\nend\n'
            'Section: cogscripts\nWorld scripts 1\nend\n'
            'Section: cogs\nWorld cogs 1\nend\n'
            'Section: templates\nWorld templates 1\nbase none type=weapon cog=shared.cog\nend\n')


class StaticPreloadTests(unittest.TestCase):
    def test_full_preloads_preserve_native_first_rows_and_use_each_parser_format(self):
        files = {f'resources/{name}{extension}': b'' for name in ('base', 'extra')
                 for extension in ('.wav', '.mat', '.snd', '.3do', '.spr', '.key', '.pup')}
        files['cog/shared.cog'] = b''
        files['misc/items.dat'] = b'tool 116 1 1 0x120 cog=shared.cog\nend\n'
        value = ninja._preload_static(ninja._grow_capacities(static_fixture(), files), files)
        self.assertEqual(bridge.records(value, 'sounds'), ['base.wav', 'extra.wav'])
        self.assertEqual(bridge.records(value, 'materials'), ['0: base.mat 1.0 1.0', '1: extra.mat 1.0 1.0'])
        for label, extension in [('soundclasses', '.snd'), ('models', '.3do'), ('sprites', '.spr'),
                                 ('keyframes', '.key'), ('puppets', '.pup')]:
            self.assertEqual(bridge.records(value, label), [f'0: base{extension}', f'1: extra{extension}'])
        self.assertEqual(bridge.records(value, 'scripts'), ['0: shared.cog'])
        self.assertEqual(bridge.records(value, 'cogs'), [])
        self.assertEqual(bridge.records(value, 'templates'), ['base none type=weapon cog=shared.cog'])

    def test_instance_capacity_counts_descriptors_separately_from_unique_scripts(self):
        inventory = ''.join(f'item_{n} {n} 0 1 0x000 cog=shared.cog\n' for n in range(67)) + 'end\n'
        files = {'cog/shared.cog': b'', 'misc/items.dat': inventory.encode()}
        value = ninja._preload_static(ninja._grow_capacities(static_fixture(), files), files)
        self.assertEqual(int(bridge.block(value, 'scripts').group(2)), 1)
        self.assertEqual(int(bridge.block(value, 'cogs').group(2)), 68)
        self.assertEqual(bridge.records(value, 'cogs'), [])

    def test_ai_pool_is_inserted_before_templates_and_after_other_allocated_pools(self):
        files = {'misc/ai/test.ai': b'', 'misc/items.dat': b'tool 116 0 1 0x000\nend\n'}
        value = ninja._preload_static(ninja._grow_capacities(static_fixture(), files), files)
        self.assertLess(value.index('Section: cogs\n'), value.index('Section: aiclass\n'))
        self.assertLess(value.index('Section: aiclass\n'), value.index('Section: templates\n'))
        self.assertEqual(bridge.records(value, 'aiclasses'), ['0: test.ai'])


class ModelAndStageBoundaryTests(unittest.TestCase):
    def test_model_personality_added_without_changing_authored_model_sound_or_comments(self):
        original = 'World models 29\n' + ''.join(f'{i}: model_{i}.3do sound_{i}.snd # label {i}\n' for i in range(29)) + 'end\n'
        result = ninja.build_models(original)
        for number in range(29):
            self.assertIn(f'{number}: model_{number}.3do sound_{number}.snd\t1\t# label {number}', result)
        with self.assertRaisesRegex(ninja.NinjaError, 'count is not 29'):
            ninja.build_models(original.replace('28: model_28.3do sound_28.snd # label 28\n', ''))
        with self.assertRaisesRegex(ninja.NinjaError, 'Unexpected original model row'):
            ninja.build_models(original.replace('model_3.3do', 'model_3.mat'))

    def test_asset_stage_rejects_source_project_and_descendants_before_reading_originals(self):
        project = Path(ninja.__file__).resolve().parent
        for stage in (project, project / 'forbidden-assets' / '..' / 'still-in-project'):
            with self.subTest(stage=str(stage)), patch.object(ninja, 'open_original') as load:
                with self.assertRaisesRegex(ninja.NinjaError, 'outside the source project'):
                    ninja.build_to_directory({}, 'unread-original.zip', stage)
                load.assert_not_called()


@unittest.skipUnless(os.environ.get('BLACKWING_NINJA_ORIGINAL') and os.environ.get('BLACKWING_BASELINES'),
                     'Optional owned-asset fixtures are not configured')
class OwnedArtifactMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archives = bridge.pinned_archives(Path(os.environ['BLACKWING_BASELINES']))
        cls.original = ninja.open_original(Path(os.environ['BLACKWING_NINJA_ORIGINAL']))
        cls.data, cls.manifest = ninja.build(cls.archives, cls.original)
        archive = Gob(cls.data)
        cls.payloads = {path: archive.read(path) for path in archive.entries}

    def verify_mutation(self, path, change):
        files = dict(self.payloads)
        files[path] = change(files[path])
        return ninja.verify(self.archives, self.original, build_gob(files))

    def test_actual_build_passes_without_gameplay_claim(self):
        result = ninja.verify(self.archives, self.original, self.data, self.manifest)
        self.assertEqual(result['status'], 'structural-pass')
        self.assertEqual(result['gameplay'], 'not-run')
        self.assertEqual(sha(self.data), 'f65bded1d3db64602e8cc25a7c96a6e7c2328b2de33bedc7808f27295488806d')
        self.assertEqual(len(self.payloads), 1016)
        self.assertFalse(any(Path(p).name.startswith('mfr_') for p in self.payloads))

    def test_maxmana_reversal_recovers_exact_owned_source_and_preserves_every_other_payload(self):
        path = 'cog/force_well.cog'
        original = self.original.archive.read(path)
        self.assertEqual(sha(original), '04b8567af599b3b7eb92a1b2cc5ec3f0d2a0e11e56dba0137a8779217fcd1830')
        added = b'   SetInv(player, 69, GetInv(player, 20) * 50);\r\n'
        self.assertEqual(self.payloads[path].count(added), 1)
        self.assertEqual(self.payloads[path].replace(added, b'', 1), original)
        predecessor = {**self.payloads, path: original}
        # Independent canonical v3 archive pin covers every other resource byte.
        self.assertEqual(sha(build_gob(predecessor)),
                         '50de33501041102606b5a6f879d61195d55c11898014e22e4d3148fbb133c6df')

    def test_missing_wrong_or_refilling_maxmana_and_changed_regeneration_are_rejected(self):
        path = 'cog/force_well.cog'
        added = b'   SetInv(player, 69, GetInv(player, 20) * 50);\r\n'
        for old, new in ((added, b''), (added, added + added),
                         (added, added.replace(b', 69,', b', 14,')),
                         (added, added.replace(b'* 50', b'* 100')),
                         (b'GetInv(player, 20) * 2);', b'GetInv(player, 20) * 4);')):
            self.assertEqual(self.payloads[path].count(old), 1)
            with self.subTest(new=new), self.assertRaises(ninja.NinjaError):
                self.verify_mutation(path, lambda data: data.replace(old, new, 1))

    def test_maxmana_reversal_rejects_source_byte_drift_hidden_by_text_normalization(self):
        with self.assertRaisesRegex(ninja.NinjaError, 'maximum-mana insertion'):
            self.verify_mutation('cog/force_well.cog', lambda data: data.replace(b'\r\n', b'\n', 1))

    def test_maxmana_receipt_cannot_claim_predecessor_runtime_for_this_output(self):
        self.assertEqual(self.manifest['recipe'], 'ninja-kage-7.0-mots-mp-prototype-4-maxmana')
        self.assertEqual(self.manifest['runtime_test']['status'], 'bounded-native-initialization-pass')
        self.assertEqual(self.manifest['runtime_test']['artifact_sha256'], sha(self.data))
        self.assertEqual(self.manifest['runtime_test']['initialized_samples'], {'host': 37, 'client': 34})
        self.assertEqual(self.manifest['runtime_test']['engine']['kind'], 'older-private-diagnostic')
        self.assertIsNone(self.manifest['runtime_test']['engine']['base_commit'])
        self.assertFalse(self.manifest['runtime_test']['engine']['current_production_positive_rank_validated'])
        self.assertFalse(self.manifest['runtime_test']['full_gameplay'])
        self.assertEqual(self.manifest['runtime_test']['predecessor']['artifact_sha256'],
                         '50de33501041102606b5a6f879d61195d55c11898014e22e4d3148fbb133c6df')
        for changes in ({'recipe': 'old-recipe'}, {'original_cog_edits': {}},
                        {'runtime_test': self.manifest['runtime_test']['predecessor']},
                        {'runtime_test': {**self.manifest['runtime_test'], 'engine': {'kind': 'current-production'}}}):
            with self.subTest(changes=changes), self.assertRaises(ninja.NinjaError):
                ninja.verify(self.archives, self.original, self.data, {**self.manifest, **changes})

    def test_default_build_requires_both_depths_of_original_force_hud_icons(self):
        for name in ('icf_thr8.bm', 'icf_thr16.bm', 'icf_lig8.bm', 'icf_lig16.bm'):
            path = 'ui/bm/' + name
            self.assertEqual(self.payloads[path], self.archives['jksnd'].read(path))
            changed = {p: data for p, data in self.payloads.items() if p != path}
            with self.subTest(path=path), self.assertRaisesRegex(ninja.NinjaError, 'HUD icon'):
                ninja.verify(self.archives, self.original, build_gob(changed))

    def test_authored_weapon_code_and_native_player_untouched_segments_are_protected(self):
        for path in ('cog/weap_saber_m.cog', 'cog/kyle_m.cog'):
            with self.subTest(path=path), self.assertRaisesRegex(ninja.NinjaError, 'COG|player'):
                self.verify_mutation(path, lambda data: data + b'\r\n# Unreviewed change\r\n')

    def test_native_inventory_descriptors_cannot_be_silently_rebound(self):
        for name in (b'cog=force_push.cog', b'cog=weap_concrifle_m.cog'):
            with self.subTest(name=name), self.assertRaisesRegex(ninja.NinjaError, 'descriptor semantics'):
                self.verify_mutation('misc/items.dat', lambda data: data.replace(name, b'cog=weap_fists_m.cog', 1))

    def test_model_personality_and_static_preload_mutations_are_rejected(self):
        with self.assertRaisesRegex(ninja.NinjaError, 'model selection/personality'):
            self.verify_mutation('misc/models.dat', lambda data: data.replace(b'\t1', b'\t2', 1))
        static = ninja.txt(self.payloads['jkl/static.jkl'])
        preload = bridge.records(static, 'models')[-1]
        with self.assertRaisesRegex(ninja.NinjaError, 'preload'):
            self.verify_mutation('jkl/static.jkl', lambda data: ninja.encoded(ninja.txt(data).replace(preload + '\n', '', 1)))

    def test_unknown_payload_and_manifest_set_drift_are_rejected(self):
        files = {**self.payloads, 'misc/unreviewed.txt': b'Not in any pinned archive'}
        with self.assertRaisesRegex(ninja.NinjaError, 'pinned source'):
            ninja.verify(self.archives, self.original, build_gob(files))
        manifest = {**self.manifest, 'resources': self.manifest['resources'][:-1]}
        with self.assertRaisesRegex(ninja.NinjaError, 'manifest exact resource set'):
            ninja.verify(self.archives, self.original, self.data, manifest)

    def test_original_object_cannot_bypass_normalized_payload_or_readme_pins(self):
        files = {path: self.original.archive.read(path) for path in self.original.archive.entries}
        material = next(path for path in files if path.endswith('.mat'))
        files[material] += b'Unreviewed original asset mutation'
        altered = ninja.Original(Gob(build_gob(files)), self.original.source_sha256, self.original.readme)
        with self.assertRaisesRegex(ninja.NinjaError, 'Normalized original payload/directory hash'):
            ninja.verify(self.archives, altered, self.data)
        altered = ninja.Original(self.original.archive, self.original.source_sha256, b'Changed original attribution')
        with self.assertRaisesRegex(ninja.NinjaError, 'Original README changed'):
            ninja.verify(self.archives, altered, self.data)

    def test_unused_pinned_retail_resource_cannot_be_justified_by_its_own_preload(self):
        existing_names = {Path(path).name for path in self.payloads}
        # A real pinned WAV has no outgoing text references. Its only incoming
        # edge in this mutation is the newly generated preload row itself.
        candidate = next((path, archive.read(path))
                         for archive in self.archives.values()
                         for path in sorted(archive.entries)
                         if path.endswith('.wav') and Path(path).name not in existing_names
                         and len(Path(path).name.encode('cp1252')) <= 31)
        path, payload = candidate
        files = {**self.payloads, path: payload}
        native_static = ninja.txt(self.archives['motsres'].read('jkl/static.jkl'))
        authored_static = ninja.txt(self.original.archive.read('jkl/static.jkl'))
        static = ninja._append_templates(native_static, authored_static)
        static = ninja._preload_static(ninja._grow_capacities(static, files), files)
        files['jkl/static.jkl'] = ninja.encoded(static)
        self.assertIn(Path(path).name, bridge.records(static, 'sounds'))
        with self.assertRaisesRegex(ninja.NinjaError, 'unreferenced imported resource'):
            ninja.verify(self.archives, self.original, build_gob(files))

    def test_manifest_cannot_broaden_the_pinned_unused_native_template_waiver(self):
        waiver = self.manifest['native_unused_template']
        for field, value in waiver.items():
            with self.subTest(field=field):
                changed = {**waiver, field: str(value) + '-unreviewed'}
                manifest = {**self.manifest, 'native_unused_template': changed}
                with self.assertRaisesRegex(ninja.NinjaError, 'manifest native template waiver mismatch'):
                    ninja.verify(self.archives, self.original, self.data, manifest)



if __name__ == '__main__':
    unittest.main()

"""Synthetic-only regression coverage for revision metadata and folder scans."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock
import hashlib
import json
import os
import struct
import unittest

from gob import Gob, build_gob
import blackwing_revisions as revisions
import verify_retail


def archive(content=b'original level'):
    return build_gob({'jkl/synthetic.jkl': content, 'episode.jk': b'Synthetic\n'})


def stamped(recipe_id='canyon-oasis', number=1, content=b'original level', **kwargs):
    return revisions.stamp_archive(archive(content), recipe_id, number,
                                   tool_version='0.2.0-test', **kwargs)[0]


def replace_resource(data, name, payload):
    parsed = Gob(data)
    resources = {entry: parsed.read(entry) for entry in parsed.entries}
    resources[name] = payload
    return build_gob(resources)


def catalog():
    return [dict(id='canyon-oasis', title='Canyon Oasis', kind='map', revision=2,
                 legacy_filenames=['bridge-canyon-v1.goo']),
            dict(id='jhs', title='Jedi High School', kind='map', revision=1,
                 legacy_filenames=['bridge-jhs-v1.goo']),
            dict(id='ninja-kage', title='Ninja Kage', kind='mod', revision=3,
                 legacy_filenames=['bridge-ninja-kage-v1.goo'])]


class RevisionMarkerTests(unittest.TestCase):
    def test_explicit_recipe_revision_registry(self):
        from blackwing_catalog import recipes
        self.assertEqual(set(revisions.RECIPE_REVISIONS), {row['id'] for row in recipes()})
        self.assertTrue(all(type(number) is int and number > 0 for number in revisions.RECIPE_REVISIONS.values()))
        self.assertEqual(revisions.revision('canyon-oasis'), 1)
        with self.assertRaises(KeyError):
            revisions.revision('not-a-supported-recipe')

    def test_filename_suffix_preserves_type_and_directories(self):
        cases = {
            'bridge-canyon-v1.goo': 'bridge-canyon_wbw_v2.goo',
            'bridge-caesars-v3.goo': 'bridge-caesars_wbw_v2.goo',
            'episode/bridge-jhs_wbw_v1.goo': 'episode/bridge-jhs_wbw_v2.goo',
            r'C:\MotS\episode\test-v7.GOO': r'C:\MotS\episode\test_wbw_v2.GOO',
            'test-v1-extra.goo': 'test-v1-extra_wbw_v2.goo',
            'archive.gob': 'archive_wbw_v2.gob',
            'bridge-shadowcaverns-rc1.goo': 'bridge-shadowcaverns_wbw_v2.goo',
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(revisions.versioned_name(source, 2), expected)
        for number in (0, -1, True, '2'):
            with self.assertRaises(ValueError):
                revisions.versioned_name('test.goo', number)
        with self.assertRaises(ValueError):
            revisions.versioned_name('test.zip', 1)
        self.assertEqual(revisions.versioned_name('bridge-shadowcaverns-rc1.goo', 1),
                         'bridge-shadowcaverns_wbw_v1.goo')
        self.assertEqual(len(revisions.versioned_name('a' * 24 + '.goo', 1).split('.')[0]), 31)
        with self.assertRaisesRegex(ValueError, '31-byte'):
            revisions.versioned_name('a' * 25 + '.goo', 1)
        with self.assertRaisesRegex(ValueError, '31-byte'):
            revisions.versioned_name('a' * 24 + '.goo', 10)

    def test_deterministic_stamp_preserves_all_logical_resources(self):
        original = archive()
        first, marker = revisions.stamp_archive(original, 'canyon-oasis', 1,
                                                tool_version='0.2.0', recipe_sha256='a' * 64)
        second, _ = revisions.stamp_archive(original, 'canyon-oasis', 1,
                                             tool_version='0.2.0', recipe_sha256='a' * 64)
        self.assertEqual(first, second)
        source, output = Gob(original), Gob(first)
        self.assertEqual(set(output.entries), set(source.entries) | {revisions.MARKER_NAME})
        for name in source.entries:
            self.assertEqual(source.read(name), output.read(name))
        self.assertEqual(revisions.validate_archive(first), marker)
        self.assertEqual(marker['payload_sha256'], hashlib.sha256(original).hexdigest())
        self.assertEqual(marker['recipe_sha256'], 'a' * 64)

    def test_no_marker_has_no_invented_revision(self):
        self.assertIsNone(revisions.validate_archive(archive()))

    def test_restamping_replaces_one_marker_and_rejects_damaged_input(self):
        first = stamped()
        newer, marker = revisions.stamp_archive(first, 'canyon-oasis', 2, tool_version='next')
        self.assertEqual(marker['revision'], 2)
        self.assertEqual(len(Gob(first).entries), len(Gob(newer).entries))
        damaged = replace_resource(first, 'jkl/synthetic.jkl', b'edited')
        with self.assertRaisesRegex(revisions.RevisionError, 'payload differs'):
            revisions.stamp_archive(damaged, 'canyon-oasis', 2, tool_version='next')

    def test_payload_tamper_fails_validation(self):
        changed = replace_resource(stamped(), 'jkl/synthetic.jkl', b'changed geometry')
        with self.assertRaisesRegex(revisions.RevisionError, 'payload differs'):
            revisions.validate_archive(changed)

    def test_added_resource_fails_validation(self):
        changed = replace_resource(stamped(), 'new/resource.txt', b'added')
        with self.assertRaises(revisions.RevisionError):
            revisions.validate_archive(changed)

    def test_malformed_marker_fields_fail_closed(self):
        baseline = stamped()
        valid = revisions.validate_archive(baseline)
        for field, value in [('schema', True), ('schema', 2), ('id', '../escape'),
                             ('revision', True), ('revision', 0), ('role', '../../x'),
                             ('appversion', '\n'), ('payload_sha256', 'f' * 63),
                             ('recipe_sha256', 'not-a-hash')]:
            with self.subTest(field=field, value=value):
                marker = dict(valid, **{field: value})
                changed = replace_resource(baseline, revisions.MARKER_NAME,
                                           json.dumps(marker).encode())
                with self.assertRaises(revisions.RevisionError):
                    revisions.validate_archive(changed)
        for raw in (b'{', b'[]', b'\xff', b'{"schema":1,"schema":1}',
                    b'[' * 2000 + b']' * 2000,
                    b' ' * (revisions.MAX_MARKER_BYTES + 1)):
            with self.subTest(raw=raw[:30]):
                with self.assertRaises(revisions.RevisionError):
                    revisions.validate_archive(replace_resource(baseline, revisions.MARKER_NAME, raw))

    def test_unknown_recipe_cannot_be_stamped(self):
        with self.assertRaises(ValueError):
            revisions.stamp_archive(archive(), 'unknown', 1, tool_version='test')


class InstallationScanTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(prefix='wbw-revisions-')
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def put(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def scan(self, **kwargs):
        return revisions.scan_installation(self.root, catalog(), **kwargs)

    def test_current_old_future_and_per_recipe_independence(self):
        self.put('episode/current.goo', stamped(number=2))
        self.put('episode/old.goo', stamped(number=1))
        self.put('episode/newer.goo', stamped(number=3))
        self.put('episode/jhs.goo', stamped('jhs', 1))
        self.put('startup/ninja.goo', stamped('ninja-kage', 1))
        report = self.scan()
        rows = {row['filename']: row for row in report['results']}
        self.assertEqual(rows['current.goo']['status'], 'current')
        self.assertEqual(rows['old.goo']['status'], 'update_available')
        self.assertEqual(rows['newer.goo']['status'], 'newer')
        self.assertFalse(rows['newer.goo']['can_update'])
        self.assertEqual(rows['jhs.goo']['status'], 'current')
        self.assertEqual(rows['ninja.goo']['status'], 'update_available')
        self.assertEqual(rows['ninja.goo']['kind'], 'mod')
        self.assertEqual(report['counts']['total'], 5)
        self.assertFalse(report['truncated'])

    def test_renamed_marked_archive_is_still_recognized(self):
        self.put('episode/something-else.GOO', stamped(number=2))
        row = self.scan()['results'][0]
        self.assertEqual((row['id'], row['status']), ('canyon-oasis', 'current'))

    def test_unavailable_recipe_preserves_inventory_without_offering_conversion(self):
        self.put('old.goo', stamped(number=1))
        self.put('current.goo', stamped(number=2))
        self.put('bridge-canyon-v1.goo', archive())
        for status in ('unavailable', 'future-status'):
            with self.subTest(status=status):
                rows = catalog()
                rows[0]['status'] = status
                report = revisions.scan_installation(self.root, rows)
                found = {row['filename']: row for row in report['results']}
                self.assertEqual(found['old.goo']['installed_revision'], 1)
                self.assertEqual(found['current.goo']['status'], 'current')
                self.assertEqual(found['bridge-canyon-v1.goo']['status'], 'unversioned')
                for row in found.values():
                    self.assertFalse(row['can_update'])
                    self.assertIn('unavailable for conversion', row['message'])
                    self.assertNotIn('regenerate', row['message'])

    def test_app_version_and_recipe_hash_do_not_invalidate_revision(self):
        data, _ = revisions.stamp_archive(archive(), 'canyon-oasis', 2,
                                          tool_version='old-app', recipe_sha256='b' * 64)
        self.put('level.goo', data)
        self.assertEqual(self.scan()['results'][0]['status'], 'current')

    def test_filename_only_never_proves_revision(self):
        self.put('episode/bridge-canyon-v1.goo', archive())
        self.put('episode/bridge-canyon_wbw_v2.goo', archive())
        rows = {row['filename']: row for row in self.scan()['results']}
        self.assertEqual(rows['bridge-canyon-v1.goo']['status'], 'unversioned')
        self.assertIsNone(rows['bridge-canyon-v1.goo']['installed_revision'])
        self.assertEqual(rows['bridge-canyon_wbw_v2.goo']['status'], 'unrecognized')
        self.assertIsNone(rows['bridge-canyon_wbw_v2.goo']['installed_revision'])

    def test_tampered_archive_is_modified_and_cannot_update_automatically(self):
        self.put('level.goo', replace_resource(stamped(), 'jkl/synthetic.jkl', b'manual edit'))
        row = self.scan()['results'][0]
        self.assertEqual(row['status'], 'modified')
        self.assertEqual(row['id'], 'canyon-oasis')
        self.assertIsNone(row['installed_revision'])
        self.assertFalse(row['can_update'])

    def test_malformed_marker_and_bad_archive_are_distinct(self):
        self.put('malformed.goo', replace_resource(stamped(), revisions.MARKER_NAME, b'{"oops":1}'))
        self.put('bad-file.goo', b'not a GOO')
        rows = {row['filename']: row for row in self.scan()['results']}
        self.assertEqual(rows['malformed.goo']['status'], 'modified')
        self.assertEqual(rows['bad-file.goo']['status'], 'error')

    def test_unknown_archive_and_unknown_recipe_marker_have_no_false_identity(self):
        self.put('retail.goo', archive())
        valid = stamped()
        marker = revisions.validate_archive(valid)
        marker['id'] = 'future-recipe'
        self.put('future.goo', replace_resource(valid, revisions.MARKER_NAME,
                                                json.dumps(marker).encode()))
        rows = self.scan()['results']
        self.assertTrue(all(row['status'] == 'unrecognized' for row in rows))
        self.assertTrue(all(row['id'] is None for row in rows))
        self.assertTrue(all(not row['can_update'] for row in rows))

    def test_duplicate_identity_and_role_warns_but_distinct_roles_do_not(self):
        self.put('episode/new.goo', stamped(number=2))
        self.put('episode/old.goo', stamped(number=1))
        self.put('startup/addon.goo', stamped(number=2, role='startup'))
        report = self.scan()
        rows = {row['filename']: row for row in report['results']}
        self.assertTrue(rows['new.goo']['duplicate'])
        self.assertTrue(rows['old.goo']['duplicate'])
        self.assertFalse(rows['addon.goo']['duplicate'])
        self.assertEqual(report['counts']['duplicates'], 2)
        self.assertTrue(any('shadow' in warning for warning in report['warnings']))
        self.assertFalse(report['truncated'])

    def test_known_legacy_hash_recovers_renamed_recipe_but_not_revision(self):
        original = archive()
        self.put('renamed.goo', original)
        recipes = catalog()
        recipes[0]['legacy_sha256'] = [hashlib.sha256(original).hexdigest()]
        row = revisions.scan_installation(self.root, recipes)['results'][0]
        self.assertEqual((row['id'], row['status']), ('canyon-oasis', 'unversioned'))
        self.assertIsNone(row['installed_revision'])

    def test_ambiguous_legacy_name_does_not_assign_recipe(self):
        self.put('bridge-canyon-v1.goo', archive())
        recipes = catalog()
        recipes[1]['legacy_filenames'] = ['bridge-canyon-v1.goo']
        row = revisions.scan_installation(self.root, recipes)['results'][0]
        self.assertIsNone(row['id'])
        self.assertEqual(row['status'], 'unrecognized')

    def test_unrecognized_retail_payload_is_not_loaded(self):
        data = build_gob({'retail.bin': b'x' * (1024 * 1024)})
        self.put('resource/retail.goo', data)
        report = self.scan(max_total_bytes=4096)
        self.assertEqual(report['results'][0]['status'], 'unrecognized')
        self.assertLess(report['scanned_bytes'], 4096)
        self.assertFalse(report['truncated'])

    def test_scan_is_read_only_including_input_timestamps(self):
        self.put('episode/level.goo', stamped(number=2))
        self.put('player.plr', b'player settings')
        before = {str(path.relative_to(self.root)): (path.read_bytes(), path.stat().st_mtime_ns)
                  for path in self.root.rglob('*') if path.is_file()}
        self.scan()
        after = {str(path.relative_to(self.root)): (path.read_bytes(), path.stat().st_mtime_ns)
                 for path in self.root.rglob('*') if path.is_file()}
        self.assertEqual(before, after)

    def test_depth_count_entry_and_read_limits_report_partial_results(self):
        self.put('deep/inside/level.goo', stamped())
        report = self.scan(max_depth=0)
        self.assertTrue(report['truncated'])
        self.assertEqual(report['counts']['total'], 0)
        self.put('one.goo', stamped())
        self.put('two.goo', stamped())
        report = self.scan(max_files=1)
        self.assertEqual(report['counts']['total'], 1)
        self.assertTrue(report['truncated'])
        self.assertTrue(self.scan(max_entries=1)['truncated'])
        report = self.scan(max_total_bytes=20)
        self.assertTrue(report['truncated'])
        self.assertTrue(all(row['status'] == 'error' for row in report['results']))
        self.assertLessEqual(report['scanned_bytes'], 20)

    def test_exact_byte_budget_cannot_silently_hide_more_archives(self):
        self.put('first.goo', stamped())
        bytes_for_one = self.scan()['scanned_bytes']
        self.put('second.goo', stamped())
        report = self.scan(max_total_bytes=bytes_for_one)
        self.assertEqual(report['counts']['total'], 1)
        self.assertTrue(report['truncated'])
        self.assertTrue(any('read-byte' in warning for warning in report['warnings']))

    def test_per_archive_limit_reports_error_without_allocating_payload(self):
        self.put('large.goo', stamped())
        report = self.scan(max_archive_bytes=32)
        self.assertEqual(report['results'][0]['status'], 'error')
        self.assertEqual(report['scanned_bytes'], 0)
        self.assertTrue(report['truncated'])

    def test_huge_directory_count_is_rejected_before_read_allocation(self):
        self.put('bad.goo', struct.pack('<4sIII', b'GOB ', 20, 12, 0xFFFFFFFF))
        report = self.scan()
        self.assertEqual(report['results'][0]['status'], 'error')
        self.assertTrue(report['truncated'])
        self.assertLess(report['scanned_bytes'], 100)

    def test_root_must_be_selected_absolute_existing_directory(self):
        for bad in ('relative-mots', self.root / 'missing'):
            with self.assertRaises(ValueError):
                revisions.scan_installation(bad, catalog())
        for kwargs in ({'max_files': 0}, {'max_depth': -1}, {'max_total_bytes': True}):
            with self.assertRaises(ValueError):
                self.scan(**kwargs)

    def test_link_to_outside_file_or_directory_is_never_followed(self):
        with TemporaryDirectory(prefix='wbw-outside-') as other:
            outside = Path(other)
            target = outside / 'secret.goo'
            target.write_bytes(stamped())
            try:
                (self.root / 'file.goo').symlink_to(target)
                (self.root / 'directory').symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f'Symlink creation unavailable: {exc}')
            report = self.scan()
            self.assertEqual(report['counts']['total'], 0)
            self.assertEqual(report['scanned_bytes'], 0)
            self.assertTrue(report['truncated'])
            with self.assertRaises(ValueError):
                revisions.scan_installation(self.root / 'directory', catalog())

    def test_windows_reparse_flag_is_treated_as_link(self):
        info = mock.Mock(st_mode=0o040755, st_file_attributes=0x400)
        self.assertTrue(revisions._is_link(info))


class TrackedVerificationTests(unittest.TestCase):
    def test_adapter_removes_only_marker_and_reports_both_hashes(self):
        generated = Gob(stamped())
        payload, marker = verify_retail.game_payload(generated, 'canyon-oasis')
        self.assertEqual(payload.data, archive())
        self.assertEqual(set(generated.entries) - set(payload.entries), {revisions.MARKER_NAME})
        result = verify_retail.tracked_result({'passed': ['synthetic check']}, generated, payload, marker)
        self.assertEqual(result['sha256'], generated.sha256)
        self.assertEqual(result['payload_sha256'], hashlib.sha256(archive()).hexdigest())
        self.assertEqual(result['tracking']['id'], 'canyon-oasis')

    def test_adapter_keeps_untracked_developer_outputs_compatible(self):
        generated = Gob(archive())
        payload, marker = verify_retail.game_payload(generated, 'canyon-oasis')
        self.assertIs(payload, generated)
        self.assertIsNone(marker)
        result = {'sha256': generated.sha256}
        self.assertEqual(verify_retail.tracked_result(dict(result), generated, payload, marker), result)

    def test_adapter_binds_selected_recipe_and_role(self):
        with self.assertRaisesRegex(AssertionError, 'different selected recipe'):
            verify_retail.game_payload(Gob(stamped('jhs')), 'canyon-oasis')
        with self.assertRaisesRegex(AssertionError, 'wrong primary/startup role'):
            verify_retail.game_payload(Gob(stamped(role='startup')), 'canyon-oasis')
        with self.assertRaisesRegex(AssertionError, 'wrong primary/startup role'):
            verify_retail.game_payload(Gob(stamped()), 'canyon-oasis', role='startup')

    def test_adapter_rejects_tampered_payload_before_independent_check(self):
        changed = replace_resource(stamped(), 'jkl/synthetic.jkl', b'edited')
        with self.assertRaisesRegex(revisions.RevisionError, 'payload differs'):
            verify_retail.game_payload(Gob(changed), 'canyon-oasis')

    def test_resolver_uses_marker_for_renamed_archive_and_rejects_duplicates(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / 'renamed.goo'
            target.write_bytes(stamped())
            self.assertEqual(verify_retail.resolve_output(root, 'bridge-canyon-v1.goo', 'canyon-oasis'), target)
            (root / 'bridge-canyon-v1.goo').write_bytes(archive())
            with self.assertRaisesRegex(AssertionError, 'exactly one'):
                verify_retail.resolve_output(root, 'bridge-canyon-v1.goo', 'canyon-oasis')

    def test_resolver_rejects_suffix_without_marker_and_wrong_recipe_at_legacy_name(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'bridge-canyon_wbw_v1.goo').write_bytes(archive())
            with self.assertRaisesRegex(AssertionError, 'exactly one'):
                verify_retail.resolve_output(root, 'bridge-canyon-v1.goo', 'canyon-oasis')
            (root / 'bridge-canyon-v1.goo').write_bytes(stamped('jhs'))
            with self.assertRaisesRegex(AssertionError, 'different selected recipe'):
                verify_retail.resolve_output(root, 'bridge-canyon-v1.goo', 'canyon-oasis')

    def test_resolver_does_not_choose_tampered_renamed_candidate(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'renamed.goo').write_bytes(replace_resource(stamped(), 'jkl/synthetic.jkl', b'edited'))
            with self.assertRaisesRegex(revisions.RevisionError, 'payload differs'):
                verify_retail.resolve_output(root, 'bridge-canyon-v1.goo', 'canyon-oasis')

    def ctf_fixture(self, root, *, recipe_id='ctf-duel', role='startup', changed=False, tracked=True):
        native = b'fieldlight 42 0 1 0x100\nysalamiri 81 0 1 0x048\nredflag2 82 0 1 0x049\n'
        payload = native.replace(b'ysalamiri 81', b'redflag 81')
        if changed:
            payload = payload.replace(b'0x048', b'0x049')
        data = build_gob({'misc/items.dat': payload})
        if tracked:
            data, _ = revisions.stamp_archive(data, recipe_id, 1, tool_version='test', role=role)
        name = 'bridge-ctf-ui_wbw_v1.goo' if tracked else 'bridge-ctf-ui.goo'
        (root / name).write_bytes(data)
        return {'motsres': Gob(build_gob({'misc/items.dat': native}))}, data

    def test_ctf_tracked_startup_keeps_independent_source_check_and_final_hash(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            archives, data = self.ctf_fixture(root)
            result = verify_retail.check_ctf_startup(archives, root, recipe_id='ctf-duel')
            self.assertEqual(result['sha256'], hashlib.sha256(data).hexdigest())
            self.assertEqual(result['tracking']['role'], 'startup')
            self.assertNotEqual(result['sha256'], result['payload_sha256'])

    def test_ctf_untracked_startup_remains_supported(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            archives, data = self.ctf_fixture(root, tracked=False)
            result = verify_retail.check_ctf_startup(archives, root)
            self.assertEqual(result['sha256'], hashlib.sha256(data).hexdigest())
            self.assertNotIn('tracking', result)

    def test_ctf_valid_checksum_cannot_hide_unreviewed_game_edit(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            archives, _ = self.ctf_fixture(root, changed=True)
            with self.assertRaisesRegex(AssertionError, 'changed unrelated native descriptors'):
                verify_retail.check_ctf_startup(archives, root, recipe_id='ctf-duel')

    def test_ctf_wrong_recipe_role_or_extra_goo_fails_closed(self):
        for recipe_id, role in (('ctf-arena', 'startup'), ('ctf-duel', 'primary')):
            with self.subTest(recipe_id=recipe_id, role=role), TemporaryDirectory() as temporary:
                root = Path(temporary)
                archives, _ = self.ctf_fixture(root, recipe_id=recipe_id, role=role)
                with self.assertRaises(AssertionError):
                    verify_retail.check_ctf_startup(archives, root, recipe_id='ctf-duel')
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            archives, _ = self.ctf_fixture(root)
            (root / 'extra.goo').write_bytes(archive())
            with self.assertRaisesRegex(AssertionError, 'extra GOO'):
                verify_retail.check_ctf_startup(archives, root, recipe_id='ctf-duel')

    def test_community_tracked_startup_reconstructs_source_and_binds_recipe(self):
        original = b'code\nSetInv(p, 10, 1);\nReturn;\nend\n'
        edited = original.replace(b', 10,', b', 131,')
        empty = Gob(build_gob({}))
        archives = {'motsres': Gob(build_gob({'cog/native.cog': original})),
                    'motsmp': empty, 'motssnd': empty}
        spec = {'key': 'jhs', 'tag': 'fixture', 'native_cog_edits': {
            'native.cog': {'sha256': hashlib.sha256(original).hexdigest(), 'edits': [
                {'old': 'SetInv(p, 10, 1);', 'new': 'SetInv(p, 131, 1);', 'count': 1,
                 'reason': 'Synthetic reviewed inventory-slot adaptation'}]}}}
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'README.txt').write_text('Synthetic instructions')
            filename = root / 'bridge-fixture-startup_wbw_v1.goo'
            for changed in (False, True):
                raw = build_gob({'cog/native.cog': edited + (b'Unexpected();\n' if changed else b'')})
                data, _ = revisions.stamp_archive(raw, 'jhs', 1, tool_version='test', role='startup')
                filename.write_bytes(data)
                if changed:
                    with self.assertRaisesRegex(AssertionError, 'exact startup source reconstruction'):
                        verify_retail.check_community_startup(archives, empty, empty, spec, {}, root)
                else:
                    result = verify_retail.check_community_startup(archives, empty, empty, spec, {}, root)
                    self.assertEqual(result['tracking']['id'], 'jhs')
                    self.assertEqual(result['sha256'], hashlib.sha256(data).hexdigest())


if __name__ == '__main__':
    unittest.main()

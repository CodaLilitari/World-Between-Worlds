"""Asset-free tests of selection, local API boundaries and safe publication paths."""
import hashlib
import io
import http.client
from email.message import Message
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
import sys
import zipfile
from unittest.mock import Mock, patch

import blackwing_app
import blackwing_catalog as catalog
import blackwing_service as service
import bridge


class SelectionTests(unittest.TestCase):
    def test_catalog_has_no_implicit_selection_and_all_existing_maps(self):
        data = catalog.catalog()
        self.assertEqual(data['default_selection'], [])
        ids = [row['id'] for row in data['recipes']]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(set(bridge.STOCK_MAPS) <= set(ids))
        self.assertTrue({'jhs', 'purgatory', 'dojo', 'caesars'} <= set(ids))
        self.assertGreaterEqual(len(ids), 26)

    def test_empty_and_magic_all_never_convert(self):
        for value in (None, [], 'all', ['all'], ['*'], ['jhs', 'jhs'], [None]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                catalog.selection(value)

    def test_selection_export_contains_exact_selected_recipe_only(self):
        data = catalog.export_plan(['canyon-oasis', 'jhs'])
        self.assertEqual([row['entry']['id'] for row in data['recipes']], ['canyon-oasis', 'jhs'])
        self.assertFalse(data['assets_included'])
        jhs = data['recipes'][1]
        digest = jhs.pop('recipe_sha256')
        self.assertEqual(digest, hashlib.sha256(catalog.canonical(jhs)).hexdigest())
        self.assertEqual(len(jhs['recipe']['gob_sha256']), 64)
        self.assertIn('bridge.py', jhs['engine_source_sha256'])

    def test_catalog_runtime_evidence_is_not_full_gameplay_claim(self):
        for row in catalog.recipes():
            if row['kind'] != 'mod':
                self.assertFalse(row['runtime_test']['full_gameplay'])

    def test_new_community_recipe_does_not_inherit_prior_host_test(self):
        import custom_registry
        import blackwing_revisions
        spec = dict(next(iter(custom_registry.entries().values())), key='synthetic-new',
                    tag='synthetic_new', title='Synthetic new map')
        with patch.object(custom_registry, 'entries', return_value={'synthetic-new': spec}), \
                patch.dict(blackwing_revisions.RECIPE_REVISIONS, {'synthetic-new': 1}):
            row = next(row for row in catalog.recipes() if row['id'] == 'synthetic-new')
            self.assertEqual(row['runtime_test']['status'], 'not-run')
            spec['runtime_test'] = dict(status='fixture-specific', scope='synthetic', full_gameplay=False)
            row = next(row for row in catalog.recipes() if row['id'] == 'synthetic-new')
            self.assertEqual(row['runtime_test']['status'], 'fixture-specific')

    def test_recipe_revisions_are_explicit_and_separate_from_app_version(self):
        import blackwing_revisions as revisions
        rows = catalog.recipes()
        self.assertEqual(set(revisions.RECIPE_REVISIONS), {row['id'] for row in rows})
        canyon = next(row for row in rows if row['id'] == 'canyon-oasis')
        self.assertEqual(canyon['output_filename'], 'bridge-canyon_wbw_v1.goo')
        with patch.dict(revisions.RECIPE_REVISIONS, {'canyon-oasis': 2}):
            latest = {row['id']: row for row in catalog.recipes()}
            self.assertEqual(latest['canyon-oasis']['revision'], 2)
            self.assertEqual(latest['jhs']['revision'], 1)
            self.assertEqual(latest['canyon-oasis']['output_filename'], 'bridge-canyon_wbw_v2.goo')

    def test_ninja_is_an_explicit_separate_prototype_selection(self):
        self.assertEqual([r['id'] for r in catalog.selection(['canyon-oasis'])], ['canyon-oasis'])
        rows = catalog.selection(['ninja-kage', 'canyon-oasis'])
        self.assertEqual([r['id'] for r in rows], ['ninja-kage', 'canyon-oasis'])
        self.assertEqual(rows[0]['status'], 'prototype')
        self.assertEqual(rows[0]['kind'], 'mod')
        self.assertIsNone(rows[1]['startup_overlay'])
        self.assertEqual([r['entry']['id'] for r in catalog.export_plan(['ninja-kage'])['recipes']], ['ninja-kage'])

    def test_changed_source_cannot_get_a_fresh_but_false_recipe_lock(self):
        changed = {**catalog.LOADED_SOURCE_HASHES, 'bridge.py': '0' * 64}
        with patch.object(catalog, 'source_hashes', return_value=changed):
            with self.assertRaisesRegex(ValueError, 'Restart World Between Worlds'):
                catalog.recipe_details('jhs')


class CommunityNoticeDeliveryTests(unittest.TestCase):
    def setUp(self):
        from gob import build_gob
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.gob = build_gob({'jkl/fixture.jkl': b'Synthetic source world\n'})
        self.notices = {'canyonstream.txt': b'Synthetic author notice\r\nExact bytes: \xff\r\n',
                        'walkthrough.txt': b'Synthetic walkthrough\r\nKeep this second file.\r\n'}
        self.spec = {'key': 'notice-fixture', 'tag': 'notice_fixture', 'title': 'Synthetic notice fixture',
                     'gob_member': 'fixture.gob', 'gob_sha256': hashlib.sha256(self.gob).hexdigest(),
                     'original_notices': [{'path': name, 'bytes': len(data),
                         'sha256': hashlib.sha256(data).hexdigest()} for name, data in self.notices.items()]}
        self.source = self.package(self.notices)
        self.row = dict(id='notice-fixture', title=self.spec['title'], revision=1, revision_label='wbw_v1',
                        startup_overlay=None, legacy_filenames=['bridge-notice_fixture-rc1.goo'],
                        output_filename='bridge-notice_fixture_wbw_v1.goo')
        self.entries = patch.object(service.custom_registry, 'entries', return_value={'notice-fixture': self.spec})
        self.entries.start()
        self.addCleanup(self.entries.stop)

    def package(self, notices):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w', zipfile.ZIP_STORED) as archive:
            archive.writestr('fixture.gob', self.gob)
            for name, data in notices.items():
                archive.writestr(name, data)
        data = stream.getvalue()
        self.spec['zip_sha256'] = hashlib.sha256(data).hexdigest()
        source = self.root / 'original.zip'
        source.write_bytes(data)
        return source

    def build(self, stage, source=None):
        # Exercise the real service, source loader, candidate writer and notices;
        # conversion semantics have their own source-preservation test suites.
        with patch.object(bridge, 'recipe', return_value=(self.gob, {'scene': 'synthetic', 'status': 'fixture'})), \
                patch.object(service.verify_retail, 'check', return_value={'passed': ['synthetic payload']}):
            return service.build_one(self.row, {}, source or self.source, stage)

    def test_service_and_tracking_deliver_both_exact_original_notices(self):
        stage = self.root / 'stage'
        result = self.build(stage)
        self.assertEqual(result['manifest_filename'], 'bridge-notice_fixture-rc1.manifest.json')
        with patch.object(catalog, 'recipes', return_value=[self.row]), \
                patch.dict(service.blackwing_revisions.RECIPE_REVISIONS, {'notice-fixture': 1}):
            tracked = service.track_outputs(self.row, stage, result, {'recipe_sha256': 'a' * 64})
        self.assertEqual(tracked['filename'], self.row['output_filename'])
        for name, content in self.notices.items():
            self.assertEqual((stage / name).read_bytes(), content)
            self.assertEqual(service.tree_hashes(stage)[name], hashlib.sha256(content).hexdigest())

    def test_external_notices_require_zip_without_changing_legacy_gob_support(self):
        self.assertEqual(service.original_hashes('notice-fixture'), {self.spec['zip_sha256']})
        raw = self.root / 'original.gob'
        raw.write_bytes(self.gob)
        with self.assertRaisesRegex(ValueError, 'original ZIP'):
            self.build(self.root / 'rejected-gob', raw)
        self.assertFalse((self.root / 'rejected-gob').exists())
        self.spec.pop('original_notices')
        self.assertEqual(service.original_hashes('notice-fixture'),
                         {self.spec['zip_sha256'], self.spec['gob_sha256']})
        result = self.build(self.root / 'legacy-gob', raw)
        self.assertTrue((self.root / 'legacy-gob' / result['filename']).is_file())

    def test_missing_or_tampered_notice_fails_even_with_repinned_zip(self):
        for kind in ('missing', 'hash', 'length'):
            notices = dict(self.notices)
            if kind == 'missing':
                notices.pop('walkthrough.txt')
            elif kind == 'hash':
                notices['walkthrough.txt'] = b'X' + notices['walkthrough.txt'][1:]
            else:
                notices['walkthrough.txt'] += b'extra'
            self.package(notices)
            stage = self.root / kind
            with self.subTest(kind=kind), patch.object(bridge, 'recipe') as builder:
                with self.assertRaisesRegex(ValueError, 'notice.*(missing|hash|length)'):
                    service.build_one(self.row, {}, self.source, stage)
                builder.assert_not_called()
                self.assertFalse(stage.exists())

    def test_changed_zip_pin_is_rejected_before_output(self):
        self.source.write_bytes(self.source.read_bytes() + b'changed ZIP')
        with self.assertRaisesRegex(ValueError, 'original ZIP'):
            self.build(self.root / 'bad-zip')
        self.assertFalse((self.root / 'bad-zip').exists())

    def test_existing_notice_is_never_overwritten(self):
        stage = self.root / 'existing'
        stage.mkdir()
        existing = stage / 'walkthrough.txt'
        existing.write_bytes(b'Existing user data')
        with patch.object(bridge, 'recipe') as builder:
            with self.assertRaisesRegex(ValueError, 'notice output already exists'):
                service.build_one(self.row, {}, self.source, stage)
            builder.assert_not_called()
        self.assertEqual(existing.read_bytes(), b'Existing user data')
        self.assertEqual({p.name for p in stage.iterdir()}, {'walkthrough.txt'})

    def test_unsafe_reserved_and_duplicate_notice_targets_fail_before_output(self):
        original_rules = self.spec['original_notices']
        for index, name in enumerate(('../outside.txt', 'nested/notice.txt', 'README.txt',
                                      'blackwing-receipt.json', 'bridge-notice_fixture-rc1.goo',
                                      'bridge-notice_fixture_wbw_v1.goo',
                                      'bridge-notice_fixture_wbw_v1.manifest.json')):
            self.spec['original_notices'] = [{**original_rules[0], 'path': name}]
            stage = self.root / ('unsafe-' + str(index))
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.build(stage)
            self.assertFalse(stage.exists())
        self.spec['original_notices'] = [original_rules[0], original_rules[0]]
        with self.assertRaisesRegex(ValueError, 'duplicate original notice'):
            self.build(self.root / 'duplicate')
        self.assertFalse((self.root / 'duplicate').exists())


class PathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('jk', 'mots', 'originals', 'settings'):
            (self.root / name).mkdir()
        self.request = dict(ids=['canyon-oasis'], jk_root=str(self.root / 'jk'),
                            mots_root=str(self.root / 'mots'), output_dir=str(self.root / 'outputs'),
                            archive_dir=str(self.root / 'originals'), archives={})
        self.env = patch.dict(os.environ, {'BLACKWING_USER_DATA_DIR': str(self.root / 'settings')})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_output_protects_sources_ancestors_and_settings(self):
        for path in (self.root, self.root / 'jk/out', self.root / 'mots',
                     self.root / 'originals/out', self.root / 'settings/out',
                     Path(service.__file__).parent / 'outputs'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                service.validate_request({**self.request, 'output_dir': str(path)})
        self.assertEqual(service.validate_request(self.request)[0][0]['id'], 'canyon-oasis')

    def test_unselected_override_rejected_before_io(self):
        with self.assertRaises(ValueError):
            service.validate_request({**self.request, 'archives': {'jhs': 'not-used'}})

    def test_frozen_executable_folder_is_not_an_output_destination(self):
        application = self.root / 'downloaded-app'
        application.mkdir()
        with patch.object(sys, 'frozen', True, create=True), patch.object(sys, 'executable', str(application / 'WBW.exe')):
            with self.assertRaises(ValueError):
                service.validate_request({**self.request, 'output_dir': str(application / 'outputs')})

    def test_no_output_created_on_source_hash_failure(self):
        with patch.object(bridge, 'pinned_archives', side_effect=ValueError('bad hash')):
            with self.assertRaises(ValueError):
                service.convert_selected(self.request)
        self.assertFalse((self.root / 'outputs').exists())

    def test_mismatched_custom_original_stops_before_output(self):
        (self.root / 'originals/jhs.zip').write_bytes(b'not the reviewed original')
        with self.assertRaisesRegex(ValueError, 'not found'):
            service.convert_selected({**self.request, 'ids': ['jhs']})
        self.assertFalse((self.root / 'outputs').exists())

    def test_case_sensitive_installation_spelling(self):
        (self.root / 'jk/episode').mkdir()
        (self.root / 'jk/episode/jk1mp.gob').write_bytes(b'synthetic archive spelling fixture')
        self.assertEqual(bridge.owned_file(self.root / 'jk', 'Episode/JK1MP.GOB').name, 'jk1mp.gob')
        with self.assertRaises(bridge.RecipeError):
            bridge.owned_file(self.root / 'jk', '../jk/episode/jk1mp.gob')

    def test_original_replaced_during_build_cannot_publish_false_receipt(self):
        original = self.root / 'originals/jhs.zip'
        original.write_bytes(b'reviewed synthetic archive')
        def replacement_during_build(row, archives, original_path, stage):
            (stage / 'level.goo').write_bytes(b'synthetic output')
            original_path.write_bytes(b'replacement archive')
            return dict(filename='level.goo', manifest_filename='manifest.json', verification={})
        with patch.object(service, 'find_originals', return_value={'jhs': original}), \
                patch.object(bridge, 'pinned_archives', return_value={}), \
                patch.object(service, 'build_one', side_effect=replacement_during_build):
            results = service.convert_selected({**self.request, 'ids': ['jhs']})
        self.assertEqual(results[0]['status'], 'failed')
        self.assertIn('Original archive changed', results[0]['error'])
        self.assertEqual(list((self.root / 'outputs').iterdir()), [])

    def test_settings_persist_paths_only(self):
        result = service.save_settings({**self.request, 'token': 'must not persist'}, self.root / 'settings')
        self.assertEqual(set(result), set(service.PATH_KEYS))
        self.assertEqual(result, service.load_settings(self.root / 'settings'))
        self.assertNotIn('token', (self.root / 'settings/settings.json').read_text())

    def test_default_output_is_separate_and_does_not_create_folders(self):
        with patch.object(service.Path, 'home', return_value=self.root / 'home'):
            settings = service.normalize_settings({})
        self.assertEqual(settings['output_dir'], str(self.root / 'home/Documents/World Between Worlds conversions'))
        self.assertFalse((self.root / 'home').exists())
        with patch.object(service.Path, 'home', return_value=self.root / 'home'):
            _, paths, _ = service.validate_request({**self.request, 'output_dir': ''})
        self.assertEqual(paths['output_dir'], self.root / 'home/Documents/World Between Worlds conversions')
        self.assertFalse(paths['output_dir'].exists())

    def test_picker_validates_original_recipe_and_preserves_cancellation(self):
        with patch.object(service.blackwing_picker, 'pick_path', return_value=None) as picker:
            for value in ({'kind': 'unknown'}, {'kind': 'original_archive'},
                          {'kind': 'original_archive', 'recipe_id': 'canyon-oasis'}):
                with self.assertRaises(ValueError):
                    service.pick_local_path(value, self.root / 'settings')
            picker.assert_not_called()
            self.assertEqual(service.pick_local_path({'kind': 'original_archive', 'recipe_id': 'jhs'},
                                                    self.root / 'settings'), {'path': None})
            picker.assert_called_once_with('original_archive', initial_path=None)
        self.assertFalse((self.root / 'settings/settings.json').exists())

    def test_tracking_is_identical_across_staging_directories(self):
        from gob import build_gob
        results = []
        row = catalog.selection(['canyon-oasis'])[0]
        for name in ('random-stage-a', 'different-stage-b'):
            stage = self.root / name
            stage.mkdir()
            (stage / 'bridge-canyon-v1.goo').write_bytes(build_gob({'test.txt': b'inert original test data'}))
            (stage / 'payload.json').write_text('{}')
            (stage / 'README.txt').write_text('Use -episode bridge-canyon-v1\n', encoding='utf-8')
            service.track_outputs(row, stage,
                {'filename': 'bridge-canyon-v1.goo', 'manifest_filename': 'payload.json',
                 'verification': {'passed': True}}, {'recipe_sha256': 'a' * 64})
            results.append(service.tree_hashes(stage))
        self.assertEqual(results[0], results[1])

    def test_tracking_preserves_game_payload_original_readme_and_startup_folder(self):
        import blackwing_revisions as revisions
        from gob import build_gob, Gob
        stage = self.root / 'stage'
        folder = stage / 'blackwing-ninja-kage'
        folder.mkdir(parents=True)
        payload = build_gob({'cog/test.cog': b'synthetic inert test', 'misc/test.dat': b'values'})
        (folder / 'blackwing-ninja-kage.goo').write_bytes(payload)
        (folder / 'source.manifest.json').write_text('{"original":true}')
        original_readme = b'Original author text \xff\xfe blackwing-ninja-kage'
        (folder / 'ORIGINAL-NINJA-KAGE.txt').write_bytes(original_readme)
        (folder / 'README.txt').write_text('Use -path blackwing-ninja-kage\nFile: blackwing-ninja-kage.goo\n', encoding='utf-8')
        row = catalog.selection(['ninja-kage'])[0]
        result = service.track_outputs(row, stage,
            {'filename': 'blackwing-ninja-kage/blackwing-ninja-kage.goo',
             'manifest_filename': 'blackwing-ninja-kage/source.manifest.json',
             'verification': {'passed': True}, 'startup_overlay': 'blackwing-ninja-kage'},
            {'recipe_sha256': 'a' * 64})
        self.assertEqual(result['filename'], 'blackwing-ninja-kage/blackwing-ninja-kage_wbw_v1.goo')
        generated = Gob.open(stage / result['filename'])
        for name in Gob(payload).entries:
            self.assertEqual(generated.read(name), Gob(payload).read(name))
        metadata = revisions.validate_archive(generated.data)
        self.assertEqual(metadata['payload_sha256'], hashlib.sha256(payload).hexdigest())
        self.assertEqual((folder / 'ORIGINAL-NINJA-KAGE.txt').read_bytes(), original_readme)
        instructions = (folder / 'README.txt').read_text()
        self.assertIn('-path blackwing-ninja-kage\n', instructions)
        self.assertIn('File: blackwing-ninja-kage_wbw_v1.goo', instructions)
        self.assertEqual(json.loads((folder / 'source.manifest.json').read_text()), {'original': True})
        self.assertEqual(result['startup_overlay'], 'blackwing-ninja-kage')

    def test_scan_needs_only_explicit_mots_folder_and_never_builds(self):
        with patch.object(service, 'build_one', side_effect=AssertionError('no conversion')):
            result = service.scan_installed({'mots_root': str(self.root / 'mots')})
        self.assertEqual(result['results'], [])
        for value in (None, {}, {'mots_root': 'relative'}):
            with self.assertRaises(ValueError):
                service.scan_installed(value)


class RejectedPostBodyTests(unittest.TestCase):
    def handler(self, headers):
        handler = blackwing_app.Handler.__new__(blackwing_app.Handler)
        handler.command = 'POST'
        handler.headers = Message()
        for name, value in headers:
            handler.headers[name] = value
        handler.connection = Mock()
        handler.connection.gettimeout.return_value = 7.0
        handler.rfile = Mock()
        return handler

    def test_ambiguous_invalid_and_oversized_framing_reads_nothing(self):
        frames = [[], [('Content-Length', '')], [('Content-Length', '-1')],
                  [('Content-Length', '+2')], [('Content-Length', '1.0')],
                  [('Content-Length', '2, 2')], [('Content-Length', '\u0662')],
                  [('Content-Length', str(blackwing_app.MAX_REQUEST + 1))],
                  [('Content-Length', '2'), ('Content-Length', '2')],
                  [('Content-Length', '2'), ('Content-Length', '3')],
                  [('Content-Length', '2'), ('Transfer-Encoding', 'chunked')],
                  [('Content-Length', '2'), ('Transfer-Encoding', '')]]
        for headers in frames:
            with self.subTest(headers=headers):
                handler = self.handler(headers)
                handler.send_response = Mock()
                handler.send_header = Mock()
                handler.end_headers = Mock()
                handler.wfile = io.BytesIO()
                handler.reply(403, {'error': 'Rejected'})
                handler.rfile.read1.assert_not_called()
                handler.rfile.read.assert_not_called()
                handler.connection.gettimeout.assert_not_called()
                self.assertTrue(handler.close_connection)
                handler.send_header.assert_any_call('Connection', 'close')
                self.assertEqual(json.loads(handler.wfile.getvalue()), {'error': 'Rejected'})

    def test_trickling_body_cannot_extend_total_deadline(self):
        handler = self.handler([('Content-Length', '20')])
        handler.rfile.read1.return_value = b'x'
        with patch.object(blackwing_app, 'REJECT_BODY_TIMEOUT', 0.5), \
                patch.object(blackwing_app.time, 'monotonic', side_effect=[0, 0, .2, .4, .6]):
            handler.discard_rejected_post()
        self.assertEqual(handler.rfile.read1.call_count, 3)
        actual = [call.args[0] for call in handler.connection.settimeout.call_args_list]
        for value, expected in zip(actual, [.5, .3, .1, 7.0], strict=True):
            self.assertAlmostEqual(value, expected)
        handler.rfile.read.assert_not_called()

    def test_discard_is_size_bounded_and_not_repeated(self):
        handler = self.handler([('Content-Length', str(blackwing_app.MAX_REQUEST))])
        handler.rfile.read1.side_effect = lambda count: b'x' * count
        with patch.object(blackwing_app.time, 'monotonic', return_value=0):
            handler.discard_rejected_post()
            handler.discard_rejected_post()
        counts = [call.args[0] for call in handler.rfile.read1.call_args_list]
        self.assertEqual(sum(counts), blackwing_app.MAX_REQUEST)
        self.assertLessEqual(max(counts), 16 * 1024)
        handler.connection.settimeout.assert_called_with(7.0)
        empty = self.handler([('Content-Length', '0')])
        empty.discard_rejected_post()
        empty.rfile.read1.assert_not_called()

    def test_eof_and_timeout_restore_socket_timeout(self):
        for end in (b'', TimeoutError('slow body'), ConnectionResetError('closed peer')):
            with self.subTest(end=end):
                handler = self.handler([('Content-Length', '2')])
                handler.rfile.read1.side_effect = [end]
                handler.discard_rejected_post()
                handler.rfile.read1.assert_called_once_with(2)
                handler.connection.settimeout.assert_called_with(7.0)

    def test_malformed_json_is_not_drained_twice(self):
        handler = self.handler([('Content-Type', 'application/json'), ('Content-Length', '3')])
        handler.rfile.read.return_value = b'bad'
        with self.assertRaises(json.JSONDecodeError):
            handler.read_json()
        handler.discard_rejected_post()
        handler.rfile.read.assert_called_once_with(3)
        handler.rfile.read1.assert_not_called()


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.server = blackwing_app.BlackwingServer(('127.0.0.1', 0), data_dir=Path(cls.temp.name))
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join()
        cls.temp.cleanup()

    def request(self, path, *, token=True, method='GET', body=None, headers=None):
        fields = {'X-Blackwing-Token': self.server.token} if token else {}
        if body is not None:
            fields['Content-Type'] = 'application/json'
            body = json.dumps(body)
        fields.update(headers or {})
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        connection.request(method, path, body=body, headers=fields)
        response = connection.getresponse()
        result = response.status, response.read(), dict(response.getheaders())
        connection.close()
        return result

    def test_local_index_injects_current_token_and_csp(self):
        code, body, headers = self.request('/', token=False)
        self.assertEqual(code, 200)
        self.assertIn(self.server.token.encode(), body)
        self.assertNotIn(b'{{TOKEN}}', body)
        self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])

    def test_private_api_requires_token(self):
        for path in ('/api/settings', '/api/catalog', '/api/recipes/jhs'):
            self.assertEqual(self.request(path, token=False)[0], 403)

    def test_cross_origin_and_dns_rebinding_rejected_even_with_token(self):
        for headers in ({'Origin': 'https://example.com'}, {'Host': 'evil.example'},
                        {'Sec-Fetch-Site': 'cross-site'}):
            self.assertEqual(self.request('/api/settings', headers=headers)[0], 403)

    def test_delayed_rejected_post_bodies_receive_complete_403_without_callbacks(self):
        # Headers and body are distinct writes in http.client. A small delay
        # reproduces the early-close WinError 10053 without a retry loop.
        body = b'not valid JSON'
        variants = ({}, {'X-Blackwing-Token': 'wrong'},
                    {'X-Blackwing-Token': self.server.token, 'Host': 'evil.example'},
                    {'X-Blackwing-Token': self.server.token, 'Origin': 'https://example.com'},
                    {'X-Blackwing-Token': self.server.token, 'Sec-Fetch-Site': 'cross-site'})
        with patch.object(blackwing_app.Handler, 'read_json', side_effect=AssertionError('must not parse')) as parser, \
                patch.object(service, 'scan_installed') as scan, \
                patch.object(service, 'save_settings') as save, \
                patch.object(service, 'pick_local_path') as picker, \
                patch.object(self.server.jobs, 'start') as job:
            for repeat in range(3):
                for path in ('/api/scan', '/api/settings', '/api/pick-path', '/api/convert'):
                    for variant in variants:
                        with self.subTest(repeat=repeat, path=path, headers=variant):
                            connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
                            try:
                                fields = {'Host': '127.0.0.1:' + str(self.server.server_port),
                                          'Content-Type': 'application/json', 'Content-Length': str(len(body)),
                                          **variant}
                                connection.putrequest('POST', path, skip_host=True)
                                for name, value in fields.items():
                                    connection.putheader(name, value)
                                connection.endheaders()
                                time.sleep(.01)
                                connection.send(body)
                                response = connection.getresponse()
                                self.assertEqual(response.status, 403)
                                self.assertEqual(response.getheader('Connection'), 'close')
                                self.assertTrue(json.loads(response.read())['error'])
                            finally:
                                connection.close()
            for callback in (parser, scan, save, picker, job):
                callback.assert_not_called()

    def test_rejected_incomplete_body_has_bounded_wait_and_no_scan(self):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        try:
            with patch.object(service, 'scan_installed') as scan:
                connection.putrequest('POST', '/api/scan')
                connection.putheader('Content-Length', '2')
                connection.putheader('Content-Type', 'application/json')
                connection.endheaders()
                # No body is sent. The rejection must finish on its receive
                # deadline rather than waiting indefinitely for two bytes.
                response = connection.getresponse()
                self.assertEqual(response.status, 403)
                self.assertTrue(json.loads(response.read())['error'])
                scan.assert_not_called()
        finally:
            connection.close()

    def test_cannot_retrieve_source_or_absolute_files(self):
        for path in ('/bridge.py', '/../bridge.py', '/docs/../bridge.py', '/docs/settings.json'):
            self.assertEqual(self.request(path)[0], 404)

    def test_packaged_ninja_documentation_references_external_evidence(self):
        import ninja_catalog
        source_root = blackwing_app.ROOT
        with tempfile.TemporaryDirectory() as temp:
            packaged = Path(temp)
            for name in ('NINJA_KAGE.md', 'VALIDATION.md'):
                (packaged / name).write_bytes((source_root / name).read_bytes())
            # A frozen app contains these Markdown files, but no repository
            # validation tree. Exercise that exact layout over the real API.
            with patch.object(blackwing_app, 'ROOT', packaged):
                for name in ('NINJA_KAGE.md', 'VALIDATION.md'):
                    code, body, headers = self.request('/docs/' + name)
                    self.assertEqual(code, 200)
                    self.assertEqual(headers['Content-Type'], 'text/plain; charset=utf-8')
                    self.assertEqual(body, (packaged / name).read_bytes())
                    self.assertIn(ninja_catalog.RUNTIME_TEST['evidence']['url'].encode(), body)
                for path in ('/docs/validation/ninja-maxmana-20260908.json',
                             '/docs/docs/validation/ninja-maxmana-20260908.json'):
                    self.assertEqual(self.request(path)[0], 404)

    def test_export_selected_only_and_reject_empty(self):
        code, body, _ = self.request('/api/export', method='POST', body={'ids': ['jhs']})
        self.assertEqual(code, 200)
        self.assertEqual([row['entry']['id'] for row in json.loads(body)['recipes']], ['jhs'])
        self.assertEqual(self.request('/api/export', method='POST', body={'ids': []})[0], 400)

    def test_settings_survive_round_trip_and_not_arbitrary_keys(self):
        code, _, _ = self.request('/api/settings', method='POST', body={'jk_root': '/user/jk', 'secret': 'no'})
        self.assertEqual(code, 200)
        data = json.loads(self.request('/api/settings')[1])
        self.assertEqual(data['jk_root'], '/user/jk')
        self.assertNotIn('secret', data)

    def test_installation_scan_is_authenticated_explicit_read_only(self):
        request = {'mots_root': self.temp.name}
        self.assertEqual(self.request('/api/scan', token=False, method='POST', body=request)[0], 403)
        self.assertEqual(self.request('/api/scan', method='POST', body={})[0], 400)
        self.assertEqual(self.request('/api/scan', method='POST', body=request,
                                      headers={'Origin': 'https://example.com'})[0], 403)
        with patch.object(service, 'convert_selected', side_effect=AssertionError('must not convert')):
            code, body, _ = self.request('/api/scan', method='POST', body=request)
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)['results'], [])

    def test_picker_endpoint_requires_current_window_and_never_saves_selection(self):
        value = {'kind': 'jk_root'}
        before = service.load_settings(self.server.data_dir)
        with patch.object(service.blackwing_picker, 'pick_path', return_value=self.temp.name) as picker:
            self.assertEqual(self.request('/api/pick-path', token=False, method='POST', body=value)[0], 403)
            self.assertEqual(self.request('/api/pick-path', method='POST', body=value,
                                          headers={'Origin': 'https://example.com'})[0], 403)
            picker.assert_not_called()
            code, body, _ = self.request('/api/pick-path', method='POST', body=value)
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body), {'path': self.temp.name})
        self.assertEqual(before, service.load_settings(self.server.data_dir))

    def test_frozen_picker_dispatch_precedes_updater_and_server(self):
        import blackwing_launcher
        with patch.object(service.blackwing_picker, 'helper_main', return_value=0) as helper, \
                patch.object(blackwing_launcher.updates, 'user_data_dir', side_effect=AssertionError('no updater')):
            args = ['jk_root', '--result-file', str(Path(self.temp.name) / 'result.json')]
            self.assertEqual(blackwing_launcher.main(['--pick-path-helper', *args]), 0)
            helper.assert_called_once_with(args)


if __name__ == '__main__':
    unittest.main()

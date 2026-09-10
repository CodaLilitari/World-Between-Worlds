"""Chooser tests use fake dialogs/processes only; no real chooser is opened."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock
import importlib.util
import io
import json
import os
import subprocess
import sys
import unittest

import blackwing_picker as picker


def encoded(status='selected', path=None, **fields):
    return json.dumps(dict(schema=1, status=status, path=path, **fields),
                      ensure_ascii=False).encode('utf-8')


class ParentPickerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory(prefix='wbw-picker-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.chosen = str(self.root / 'Jedi Knight — 星.zip')

    def child(self, payload, *, returncode=0, capture=None):
        def run(command, **options):
            self.assertIsInstance(command, list)
            self.assertFalse(options['shell'])
            self.assertEqual(options['stdin'], subprocess.DEVNULL)
            self.assertEqual(options['stdout'], subprocess.DEVNULL)
            self.assertEqual(options['stderr'], subprocess.DEVNULL)
            result = Path(command[command.index('--result-file') + 1])
            self.assertTrue(result.is_absolute())
            self.assertFalse(result.exists())
            result.write_bytes(payload)
            if capture is not None:
                capture.append((command, options, result))
            return SimpleNamespace(returncode=returncode)
        return run

    def test_import_does_not_open_a_dialog_or_launch_a_helper(self):
        with mock.patch.object(picker.subprocess, 'run') as process:
            spec = importlib.util.spec_from_file_location('wbw_picker_import_test', picker.__file__)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        process.assert_not_called()

    def test_single_unicode_file_selection_uses_argv_and_removes_private_response(self):
        capture = []
        initial = str(self.root / 'maps ; $(ignored) — 星')
        with mock.patch.object(picker.subprocess, 'run', side_effect=self.child(
                encoded(path=self.chosen), capture=capture)):
            result = picker.pick_path('original_archive', initial)
        self.assertEqual(result, self.chosen)
        command, _, result_file = capture[0]
        self.assertEqual(command[command.index('--initial-path') + 1], initial)
        self.assertNotIn('$(ignored)', command[0])
        self.assertFalse(result_file.exists())
        self.assertFalse(result_file.parent.exists())
        self.assertFalse(Path(self.chosen).exists())  # The chooser did not read/create an archive.

    def test_cancel_returns_none(self):
        with mock.patch.object(picker.subprocess, 'run', side_effect=self.child(encoded('cancelled'))):
            self.assertIsNone(picker.pick_path('mots_root'))

    def test_all_folder_kinds_return_one_string(self):
        for kind in picker.KINDS:
            if kind == 'original_archive':
                continue
            with self.subTest(kind=kind), mock.patch.object(
                    picker.subprocess, 'run', side_effect=self.child(encoded(path=str(self.root)))):
                self.assertEqual(picker.pick_path(kind), str(self.root))

    def test_original_filter_rejects_converted_goo_and_non_single_results(self):
        for path in (str(self.root / 'converted.goo'), [self.chosen], 'relative.zip', ''):
            with self.subTest(path=path), mock.patch.object(picker.subprocess, 'run',
                    side_effect=self.child(encoded(path=path))):
                with self.assertRaises(picker.PickerError):
                    picker.pick_path('original_archive')

    def test_invalid_kind_or_initial_data_never_launches(self):
        with mock.patch.object(picker.subprocess, 'run') as process:
            for kind, initial in [('anything', None), ('mots_root', ['not a path']),
                                  ('mots_root', 'bad\0path')]:
                with self.assertRaises(picker.PickerError):
                    picker.pick_path(kind, initial)
        process.assert_not_called()

    def test_relative_initial_path_is_omitted_and_file_initial_uses_its_parent(self):
        capture = []
        with mock.patch.object(picker.subprocess, 'run', side_effect=self.child(
                encoded('cancelled'), capture=capture)):
            picker.pick_path('mots_root', 'unfinished relative path')
            picker.pick_path('original_archive', self.chosen)
        self.assertNotIn('--initial-path', capture[0][0])
        second = capture[1][0]
        self.assertEqual(second[second.index('--initial-path') + 1], str(self.root))

    def test_only_one_picker_can_run_and_failure_releases_lock(self):
        picker._PICKER_LOCK.acquire()
        try:
            with mock.patch.object(picker.subprocess, 'run') as process:
                with self.assertRaisesRegex(picker.PickerError, 'already open'):
                    picker.pick_path('mots_root')
                process.assert_not_called()
        finally:
            picker._PICKER_LOCK.release()
        with mock.patch.object(picker.subprocess, 'run', side_effect=OSError('fake unavailable process')):
            with self.assertRaisesRegex(picker.PickerError, 'could not start'):
                picker.pick_path('mots_root')
        self.assertTrue(picker._PICKER_LOCK.acquire(blocking=False))
        picker._PICKER_LOCK.release()

    def test_helper_errors_missing_malformed_oversized_and_failed_exit_are_clear(self):
        cases = [(b'{', 0), (b'[]', 0), (b'x' * (picker.MAX_RESULT_BYTES + 1), 0),
                 (encoded('error', message='No desktop available. Enter a path manually.'), 2),
                 (encoded(path=self.chosen), 2)]
        for payload, returncode in cases:
            with self.subTest(payload=payload[:40]), mock.patch.object(picker.subprocess, 'run',
                    side_effect=self.child(payload, returncode=returncode)):
                with self.assertRaises(picker.PickerError):
                    picker.pick_path('original_archive')
        with mock.patch.object(picker.subprocess, 'run', return_value=SimpleNamespace(returncode=2)):
            with self.assertRaisesRegex(picker.PickerError, 'could not complete'):
                picker.pick_path('mots_root')

    def test_frozen_command_uses_launcher_helper_route(self):
        with mock.patch.object(picker.sys, 'frozen', True, create=True):
            command = picker._helper_command('mots_root', str(self.root), self.root / 'result.json')
        self.assertEqual(command[:3], [sys.executable, '--pick-path-helper', 'mots_root'])
        self.assertNotIn(picker.__file__, command)


class HelperPickerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory(prefix='wbw-picker-helper-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_helper_writes_utf8_json_without_stdout_in_windowed_build(self):
        target = self.root / 'result.json'
        chosen = str(self.root / '星 — Maps')
        with mock.patch.object(picker, '_choose', return_value=chosen) as choose, mock.patch.object(
                picker.sys, 'stdout', None):
            result = picker.helper_main(['mots_root', '--result-file', str(target)])
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(target.read_text(encoding='utf-8'))['path'], chosen)
        choose.assert_called_once_with('mots_root', None)

    def test_helper_cancel_and_error_protocol(self):
        for selection, status, code in [(None, 'cancelled', 0),
                                         (picker.PickerError('Manual path required.'), 'error', 2)]:
            target = self.root / (status + '.json')
            patch = mock.patch.object(picker, '_choose', side_effect=selection) if isinstance(
                selection, Exception) else mock.patch.object(picker, '_choose', return_value=selection)
            with patch:
                self.assertEqual(picker.helper_main(['mots_root', '--result-file', str(target)]), code)
            self.assertEqual(json.loads(target.read_text())['status'], status)

    def test_invalid_output_path_is_rejected_before_dialog_and_existing_file_preserved(self):
        target = self.root / 'existing.json'
        target.write_bytes(b'preserve')
        with mock.patch.object(picker, '_choose') as choose:
            self.assertEqual(picker.helper_main(['mots_root', '--result-file', str(target)]), 2)
            self.assertEqual(picker.helper_main(['mots_root', '--result-file', 'relative.json']), 2)
        choose.assert_not_called()
        self.assertEqual(target.read_bytes(), b'preserve')

    def test_helper_optional_stdout_protocol_uses_mock_only(self):
        output = io.StringIO()
        with mock.patch.object(picker, '_choose', return_value=None), mock.patch.object(picker.sys, 'stdout', output):
            self.assertEqual(picker.helper_main(['mots_root']), 0)
        self.assertEqual(json.loads(output.getvalue())['status'], 'cancelled')

    def test_tk_dialog_is_single_file_filtered_and_hidden_root_is_destroyed(self):
        root = mock.Mock()
        tk = SimpleNamespace(Tk=mock.Mock(return_value=root), TclError=RuntimeError)
        dialogs = SimpleNamespace(askopenfilename=mock.Mock(return_value=str(self.root / 'original.zip')),
                                  askdirectory=mock.Mock(return_value=str(self.root)))
        tk.filedialog = dialogs
        with mock.patch.dict(sys.modules, {'tkinter': tk, 'tkinter.filedialog': dialogs}):
            self.assertEqual(picker._pick_with_tk('original_archive', str(self.root)), str(self.root / 'original.zip'))
            root.withdraw.assert_called_once()
            root.destroy.assert_called_once()
            options = dialogs.askopenfilename.call_args.kwargs
            self.assertNotIn('multiple', options)
            self.assertIn('*.zip', options['filetypes'][0][1])
            self.assertIn('*.gob', options['filetypes'][0][1])
            self.assertNotIn('*.goo', options['filetypes'][0][1])
            self.assertEqual(options['initialdir'], str(self.root))

    def test_tk_directory_picker_allows_creating_output_folder_only(self):
        root = mock.Mock()
        dialogs = SimpleNamespace(askdirectory=mock.Mock(return_value=str(self.root)))
        tk = SimpleNamespace(Tk=mock.Mock(return_value=root), TclError=RuntimeError, filedialog=dialogs)
        with mock.patch.dict(sys.modules, {'tkinter': tk, 'tkinter.filedialog': dialogs}):
            picker._pick_with_tk('mots_root', None)
            self.assertTrue(dialogs.askdirectory.call_args.kwargs['mustexist'])
            picker._pick_with_tk('output_dir', None)
            self.assertFalse(dialogs.askdirectory.call_args.kwargs['mustexist'])

    def test_tk_unavailable_uses_fallback_and_headless_fails_with_manual_path(self):
        with mock.patch.object(picker, '_pick_with_tk', side_effect=picker._Unavailable()), mock.patch.object(
                picker, '_pick_with_windows', side_effect=picker._Unavailable()), mock.patch.object(
                picker, '_pick_with_linux', side_effect=picker._Unavailable()):
            with self.assertRaisesRegex(picker.PickerError, 'Enter the local path manually'):
                picker._choose('mots_root', None)
        with mock.patch.dict(picker.os.environ, {}, clear=True), mock.patch.object(picker.subprocess, 'run') as run:
            with self.assertRaises(picker._Unavailable):
                picker._pick_with_linux('mots_root', None)
            run.assert_not_called()

    def test_windows_fallback_keeps_user_path_out_of_script(self):
        initial = str(self.root / 'maps ; $(not executed) — 星')
        with mock.patch.object(picker.shutil, 'which', return_value='powershell.exe'), mock.patch.object(
                picker.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=encoded(path=str(self.root)))) as run:
            self.assertEqual(picker._pick_with_windows('mots_root', initial), str(self.root))
        command = run.call_args.args[0]
        self.assertEqual(command[-1], picker._WINDOWS_SCRIPT)
        self.assertNotIn(initial, command[-1])
        self.assertFalse(run.call_args.kwargs['shell'])
        self.assertEqual(run.call_args.kwargs['env']['WBW_PICKER_INITIAL'], initial)
        self.assertIn('-STA', command)
        self.assertIn('$dialog.Multiselect = $false', picker._WINDOWS_SCRIPT)

    def test_linux_zenity_and_kdialog_use_single_selection_argument_arrays(self):
        for backend in ('zenity', 'kdialog'):
            with self.subTest(backend=backend), mock.patch.dict(picker.os.environ, {'DISPLAY': ':fake'}), mock.patch.object(
                    picker.shutil, 'which', side_effect=lambda executable: executable if executable == backend else None), mock.patch.object(
                    picker.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=(str(self.root / 'original.GOB') + '\n').encode(), stderr=b'')) as run:
                self.assertEqual(picker._pick_with_linux('original_archive', str(self.root)), str(self.root / 'original.GOB'))
            self.assertIsInstance(run.call_args.args[0], list)
            self.assertNotIn('--multiple', run.call_args.args[0])
            self.assertFalse(run.call_args.kwargs['shell'])

    def test_linux_cancel_and_backend_error_use_fake_processes(self):
        with mock.patch.dict(picker.os.environ, {'DISPLAY': ':fake'}), mock.patch.object(picker.shutil, 'which', return_value='zenity'):
            with mock.patch.object(picker.subprocess, 'run', return_value=SimpleNamespace(returncode=1, stdout=b'', stderr=b'optional theme warning')):
                self.assertIsNone(picker._pick_with_linux('mots_root', None))
            with mock.patch.object(picker.subprocess, 'run', return_value=SimpleNamespace(returncode=2, stdout=b'', stderr=b'failed')):
                with self.assertRaises(picker._Unavailable):
                    picker._pick_with_linux('mots_root', None)


if __name__ == '__main__':
    unittest.main()

"""User-invoked native path selection, isolated from the workbench HTTP thread.

The desktop dialog runs in a helper's main thread. Only its selected path comes
back; this module never reads archive contents, enumerates user directories,
captures the desktop, uploads files, or opens a chooser during import.
"""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading


KINDS = ('jk_root', 'mots_root', 'archive_dir', 'output_dir', 'original_archive')
TITLES = {
    'jk_root': 'Choose your Jedi Knight installation folder',
    'mots_root': 'Choose your Mysteries of the Sith installation folder',
    'archive_dir': 'Choose your original custom-map and mod archive folder',
    'output_dir': 'Choose where World Between Worlds saves conversions',
    'original_archive': 'Choose one original map or mod ZIP or GOB',
}
MAX_RESULT_BYTES = 16_384
_PICKER_LOCK = threading.Lock()


class PickerError(RuntimeError):
    """A path could not be chosen; typing a local path remains available."""


class _Unavailable(PickerError):
    pass


def _initial_directory(kind, value):
    if value is None or value == '':
        return None
    if not isinstance(value, str) or len(value) > 4096 or '\0' in value:
        raise PickerError('Invalid initial folder. Clear it and browse again, or enter a local path.')
    path = Path(value).expanduser()
    if not path.is_absolute():
        return None
    if kind == 'original_archive' and path.suffix.lower() in {'.zip', '.gob'}:
        path = path.parent
    return str(path)


def _selected_path(kind, value):
    if value is None or value == '':
        return None
    if (not isinstance(value, str) or len(value) > 4096 or '\0' in value
            or not Path(value).is_absolute()):
        raise PickerError('The chooser returned an invalid path. Enter the local path manually.')
    if kind == 'original_archive' and Path(value).suffix.lower() not in {'.zip', '.gob'}:
        raise PickerError('Choose one original .zip or .gob archive. Converted .goo files are not original inputs.')
    return value


def _process_options():
    return {'creationflags': getattr(subprocess, 'CREATE_NO_WINDOW', 0)} if os.name == 'nt' else {}


def _helper_command(kind, initial, result_file):
    if getattr(sys, 'frozen', False):
        command = [sys.executable, '--pick-path-helper', kind]
    else:
        command = [sys.executable, '-B', str(Path(__file__).resolve()), '--helper', kind]
    if initial is not None:
        command += ['--initial-path', initial]
    return command + ['--result-file', str(result_file)]


def _decode_result(raw, kind):
    if len(raw) > MAX_RESULT_BYTES:
        raise PickerError('The chooser response was too large. Enter a local path manually.')
    try:
        result = json.loads(raw.decode('utf-8-sig'))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise PickerError('The chooser did not return a valid result. Enter a local path manually.') from exc
    if not isinstance(result, dict) or type(result.get('schema')) is not int or result['schema'] != 1:
        raise PickerError('The chooser returned an unsupported result. Enter a local path manually.')
    if result.get('status') == 'cancelled' and result.get('path') is None:
        return None
    if result.get('status') == 'selected':
        selected = _selected_path(kind, result.get('path'))
        if selected is not None:
            return selected
    if result.get('status') == 'error':
        message = result.get('message')
        if isinstance(message, str) and 0 < len(message) <= 1024:
            raise PickerError(message)
    raise PickerError('The chooser failed. Enter the local path manually.')


def pick_path(kind, initial_path=None):
    """Open exactly one explicitly requested chooser; return its path or None.

    No UI appears until this function is called. It is safe to invoke from an
    HTTP worker thread: Tk/native GUI work is delegated to the child main thread.
    A private result file also works with frozen executables without stdout.
    """
    if kind not in KINDS:
        raise PickerError('Unsupported path chooser.')
    initial = _initial_directory(kind, initial_path)
    if not _PICKER_LOCK.acquire(blocking=False):
        raise PickerError('A file chooser is already open. Finish or cancel it before opening another.')
    try:
        with tempfile.TemporaryDirectory(prefix='wbw-picker-') as temporary:
            result_file = Path(temporary) / 'result.json'
            command = _helper_command(kind, initial, result_file)
            try:
                completed = subprocess.run(command, stdin=subprocess.DEVNULL,
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                           check=False, shell=False, **_process_options())
            except OSError as exc:
                raise PickerError('The native chooser could not start. Enter the local path manually.') from exc
            if not result_file.is_file():
                raise PickerError('The native chooser could not complete. Enter the local path manually.')
            with result_file.open('rb') as stream:
                raw = stream.read(MAX_RESULT_BYTES + 1)
            selected = _decode_result(raw, kind)
            if completed.returncode != 0:
                raise PickerError('The native chooser exited unexpectedly. Enter the local path manually.')
            return selected
    except OSError as exc:
        raise PickerError('The chooser could not exchange its local result. Enter the local path manually.') from exc
    finally:
        _PICKER_LOCK.release()


def _pick_with_tk(kind, initial):
    """Importing Tk is harmless; only the child creates its root/dialog."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError as exc:
        raise _Unavailable('Tk is unavailable.') from exc
    root = None
    try:
        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes('-topmost', True)
        except tk.TclError:
            pass
        options = {'parent': root, 'title': TITLES[kind]}
        if initial is not None:
            options['initialdir'] = initial
        if kind == 'original_archive':
            selected = filedialog.askopenfilename(
                **options, filetypes=[('Original archives', '*.zip *.ZIP *.gob *.GOB')])
        else:
            selected = filedialog.askdirectory(**options, mustexist=kind != 'output_dir')
        return _selected_path(kind, selected)
    except tk.TclError as exc:
        raise _Unavailable('Tk could not connect to the desktop.') from exc
    finally:
        if root is not None:
            try:
                root.destroy()
            except tk.TclError:
                pass


# This script is fixed application code. All user path data is supplied through
# environment variables, never interpolated into PowerShell source.
_WINDOWS_SCRIPT = r'''
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Application]::EnableVisualStyles()
$dialog = $null
try {
    if ($env:WBW_PICKER_KIND -eq 'original_archive') {
        $dialog = New-Object System.Windows.Forms.OpenFileDialog
        $dialog.Title = $env:WBW_PICKER_TITLE
        $dialog.Filter = 'Original archives (*.zip;*.gob)|*.zip;*.gob'
        $dialog.Multiselect = $false
        $dialog.CheckFileExists = $true
        if ($env:WBW_PICKER_INITIAL) { $dialog.InitialDirectory = $env:WBW_PICKER_INITIAL }
    } else {
        $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
        $dialog.Description = $env:WBW_PICKER_TITLE
        $dialog.ShowNewFolderButton = ($env:WBW_PICKER_KIND -eq 'output_dir')
        if ($env:WBW_PICKER_INITIAL) { $dialog.SelectedPath = $env:WBW_PICKER_INITIAL }
    }
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $chosen = if ($env:WBW_PICKER_KIND -eq 'original_archive') { $dialog.FileName } else { $dialog.SelectedPath }
        $result = @{schema=1;status='selected';path=$chosen}
    } else { $result = @{schema=1;status='cancelled';path=$null} }
    [Console]::Out.Write(($result | ConvertTo-Json -Compress))
} finally { if ($null -ne $dialog) { $dialog.Dispose() } }
'''


def _pick_with_windows(kind, initial):
    executable = shutil.which('powershell.exe')
    if executable is None:
        raise _Unavailable('The Windows native dialog fallback is unavailable.')
    environment = dict(os.environ, WBW_PICKER_KIND=kind, WBW_PICKER_TITLE=TITLES[kind],
                       WBW_PICKER_INITIAL=initial or '')
    try:
        result = subprocess.run([executable, '-NoProfile', '-NonInteractive', '-STA',
                                 '-Command', _WINDOWS_SCRIPT], env=environment,
                                stdin=subprocess.DEVNULL, capture_output=True, check=False,
                                shell=False, **_process_options())
    except OSError as exc:
        raise _Unavailable('The Windows native dialog could not start.') from exc
    if result.returncode != 0:
        raise _Unavailable('The Windows native dialog could not connect to the desktop.')
    return _decode_result(result.stdout, kind)


def _pick_with_linux(kind, initial):
    if not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY'):
        raise _Unavailable('No graphical desktop session is available.')
    zenity, kdialog = shutil.which('zenity'), shutil.which('kdialog')
    if zenity:
        command = [zenity, '--file-selection', '--title=' + TITLES[kind]]
        if initial is not None:
            command += ['--filename=' + initial.rstrip('/') + '/']
        if kind == 'original_archive':
            command += ['--file-filter=Original archives | *.zip *.ZIP *.gob *.GOB']
        else:
            command += ['--directory']
    elif kdialog:
        command = [kdialog, '--title', TITLES[kind]]
        if kind == 'original_archive':
            command += ['--getopenfilename', initial or os.path.expanduser('~'),
                        '*.zip *.ZIP *.gob *.GOB|Original archives (*.zip *.gob)']
        else:
            command += ['--getexistingdirectory', initial or os.path.expanduser('~')]
    else:
        raise _Unavailable('No native dialog backend is available.')
    try:
        result = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True,
                                check=False, shell=False)
    except OSError as exc:
        raise _Unavailable('The Linux native dialog could not start.') from exc
    if result.returncode == 1:
        return None
    if result.returncode != 0:
        raise _Unavailable('The Linux native dialog could not connect to the desktop.')
    try:
        value = result.stdout.decode('utf-8').rstrip('\r\n')
    except UnicodeError as exc:
        raise PickerError('The chooser returned an invalid path. Enter it manually.') from exc
    return _selected_path(kind, value)


def _choose(kind, initial):
    try:
        return _pick_with_tk(kind, initial)
    except _Unavailable:
        try:
            if os.name == 'nt':
                return _pick_with_windows(kind, initial)
            if sys.platform.startswith('linux'):
                return _pick_with_linux(kind, initial)
        except _Unavailable:
            pass
    raise PickerError('No desktop file chooser is available. Enter the local path manually. '
                      'The portable release should include Tk; Linux can also use an existing zenity or kdialog installation.')


def helper_main(argv=None):
    """Internal launcher route: --pick-path-helper KIND [helper options]."""
    parser = argparse.ArgumentParser(description='Internal World Between Worlds path chooser')
    parser.add_argument('kind', choices=KINDS)
    parser.add_argument('--initial-path')
    parser.add_argument('--result-file', type=Path)
    args = parser.parse_args(argv)
    # Reject an unusable output channel before asking the user to choose.
    if args.result_file is not None and (not args.result_file.is_absolute() or args.result_file.exists()):
        return 2
    try:
        initial = _initial_directory(args.kind, args.initial_path)
        selected = _choose(args.kind, initial)
        result = {'schema': 1, 'status': 'selected' if selected is not None else 'cancelled',
                  'path': selected}
        code = 0
    except PickerError as exc:
        result = {'schema': 1, 'status': 'error', 'path': None, 'message': str(exc)}
        code = 2
    raw = json.dumps(result, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    if args.result_file is not None:
        if not args.result_file.is_absolute():
            return 2
        try:
            with args.result_file.open('xb') as stream:
                stream.write(raw)
        except OSError:
            return 2
    elif sys.stdout is not None:
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout.buffer.write(raw + b'\n')
        else:
            sys.stdout.write(raw.decode('utf-8') + '\n')
    else:
        return 2
    return code


if __name__ == '__main__':
    arguments = sys.argv[1:]
    if arguments[:1] == ['--helper']:
        arguments = arguments[1:]
    raise SystemExit(helper_main(arguments))

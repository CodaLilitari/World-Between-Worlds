"""Launch World Between Worlds, applying a verified release within a bounded wait.

Source: python -B blackwing_launcher.py [--no-update] [--no-browser]
Frozen: WBW[.exe] [--no-update] [--no-browser]
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import queue
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse

# Isolated (-I) Python omits the script directory. Resolve this fixed local
# module root explicitly rather than consulting PYTHONPATH or the current cwd.
APP_ROOT = Path(__file__).resolve().parent
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(APP_ROOT))

import blackwing_update as updates
from blackwing_version import VERSION, REPOSITORY, TITLE

STARTUP_UPDATE_SECONDS = 8.0
READY_SECONDS = 15.0


def log(data_dir, message):
    try:
        path = Path(data_dir) / "launcher.log"
        if path.exists() and path.stat().st_size > 256 * 1024:
            path.replace(path.with_suffix(".previous.log"))
        with path.open("a", encoding="utf-8") as file:
            file.write(time.strftime("%Y-%m-%d %H:%M:%S ") + message + "\n")
    except OSError:
        pass  # Logging must not prevent the offline application from opening.


def bounded_update(root, version, seconds=STARTUP_UPDATE_SECONDS):
    """A daemon worker cannot hold the launcher past its startup wait budget."""
    results = queue.Queue(maxsize=1)
    deadline = time.monotonic() + seconds

    def check():
        try:
            transport = updates.GitHubTransport(deadline)
            results.put((updates.check_and_stage(root, version, transport), None))
        except Exception as error:
            # A release outage, rate limit, offline connection or invalid package
            # must not make the installed app unusable.
            results.put((None, f"{type(error).__name__}: {error}"))

    thread = threading.Thread(target=check, name="blackwing-update", daemon=True)
    thread.start()
    try:
        return results.get(timeout=max(0, deadline - time.monotonic()))
    except queue.Empty:
        return None, "Update check timed out; launching the working application"


def launch_command(candidate, app_args, handoff=False):
    child_args = ["--expect-version", candidate["version"], *app_args] if handoff else ["--run-app", *app_args]
    if candidate is None:
        if getattr(sys, "frozen", False):
            return [sys.executable, *child_args]
        return [sys.executable, "-I", "-B", str(APP_ROOT / "blackwing_launcher.py"), *child_args]
    manifest = candidate["manifest"]
    entry = candidate["path"] / manifest["entrypoint"]
    if manifest["kind"] == "source":
        return [sys.executable, "-I", "-B", str(entry), *child_args]
    return [str(entry), *child_args]


def process_parents():
    """Return PID ancestry only; no process command lines or unrelated file data."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        class Entry(ctypes.Structure):
            _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                        ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                        ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                        ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
                        ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260)]
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        kernel.Process32FirstW.argtypes = kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
        kernel.Process32FirstW.restype = kernel.Process32NextW.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
        if snapshot == ctypes.c_void_p(-1).value:
            return {}
        result = {}
        try:
            entry = Entry(); entry.dwSize = ctypes.sizeof(entry)
            present = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
            while present:
                result[entry.th32ProcessID] = entry.th32ParentProcessID
                present = kernel.Process32NextW(snapshot, ctypes.byref(entry))
        finally:
            kernel.CloseHandle(snapshot)
        return result
    result = {}
    try:
        for path in Path("/proc").iterdir():
            if path.name.isdigit():
                try:
                    value = (path / "stat").read_text()
                    # comm in parentheses may itself contain spaces/parentheses.
                    result[int(path.name)] = int(value[value.rfind(")") + 2:].split()[1])
                except (OSError, ValueError, IndexError):
                    pass
    except OSError:
        pass
    return result


def is_descendant(pid, parent, parents=None):
    parents = process_parents() if parents is None else parents
    visited = set()
    while pid in parents and pid not in visited:
        if pid == parent:
            return True
        visited.add(pid)
        pid = parents[pid]
    return pid == parent


def stop_owned(process):
    """Stop only this supervised process and its currently observed descendants."""
    parents = process_parents()
    children = [pid for pid in parents if pid != process.pid and is_descendant(pid, process.pid, parents)]
    for pid in children:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill(); process.wait(timeout=3)


def valid_ready(data, pid, version, allow_descendant=False):
    if not isinstance(data, dict) or type(data.get("pid")) is not int or data.get("version") != version:
        return False
    if data["pid"] != pid and (not allow_descendant or not is_descendant(data["pid"], pid)):
        return False
    try:
        url = urllib.parse.urlsplit(data.get("url", ""))
        return url.scheme == "http" and url.hostname == "127.0.0.1" and bool(url.port) and not url.username and not url.password
    except (TypeError, ValueError):
        return False


def start_supervised(candidate, app_args, data_dir, ready_seconds=READY_SECONDS, update_status=None, handoff=False):
    """Only the child we created may be terminated after a failed bootstrap."""
    data_dir = Path(data_dir)
    runtime = data_dir / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="ready-", suffix=".json", dir=runtime)
    os.close(fd)
    ready = Path(name)
    ready.unlink()  # An empty pre-created file must not count as readiness.
    env = os.environ.copy()
    env["BLACKWING_USER_DATA_DIR"] = str(data_dir.resolve())
    if handoff:
        env["BLACKWING_HANDOFF_READY_FILE"] = str(ready)
        env.pop("BLACKWING_READY_FILE", None)
    else:
        env["BLACKWING_READY_FILE"] = str(ready)
        env.pop("BLACKWING_HANDOFF_READY_FILE", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if update_status:
        env["BLACKWING_UPDATE_STATUS"] = update_status
    version = candidate["version"] if candidate else VERSION
    output = (runtime / f"app-{version}.log").open("ab")
    process = None
    try:
        process = subprocess.Popen(launch_command(candidate, app_args, handoff=handoff), env=env,
                                   cwd=str(candidate["path"] if candidate else APP_ROOT),
                                   stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        deadline = time.monotonic() + ready_seconds
        while time.monotonic() < deadline:
            if process.poll() is not None:
                return None, f"Application exited before ready (exit {process.returncode})"
            try:
                standalone = candidate["manifest"]["kind"] == "standalone" if candidate else getattr(sys, "frozen", False)
                if ready.stat().st_size <= 4096:
                    ready_data = json.loads(ready.read_text(encoding="utf-8"))
                    expected_version = version
                    if handoff and isinstance(ready_data, dict):
                        reported = ready_data.get("version")
                        if updates.Version(reported) < updates.Version(version):
                            continue
                        expected_version = reported
                    # Windows venv python.exe redirects to an interpreter child,
                    # just as a native bootloader may create the serving child.
                    allow_descendant = standalone or (os.name == "nt" and sys.prefix != sys.base_prefix)
                    if valid_ready(ready_data, process.pid, expected_version, allow_descendant=allow_descendant):
                        process.blackwing_url = ready_data["url"]
                        process.blackwing_version = ready_data["version"]
                        return process, None
            except (OSError, ValueError, UnicodeError):
                pass
            time.sleep(0.05)
        stop_owned(process)
        return None, "Application did not report a compatible ready state"
    except OSError as error:
        return None, f"Could not launch application: {error}"
    finally:
        output.close()
        try:
            ready.unlink(missing_ok=True)
        except OSError:
            pass


def notify_handoff_ready(url, version):
    """Propagate readiness through a strictly newer cached-launcher handoff."""
    path = os.environ.get("BLACKWING_HANDOFF_READY_FILE")
    if path:
        with Path(path).open("x", encoding="utf-8") as stream:
            json.dump({"pid": os.getpid(), "url": url, "version": version}, stream)


def wait_application(process):
    try:
        return process.wait()
    except KeyboardInterrupt:
        stop_owned(process)
        return process.returncode


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ['--pick-path-helper']:
        from blackwing_picker import helper_main
        return helper_main(argv[1:])
    if REPOSITORY != updates.REPOSITORY:
        raise SystemExit("Launcher/release repository configuration mismatch")
    parser = argparse.ArgumentParser(description="World Between Worlds launcher")
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument("--no-update", action="store_true", help="Open the installed application without network update checks")
    parser.add_argument("--no-browser", action="store_true", help="Start the workbench without opening a browser")
    parser.add_argument("--scan-mots", metavar="FOLDER", help="Check installed recipe revisions using this application's catalog; print JSON and exit")
    parser.add_argument("--run-app", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--expect-version", help=argparse.SUPPRESS)
    args, app_args = parser.parse_known_args(argv)
    if args.no_browser:
        app_args.append("--no-browser")
    if args.expect_version and args.expect_version != VERSION:
        print("Cached launcher version does not match its verified package", file=sys.stderr)
        return 1
    if args.scan_mots:
        from blackwing_app import main as app_main
        return app_main(["--scan-mots", args.scan_mots])
    if args.run_app:
        from blackwing_app import main as app_main
        return app_main(app_args)
    data_dir = updates.user_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    root = updates.cache_root(data_dir)
    installed = updates.installed_candidates(root, VERSION)
    # Give the latest previously ready release control of update policy before
    # any network check. Strict VERSION advancement prevents recursive handoffs.
    # The original shortcut remains a bounded hash/path-checking bootstrap.
    for newer in installed:
        handoff_args = [*app_args, *(["--no-update"] if args.no_update else [])]
        process, error = start_supervised(newer, handoff_args, data_dir,
            ready_seconds=STARTUP_UPDATE_SECONDS + READY_SECONDS + 3, handoff=True)
        if process is not None:
            notify_handoff_ready(process.blackwing_url, process.blackwing_version)
            return wait_application(process)
        log(data_dir, f"Cached launcher handoff failed: {error}")
        try:
            updates.reject(root, newer)
        except (OSError, updates.UpdateError) as error:
            log(data_dir, str(error))
    # Failed handoffs were removed from active state; use only surviving ready
    # versions as app fallbacks. Do not retry a rejected updater as --run-app.
    installed = updates.installed_candidates(root, VERSION)
    current = installed[0]["version"] if installed else VERSION
    candidate = None
    update_status = "Update checks disabled for this launch." if args.no_update else "No newer compatible published release found."
    if not args.no_update:
        candidate, error = bounded_update(root, current)
        if error:
            log(data_dir, error)
            update_status = "Update check unavailable; opened the installed app."
        elif candidate:
            update_status = "Verified update available: " + candidate["version"]
    options = ([candidate] if candidate else []) + installed + [None]
    seen = set()
    for option in options:
        identity = option["name"] if option else "bundled"
        if identity in seen:
            continue
        seen.add(identity)
        if option:
            try:
                option = updates.verify_cached(root, option["name"])
            except (OSError, updates.UpdateError) as error:
                log(data_dir, f"Cached application rejected: {error}")
                continue
        process, error = start_supervised(option, app_args, data_dir, update_status=update_status)
        if process is None:
            log(data_dir, f"{identity}: {error}")
            if option:
                update_status = "Updated application could not start; restored the previous working app."
                try:
                    updates.reject(root, option)
                except (OSError, updates.UpdateError) as reject_error:
                    log(data_dir, str(reject_error))
            continue
        if option:
            try:
                updates.activate(root, option)
            except (OSError, updates.UpdateError) as error:
                log(data_dir, f"Application ready; cache activation postponed: {error}")
        log(data_dir, f"Application ready: {option['version'] if option else VERSION}")
        version = option['version'] if option else VERSION
        notify_handoff_ready(process.blackwing_url, version)
        print(f"{TITLE} {version} - {process.blackwing_url}", flush=True)
        return wait_application(process)
    print("World Between Worlds could not start. See launcher.log and runtime logs in " + str(data_dir), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

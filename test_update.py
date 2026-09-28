"""Asset-free updater regression: synthetic releases and real child bootstrap.

No test requests the internet, modifies source files, launches a game, or needs
retail data. Run: python -B -m unittest test_update -v
"""
from io import BytesIO
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import zipfile

import blackwing_update as update
import blackwing_launcher as launcher

PROJECT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("blackwing_package_builder", PROJECT / "packaging/build_release.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class FakeTransport:
    def __init__(self, values):
        self.values = values
        self.calls = []

    def fetch(self, url, limit):
        self.calls.append(url)
        value = self.values[url]
        if isinstance(value, Exception):
            raise value
        if len(value) > limit:
            raise update.UpdateError("Fake response exceeds requested byte budget")
        return value


def payloads(version="0.2.0-rc2", app=None):
    if app is None:
        app = """import json, os, time
from pathlib import Path
from blackwing_version import VERSION
def main(argv=None):
    data=Path(os.environ['BLACKWING_USER_DATA_DIR'])
    (data/'ran-version.txt').write_text(VERSION)
    Path(os.environ['BLACKWING_READY_FILE']).write_text(json.dumps({'pid':os.getpid(),'url':'http://127.0.0.1:12345/','version':VERSION}))
    # Stay alive until the outer test launcher has accepted readiness, including
    # a cached launcher's handoff. A short fixed lifetime races OS scheduling.
    stop = data/'test-parent-accepted-ready'
    deadline = time.monotonic() + 10
    while not stop.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    return 0 if stop.exists() else 9
"""
    result = {name: b"# Synthetic unused package fixture.\n" for name in update.SOURCE_REQUIRED}
    launcher_code = (PROJECT / "blackwing_launcher.py").read_text(encoding="utf-8")
    # A cached updater executes in a real child. Stub its network boundary in
    # the synthetic package so this suite never contacts a published repository.
    hook = '''def bounded_update(root, version, seconds=8):
    (Path(os.environ["BLACKWING_USER_DATA_DIR"])/"new-updater-used.txt").write_text(VERSION)
    return None, None

'''
    launcher_code = launcher_code.replace('if __name__ == "__main__":', hook + 'if __name__ == "__main__":')
    result.update({"LICENSE": b"MIT synthetic fixture\n",
            "blackwing_app.py": app.encode(),
            "blackwing_version.py": f'VERSION={version!r}\nREPOSITORY={update.REPOSITORY!r}\nTITLE="World Between Worlds"\n'.encode(),
            "blackwing_launcher.py": launcher_code.encode(),
            "blackwing_update.py": (PROJECT / "blackwing_update.py").read_bytes()})
    return result


def make_package(version="0.2.0-rc2", app=None):
    package, data = builder.build_package(payloads(version, app), version)
    return {**package, "version": version, "url": update.asset_url(version, package["filename"])}, data


def release_wire(version="0.2.0-rc2", app=None):
    package, data = make_package(version, app)
    listed = {k: v for k, v in package.items() if k not in {"version", "url"}}
    manifest = update.json_bytes({"schema": 1, "repository": update.REPOSITORY, "version": version, "packages": [listed]})
    murl = update.asset_url(version, update.RELEASE_MANIFEST)
    release = {"draft": False, "prerelease": bool(update.Version(version).pre), "published_at": "2026-09-08T00:00:00Z", "tag_name": "v" + version,
               "assets": [{"name": update.RELEASE_MANIFEST, "size": len(manifest), "browser_download_url": murl, "digest": "sha256:" + update.sha256(manifest)},
                          {"name": package["filename"], "size": len(data), "browser_download_url": package["url"], "digest": "sha256:" + package["sha256"]}]}
    return release, {murl: manifest, package["url"]: data}, package, data


def rewrite_zip(data, transform):
    with zipfile.ZipFile(BytesIO(data)) as z:
        rows = [(info, z.read(info)) for info in z.infolist()]
    rows = transform(rows)
    out = BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for info, value in rows:
            z.writestr(info, value)
    return out.getvalue()


class Versions(unittest.TestCase):
    def test_rc_and_stable_ordering(self):
        versions = ["0.1.9", "0.2.0-alpha.1", "0.2.0-beta.1", "0.2.0-rc1", "0.2.0-rc2", "0.2.0-rc10", "0.2.0", "0.2.1", "1.0.0"]
        self.assertEqual(sorted(reversed(versions), key=update.Version), versions)
        self.assertEqual(update.Version("1.2.3+one"), update.Version("1.2.3+two"))
        self.assertLess(update.Version("1.2.3-2"), update.Version("1.2.3-alpha"))
        self.assertLess(update.Version("1.2.3-rc.9"), update.Version("1.2.3-rc.10"))

    def test_invalid_versions(self):
        for value in (None, "", "v1.2.3", "1.2", "01.2.3", "1.2.3-01", "1.2.3/evil", "1.2.3-", "1.2.3\n"):
            with self.subTest(value=value), self.assertRaises(update.UpdateError):
                update.Version(value)


class Discovery(unittest.TestCase):
    def test_publisher_migration_keeps_release_and_package_identity_explicit(self):
        self.assertEqual(update.REPOSITORY, 'CodaLilitari/World-Between-Worlds')
        release, values, package, data = release_wire()
        values[update.API_URL] = update.json_bytes([release])
        selected = update.discover('0.2.0-rc1', FakeTransport(values))
        manifest, _ = update.inspect_archive(data, selected)
        self.assertEqual(manifest['repository'], update.REPOSITORY)

        manifest_url = update.asset_url('0.2.0-rc2', update.RELEASE_MANIFEST)
        former_release = json.loads(values[manifest_url])
        former_release['repository'] = 'andreipemberton/World-Between-Worlds'
        values[manifest_url] = update.json_bytes(former_release)
        release['assets'][0].pop('digest')
        values[update.API_URL] = update.json_bytes([release])
        with self.assertRaisesRegex(update.UpdateError, 'Release manifest identity mismatch'):
            update.discover('0.2.0-rc1', FakeTransport(values))
        manifest['repository'] = 'andreipemberton/World-Between-Worlds'
        with self.assertRaisesRegex(update.UpdateError, 'Invalid package identity'):
            update.package_manifest(update.json_bytes(manifest), package)

    def transport(self, releases):
        listed, values = [], {}
        for version in releases:
            release, wire, _, _ = release_wire(version)
            listed.append(release); values.update(wire)
        values[update.API_URL] = update.json_bytes(listed)
        return FakeTransport(values)

    def test_rc_gets_newest_compatible_release(self):
        transport = self.transport(["0.2.0-rc2", "0.2.0-rc10", "0.1.0"])
        selected = update.discover("0.2.0-rc1", transport)
        self.assertEqual(selected["version"], "0.2.0-rc10")
        self.assertIn("/releases?", transport.calls[0])
        self.assertNotIn("latest", transport.calls[0])

    def test_stable_skips_prerelease(self):
        self.assertEqual(update.discover("0.2.0", self.transport(["0.3.0-rc1", "0.2.1"]))["version"], "0.2.1")

    def test_no_downgrade_or_same_version_repack(self):
        self.assertIsNone(update.discover("0.2.0", self.transport(["0.2.0", "0.1.0"])))

    def test_draft_and_unpublished_are_not_updates(self):
        release, values, _, _ = release_wire()
        for change in ({"draft": True}, {"published_at": None}):
            wire = {**values, update.API_URL: update.json_bytes([{**release, **change}])}
            self.assertIsNone(update.discover("0.2.0-rc1", FakeTransport(wire)))

    def test_manifest_and_asset_identity_checks(self):
        for mutation in ("url", "repository", "version", "asset-digest", "size"):
            release, values, package, _ = release_wire()
            murl = update.asset_url(package["version"], update.RELEASE_MANIFEST)
            manifest = json.loads(values[murl])
            if mutation == "url":
                release["assets"][0]["browser_download_url"] = "https://example.org/wbw-release.json"
            elif mutation in {"repository", "version"}:
                manifest[mutation] = "elsewhere/repository" if mutation == "repository" else "99.0.0"
                values[murl] = update.json_bytes(manifest)
                release["assets"][0].pop("digest")
            elif mutation == "asset-digest":
                release["assets"][1]["digest"] = "sha256:" + "0" * 64
            else:
                release["assets"][1]["size"] += 1
            values[update.API_URL] = update.json_bytes([release])
            with self.subTest(mutation=mutation), self.assertRaises(update.UpdateError):
                update.discover("0.2.0-rc1", FakeTransport(values))

    def test_incompatible_python_falls_through_to_older_compatible(self):
        transport = self.transport(["0.2.0-rc3", "0.2.0-rc2"])
        releases = json.loads(transport.values[update.API_URL])
        first = releases[0]
        url = first["assets"][0]["browser_download_url"]
        manifest = json.loads(transport.values[url]); manifest["packages"][0]["python_min"] = [3, 99]
        transport.values[url] = update.json_bytes(manifest)
        first["assets"][0].pop("digest")
        transport.values[update.API_URL] = update.json_bytes(releases)
        self.assertEqual(update.discover("0.2.0-rc1", transport)["version"], "0.2.0-rc2")

    def test_wrong_platform_is_not_downloaded(self):
        self.assertIsNone(update.discover("0.2.0-rc1", self.transport(["0.2.0-rc2"]), target=("standalone", "linux", "x86_64")))

    def test_duplicate_json_is_rejected(self):
        with self.assertRaises(update.UpdateError):
            update.parse_json(b'{"version":"1.0.0","version":"2.0.0"}')


class Transport(unittest.TestCase):
    def test_trust_boundary(self):
        self.assertTrue(update.trusted_url(update.API_URL))
        self.assertTrue(update.trusted_url(update.asset_url("1.0.0", "source.zip")))
        self.assertTrue(update.trusted_url("https://release-assets.githubusercontent.com/github-production-release-asset/x?token=x", redirect=True))
        for url in (f"http://github.com/{update.REPOSITORY}/releases/download/v1.0.0/source.zip",
                    "https://github.com/other/repo/releases/download/v1.0.0/source.zip",
                    f"https://github.com.evil.example/{update.REPOSITORY}/releases/download/v1.0.0/source.zip",
                    f"https://user:pass@github.com/{update.REPOSITORY}/releases/download/v1.0.0/source.zip",
                    f"https://github.com:444/{update.REPOSITORY}/releases/download/v1.0.0/source.zip",
                    "https://github.com/andreipemberton/World-Between-Worlds/releases/download/v1.0.0/source.zip",
                    "https://api.github.com/repos/andreipemberton/World-Between-Worlds/releases?per_page=30",
                    "https://objects.githubusercontent.com/arbitrary"):
            with self.subTest(url=url):
                self.assertFalse(update.trusted_url(url))
                with self.assertRaises(update.UpdateError):
                    update.GitHubTransport().fetch(url, 10)

    def test_redirect_outside_github_rejected(self):
        with self.assertRaises(update.UpdateError):
            update._Redirects().redirect_request(None, None, 302, "found", {}, "https://example.org/x")

    def test_transport_enforces_stream_length_and_deadline(self):
        class Response(BytesIO):
            def __init__(self, data, length=None):
                super().__init__(data); self.headers = {} if length is None else {"Content-Length": length}
            def geturl(self):
                return update.API_URL
        for data, length, limit in ((b"12345", None, 4), (b"123", "5", 10), (b"12345", "5", 4), (b"123", "bad", 10)):
            t = update.GitHubTransport()
            with patch.object(t.opener, "open", return_value=Response(data, length)):
                with self.subTest(length=length, limit=limit), self.assertRaises(update.UpdateError):
                    t.fetch(update.API_URL, limit)
        with self.assertRaises(update.UpdateError):
            update.GitHubTransport(time.monotonic() - 1).fetch(update.API_URL, 10)


class ArchiveAndCache(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "updates"
        self.package, self.data = make_package()

    def mutated(self, data):
        return {**self.package, "size": len(data), "sha256": update.sha256(data)}

    def test_deterministic_source_package(self):
        self.assertEqual(self.data, make_package()[1])
        manifest, values = update.inspect_archive(self.data, self.package)
        self.assertEqual(set(values), set(payloads()) | {update.PACKAGE_MANIFEST})
        self.assertEqual(manifest["version"], self.package["version"])

    def test_wrong_outer_hash_and_size(self):
        for change in ({"sha256": "0" * 64}, {"size": len(self.data) + 1}):
            with self.subTest(change=change), self.assertRaises(update.UpdateError):
                update.inspect_archive(self.data, {**self.package, **change})

    def test_unsafe_paths_rejected_before_install(self):
        for name in ("../escape.py", "/absolute.py", "C:/absolute.py", "a\\b.py", "a//b.py", "a/./b.py", "CON.txt", "aux.py", "a./b.py", "a /b.py", "a:b.py", "a\x00.py"):
            with self.subTest(name=name), self.assertRaises(update.UpdateError):
                update.safe_name(name)

    def test_extra_asset_file_rejected(self):
        for name in ("original.gob", "output.goo", "textures/x.mat", "cog/kyle.cog", "private-report.txt"):
            changed = rewrite_zip(self.data, lambda rows: rows + [(zipfile.ZipInfo(name), b"synthetic forbidden payload")])
            with self.subTest(name=name), self.assertRaises(update.UpdateError):
                update.inspect_archive(changed, self.mutated(changed))

    def test_case_collision_and_symlink_rejected(self):
        collision = rewrite_zip(self.data, lambda rows: rows + [(zipfile.ZipInfo("license"), b"case collision")])
        with self.assertRaises(update.UpdateError):
            update.inspect_archive(collision, self.mutated(collision))
        def symlink(rows):
            info, data = rows[0]
            info.create_system = 3; info.external_attr = (stat.S_IFLNK | 0o777) << 16
            return [(info, data), *rows[1:]]
        changed = rewrite_zip(self.data, symlink)
        with self.assertRaises(update.UpdateError):
            update.inspect_archive(changed, self.mutated(changed))

    def test_manifest_does_not_authorize_arbitrary_commands(self):
        def command(rows):
            out = []
            for info, data in rows:
                if info.filename == update.PACKAGE_MANIFEST:
                    m = json.loads(data); m["entrypoint"] = "powershell.exe -Command evil"
                    data = update.json_bytes(m)
                out.append((info, data))
            return out
        changed = rewrite_zip(self.data, command)
        with self.assertRaises(update.UpdateError):
            update.inspect_archive(changed, self.mutated(changed))

    def test_file_corruption_is_detected(self):
        changed = rewrite_zip(self.data, lambda rows: [(i, b"bad" if i.filename == "LICENSE" else v) for i, v in rows])
        with self.assertRaises(update.UpdateError):
            update.inspect_archive(changed, self.mutated(changed))

    def test_package_identity_must_match_release(self):
        with self.assertRaises(update.UpdateError):
            update.inspect_archive(self.data, {**self.package, "version": "9.9.9"})

    def test_stage_activate_and_preserve_previous(self):
        settings = self.root.parent / "settings.json"; settings.write_text('{"preserved":true}')
        first = update.stage_update(self.root, self.package, self.data)
        self.assertEqual(update.read_state(self.root), {})
        update.activate(self.root, first)
        package, data = make_package("0.2.0-rc3")
        second = update.stage_update(self.root, package, data)
        update.activate(self.root, second)
        state = update.read_state(self.root)
        self.assertEqual((state["active"], state["previous"]), (second["name"], first["name"]))
        self.assertTrue(first["path"].exists())
        self.assertEqual(settings.read_text(), '{"preserved":true}')
        self.assertEqual([p["version"] for p in update.installed_candidates(self.root, "0.2.0-rc1")], ["0.2.0-rc3", "0.2.0-rc2"])
        update.activate(self.root, first)
        self.assertEqual(update.read_state(self.root)["active"], second["name"])

    def test_atomic_stage_failure_has_no_visible_candidate(self):
        with patch.object(update.os, "rename", side_effect=OSError("synthetic failure")):
            with self.assertRaises(update.UpdateError):
                update.stage_update(self.root, self.package, self.data)
        self.assertEqual(list((self.root / "versions").iterdir()), [])
        self.assertEqual(update.installed_candidates(self.root, "0.1.0"), [])

    def test_cache_tamper_is_rejected(self):
        first = update.stage_update(self.root, self.package, self.data)
        (first["path"] / "LICENSE").write_bytes(b"changed")
        with self.assertRaises(update.UpdateError):
            update.verify_cached(self.root, first["name"])

    def test_cache_manifest_tamper_is_rejected(self):
        first = update.stage_update(self.root, self.package, self.data)
        path = first["path"] / update.PACKAGE_MANIFEST
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaises(update.UpdateError):
            update.verify_cached(self.root, first["name"])

    def test_reject_retains_old_app_and_blocks_repeat_candidate(self):
        first = update.stage_update(self.root, self.package, self.data)
        update.activate(self.root, first)
        release, wire, package, data = release_wire("0.2.0-rc3")
        second = update.stage_update(self.root, package, data)
        update.reject(self.root, second)
        wire[update.API_URL] = update.json_bytes([release])
        transport = FakeTransport(wire)
        self.assertIsNone(update.check_and_stage(self.root, "0.2.0-rc2", transport))
        self.assertNotIn(package["url"], transport.calls)
        self.assertEqual(update.read_state(self.root)["active"], first["name"])

    def test_verified_background_stage_is_reused_without_second_download(self):
        release, wire, package, data = release_wire()
        candidate = update.stage_update(self.root, package, data)
        wire[update.API_URL] = update.json_bytes([release])
        wire[package["url"]] = AssertionError("A verified staged ZIP must not be downloaded again")
        transport = FakeTransport(wire)
        result = update.check_and_stage(self.root, "0.2.0-rc1", transport)
        self.assertEqual(result["name"], candidate["name"])
        self.assertNotIn(package["url"], transport.calls)

    def test_bad_state_cannot_escape_cache(self):
        self.root.mkdir()
        for value in ('{"active":"../../other.py"}', '{"active":[],"previous":{}}'):
            (self.root / "state.json").write_text(value)
            self.assertEqual(update.installed_candidates(self.root, "0.1.0"), [])

    def test_standalone_contract_and_linux_executable_mode(self):
        # Synthetic inert bytes exercise packaging only; this is never executed.
        contents = {"WBW": b"not an executable", "LICENSE": b"MIT",
                    "PYTHON-LICENSE.txt": b"synthetic license", "PYINSTALLER-COPYING.txt": b"synthetic license",
                    "PYINSTALLER-NOTICE.txt": b"synthetic notice"}
        p, data = builder.build_package(contents, "1.0.0", "standalone", "linux", "x86_64", libc_min=[2, 35])
        result = update.stage_update(self.root, {**p, "version": "1.0.0"}, data)
        self.assertEqual(result["manifest"]["entrypoint"], "WBW")
        if os.name != "nt":
            self.assertTrue((result["path"] / "WBW").stat().st_mode & stat.S_IXUSR)

    def test_native_libc_compatibility_floor(self):
        metadata = {"kind": "standalone", "platform": "linux", "arch": "x86_64", "python_min": [3, 10], "libc_min": [2, 35]}
        target = ("standalone", "linux", "x86_64")
        for current, expected in (((2, 34), False), ((2, 35), True), ((2, 43), True), (None, False)):
            with patch.object(update, "glibc_version", return_value=current):
                self.assertEqual(update.compatible(metadata, target), expected)
        with self.assertRaises(update.UpdateError):
            update.compatible({**metadata, "libc_min": None}, target)


class LauncherIntegration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data_dir = Path(self.temp.name)
        self.root = update.cache_root(self.data_dir)
        # Model an installed release independently of the checkout's VERSION.
        # Otherwise an RC bump can make the synthetic update equal/older and
        # accidentally launch the real app instead of the finite test fixture.
        package, data = make_package("0.2.0-rc1")
        base = update.stage_update(self.root, package, data)
        for attribute, value in (("VERSION", base["version"]), ("APP_ROOT", base["path"])):
            isolated = patch.object(launcher, attribute, value)
            isolated.start()
            self.addCleanup(isolated.stop)
        original_wait = launcher.wait_application
        def acknowledge_ready(process):
            (self.data_dir / "test-parent-accepted-ready").write_text("ready")
            return original_wait(process)
        waiter = patch.object(launcher, "wait_application", side_effect=acknowledge_ready)
        waiter.start()
        self.addCleanup(waiter.stop)

    def test_update_download_stage_launch_and_activate_same_invocation(self):
        release, wire, _, _ = release_wire()
        wire[update.API_URL] = update.json_bytes([release])
        candidate = update.check_and_stage(self.root, "0.2.0-rc1", FakeTransport(wire))
        with patch.dict(os.environ, {"BLACKWING_USER_DATA_DIR": str(self.data_dir)}), patch.object(launcher, "bounded_update", return_value=(candidate, None)):
            self.assertEqual(launcher.main(["--no-browser"]), 0)
        self.assertEqual((self.data_dir / "ran-version.txt").read_text(), "0.2.0-rc2")
        self.assertEqual(update.read_state(self.root)["active"], candidate["name"])
        update.verify_cached(self.root, candidate["name"])  # -B kept it immutable.

    def test_failed_updated_bootstrap_falls_back_to_previous(self):
        package, data = make_package()
        good = update.stage_update(self.root, package, data); update.activate(self.root, good)
        package, data = make_package("0.2.0-rc3", "def main(argv=None):\n    return 7\n")
        bad = update.stage_update(self.root, package, data)
        settings = self.data_dir / "settings.json"; settings.write_text("preserve")
        with patch.dict(os.environ, {"BLACKWING_USER_DATA_DIR": str(self.data_dir)}), patch.object(launcher, "bounded_update", return_value=(bad, None)), patch.object(launcher, "VERSION", good["version"]), patch.object(launcher, "APP_ROOT", good["path"]):
            self.assertEqual(launcher.main(["--no-browser"]), 0)
        self.assertEqual((self.data_dir / "ran-version.txt").read_text(), "0.2.0-rc2")
        self.assertEqual(update.read_state(self.root)["active"], good["name"])
        self.assertIn(bad["name"], update.read_state(self.root)["rejected"])
        self.assertEqual(settings.read_text(), "preserve")

    def test_no_update_uses_cached_working_app_without_network(self):
        package, data = make_package()
        candidate = update.stage_update(self.root, package, data); update.activate(self.root, candidate)
        with patch.dict(os.environ, {"BLACKWING_USER_DATA_DIR": str(self.data_dir)}), patch.object(launcher, "bounded_update", side_effect=AssertionError("network forbidden")):
            self.assertEqual(launcher.main(["--no-update", "--no-browser"]), 0)

    def test_offline_falls_back_without_changing_cache(self):
        package, data = make_package()
        candidate = update.stage_update(self.root, package, data); update.activate(self.root, candidate)
        with patch.dict(os.environ, {"BLACKWING_USER_DATA_DIR": str(self.data_dir)}), patch.object(launcher, "bounded_update", return_value=(None, "offline")), patch.object(launcher, "VERSION", candidate["version"]), patch.object(launcher, "APP_ROOT", candidate["path"]):
            self.assertEqual(launcher.main(["--no-browser"]), 0)
        self.assertEqual(update.read_state(self.root)["active"], candidate["name"])

    def test_original_shortcut_runs_new_cached_updater_logic(self):
        package, data = make_package()
        candidate = update.stage_update(self.root, package, data); update.activate(self.root, candidate)
        with patch.dict(os.environ, {"BLACKWING_USER_DATA_DIR": str(self.data_dir)}), patch.object(launcher, "bounded_update", side_effect=AssertionError("old updater must hand off before network")):
            self.assertEqual(launcher.main(["--no-browser"]), 0)
        self.assertEqual((self.data_dir / "new-updater-used.txt").read_text(), "0.2.0-rc2")
        self.assertEqual((self.data_dir / "ran-version.txt").read_text(), "0.2.0-rc2")

    def test_future_helper_module_can_update_through_original_bootstrap(self):
        files = payloads("0.2.0-rc3")
        files["future_adapter.py"] = b'IDENTITY = "new helper updater executed"\n'
        files["blackwing_launcher.py"] = files["blackwing_launcher.py"].replace(
            b').write_text(VERSION)', b').write_text(__import__("future_adapter").IDENTITY)')
        self.assertNotIn("future_adapter.py", update.SOURCE_FILES)
        with self.assertRaises(update.UpdateError):
            builder.build_package(files, "0.2.0-rc3")
        # Emulate a later reviewed builder explicitly adding this original module.
        with patch.object(update, "SOURCE_FILES", update.SOURCE_FILES | {"future_adapter.py"}):
            package, data = builder.build_package(files, "0.2.0-rc3")
        candidate = update.stage_update(self.root, {**package,"version":"0.2.0-rc3"}, data)
        update.activate(self.root, candidate)
        with patch.dict(os.environ, {"BLACKWING_USER_DATA_DIR": str(self.data_dir)}), patch.object(launcher, "bounded_update", side_effect=AssertionError("original updater must not run")):
            self.assertEqual(launcher.main(["--no-browser"]), 0)
        self.assertEqual((self.data_dir / "new-updater-used.txt").read_text(), "new helper updater executed")

    def test_broken_new_launcher_handoff_restores_bundled_app(self):
        base_package, base_data = make_package("0.2.0-rc1")
        base = update.stage_update(self.root, base_package, base_data)
        bad_files = payloads("0.2.0-rc2")
        bad_files["blackwing_launcher.py"] = b"raise SystemExit(7)\n"
        package, data = builder.build_package(bad_files, "0.2.0-rc2")
        bad = update.stage_update(self.root, {**package,"version":"0.2.0-rc2"}, data); update.activate(self.root, bad)
        with patch.dict(os.environ, {"BLACKWING_USER_DATA_DIR": str(self.data_dir)}), patch.object(launcher, "APP_ROOT", base["path"]):
            self.assertEqual(launcher.main(["--no-update", "--no-browser"]), 0)
        self.assertEqual((self.data_dir / "ran-version.txt").read_text(), "0.2.0-rc1")
        self.assertIn(bad["name"], update.read_state(self.root)["rejected"])

    @unittest.skipUnless(os.name == "nt" and sys.prefix != sys.base_prefix, "Windows venv ancestry path")
    def test_fallback_ready_survives_slow_ancestry_lookup(self):
        original = launcher.is_descendant
        delayed = []
        def slow_ancestry(*args, **kwargs):
            if not delayed:
                delayed.append(True)
                time.sleep(0.45)  # Longer than the old fixture's 0.3s lifetime.
            return original(*args, **kwargs)
        with patch.object(launcher, "is_descendant", side_effect=slow_ancestry):
            self.test_broken_new_launcher_handoff_restores_bundled_app()
        self.assertTrue(delayed)

    def test_timeout_returns_without_waiting_for_worker(self):
        def delayed(*args, **kwargs):
            time.sleep(0.25)
            return None
        start = time.monotonic()
        with patch.object(update, "check_and_stage", side_effect=delayed):
            result, error = launcher.bounded_update(self.root, "0.2.0-rc1", seconds=0.02)
        self.assertIsNone(result); self.assertIn("timed out", error)
        self.assertLess(time.monotonic() - start, 0.2)

    def test_ready_requires_own_pid_version_and_loopback(self):
        good = {"pid": 123, "version": "1.0.0", "url": "http://127.0.0.1:1234/"}
        self.assertTrue(launcher.valid_ready(good, 123, "1.0.0"))
        for change in ({"pid": 124}, {"version": "2.0.0"}, {"url": "http://example.org:1234/"}, {"url": "http://127.0.0.1/"}):
            self.assertFalse(launcher.valid_ready({**good, **change}, 123, "1.0.0"))

    def test_native_pid_ancestry_accepts_owned_bootloader_child(self):
        child = "import json,os,time;from pathlib import Path;Path(os.environ['BLACKWING_READY_FILE']).write_text(json.dumps({'pid':os.getpid(),'url':'http://127.0.0.1:12345/','version':'0.2.0-rc2'}));time.sleep(0.5)"
        wrapper = "import subprocess,sys;raise SystemExit(subprocess.call([sys.executable,'-B','-c'," + repr(child) + "]))"
        candidate = {"path": self.data_dir, "version": "0.2.0-rc2", "manifest": {"kind": "standalone"}}
        with patch.object(launcher, "launch_command", return_value=[sys.executable, "-B", "-c", wrapper]):
            process, error = launcher.start_supervised(candidate, [], self.data_dir, ready_seconds=2)
        self.assertIsNone(error)
        self.assertIsNotNone(process)
        self.assertEqual(process.wait(timeout=3), 0)
        self.assertFalse(launcher.is_descendant(os.getpid(), process.pid))

    @unittest.skipUnless(os.name == "nt", "Windows virtual-environment redirector")
    def test_windows_venv_source_accepts_owned_interpreter_child(self):
        for candidate in (None, {"path": self.data_dir, "version": "0.2.0-rc2", "manifest": {"kind": "source"}}):
            with self.subTest(bundled=candidate is None):
                version = candidate["version"] if candidate else launcher.VERSION
                child = "import json,os,time;from pathlib import Path;Path(os.environ['BLACKWING_READY_FILE']).write_text(json.dumps({'pid':os.getpid(),'url':'http://127.0.0.1:12345/','version':" + repr(version) + "}));time.sleep(0.5)"
                wrapper = "import subprocess,sys;raise SystemExit(subprocess.call([sys.executable,'-B','-c'," + repr(child) + "]))"
                # Model a venv even when this test runs under the base Python.
                # The real wrapper child exercises the OS ancestry lookup.
                with patch.object(launcher.sys, "prefix", "synthetic-venv"), patch.object(launcher.sys, "base_prefix", "synthetic-base"), patch.object(launcher, "launch_command", return_value=[sys.executable, "-B", "-c", wrapper]):
                    process, error = launcher.start_supervised(candidate, [], self.data_dir, ready_seconds=2)
                self.assertIsNone(error)
                self.assertIsNotNone(process)
                self.assertEqual(process.wait(timeout=3), 0)

    def test_descendant_ready_still_requires_ancestry_version_and_loopback(self):
        good = {"pid": 124, "version": "1.0.0", "url": "http://127.0.0.1:1234/"}
        with patch.object(launcher, "process_parents", return_value={124: 123, 125: 999}):
            self.assertTrue(launcher.valid_ready(good, 123, "1.0.0", allow_descendant=True))
            for change in ({"pid": 125}, {"pid": True}, {"version": "2.0.0"}, {"url": "http://example.org:1234/"}, {"url": "http://127.0.0.1/"}):
                with self.subTest(change=change):
                    self.assertFalse(launcher.valid_ready({**good, **change}, 123, "1.0.0", allow_descendant=True))

    def test_failed_ready_timeout_stops_owned_process(self):
        candidate = {"path": self.data_dir, "version": "0.2.0-rc2", "manifest": {"kind": "source"}}
        real_popen = subprocess.Popen
        children = []
        def tracked(*args, **kwargs):
            process = real_popen(*args, **kwargs); children.append(process); return process
        with patch.object(launcher, "launch_command", return_value=[sys.executable, "-B", "-c", "import time;time.sleep(20)"]), patch.object(launcher.subprocess, "Popen", side_effect=tracked):
            process, error = launcher.start_supervised(candidate, [], self.data_dir, ready_seconds=0.1)
        self.assertIsNone(process)
        self.assertIn("did not report", error)
        self.assertIsNotNone(children[0].poll())


class Packaging(unittest.TestCase):
    def test_repository_only_ninja_evidence_preserves_source_update_contract(self):
        import ninja_catalog
        evidence = ninja_catalog.RUNTIME_TEST['evidence']
        relative = 'docs/validation/ninja-maxmana-20260908.json'
        expected_url = 'https://github.com/CodaLilitari/World-Between-Worlds/blob/v0.2.0-rc2/' + relative
        self.assertEqual(evidence['url'], expected_url)
        self.assertFalse(evidence['bundled'])
        self.assertNotIn('path', evidence)
        files = builder.source_payloads(PROJECT)
        self.assertNotIn(relative, files)
        self.assertFalse(update.source_member_allowed(relative))
        for document in ('NINJA_KAGE.md', 'VALIDATION.md'):
            self.assertIn(expected_url.encode(), files[document])
            self.assertNotIn(('](' + relative + ')').encode(), files[document])
        # The repository keeps the report; updater/source ZIPs deliberately do
        # not. Check its content pin when running in the full repository.
        report = PROJECT / relative
        if report.is_file():
            self.assertEqual(update.sha256(report.read_bytes()), evidence['sha256'])

    def test_allowlist_excludes_assets_private_evidence_and_tests(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, data in payloads().items():
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_bytes(data)
            for name in ("retail.gob", "converted.goo", "kyle.cog", "test_private_audit.py", "private-audit.json"):
                (root / name).write_text("must not be packaged")
            self.assertEqual(set(builder.source_payloads(root)), set(payloads()))

    def test_personal_absolute_path_blocks_source_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, data in payloads().items():
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_bytes(data)
            synthetic_path = "C:" + "\\" + "Users" + "\\" + "Example" + "\\" + "private"
            (root / "blackwing_app.py").write_text("private = " + repr(synthetic_path) + "\n")
            with self.assertRaises(update.UpdateError):
                builder.source_payloads(root)


if __name__ == "__main__":
    unittest.main()

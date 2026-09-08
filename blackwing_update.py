"""Bounded, repository-pinned World Between Worlds release installation.

Trust is the public HTTPS GitHub release in REPOSITORY, not an unsigned hash
from an arbitrary URL. Hashes bind the exact release asset and all installed
files. Metadata never supplies a command. No game assets belong in a package.
"""
from __future__ import annotations

from contextlib import contextmanager
from functools import total_ordering
from io import BytesIO
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile

from blackwing_version import REPOSITORY

# This pin is trusted application code, never an environment/user/remote value.
if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", REPOSITORY):
    raise RuntimeError("Invalid compiled-in release repository")
API_URL = f"https://api.github.com/repos/{REPOSITORY}/releases?per_page=30"
RELEASE_MANIFEST = "wbw-release.json"
PACKAGE_MANIFEST = "wbw-package.json"
MAX_METADATA = 1024 * 1024
MAX_ARCHIVE = 128 * 1024 * 1024
MAX_EXPANDED = 256 * 1024 * 1024
MAX_FILES = 128
SOURCE_FILES = frozenset({
    "blackwing_app.py", "blackwing_version.py", "blackwing_launcher.py",
    "blackwing_update.py", "bridge.py", "gob.py", "custom_registry.py",
    "custom_catalog.py", "author_catalog.py", "jhs_catalog.py",
    "community_runtime.py", "blackwing_catalog.py", "blackwing_service.py",
    "blackwing_runtime.py", "LICENSE", "NOTICE.md", "WBW-README.md",
    "caesars_audit.py", "verify_retail.py", "ninja_catalog.py", "ninja_converter.py",
    "force_icon_palette.py", "test_force_icon_palette.py",
    "ui/index.html", "ui/app.js", "ui/styles.css",
    "ui/test_ui.mjs", "ui/README.md", "README.md", "TESTING.md",
    "SUPPORTED_CUSTOM_SOURCES.txt", "COMMUNITY_RC1.md", "VALIDATION.md",
    "RECIPES.md", "recipes.json", "NINJA_KAGE.md", "SCREENSHOTS.md", "packaging/export_catalog.py",
    "test_blackwing.py", "test_bridge.py", "test_caesars.py", "test_community.py",
    "test_ninja.py", "test_update.py", "packaging/README.md", "packaging/USER_GUIDE.md",
    "packaging/build_release.py", "packaging/build_standalone.py",
    "packaging/merge_manifests.py", "packaging/requirements-build.txt",
    "packaging/ci-release.yml", "packaging/Launch-WBW.bat", "packaging/launch-wbw.sh",
    "Launch-WBW.bat", "launch-wbw.sh",
})
SOURCE_REQUIRED = frozenset({"blackwing_app.py", "blackwing_version.py",
    "blackwing_launcher.py", "blackwing_update.py", "LICENSE", "bridge.py", "gob.py",
    "community_runtime.py", "custom_registry.py", "custom_catalog.py", "author_catalog.py",
    "jhs_catalog.py", "blackwing_catalog.py", "blackwing_service.py", "force_icon_palette.py",
    "ui/index.html", "ui/app.js", "ui/styles.css"})
HEX = re.compile(r"[0-9a-f]{64}\Z")


class UpdateError(ValueError):
    """An unavailable, incompatible or untrusted update; keep the working app."""


@total_ordering
class Version:
    """SemVer precedence with natural suffix order for legacy rcN-style tags."""
    pattern = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
                         r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
                         r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?\Z")

    def __init__(self, value):
        if not isinstance(value, str) or len(value) > 80:
            raise UpdateError("Invalid release version")
        m = self.pattern.fullmatch(value)
        if not m:
            raise UpdateError("Release does not use a semantic version")
        self.text = value
        self.core = tuple(int(m[i]) for i in (1, 2, 3))
        self.pre = tuple(m[4].split(".")) if m[4] else ()
        if any(x.isdigit() and len(x) > 1 and x[0] == "0" for x in self.pre):
            raise UpdateError("Numeric prerelease identifier has a leading zero")

    def __eq__(self, other):
        return isinstance(other, Version) and (self.core, self.pre) == (other.core, other.pre)

    def __lt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        if self.core != other.core:
            return self.core < other.core
        if not self.pre or not other.pre:
            return bool(self.pre) and not other.pre
        for a, b in zip(self.pre, other.pre):
            if a == b:
                continue
            if a.isdigit() and b.isdigit():
                return int(a) < int(b)
            if a.isdigit() != b.isdigit():
                return a.isdigit()
            # rc1 is a legal SemVer identifier; common rcN releases must not
            # select rc2 after rc10. Enforce natural numeric suffix precedence.
            ma, mb = re.fullmatch(r"([a-zA-Z]+)([0-9]+)", a), re.fullmatch(r"([a-zA-Z]+)([0-9]+)", b)
            if ma and mb and ma[1] == mb[1]:
                return int(ma[2]) < int(mb[2])
            return a < b
        return len(self.pre) < len(other.pre)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")


def parse_json(data):
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise UpdateError("Duplicate JSON key")
            result[key] = value
        return result
    try:
        return json.loads(data, object_pairs_hook=no_duplicates)
    except (ValueError, UnicodeError) as error:
        raise UpdateError("Invalid update JSON") from error


def user_data_dir():
    override = os.environ.get("BLACKWING_USER_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "World Between Worlds"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "world-between-worlds"


def runtime_target(frozen=None):
    frozen = getattr(sys, "frozen", False) if frozen is None else frozen
    if not frozen:
        return ("source", "any", "any")
    system = {"win32": "windows", "linux": "linux"}.get(sys.platform, sys.platform)
    machine = platform.machine().lower()
    machine = {"amd64": "x86_64", "aarch64": "arm64"}.get(machine, machine)
    return ("standalone", system, machine)


def asset_url(version, name):
    Version(version)
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,140}", name):
        raise UpdateError("Invalid release asset filename")
    return f"https://github.com/{REPOSITORY}/releases/download/v{version}/{name}"


def trusted_url(url, redirect=False):
    try:
        parsed = urllib.parse.urlsplit(url)
        port = parsed.port
    except (TypeError, ValueError):
        return False
    if parsed.scheme != "https" or parsed.username or parsed.password or port not in (None, 443) or parsed.fragment:
        return False
    if url == API_URL:
        return True
    if parsed.hostname == "github.com":
        prefix = f"/{REPOSITORY}/releases/download/v"
        if not parsed.path.startswith(prefix) or parsed.query:
            return False
        suffix = parsed.path[len(prefix):].split("/")
        try:
            return len(suffix) == 2 and asset_url(*suffix) == url
        except UpdateError:
            return False
    return redirect and parsed.hostname in {"release-assets.githubusercontent.com", "objects.githubusercontent.com"}


class _Redirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not trusted_url(newurl, redirect=True):
            raise UpdateError("Release download redirected outside GitHub asset hosts")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class GitHubTransport:
    """Small stdlib transport with a per-operation and absolute time budget."""
    def __init__(self, deadline=None):
        self.deadline = deadline or time.monotonic() + 8
        self.opener = urllib.request.build_opener(_Redirects())

    def fetch(self, url, limit):
        if not trusted_url(url):
            raise UpdateError("Untrusted release URL")
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise UpdateError("Update check exceeded the startup time budget")
        request = urllib.request.Request(url, headers={
            "User-Agent": "World-Between-Worlds-Updater", "Accept": "application/vnd.github+json" if url == API_URL else "application/octet-stream",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        with self.opener.open(request, timeout=min(3, remaining)) as response:
            if not trusted_url(response.geturl(), redirect=True):
                raise UpdateError("Unexpected final release URL")
            length = response.headers.get("Content-Length")
            if length is not None and (not length.isdigit() or int(length) > limit):
                raise UpdateError("Release response exceeds download limit")
            data = bytearray()
            while True:
                if time.monotonic() >= self.deadline:
                    raise UpdateError("Update download exceeded startup time budget")
                chunk = response.read(min(65536, limit + 1 - len(data)))
                if not chunk:
                    break
                data.extend(chunk)
                if len(data) > limit:
                    raise UpdateError("Release response exceeds download limit")
            if length is not None and len(data) != int(length):
                raise UpdateError("Truncated release response")
            return bytes(data)


def _integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def _package_fields(package):
    if not isinstance(package, dict) or package.get("kind") not in {"source", "standalone"}:
        raise UpdateError("Invalid package kind")
    target = (package["kind"], package.get("platform"), package.get("arch"))
    if target[0] == "source" and target != ("source", "any", "any"):
        raise UpdateError("Invalid source package target")
    if target[0] == "standalone" and (target[1] not in {"windows", "linux"} or target[2] not in {"x86_64", "arm64"}):
        raise UpdateError("Unsupported standalone package target")
    if target[:2] == ("standalone", "linux"):
        minimum = package.get("libc_min")
        if not isinstance(minimum, list) or len(minimum) != 2 or not all(_integer(n, 0, 999) for n in minimum):
            raise UpdateError("Linux standalone package needs its glibc compatibility floor")
    pymin = package.get("python_min")
    if not isinstance(pymin, list) or len(pymin) != 2 or not all(_integer(n, 0, 99) for n in pymin) or pymin[0] != 3:
        raise UpdateError("Invalid Python compatibility requirement")
    return target


def glibc_version():
    name, value = platform.libc_ver()
    if name.lower() != "glibc" or not re.fullmatch(r"[0-9]+\.[0-9]+(?:\.[0-9]+)*", value):
        return None
    return tuple(int(n) for n in value.split(".")[:2])


def compatible(package, target):
    if _package_fields(package) != target:
        return False
    if target[0] == "source":
        return tuple(package["python_min"]) <= sys.version_info[:2]
    if target[1] == "linux":
        current = glibc_version()
        return current is not None and current >= tuple(package["libc_min"])
    return True


def discover(current_version, transport, target=None):
    """Return one newer compatible public release; RC installs include RCs."""
    current = Version(current_version)
    target = target or runtime_target()
    releases = parse_json(transport.fetch(API_URL, MAX_METADATA))
    if not isinstance(releases, list) or len(releases) > 30:
        raise UpdateError("Invalid published release list")
    candidates = []
    for release in releases:
        if not isinstance(release, dict) or release.get("draft") is not False or not release.get("published_at"):
            continue
        tag = release.get("tag_name", "")
        try:
            version = Version(tag[1:]) if isinstance(tag, str) and tag.startswith("v") else None
        except UpdateError:
            continue
        if version is None or version <= current or (not current.pre and (version.pre or release.get("prerelease"))):
            continue
        assets = release.get("assets", [])
        if not isinstance(assets, list):
            continue
        matches = [a for a in assets if isinstance(a, dict) and a.get("name") == RELEASE_MANIFEST]
        if len(matches) == 1:
            candidates.append((version, release, matches[0]))
    for version, release, manifest_asset in sorted(candidates, key=lambda row: row[0], reverse=True):
        url = asset_url(version.text, RELEASE_MANIFEST)
        if manifest_asset.get("browser_download_url") != url:
            raise UpdateError("Manifest asset URL does not belong to the expected release")
        data = transport.fetch(url, MAX_METADATA)
        digest = manifest_asset.get("digest")
        if digest is not None and digest != "sha256:" + sha256(data):
            raise UpdateError("GitHub manifest asset digest mismatch")
        manifest = parse_json(data)
        if not isinstance(manifest, dict) or manifest.get("schema") != 1 or manifest.get("repository") != REPOSITORY or manifest.get("version") != version.text:
            raise UpdateError("Release manifest identity mismatch")
        packages = manifest.get("packages")
        if not isinstance(packages, list) or len(packages) > 8:
            raise UpdateError("Invalid release package list")
        selected = []
        for package in packages:
            if not compatible(package, target):
                continue
            if not HEX.fullmatch(str(package.get("sha256", ""))) or not _integer(package.get("size"), 1, MAX_ARCHIVE):
                raise UpdateError("Invalid package digest or size")
            name = package.get("filename")
            package_url = asset_url(version.text, name)
            matching_assets = [a for a in release["assets"] if isinstance(a, dict) and a.get("name") == name]
            if len(matching_assets) != 1 or matching_assets[0].get("browser_download_url") != package_url or matching_assets[0].get("size") != package["size"]:
                raise UpdateError("Package does not match its published GitHub asset")
            git_digest = matching_assets[0].get("digest")
            if git_digest is not None and git_digest != "sha256:" + package["sha256"]:
                raise UpdateError("GitHub package digest mismatch")
            selected.append({**package, "version": version.text, "url": package_url})
        if len(selected) > 1:
            raise UpdateError("Ambiguous compatible release packages")
        if selected:
            return selected[0]
    return None


def safe_name(name):
    if not isinstance(name, str) or not name or len(name) > 180 or not name.isascii() or "\\" in name or ":" in name:
        raise UpdateError("Unsafe package member name")
    parts = name.split("/")
    reserved = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
    if any(p in ("", ".", "..") or p.endswith((".", " ")) or p.split(".")[0].lower() in reserved for p in parts):
        raise UpdateError("Unsafe or ambiguous package member path")
    if any(ord(c) < 32 or c in '<>"|?*' for c in name):
        raise UpdateError("Invalid package member character")
    return name


def allowed_files(kind, system):
    return SOURCE_FILES if kind == "source" else frozenset({
        "WBW.exe" if system == "windows" else "WBW",
        "LICENSE", "NOTICE.md", "WBW-README.md", "PYTHON-LICENSE.txt",
        "PYINSTALLER-COPYING.txt", "PYINSTALLER-NOTICE.txt",
    })


def source_member_allowed(name):
    """Stable bootstrap contract for future original code, never game assets.

    The maintainer's package builder still copies only SOURCE_FILES. This broader
    installer grammar lets a later reviewed release add an application helper or
    UI module, so the original downloaded bootstrap can verify and hand off to it.
    """
    if name in SOURCE_FILES:
        return True
    return bool(re.fullmatch(r"(?:[a-z][a-z0-9_]{0,70}\.py|packaging/[a-z][a-z0-9_]{0,70}\.py|ui/[a-z][a-z0-9_.-]{0,70}\.(?:js|mjs|css|html))", name))


def package_manifest(data, expected):
    manifest = parse_json(data)
    if not isinstance(manifest, dict) or manifest.get("schema") != 1 or manifest.get("repository") != REPOSITORY:
        raise UpdateError("Invalid package identity")
    Version(manifest.get("version"))
    _package_fields(manifest)
    for key in ("version", "kind", "platform", "arch", "python_min", "libc_min"):
        if manifest.get(key) != expected.get(key):
            raise UpdateError("Package and release manifests disagree: " + key)
    entry = "blackwing_launcher.py" if manifest["kind"] == "source" else ("WBW.exe" if manifest["platform"] == "windows" else "WBW")
    if manifest.get("entrypoint") != entry:
        raise UpdateError("Unsupported package entrypoint")
    rows = manifest.get("files")
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_FILES:
        raise UpdateError("Invalid package file manifest")
    names, total = set(), 0
    for row in rows:
        if not isinstance(row, dict):
            raise UpdateError("Invalid package file record")
        name = safe_name(row.get("path"))
        allowed = source_member_allowed(name) if manifest["kind"] == "source" else name in allowed_files(manifest["kind"], manifest["platform"])
        if not allowed or name.lower() in names:
            raise UpdateError("Unallowlisted or duplicate package file")
        if not _integer(row.get("size"), 0, MAX_EXPANDED) or not HEX.fullmatch(str(row.get("sha256", ""))):
            raise UpdateError("Invalid package file size or digest")
        total += row["size"]
        names.add(name.lower())
    required = SOURCE_REQUIRED if manifest["kind"] == "source" else {
        entry.lower(), "license", "python-license.txt", "pyinstaller-copying.txt", "pyinstaller-notice.txt"}
    if not {p.lower() for p in required}.issubset(names) or total > MAX_EXPANDED:
        raise UpdateError("Incomplete or oversized application package")
    return manifest


def inspect_archive(data, expected):
    if len(data) != expected["size"] or len(data) > MAX_ARCHIVE or sha256(data) != expected["sha256"]:
        raise UpdateError("Downloaded package size or SHA256 mismatch")
    try:
        with zipfile.ZipFile(BytesIO(data)) as archive:
            infos = archive.infolist()
            if not 2 <= len(infos) <= MAX_FILES + 1:
                raise UpdateError("Invalid package member count")
            names, total = set(), 0
            for info in infos:
                name = safe_name(info.filename)
                mode = info.external_attr >> 16
                if (info.orig_filename != info.filename or name.lower() in names or info.is_dir()
                        or info.external_attr & (0x10 | 0x40 | 0x400) or info.flag_bits & 1
                        or stat.S_IFMT(mode) not in (0, stat.S_IFREG)):
                    raise UpdateError("Duplicate, encrypted or non-regular ZIP member")
                if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                    raise UpdateError("Unsupported ZIP compression")
                total += info.file_size
                if info.file_size > MAX_EXPANDED or total > MAX_EXPANDED:
                    raise UpdateError("Expanded package exceeds limit")
                names.add(name.lower())
            if PACKAGE_MANIFEST not in names or archive.getinfo(PACKAGE_MANIFEST).file_size > MAX_METADATA:
                raise UpdateError("Missing or oversized package manifest")
            manifest = package_manifest(archive.read(PACKAGE_MANIFEST), expected)
            expected_names = {row["path"] for row in manifest["files"]} | {PACKAGE_MANIFEST}
            if {i.filename for i in infos} != expected_names:
                raise UpdateError("ZIP members do not exactly match package manifest")
            payloads = {PACKAGE_MANIFEST: archive.read(PACKAGE_MANIFEST)}
            for row in manifest["files"]:
                if archive.getinfo(row["path"]).file_size != row["size"]:
                    raise UpdateError("ZIP member size differs from file manifest")
                value = archive.read(row["path"])
                if len(value) != row["size"] or sha256(value) != row["sha256"]:
                    raise UpdateError("Package file digest mismatch")
                payloads[row["path"]] = value
            return manifest, payloads
    except (zipfile.BadZipFile, KeyError, RuntimeError, NotImplementedError) as error:
        raise UpdateError("Invalid application ZIP") from error


def cache_root(data_dir, target=None):
    return Path(data_dir) / "updates" / "-".join(target or runtime_target())


def _atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".state-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(json_bytes(value))
            file.flush()
            os.fsync(file.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def read_state(root):
    try:
        path = Path(root) / "state.json"
        if path.stat().st_size > MAX_METADATA:
            return {}
        state = parse_json(path.read_bytes())
        return state if isinstance(state, dict) else {}
    except (OSError, UpdateError):
        return {}


@contextmanager
def cache_lock(root):
    """OS-released advisory lock; a crash does not leave a permanent lock."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    file = (root / ".lock").open("a+b")
    locked = False
    try:
        if os.name == "nt":
            import msvcrt
            file.seek(0); file.write(b"0"); file.flush(); file.seek(0)
            msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locked = True
        yield
    except OSError as error:
        raise UpdateError("Another launcher is updating the version cache") from error
    finally:
        if locked:
            if os.name == "nt":
                import msvcrt
                file.seek(0); msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(file, fcntl.LOCK_UN)
        file.close()


def _directory(root, name):
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9.+-]{1,80}-[0-9a-f]{16}", name):
        raise UpdateError("Invalid cached version directory")
    path = Path(root) / "versions" / name
    if path.is_symlink() or not path.resolve().is_relative_to(Path(root).resolve()):
        raise UpdateError("Cached version escapes application cache")
    return path


def verify_cached(root, name):
    path = _directory(root, name)
    receipt_path = path / ".receipt.json"
    if receipt_path.is_symlink() or receipt_path.stat().st_size > MAX_METADATA:
        raise UpdateError("Invalid cache receipt")
    expected = parse_json(receipt_path.read_bytes())
    if not isinstance(expected, dict) or name != expected.get("version", "") + "-" + str(expected.get("sha256", ""))[:16]:
        raise UpdateError("Cached package receipt mismatch")
    manifest_path = path / PACKAGE_MANIFEST
    if manifest_path.is_symlink() or manifest_path.stat().st_size > MAX_METADATA:
        raise UpdateError("Invalid cached package manifest")
    manifest_data = manifest_path.read_bytes()
    if sha256(manifest_data) != expected.get("package_manifest_sha256"):
        raise UpdateError("Cached package manifest changed")
    manifest = package_manifest(manifest_data, expected)
    expected_names = {row["path"] for row in manifest["files"]} | {PACKAGE_MANIFEST, ".receipt.json"}
    actual = set()
    for item in path.rglob("*"):
        if item.is_symlink():
            raise UpdateError("Symbolic link in cached application")
        if item.is_file():
            relative = item.relative_to(path).as_posix()
            # Python is launched with -B; cached code must never acquire extras.
            actual.add(relative)
    if actual != expected_names:
        raise UpdateError("Cached package file set changed")
    for row in manifest["files"]:
        file = path / row["path"]
        if file.stat().st_size != row["size"] or sha256(file.read_bytes()) != row["sha256"]:
            raise UpdateError("Cached application file changed")
    return {"name": name, "path": path, "version": manifest["version"], "manifest": manifest,
            "archive_sha256": expected["sha256"]}


def stage_update(root, package, data):
    manifest, payloads = inspect_archive(data, package)
    name = package["version"] + "-" + package["sha256"][:16]
    root = Path(root)
    with cache_lock(root):
        final = _directory(root, name)
        if final.exists():
            return verify_cached(root, name)
        final.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=".stage-", dir=final.parent))
        try:
            for relative, value in payloads.items():
                dest = temporary / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                with dest.open("xb") as file:
                    file.write(value)
                    file.flush(); os.fsync(file.fileno())
            _atomic_json(temporary / ".receipt.json", {**package, "package_manifest_sha256": sha256(payloads[PACKAGE_MANIFEST])})
            if manifest["kind"] == "standalone" and manifest["platform"] == "linux":
                (temporary / "WBW").chmod(0o755)
            os.rename(temporary, final)
        finally:
            if temporary.exists():
                # This path is generated beneath our own verified cache only.
                shutil.rmtree(temporary)
        return verify_cached(root, name)


def installed_candidates(root, minimum):
    """Previously ready versions only, newest first; malformed cache is ignored."""
    state = read_state(root)
    result = []
    names = [state.get("active"), state.get("previous")]
    for name in dict.fromkeys(n for n in names if isinstance(n, str)):
        if not name:
            continue
        try:
            candidate = verify_cached(root, name)
            manifest = candidate["manifest"]
            if compatible(manifest, runtime_target()) and Version(candidate["version"]) > Version(minimum):
                result.append(candidate)
        except (OSError, UpdateError):
            continue
    return sorted(result, key=lambda c: Version(c["version"]), reverse=True)


def activate(root, candidate):
    """Call only after the supervised application reported ready."""
    candidate = verify_cached(root, candidate["name"])
    with cache_lock(root):
        state = read_state(root)
        old = state.get("active")
        if old and old != candidate["name"]:
            try:
                previous = verify_cached(root, old)
                if Version(previous["version"]) > Version(candidate["version"]):
                    return  # A concurrent launcher already activated a newer release.
                state["previous"] = old
            except (OSError, UpdateError):
                pass
        state["active"] = candidate["name"]
        _atomic_json(Path(root) / "state.json", state)


def reject(root, candidate):
    with cache_lock(root):
        state = read_state(root)
        rejected = state.get("rejected", [])
        safe_rejected = [n for n in rejected if isinstance(n, str)] if isinstance(rejected, list) else []
        state["rejected"] = list(dict.fromkeys([*safe_rejected, candidate["name"]]))[-20:]
        if state.get("active") == candidate["name"]:
            state["active"] = state.pop("previous", None)
        _atomic_json(Path(root) / "state.json", state)


def check_and_stage(root, current_version, transport=None, target=None):
    transport = transport or GitHubTransport()
    package = discover(current_version, transport, target)
    if package is None:
        return None
    name = package["version"] + "-" + package["sha256"][:16]
    rejected = read_state(root).get("rejected", [])
    if isinstance(rejected, list) and name in rejected:
        return None
    if _directory(root, name).exists():
        cached = verify_cached(root, name)
        if cached["archive_sha256"] != package["sha256"]:
            raise UpdateError("Cached archive digest does not match this release")
        return cached
    if isinstance(transport, GitHubTransport):
        # The launcher still waits only eight seconds. A slow standalone asset
        # can finish staging in the background while the working app runs, and
        # the next launch can reuse it without downloading it again.
        transport.deadline = time.monotonic() + 120
    return stage_update(root, package, transport.fetch(package["url"], package["size"]))

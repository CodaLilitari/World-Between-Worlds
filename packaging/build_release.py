"""Build deterministic allowlisted application ZIPs, never a workspace archive.

Run from any cwd: python packaging/build_release.py --out /path/to/artifacts
Standalone: add --binary /path/to/WBW --platform linux --arch x86_64
Use merge_manifests.py to combine the per-platform release metadata before upload.
"""
from __future__ import annotations
import argparse
from io import BytesIO
import json
from pathlib import Path
import re
import stat
import sys
import zipfile

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
import blackwing_update as update

# Metadata and recipe strings may name assets, but no such payload is collected.
PRIVATE_PATH = re.compile(rb"(?i)(?:[a-z]:[\\/]+(?:users[\\/]|codextemp[\\/])|[\\/]home[\\/][^\s/\\]+[\\/]|[\\/]users[\\/][^\s/\\]+[\\/])")
FIXED_DATE = (2026, 1, 1, 0, 0, 0)


def source_payloads(project=PROJECT):
    project = Path(project)
    result = {}
    redirects = {
        "Launch-WBW.bat": "packaging/Launch-WBW.bat",
        "launch-wbw.sh": "packaging/launch-wbw.sh",
        "WBW-README.md": "packaging/USER_GUIDE.md",
    }
    for name in sorted(update.SOURCE_FILES):
        path = project / redirects.get(name, name)
        if not path.exists():
            if name in update.SOURCE_REQUIRED:
                raise update.UpdateError("Missing required source package file: " + name)
            continue
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(project.resolve()):
            raise update.UpdateError("Source package input is not a local regular file: " + name)
        data = path.read_bytes()
        if PRIVATE_PATH.search(data):
            raise update.UpdateError("Personal absolute path in source package input: " + name)
        result[name] = data
    return result


def build_package(payloads, version, kind="source", system="any", arch="any", libc_min=None):
    update.Version(version)
    allowed = update.allowed_files(kind, system)
    if not set(payloads).issubset(allowed):
        raise update.UpdateError("Unallowlisted package payload")
    entry = "blackwing_launcher.py" if kind == "source" else ("WBW.exe" if system == "windows" else "WBW")
    manifest = {"schema": 1, "repository": update.REPOSITORY, "version": version,
                "kind": kind, "platform": system, "arch": arch, "python_min": [3, 10],
                "entrypoint": entry,
                "files": [{"path": name, "size": len(value), "sha256": update.sha256(value)}
                          for name, value in sorted(payloads.items())]}
    if kind == "standalone" and system == "linux":
        libc_min = libc_min or update.glibc_version()
        if libc_min is None:
            raise update.UpdateError("Use a native glibc Linux builder or explicitly provide the audited libc floor")
        manifest["libc_min"] = list(libc_min)
    manifest_data = update.json_bytes(manifest)
    update.package_manifest(manifest_data, manifest)
    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, value in sorted({**payloads, update.PACKAGE_MANIFEST: manifest_data}.items()):
            info = zipfile.ZipInfo(name, FIXED_DATE)
            info.create_system = 3
            executable = name in {"WBW", "launch-wbw.sh"}
            info.external_attr = (stat.S_IFREG | (0o755 if executable else 0o644)) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, value, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    data = output.getvalue()
    suffix = "source" if kind == "source" else f"{system}-{arch}"
    package = {"kind": kind, "platform": system, "arch": arch, "python_min": [3, 10],
               "filename": f"World-Between-Worlds-{version}-{suffix}.zip", "size": len(data), "sha256": update.sha256(data)}
    if "libc_min" in manifest:
        package["libc_min"] = manifest["libc_min"]
    update.inspect_archive(data, {**package, "version": version})
    return package, data


def write_release(out, version, package, data):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / package["filename"]
    # Never silently replace a release artifact whose bytes differ.
    if dest.exists() and dest.read_bytes() != data:
        raise update.UpdateError("Different artifact already exists at " + str(dest))
    dest.write_bytes(data)
    manifest = {"schema": 1, "repository": update.REPOSITORY, "version": version, "packages": [package]}
    fragment = out / (package["filename"][:-4] + ".release.json")
    fragment.write_bytes(update.json_bytes(manifest))
    return dest, fragment


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--version")
    parser.add_argument("--binary", type=Path)
    parser.add_argument("--platform", choices=("windows", "linux"))
    parser.add_argument("--arch", choices=("x86_64", "arm64"), default="x86_64")
    parser.add_argument("--libc-min", help="Audited major.minor glibc floor for a separately built Linux binary")
    args = parser.parse_args(argv)
    from blackwing_version import VERSION, REPOSITORY
    if REPOSITORY != update.REPOSITORY:
        parser.error("Repository configuration mismatch")
    version = args.version or VERSION
    if version != VERSION:
        parser.error("Set blackwing_version.VERSION to the release version before packaging")
    if args.binary:
        if not args.platform or not args.binary.is_file() or args.binary.is_symlink():
            parser.error("A regular built binary and --platform are required")
        name = "WBW.exe" if args.platform == "windows" else "WBW"
        payloads = {name: args.binary.read_bytes(), "LICENSE": (PROJECT / "LICENSE").read_bytes()}
        for notice in ("PYTHON-LICENSE.txt", "PYINSTALLER-COPYING.txt", "PYINSTALLER-NOTICE.txt"):
            path = args.binary.parent / notice
            if not path.is_file() or path.is_symlink():
                parser.error("Separately built binary requires adjacent " + notice)
            payloads[notice] = path.read_bytes()
        for name in ("NOTICE.md",):
            if (PROJECT / name).is_file():
                payloads[name] = (PROJECT / name).read_bytes()
        libc_min = None
        if args.libc_min:
            if not re.fullmatch(r"[0-9]{1,3}\.[0-9]{1,3}", args.libc_min):
                parser.error("--libc-min must be major.minor")
            libc_min = tuple(map(int, args.libc_min.split(".")))
        package, data = build_package(payloads, version, "standalone", args.platform, args.arch, libc_min)
    else:
        package, data = build_package(source_payloads(), version)
    dest, fragment = write_release(args.out, version, package, data)
    print(json.dumps({"archive": str(dest), "sha256": package["sha256"], "bytes": package["size"], "release_fragment": str(fragment)}, indent=2))


if __name__ == "__main__":
    main()

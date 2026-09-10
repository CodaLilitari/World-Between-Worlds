"""Build a local-platform PyInstaller executable from an allowlisted staging tree.

Install packaging/requirements-build.txt in a disposable virtual environment.
This does not install dependencies, download assets, invoke a shell, or publish.
"""
import argparse
import importlib.util
import importlib.metadata
from pathlib import Path
import re
import shutil
import subprocess
import sys
import sysconfig
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import blackwing_update as update
from build_release import source_payloads, build_package, write_release


def runtime_notices():
    candidates = [Path(sys.base_prefix) / "LICENSE.txt", Path(sys.base_prefix) / "LICENSE",
                  Path(sysconfig.get_path("stdlib")) / "LICENSE.txt"]
    python_license = next((p for p in candidates if p.is_file()), None)
    if python_license is None:
        raise update.UpdateError("Could not locate the build interpreter's Python license")
    result = {"PYTHON-LICENSE.txt": python_license.read_bytes()}
    distribution = importlib.metadata.distribution("pyinstaller")
    for name in ("COPYING.txt", "COPYING", "LICENSE.txt", "LICENSE"):
        matches = [p for p in distribution.files or [] if Path(str(p)).name == name]
        if matches:
            result["PYINSTALLER-COPYING.txt"] = distribution.locate_file(matches[0]).read_bytes()
            break
    if "PYINSTALLER-COPYING.txt" not in result:
        raise update.UpdateError("Could not locate PyInstaller's distribution license")
    result["PYINSTALLER-NOTICE.txt"] = (f"Built with PyInstaller {distribution.version}.\n"
        "PyInstaller bootloader is distributed under its GPL license with the stated bootloader exception.\n"
        "The bundled application code remains under its own MIT license.\n"
        "See PYINSTALLER-COPYING.txt and PYTHON-LICENSE.txt for the accompanying runtime notices.\n").encode()
    # Preserve the old native updater's accepted filenames. Tcl/Tk notices belong
    # in this existing notice file rather than a new, bootstrap-incompatible file.
    from PyInstaller.utils.hooks.tcl_tk import tcltk_info
    if not tcltk_info.available:
        raise update.UpdateError("The standalone builder needs Tcl/Tk for the native path chooser")
    python_terms = python_license.read_bytes()
    for component in ("tcl", "tk"):
        version = ".".join(map(str, getattr(tcltk_info, component + "_version")))
        data_dir = Path(getattr(tcltk_info, component + "_data_dir"))
        documents = [data_dir / "license.terms",
                     Path(sys.base_prefix) / "share/doc" / ("lib" + component + version) / "copyright"]
        if sys.platform.startswith("linux"):
            # A setup-python/venv interpreter can live outside /usr while its
            # Tcl/Tk shared libraries and distro notices still come from /usr.
            documents.append(Path("/usr/share/doc") / ("lib" + component + version) / "copyright")
        document = next((path for path in documents if path.is_file()), None)
        if document is not None:
            notice = document.read_bytes()
            origin = document.name if document.name == "license.terms" else document.parent.name + "/copyright"
        elif sys.platform == "win32":
            # Official Windows Python includes the Tcl license verbatim in its
            # combined LICENSE.txt, but does not always ship tcl8.6/license.terms.
            # Select the complete supplied Tcl/Tk paragraph, never paraphrase it.
            blocks = re.findall(
                rb"This software is copyrighted by the Regents of the University of[\s\S]*?"
                rb"terms specified in this license\.", python_terms)
            matches = [block for block in blocks if b"Scriptics Corporation" in block
                       and ((b"Apple Inc." in block) == (component == "tk"))]
            if len(matches) != 1:
                raise update.UpdateError("Could not identify the build interpreter's " + component + " license")
            notice, origin = matches[0], "Python LICENSE.txt"
        else:
            raise update.UpdateError("Could not locate the build interpreter's " + component + " license")
        if not notice.strip():
            raise update.UpdateError("Empty Tcl/Tk runtime license")
        heading = f"\n\n--- {component.upper()} {version} runtime notice ({origin}) ---\n"
        result["PYINSTALLER-NOTICE.txt"] += heading.encode("utf-8") + notice + b"\n"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, help="Optional empty build parent; build inputs are copied here from the explicit source allowlist")
    args = parser.parse_args(argv)
    if importlib.util.find_spec("PyInstaller") is None:
        parser.error("PyInstaller is not installed in this interpreter; use a disposable build virtual environment")
    target = update.runtime_target(frozen=True)
    if target[1] not in {"windows", "linux"}:
        parser.error("Standalone packaging supports native Windows and Linux builders")
    if args.work_dir:
        args.work_dir.mkdir(parents=True, exist_ok=True)
    # The temporary work tree contains only application code and UI, never retail
    # archives, audit reports or conversion outputs from the source directory.
    with tempfile.TemporaryDirectory(prefix="wbw-build-", dir=args.work_dir) as temp:
        work = Path(temp)
        source = work / "source"
        source.mkdir()
        for name, data in source_payloads().items():
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile",
                   "--name", "WBW", "--distpath", str(work / "dist"),
                   "--workpath", str(work / "work"), "--specpath", str(work)]
        for ui_name in ("index.html", "app.js", "styles.css", "coda-wbw.js"):
            ui_file = source / "ui" / ui_name
            if ui_file.is_file():
                command += ["--add-data", str(ui_file) + ":ui"]
        # Catalog selection uses importlib; explicitly include only the reviewed
        # modules staged above instead of relying on static-import discovery.
        for module in sorted(source.glob("*.py")):
            if module.stem.startswith("test_"):
                continue
            if module.stem != "blackwing_launcher":
                command += ["--hidden-import", module.stem]
            command += ["--add-data", str(module) + ":."]
        for document in sorted(source.rglob("*")):
            if document.is_file() and (document.suffix in {".md", ".txt"} or document.name in {"LICENSE", "recipes.json"}):
                parent = document.parent.relative_to(source).as_posix()
                command += ["--add-data", str(document) + ":" + parent]
        command += [str(source / "blackwing_launcher.py")]
        subprocess.run(command, cwd=source, check=True)
        name = "WBW.exe" if target[1] == "windows" else "WBW"
        binary = work / "dist" / name
        from blackwing_version import VERSION
        payloads = {name: binary.read_bytes(), "LICENSE": (source / "LICENSE").read_bytes(), **runtime_notices()}
        for notice in ("NOTICE.md", "WBW-README.md"):
            if (source / notice).is_file():
                payloads[notice] = (source / notice).read_bytes()
        package, data = build_package(payloads, VERSION, *target)
        dest, fragment = write_release(args.out, VERSION, package, data)
        print(f"Built {dest.name}: {package['sha256']}")
        print(f"Release fragment: {fragment}")


if __name__ == "__main__":
    main()

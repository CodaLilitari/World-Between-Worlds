# Application release packaging

The runtime uses Python's standard library. Source and standalone packages share
the same HTTPS release discovery, manifest validation, cache and ready-handshake
logic. `USER_GUIDE.md` is the allowlisted public package guide.

The original shortcut first validates and hands off to the newest previously
ready cached launcher. That launcher performs the release check with its own
updated policy; it is not permanently bypassed through `--run-app`. Handoffs
strictly increase the actual launcher version, propagate owned-process readiness,
and fall back when a cached launcher fails. `--no-update` also propagates.
Metadata discovery uses the eight-second startup budget. Once a compatible
package is selected, its bounded download may continue for up to two minutes in
the background after the app opens; the next launch reuses a verified stage.

The persistent bootstrap accepts a bounded forward-compatible code-file grammar:
root Python modules, `packaging/*.py` helpers and single-level UI JS/MJS/CSS/HTML
files, plus its exact documented file set. Every path still passes the ZIP safety,
hash, size and manifest checks. It does not accept GOB/GOO/COG/MAT/3DO or arbitrary
asset extensions. The maintainer's builder retains an exact `SOURCE_FILES`
allowlist and must deliberately add each new source file. New top-level data
formats or removal of the required core modules would require a reviewed package
contract change; do not describe such packages as compatible with this bootstrap.

Set `blackwing_version.VERSION` before building. The initial GUI release is
`0.2.0-rc1`. Source package:

```sh
python -B packaging/build_release.py --out artifacts
```

The builder copies an explicit application-file allowlist. It does not archive
the project directory. It rejects personal absolute paths in text inputs and
does not collect game assets, mod readmes, private evidence or generated
conversions. The source release includes an explicit list of public synthetic
tests, UI test files and maintainer documentation. A generated per-file manifest
lists the exact payload hashes.
The original Coda interface illustration is embedded as a PNG data URL in the
explicitly allowed `ui/coda-wbw.js`. Its decoded bytes match the native original
documented in `SCREENSHOTS.md`. Reference sheets and game screenshots are not
package inputs. This packaging preserves older launchers' code-file grammar.
Repeated source builds with identical input bytes produce identical ZIP bytes.

Standalone packages require a native platform builder; PyInstaller does not
cross-compile Windows binaries on Linux or vice versa. Use a disposable Python
virtual environment, install `requirements-build.txt`, then run:

```sh
python -B packaging/build_standalone.py --out artifacts
```

The build interpreter must include Tkinter and Tcl/Tk runtime data. PyInstaller's
normal Tk hooks bundle them for the explicit folder/file chooser; missing runtime
or license notices fail the build. Exact Tcl/Tk notices are appended to the existing
`PYINSTALLER-NOTICE.txt` so older native bootstraps accept the package file set.
The chooser is launched only by a user's Browse action in a separate helper
process. Tests must not open real desktop dialogs. Plain path entry remains
available when using source builds without Tk or without a desktop session.

The build stages only allowlisted inputs in a temporary tree and uses a fixed
entrypoint. Public documents are embedded at their exact relative paths for the
app's documentation routes; source modules are also embedded for recipe exports.
The resulting one-file executable is placed in a platform ZIP with the MIT,
Python, Tcl/Tk and PyInstaller notices and generated package manifest. Standalone reproducibility is
not claimed: the interpreter, OS and native toolchain must be recorded. A Linux
build records a conservative `libc_min` equal to its build system's glibc version.
The updater skips older glibc and musl installations. Ubuntu 22.04 CI therefore
targets glibc 2.35 or newer; a newer local Linux builder records its stricter
floor. Test each intended distribution. Windows CI uses Windows Server 2022 to produce a Windows executable;
Windows 11 runtime testing is a separate gate.

The actual workflow is `.github/workflows/release.yml`; `ci-release.yml` is an
identical copy included in source packages. It runs every public Python test and
the Node UI suite on Windows Server 2022 and Ubuntu 22.04 with Python 3.12 and
Node 22. It checks the committed `recipes.json` against the current source, builds
both native packages, verifies their archive manifests, and runs each executable
with `--version`. It requires two independent source-package builds to produce
identical bytes. Fixed ZIP metadata and build environment variables do not make
the native binary reproducible; native bit-for-bit reproducibility remains
unclaimed. The final job independently verifies all three packages and assembles
`wbw-release.json`. All action references are pinned to full official commit
SHAs with release-version comments. Workflow permissions are read-only.

Before dispatch, finish source changes, regenerate the recipe lock with
`python -B packaging/export_catalog.py --output recipes.json`, and commit the
reviewed source. Preserve LF source bytes through `.gitattributes`; both runners
disable Git automatic line-ending conversion before checkout. Once the workflow
exists on the public repository's default branch, use Actions **World Between
Worlds release packages**, **Run workflow**, or:

```sh
gh workflow run release.yml --repo andreipemberton/World-Between-Worlds
```

Select the intended branch in Actions when building a different ref. After the
run succeeds, download its `wbw-release-ready` artifact: it contains exactly the
three release ZIPs and merged `wbw-release.json`. Intermediate platform artifacts
include their individual manifest fragments. Artifacts expire after 14 days.
The run summary records the source commit and package hashes. This workflow
does not create a tag, publish a release, or enable automatic publication.

Collect the platform ZIPs and their `.release.json` fragments in one directory,
then combine them:

```sh
python -B packaging/merge_manifests.py artifacts/*.release.json --out artifacts/wbw-release.json
```

PowerShell does not expand wildcard arguments for all native commands. Pass the
three exact fragment paths there, or build the manifest in the provided Linux
CI job. Upload the exact ZIPs and `wbw-release.json` as assets of the public
release tagged `v<VERSION>` in `andreipemberton/World-Between-Worlds`. Do not use a
GitHub autogenerated source archive as an updater package. RC installs read the
published releases list because `/latest` excludes prereleases.

The release manifest binds version, repository, kind, OS/architecture, minimum
Python version, asset filename, byte length and SHA-256. The package manifest
binds the fixed launcher and every allowed file. The installer rejects extra
files, unsafe paths, Windows path aliases, encrypted members, symlinks and other
nonregular file types. HTTPS release identity is the trust root; hashes provide
integrity rather than independent publisher authentication.

Launcher readiness uses `BLACKWING_READY_FILE`. After binding loopback, the app
writes JSON `{ "pid": <own pid>, "url": "http://127.0.0.1:<port>/", "version":
"<VERSION>" }`. The launcher validates all three fields before activating the
cache version. Source readiness requires the exact child PID; standalone
readiness also accepts a verified descendant of its owned PyInstaller bootloader.
A failed candidate remains on disk for diagnosis and is excluded
from repeated attempts. Settings, game roots and outputs remain external.

Primary references: [GitHub releases API](https://docs.github.com/en/rest/releases/releases),
[GitHub release assets API](https://docs.github.com/en/rest/releases/assets),
[Python zipfile safety](https://docs.python.org/3/library/zipfile.html), and
[PyInstaller operating modes](https://pyinstaller.org/en/stable/operating-mode.html).

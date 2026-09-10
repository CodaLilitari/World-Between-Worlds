# World Between Worlds

JK to MotS conversion workbench. Supply your own legally owned game data and
original level archives. This application package contains conversion tooling,
reviewed recipes and original interface artwork; it contains no game or mod assets.

## First conversion

1. Extract the standalone ZIP and open WBW. It includes Python and its native
   folder chooser; no separate Python, Gradio, PyTorch or GPU installation is needed.
2. Click Browse for your Jedi Knight installation, then Browse for your MotS
   installation. Save folders if you want WBW to remember them. You can paste
   absolute paths instead when running without a supported desktop chooser.
3. Optionally click Scan MotS folder to check your installed conversions.
   Queue only the reported recipes you want to rebuild.
4. Choose a level or mod from the dropdown, then Add to queue. Repeat for more
   selections. The full library provides search and gameplay/category filters.
5. For each custom level or mod, Browse for its original ZIP/GOB. If you do not
   have it, Download original opens the reviewed source page in your browser.
   Download there, then explicitly select the local file when you return to WBW.
   The application does not automatically fetch or select community archives.
6. Click Convert selected. Output defaults to Documents/World Between Worlds
   conversions; optional advanced settings let you choose a separate destination.
7. Read the generated README beside each output for its exact installation and
   MotS launch instructions. Replace old installed copies after reviewing the
   new files; update required startup folders together. Keep originals separately.

The chooser selects one folder or one original archive at a time. Cancelling
keeps the previous value. Converting does not install, launch, combine, or load
mods. Ninja Kage 7.0 remains an optional prototype. The interface has no music
or audio. Source packages use Python 3.10+ and may need the operating system's
Tkinter desktop package for Browse; entering paths works without it.

## Launching and application updates

For the Python source package, install Python 3.10 or newer. On Windows 11,
run `Launch-WBW.bat`. On Linux, run `sh launch-wbw.sh`. The platform
standalone package runs `WBW.exe` or `./WBW` without a
separate Python installation. If your ZIP extractor drops the Linux executable
permission, run `chmod +x WBW` once.

The launcher checks published releases from `andreipemberton/World-Between-Worlds`
with an eight-second startup wait limit. If a compatible newer package finishes
verification in that window, it opens in the same invocation. Offline, a rate
limit, a timeout or a rejected package leaves the installed app available.
If a larger download exceeds the startup wait, it may finish staging in the
background while the current app runs, with a two-minute download limit. The next
launch can use that verified stage without downloading it again.
Release-candidate installations include later RCs and stable releases; stable
installations ignore prereleases. Use `--no-update` to skip the network check,
and `--no-browser` to start the local server without opening a browser.

Updates are staged in a versioned user-data cache. They do not overwrite this
downloaded folder, source checkouts, selected game installations or generated
conversions. A candidate becomes active only after its local server reports
ready. Early startup failure falls back to the previous working app. Both
application versions remain on disk; generated outputs and settings are kept
separately. Runtime gameplay compatibility is independent of updater validation.

User data defaults to `%LOCALAPPDATA%\World Between Worlds` on Windows and
`$XDG_DATA_HOME/world-between-worlds` (or `~/.local/share/world-between-worlds`) on
Linux. `BLACKWING_USER_DATA_DIR` can select a different location. The diagnostic
files `launcher.log` and `runtime/app-<version>.log` live there. Do not move game
assets into the application cache.

Update trust rests on HTTPS and the named GitHub repository's published release.
The updater verifies asset sizes, SHA-256 hashes, an exact file manifest, and
safe ZIP paths. These hashes do not provide an independent publisher signature
against compromise of that repository. Release metadata cannot name arbitrary
commands or alternate download hosts.

Each recipe now has its own revision, independent of the program version.
For example, Canyon exports as `bridge-canyon_wbw_v1.goo`. A future Canyon
recipe correction advances it to `wbw_v2`; an unrelated program update does
not mark every map outdated. The archive contains a checked revision record
so detection also works if you rename the GOO.

In the workbench, enter your MotS installation folder and click the installed
level scan button. The scan reads local GOOs and reports current, outdated,
newer, unversioned and changed files, including duplicates. It compares against
this installed WBW's catalog. It does not install, replace, delete or convert
anything. Queue only the reported recipes you want to regenerate, then review
the outputs and replace their old installed copies. All multiplayer participants
need matching files. Keep required startup overlays with their matching results.

Older exports without tracking metadata are reported as unversioned when their
legacy names are recognized. Reconvert these to get a tracked revision; renaming
an old GOO to `wbw_v1` does not make it current.

For a read-only JSON report without opening the workbench or checking application
updates, use one of these commands:

```text
WBW.exe --scan-mots "C:\Games\Mysteries of the Sith"
./WBW --scan-mots /games/mots
python blackwing_app.py --scan-mots /games/mots
```

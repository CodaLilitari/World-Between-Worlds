# World Between Worlds

JK to MotS conversion workbench. Supply your own legally owned game data and
original level archives. This application package contains conversion tooling
and reviewed recipes; it contains no game or mod assets.

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

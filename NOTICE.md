# World Between Worlds: provenance and asset boundary

World Between Worlds is an independent JK-to-MotS conversion workbench. It is
separate from [OpenJKDF2-MotS-Fixes](https://github.com/andreipemberton/OpenJKDF2-MotS-Fixes)
and from upstream OpenJKDF2. It does not contain an engine executable.

Original tooling: Andrei Pemberton, with Coda Lilitari. The GitHub and Git
account is the actual `andreipemberton` account. Coda Lilitari is a human-facing
collaboration credit, not an invented account or an additional map author.

The MIT license applies to the original World Between Worlds software and documentation.
It does not relicense Jedi Knight, Mysteries of the Sith, community levels,
mods, their assets, or third-party runtime components. The source contains
hashes, filenames, reviewed transformation rules and small matching/edit
anchors needed to reproduce conversions. Original game/mod archives and full
asset payloads are not distributed with the application.

Users supply their own game installations and the exact original custom
archives identified in `SUPPORTED_CUSTOM_SOURCES.txt`. World Between Worlds reads required
resources locally, applies the selected recipes, and writes generated files to
a separate chosen output folder. It does not download paid game data, bypass
copy protection, upload source files, or publish converted game assets.

Each generated `blackwing-receipt.json` records the input hashes, exact recipe
lock, source module hashes, output member hashes and verification result.
`blackwing-recipe.json` records the recipe independently. Export selected
recipes exports instructions and provenance; it includes no game payloads.
Generated levels/mods can still contain copyrighted assets and remain subject
to their original authors' terms. A conversion receipt grants no redistribution
permission. Original author credits remain attached to each catalog entry.

Screenshots in the repository document observed engine output for selected
conversions. They are illustrative test evidence, not reusable game assets,
and are not part of the conversion payload or updater packages. Their captions
identify the source, runtime, mode, camera staging and test limitations.

The World Between Worlds name/theme is an unofficial community-tool presentation.
The wing emblem and interface illustration are original. The Light Sith Coda
illustration was generated for this application from the user's canonical Coda
reference; it is original fan art, not extracted game art or a film screenshot.
No game/mod payload is hidden in the illustration. Its native PNG, generation
prompt and provenance are documented in SCREENSHOTS.md. The private character
reference sheet is not distributed. No official Star Wars logo, Lucasfilm or
LucasArts affiliation or endorsement is claimed. This notice does not grant
rights to third-party characters, settings or trademarks.

Standalone builds include a Python runtime, Tcl/Tk chooser runtime and PyInstaller bootloader, with
their license notices beside the executable. Build dependencies are not needed
to run the standalone packages. The Python source package uses only the Python
standard library at runtime.

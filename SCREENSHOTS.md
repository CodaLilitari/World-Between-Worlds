# Original JK and converted MotS views

These six images are actual 1280 × 960 game framebuffer captures from three
multiplayer levels. The left column uses the original archive in OpenJKDF2's
JK mode; the right column uses the locally converted archive in its MotS mode.
The original column does not use the retail JK executable.

| Map | Original JK | Converted MotS |
| --- | --- | --- |
| Canyon Oasis | ![Canyon Oasis in JK mode](https://raw.githubusercontent.com/andreipemberton/World-Between-Worlds/main/docs/screenshots/canyon-jk.png) | ![Canyon Oasis converted for MotS](https://raw.githubusercontent.com/andreipemberton/World-Between-Worlds/main/docs/screenshots/canyon-mots.png) |
| Jedi's High School 1.0, PeD_HeAd | ![Jedi's High School in JK mode](https://raw.githubusercontent.com/andreipemberton/World-Between-Worlds/main/docs/screenshots/jhs-jk.png) | ![Jedi's High School converted for MotS](https://raw.githubusercontent.com/andreipemberton/World-Between-Worlds/main/docs/screenshots/jhs-mots.png) |
| Nar Shaddaa Loading Terminal | ![Nar Shaddaa in JK mode](https://raw.githubusercontent.com/andreipemberton/World-Between-Worlds/main/docs/screenshots/narshaddaa-jk.png) | ![Nar Shaddaa converted for MotS](https://raw.githubusercontent.com/andreipemberton/World-Between-Worlds/main/docs/screenshots/narshaddaa-mots.png) |

In each pictured pair the camera matrix, sector and field of view match.
Inspection found the corresponding visible geometry and materials present.
These views provide useful evidence that converted geometry, textures and
lighting render. A single view cannot establish complete traversal or every
surface, trigger, weapon and multiplayer interaction.

A private diagnostic build enabled hidden rendering and framebuffer capture,
with the camera placed at the authored first multiplayer spawn plus a fixed
eye-height offset. Both modes used the same build, based on the tested
OpenJKDF2-MotS-Fixes runtime. The diagnostic changed no map, lighting or shader
data. These are original framebuffer images without resizing, retouching,
compositing or image generation. Animation phases were not synchronized to an
exact simulation tick. The native starting weapons differ: JK shows a Bryar
pistol and MotS shows a green lightsaber. These are not matched weapon loadouts.

[Machine-readable provenance](https://github.com/andreipemberton/World-Between-Worlds/blob/main/docs/screenshots/provenance.json) records the
capture method, runtime and archive hashes, image hashes, settings, source URLs,
and the limits of the observations. The reviewed originals are listed in
[SUPPORTED_CUSTOM_SOURCES.txt](SUPPORTED_CUSTOM_SOURCES.txt).

The screenshots illustrate compatibility and preserve the original game's and
level author's attribution. They are documentation in the repository; they are
excluded from the source, native application and updater ZIPs. The application
packages contain no game assets. See [NOTICE.md](NOTICE.md).

## Selecting a mod to convert

![Ninja Kage as a selectable prototype](https://raw.githubusercontent.com/andreipemberton/World-Between-Worlds/main/docs/screenshots/ninja-selectable-prototype.png)

This unedited 1480×1040 screenshot shows Ninja Kage selected in an isolated
headless Chrome test, with the prototype limit and separate mod output explained.
The visible folder examples are empty-field placeholders; the screenshot was
taken before entering local paths. The accompanying browser test checked that a
map-only conversion omits Ninja entirely, while explicitly selecting both creates
separate results. [Screenshot and conversion provenance](docs/validation/ninja-selection-20260908.json)
records the exact source and output hashes. Conversion does not launch a game or
load the resulting mod.

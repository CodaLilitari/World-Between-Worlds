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
separate results. [Screenshot and conversion provenance](https://github.com/andreipemberton/World-Between-Worlds/blob/v0.2.0-rc1/docs/validation/ninja-selection-20260908.json)
records the exact source and output hashes. Conversion does not launch a game or
load the resulting mod.

## Native MotS selection of converted CTF episodes

![The Duel selected in the native MotS host menu](https://raw.githubusercontent.com/andreipemberton/World-Between-Worlds/v0.2.0-rc2/docs/screenshots/ctf-host-duel.png)

The existing **Choose Episode** list offers the converted CTF episodes alongside
the stock MotS episodes. The native OK result returned the correct TYPE 8 map
for [The Duel](https://raw.githubusercontent.com/andreipemberton/World-Between-Worlds/v0.2.0-rc2/docs/screenshots/ctf-host-duel.png),
[The Arena of Dark and Light](https://raw.githubusercontent.com/andreipemberton/World-Between-Worlds/v0.2.0-rc2/docs/screenshots/ctf-host-arena.png)
and [The Challenge at Nar Shaddaa](https://raw.githubusercontent.com/andreipemberton/World-Between-Worlds/v0.2.0-rc2/docs/screenshots/ctf-host-challenge.png).
Long episode titles clip within the original list box; the selected level is
shown in the lower box. CTF is selected through the episode rather than a separate
game-mode button. No CTF-specific host-menu change was added.

![Native MotS personality choices](https://raw.githubusercontent.com/andreipemberton/World-Between-Worlds/v0.2.0-rc2/docs/screenshots/mots-native-personalities.png)

The native character form distinguishes **Mysteries of the Sith (personalities)**
from **Jedi Knight (ranked Jedi only)**. The test used the four native personality
choices, saved each character and reloaded all four with the room fields returned
by the CTF host menu. The [Scout selection capture](https://raw.githubusercontent.com/andreipemberton/World-Between-Worlds/v0.2.0-rc2/docs/screenshots/ctf-load-scout.png)
shows The Duel, the selected saved character and its Scout personality together.

These five original 1280 × 960 PNGs are unchanged captures from a fifteen-frame
native-menu replay on the pinned e9-based private diagnostic. The driver invoked
normal in-process GUI handlers and read its own hidden window framebuffer; it
used no physical OS input, synthetic image, retouching or resizing. The
[sanitized evidence](https://github.com/andreipemberton/World-Between-Worlds/blob/v0.2.0-rc2/docs/validation/ctf-native-menu-20260908.json)
records exact provenance and image hashes. No network game was started by this
GUI test, so the images do not establish flag mechanics, scoring or multiplayer
personality behavior. These are repository documentation only; all five are
excluded from application and updater ZIPs.

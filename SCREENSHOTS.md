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

## Restored Force allocation in the Ninja conversion

These additional images are actual native multiplayer character-menu renders
from the corrected Ninja Kage conversion in MotS mode. The automated test used
native menu callbacks to create a rank-five Jedi, allocate/reset/refund points,
exercise Defense restrictions, and save the resulting character. A separate
process reloaded the saved ranks and appearance. No direct rank or power grants
were used.

| Available at rank five | Three points in each power | Disabled by Defense |
| --- | --- | --- |
| ![Throw and Lightning available](https://raw.githubusercontent.com/andreipemberton/World-Between-Worlds/main/docs/screenshots/ninja-force-available.png) | ![Throw and Lightning allocated](https://raw.githubusercontent.com/andreipemberton/World-Between-Worlds/main/docs/screenshots/ninja-force-allocated.png) | ![Throw and Lightning disabled](https://raw.githubusercontent.com/andreipemberton/World-Between-Worlds/main/docs/screenshots/ninja-force-disabled.png) |

The added icons retain their original 28×28 shapes. Their colors are remapped
into the actual MotS menu palette, with visibly distinct dark disabled states.
The displayed rank-five budget starts at fifteen stars; allocating three to
each restored power leaves nine on screen. Native multiplayer save behavior
discards unspent allocation stars on exit, so the saved character's spend field
is zero. This is not a campaign-progression test.

All 43 native actions and 42 rendered frames passed the independent checks.
The native keyboard list showed **Force Throw / H** and **Force Lightning / L**;
F2/F3/F4 bindings also matched their inventory actions. Mouse-hover hints and
physical mouse/keyboard operation were not exercised. Menu evidence does not
establish combat, respawn, other personalities or compatibility of the separate
stock-MotS Force add-on.

These unretouched 1280×960 OpenGL framebuffer PNGs were captured in a hidden,
unfocused game window. The private test driver is excluded from releases.
[Exact runtime, GOO, save and image provenance](https://github.com/andreipemberton/World-Between-Worlds/blob/main/docs/validation/ninja-force-ui-20260908.json)
records the test boundary and hashes without distributing the game or profile
payloads.

# How a conversion is saved and replayed

World Between Worlds accepts reviewed original versions. It does not ask an AI model to
reconstruct a conversion when the user clicks a map. The work for each supported
map/mod is already executable code and pinned recipe data in the release.

`recipes.json` is the published asset-free snapshot of those recipe locks. The
workbench's Details view and Export selected recipes expose the same records.
They include the source ZIP/GOB/world hashes, declared dependency and script
sets, counted edits, reviewed original omissions, native overrides, and the
SHA-256 hashes of the converter modules that implement shared transformations.
The module hashes matter: a rule plus its versioned implementation defines the
conversion more precisely than a prose description alone.

The converter resolves needed resources from the selected original archive and
the user's owned JK/MotS installations. Its maps use explicit override order,
safe archive paths, namespaced resources/template names and individually reviewed
inventory/COG adjustments. It will reject an unreviewed original hash, an edit
anchor whose occurrence count changed, or an unexpected unresolved dependency.
Known original omissions are narrow named exceptions with recorded evidence;
there is no general ignore-missing switch.

Each generated result includes:

- The converted GOO and its member/source manifest.
- A per-recipe `wbw_vN` filename suffix and embedded revision record, for
  example `bridge-canyon_wbw_v1.goo`.
- Any startup overlay required before inventory/player/model initialization.
- `blackwing-recipe.json`: the exact recipe lock used for that conversion.
- `blackwing-receipt.json`: the lock, original/owned input hashes, generated-file
  hashes and independent structural verification result.

The receipts are local artifacts. The application package contains no retail
or original community asset payloads, and Export selected recipes contains no
generated GOO. Repeating a conversion with the same recipe implementation and
matching inputs must produce identical game archive bytes. Different converter
versions can have different receipt/recipe hashes even if a particular map's
game bytes remain unchanged.

The recipes use separate paths for stock maps, custom map episodes and startup
gameplay mods. A mod such as Ninja Kage has no fictitious level added to it.
Multiple selected results stay separate; selecting multiple recipes never means
loading their gameplay overlays together.

Map locks also record `mots-force-pickups-v2-native-visuals`: hashes of the owned
native Force Boost and Surge scripts, models, materials and template bindings,
counted edit anchors, and explicit source-to-output
bindings. The generated manifest records each adapted script's source and output
hash. Both JK Surge locations inherit one MotS-compatible surge controller and
timer. Force pickups use native neutral MotS models, while their original
positions and authored respawn values remain. The native Boost script animates
the native material used by its model. Multiplayer refill limits use the active
maximum in bin 69. This is a map compatibility rule, not the separate Force-power
restoration mod, and does not select or load Ninja Kage. Exported recipe locks
contain instructions and hashes only, never the full source or converted COGs.

## Installed recipe revisions

Application releases and conversion revisions are separate. `0.2.0-rc4` is an
application release; `wbw_v1` is the first explicitly tracked revision of an
individual recipe. The integers in `blackwing_revisions.RECIPE_REVISIONS` must
be advanced only for recipes whose conversion behavior or required output
changes. A shared compatibility fix must advance every affected recipe.
Documentation, UI or unrelated recipe changes do not make all maps outdated.
Keep those revision changes in source control alongside the code and tests.

After the normal structural verifier passes, the workbench stamps each generated
GOO, including required startup GOOs, with `wbw/recipe.json`. This contains the
recipe ID, its integer revision, application version, primary/startup role,
recipe-lock hash and a SHA-256 checksum of the canonical game payload before
stamping. It contains no game asset data. Every original game-resource member
stays byte-identical. The final archive receives `_wbw_vN` before `.goo`; legacy
trailing `-vN` or `-rcN` labels are replaced. The stem must fit the engine's
31-byte episode identifier limit.

The original payload manifest remains unchanged. A new tracked-conversion
manifest binds that verified payload, the metadata and the final archive hash.
The independent verifier accepts marked archives after checking recipe identity,
role and the payload checksum, then verifies the actual game payload separately.
The receipt records all final files. Filename version numbers provide a visible
hint; the scanner reads and checks the embedded record even after a file is
renamed. The checksum detects accidental payload changes; it is not a publisher
signature. The low-level `bridge.py` candidate-building commands still produce
raw, untracked developer candidates; the workbench conversion service performs
the revision-stamping step.

Use the explicit installation scan to compare against the recipe catalog in the
currently running WBW application. Current, older, newer, unversioned, modified
and unrecognized archives are reported separately. An old filename such as
`bridge-canyon-v1.goo` predates this scheme; it is not proof of `wbw_v1`.
Legacy filename matches are labeled unversioned, and unknown files are never
assigned a current revision from their filename alone. Duplicates are reported
because installing a new GOO beside an older one can leave both available.

Scanning is read-only and does not fetch original archives, launch the game,
convert a queue, install files, or remove old copies. Filesystem links are not
followed; bounded traversal and read limits are reported if reached. Select
only the recipes you want to regenerate, retain the original source archives,
and replace the old installed copies after reviewing the new outputs. Required
startup folders must be updated together with their corresponding levels.

The map recipe also expands `World cogs` for the additional native template
instances, while preserving the original declared budget and its spare slots.
This budget is separate from the compiled script table and from inventory's
static world. Every explicit `cog=` binding consumes an instance even if another
template already uses the same filename; inheritance shares the existing
instance. The output manifest records the source budget, added bindings, final
minimum and chosen capacity. The verifier computes them independently.

Maintainers regenerate the published catalog after the final source changes:

```text
python packaging/export_catalog.py --output recipes.json
```

That command exports metadata only. It does not convert all maps or read game
assets. Actual conversion still requires an explicit selection and local inputs.


---

# Detailed conversion reference

The following developer reference was moved out of the main README for RC4. Low-level candidate commands are optional; use the workbench for tracked end-user conversions.

## Conversion engine and command line

An original Python tool that builds experimental OpenMotS episodes locally from
the user's existing Jedi Knight and Mysteries of the Sith archives. It accepts
all nine maps in the pinned retail JK multiplayer episodes, authentic **Jedi Dojo
by Tee**, the reviewed original **Caesar's Palace**, and fifteen additional
community maps, including the recovered original **Jedi's High School**. Each recipe is
specific to audited source hashes; this is not a converter for arbitrary maps
or archive revisions.

This project contains original code, synthetic tests, and conversion recipes,
with no retail or community level
assets. Generated game assets must remain in a separate local directory.

All nine stock maps, Dojo, and Caesar's final v3 recipe have completed measured,
isolated 60-second multiplayer host runs with advancing simulation. The earlier
CTF runs did not check the active flag descriptor. All three CTF maps subsequently
passed fresh 60-second host runs with the required startup overlay mounted and
active bin 81 observed as `redflag`; neighboring native descriptors remained
unchanged. These checks establish descriptor loading and simulation, with HUD
rendering, traversal, visuals, combat, map mechanics, CTF scoring, and two-peer
synchronization still requiring gameplay checks. The builder labels each manifest
`structurally-built-gameplay-unverified`. See [VALIDATION.md](VALIDATION.md) for
exact evidence and remaining checks.

The fifteen new community candidates also pass independent verification and
60-second MotS multiplayer host checks. Targeted runtime observations confirm
Morpheus's template parameters, Jawa's active rapid-fire weapon script,
Stargate's unarmed inventory and Drazen's treasure-item flags. These checks are
documented separately from full gameplay acceptance in COMMUNITY_RC1.md and
VALIDATION.md. Use a runtime including the backpack fix in fork commit
`4dc57962e46a72662b59d36c30f15eacef6234b5` for Drazen's item-transfer behavior;
the converter does not modify the engine executable. A private game-script
comparison reproduced the old lost item and recovered it on the corrected build.

Matched-camera JK/MotS screenshots are available for Canyon Oasis, Jedi's High
School and Nar Shaddaa. A separate JHS comparison also passed the authored
open/close cycle of one door and the lower/return cycle of one elevator in both
games. These bounded checks and their remaining gameplay limits are recorded in
[VALIDATION.md](VALIDATION.md).

## Supported stock maps

The first six maps come from `Episode/JK1MP.GOB`; the three CTF maps come from
`Episode/JK1CTF.GOB`. Each output is a separate single-level episode.

| Recipe key | Original title | Source JKL | Output from `--all` |
|---|---|---|---|
| `nar-shaddaa` | Nar Shaddaa Loading Terminal | `m2.jkl` | `bridge-narshaddaa-v1.goo` |
| `bespin` | Bespin Mining Station | `m4.jkl` | `bridge-bespin-v1.goo` |
| `blades-of-death` | Blades of Death | `m5.jkl` | `bridge-blades-v1.goo` |
| `canyon-oasis` | Canyon Oasis | `m10.jkl` | `bridge-canyon-v1.goo` |
| `valley` | The Valley of the Jedi Tower | `m_boss15.jkl` | `bridge-valley-v2.goo` |
| `battleground` | Battleground Jedi | `m_boss17.jkl` | `bridge-battleground-v1.goo` |
| `ctf-duel` | The Duel | `c1.jkl` | `bridge-ctf_duel-v1.goo` |
| `ctf-arena` | The Arena of Dark and Light | `c2.jkl` | `bridge-ctf_arena-v1.goo` |
| `ctf-challenge` | The Challenge at Nar Shaddaa | `c3.jkl` | `bridge-ctf_challenge-v1.goo` |

## Build and verify

Use Python 3.10 or later; no third-party packages are required. From this source
folder, set paths to your own installations and a separate output directory:

```powershell
$jkGameRoot = 'D:\Games\Jedi Knight'
$motsGameRoot = 'D:\Games\Mysteries of the Sith'
$stockOutput = 'D:\Mod Experiments\stock-bridge'
python -m unittest -v
python bridge.py convert-stock --jk-root $jkGameRoot --mots-root $motsGameRoot --all --output $stockOutput
python verify_retail.py --jk-root $jkGameRoot --mots-root $motsGameRoot --all-stock-dir $stockOutput
```

`--all` writes the nine filenames above, each with an adjacent `.manifest.json`,
and the mandatory shared `bridge-ctf-ui` startup directory described below. It
preflights destinations and builds all candidates before writing. Existing episode
archives or manifests are refused; an existing startup directory is reused only
if its exact three files match. An I/O failure during writing can leave completed
files; the output set is not written as an atomic transaction.

For one map, `--output` names a file:

```powershell
$canyonOutput = 'D:\Mod Experiments\canyon.goo'
python bridge.py convert-stock --jk-root $jkGameRoot --mots-root $motsGameRoot --map canyon-oasis --output $canyonOutput
python verify_retail.py --jk-root $jkGameRoot --mots-root $motsGameRoot --stock-map canyon-oasis --archive $canyonOutput
```

The builder's `--map` accepts a recipe key, exact title, or source JKL name/stem,
case-insensitively; `--map "Canyon Oasis"` and `--map m10.jkl` select the same
recipe. The verifier's `--stock-map` accepts the stable keys in the table.
`convert-valley` and `convert-battleground` remain available as shorthands.
`--all-stock-dir` uses the verifier's independent source-world table to check all
nine named outputs and the mandatory startup overlay in `bridge-ctf-ui`. It cannot
be combined with `--archive` or custom-level flags. Individual CTF verification
also requires the overlay, defaulting to `bridge-ctf-ui` beside the episode GOO;
`--ctf-startup DIR` selects a different overlay directory.

The common retail inputs are:

| Installation | Required archives |
|---|---|
| Jedi Knight | `Episode/JK1MP.GOB`, `Resource/Res2.gob`, `Resource/Res1hi.gob` |
| Mysteries of the Sith | `episode/JKM_MP.GOO`, `resource/JKMRES.GOO`, `resource/JKMSNDLO.GOO` |
| Additional for Battleground Jedi | JK `Episode/JK1.GOB` |
| Additional for the three CTF maps | JK `Episode/JK1CTF.GOB` |

Building all stock maps therefore requires all eight archives. `bridge.py`
contains their exact SHA-256 pins, the stock world hashes, and reviewed COG sets.
Both JK resource archives are required. Optional `--baselines` retains the
original lab layout and is used instead of both game-root flags.

Choose fresh output paths outside this source project. The builder does not
launch the game or alter a profile. To test an output, place a copy in the
`episode` directory of an isolated installation and launch OpenJKDF2/OpenMotS in
MotS mode. CTF additionally requires the startup installation and launch arguments
below. Compatibility with the 1998 retail MotS executable is not established.

Each output contains `episode.jk`, its `jkl/br_*.jkl`, level strings, and dependency
payloads. The adjacent manifest records source archives, resource paths and hashes,
output names, generated hashes, and reviewed original omissions.
`python bridge.py inventory <archive>` prints an inventory without extracting
files. The GOB/GOO reader checks directory and payload bounds, overlaps, unsafe
paths, Windows device names, case collisions, legacy encoding, and length
constraints. The writer emits deterministic version-20 archives and reopens them
to verify their bytes.

## Required CTF startup overlay

The engine initializes inventory before selecting an episode. A copy of
`misc/items.dat` inside a CTF episode therefore cannot supply the startup flag
descriptor by itself. `convert-stock --all`, or `--map` selecting any of the three
CTF recipes, automatically creates `bridge-ctf-ui` beside the episode output(s),
containing exactly:

- `bridge-ctf-ui.goo`, containing only the adapted native `misc/items.dat`;
- `bridge-ctf-ui.manifest.json`, recording source and output hashes;
- `README.txt`, with installation and launch instructions.

For CTF episodes already generated, build the same overlay separately:

```powershell
$ctfStartup = 'D:\Mod Experiments\stock-bridge\bridge-ctf-ui'
python bridge.py build-ctf-startup --mots-root $motsGameRoot --output $ctfStartup
python verify_retail.py --jk-root $jkGameRoot --mots-root $motsGameRoot --all-stock-dir $stockOutput
```

The helper requires the pinned native `JKMRES.GOO` and `JKMSNDLO.GOO`. It refuses
a source-project destination or an existing overlay with missing, changed, or
extra files. The verifier independently checks that the overlay GOO contains
only `misc/items.dat` and that only bin 81's descriptor name differs from native
MotS. Packaging checks alone do not establish that an engine process loaded it.

To play a converted CTF episode:

1. Copy the whole `bridge-ctf-ui` directory beside an isolated runtime's
   `resource` and `episode` directories, preserving its name and three files.
2. Put the selected converted CTF GOO(s) in that runtime's `episode` directory.
3. From the runtime working directory, launch the engine with arguments
   `-motsCompat -path bridge-ctf-ui`, then select the CTF episode in Multiplayer.
4. Every host and client must start with the same overlay. Restart the engine
   without `-path bridge-ctf-ui` before playing other modes.

In MotS mode, use the host menu's **Choose Episode** list: select **CTF - The Duel -
MotS bridge prototype**, **CTF - The Arena of Dark and Light - MotS bridge prototype**,
or **CTF - The Challenge at Nar Shaddaa - MotS bridge prototype**, then its level and
**OK**. These reviewed episodes retain TYPE 8 and their original CTF controllers;
there is no separate CTF button to add. RC6 introduces the visible **CTF -** prefix
and advances only these three level recipes to **wbw_v2**. Their other game members
and the startup-mod payload are unchanged from RC5. The UI flags the additional
mod before selection, in the queue, in Details and with each completed result.

A native-menu test selected all three episodes and checked
their actual returned map names. It also created, saved and reloaded all four
MotS personalities using the native character menus. The production host and
character menus needed no CTF-specific patch. See the
[native menu evidence](https://github.com/andreipemberton/World-Between-Worlds/blob/v0.2.0-rc2/docs/validation/ctf-native-menu-20260908.json)
and [screenshots](SCREENSHOTS.md). This establishes menu selection, not flag
pickup, capture, scoring or multiplayer personality behavior.

For example, with the engine executable in the current runtime directory:

```powershell
.\openjkdf2.exe -motsCompat -path bridge-ctf-ui
```

Use the short relative `-path` value shown here. The engine's command-line parser
splits on whitespace, so quoting a spaced absolute `-path` is unreliable; the
runtime working directory itself can contain spaces. Keep this overlay separate
from SBX, Manowar, KFY, and other mods. Extra GOO files or loose `misc/items.dat`
overrides can change resource precedence. The generated `README.txt` also gives
optional multiplayer autostart arguments for each CTF episode.

This requirement also applies to future custom CTF recipes, with their own
reviewed mod instructions when they use a different system. The current custom
catalog has no enabled CTF conversion. Neither TYPE 8 alone nor a `ctf` filename
proves capture-the-flag behavior; inspect the original controllers and objectives.
See [the CTF review and historical-port comparison](docs/validation/CTF_REVIEW_2026-09-25.md).

## Jedi Dojo

Obtain the original [Jedi Dojo archive from Massassi](https://www.massassi.net/levels/files/429.shtml).
The recipe accepts the authentic ZIP or its extracted GOB:

```powershell
$dojoInput = 'D:\Mod Downloads\dojo.zip'
$dojoOutput = 'D:\Mod Experiments\dojo.goo'
python bridge.py convert-dojo --jk-root $jkGameRoot --mots-root $motsGameRoot --level-archive $dojoInput --output $dojoOutput
python verify_retail.py --jk-root $jkGameRoot --mots-root $motsGameRoot --dojo-archive $dojoInput --archive $dojoOutput
```

The ZIP SHA-256 is
`27f6a44f209cdc8fcebfe0fffd3230b2e7cbc1cf5982ef07133b10bdc70bc4da`;
`dojo.gob` is
`6ce07727918159fefd9f5cb8728bf4a618263a44d3a414fa365ea26c35954910`.
The original readme credits Tee, dates the level June 1999, and permits derivative
levels with credit. The generated level preserves its original credit text.
That permission does not make included retail resources freely redistributable.

The existing Dojo recipe retains its level-introduction and wooden-crate actor
COGs. Template defaults are rewritten by symbol type; numeric placement arguments
and credit strings are preserved. Its nine wooden crates use the original
`actor_wc.cog`, which compares against undeclared `totaldamage`; the current
engine initializes unknown identifiers to zero. The JK and MotS script versions
are identical. This inherited behavior is preserved, with repeated damage, crate
destruction, drops, and replication still awaiting gameplay checks.

## Caesar's Palace

The recipe now accepts the reviewed original
[Caesar's Palace archive by WAR_Shockwave](https://www.massassi.net/levels/files/1400.shtml)
while preserving its exact original omissions. The ZIP SHA-256 is
`b7a9f16b9141a4ef56c97784ef5a49914655a87ad6db59a2014429ee6ffe5fbd`;
`caesars.gob` is
`56393dc8b9c855e06799650d08dfe24268344d1fe3f6972140e2525ac3a4e3f0`.

```powershell
$caesarsInput = 'D:\Mod Downloads\caesars.zip'
$caesarsOutput = 'D:\Mod Experiments\caesars-v3.goo'
python bridge.py audit-caesars --jk-root $jkGameRoot --mots-root $motsGameRoot --level-archive $caesarsInput
python bridge.py convert-caesars --jk-root $jkGameRoot --mots-root $motsGameRoot --level-archive $caesarsInput --output $caesarsOutput
python verify_retail.py --jk-root $jkGameRoot --mots-root $motsGameRoot --caesars-archive $caesarsInput --archive $caesarsOutput
```

Earlier tooling rejected the level because eleven declared resources were
absent. That established missing declarations, not an unloadable map. Inspection
of their actual use and the current port's loaders corrected that diagnosis:

- Nineteen world surfaces reference `windowout.mat`, `floor1.mat`, or
  `window2.mat`; all nineteen have non-rendered geometry mode 0. `tv.mat`,
  `disco.mat`, and `discofloor.mat` have animation references but no world surfaces.
- `00_glass.mat` is absent despite being declared by the original shard model;
  its only face is untextured and has no texture vertices. The map also lists
  that material. This does not by itself prove a broken visible glass texture.
- `kk60008.wav`, `none.wav`, and `trap.wav` remain absent. The voice instance
  overrides the first with `none.wav`; intentional silence is a possible
  explanation, not established author intent. Trap playback and projectile
  behavior are separate operations and still need individual tests.
- `riverthrust.cog` is absent. Its original placement and all fifty arguments
  remain recorded; no replacement script or guessed behavior is supplied.

The current port [falls back to `dflt.mat` for missing materials](https://github.com/andreipemberton/OpenJKDF2-MotS-Fixes/blob/f40e965bbe4133aef9e9b9eccabb2fbf0a34a9fb/src/World/sithMaterial.c#L141),
[skips a missing COG instance](https://github.com/andreipemberton/OpenJKDF2-MotS-Fixes/blob/f40e965bbe4133aef9e9b9eccabb2fbf0a34a9fb/src/Cog/sithCog.c#L533),
and [returns failure from missing sound playback without stopping the caller's COG](https://github.com/andreipemberton/OpenJKDF2-MotS-Fixes/blob/f40e965bbe4133aef9e9b9eccabb2fbf0a34a9fb/src/Cog/sithCogFunctionSound.c#L22).
Those mechanisms explain why absence alone is insufficient to diagnose failure;
they do not recover omitted content or establish that every omission is harmless.

The exception is restricted to those eleven names, their exact original
referrers, and pinned archive hashes. All eleven references receive the `br_`
namespace and must remain absent from both the generated payload and the native
catalog, preventing an unrelated MotS resource from silently filling a gap.
There is no general ignore-missing switch. The manifest records
`preserve-reviewed-original-omissions-v1`, with no substitute assets.

One long COG filename has a reviewed alias to fit the legacy length limit:
`00_sectorliteanimflicker2.cog` becomes `br_sectorliteanimflicker2.cog`.
The `caesars-original-omissions-v3` recipe also changes exactly one startup
`SetInv(player, 10, 1)` saber grant to bin `131`. Leaving JK bin 10 unchanged would
select MotS's EWEB bin through ordinal mapping. Original fists/Bryar grants
`1`/`2` already map correctly to `121`/`122` and remain unchanged, as do
`AutoSelectWeapon` mode `1` and current-weapon value `0`.

For a wider read-only audit of owned JK archives and an optional directory of
candidate resources:

```powershell
$candidateResources = 'D:\Mod Research\Caesar Candidates'
$auditOutput = 'D:\Mod Research\caesars-audit.json'
python caesars_audit.py --caesars $caesarsInput --jk-root $jkGameRoot --resource-dir $candidateResources --output $auditOutput
```

`--resource-dir` is optional and belongs to `caesars_audit.py`. It inventories
matching candidate filenames, sizes, and hashes; it does not install, apply, or
copy them into a conversion. `--jk-root` can be repeated for additional owned
installations. Candidate provenance and compatibility remain separate questions.

The inspected port's [world checksum](https://github.com/andreipemberton/OpenJKDF2-MotS-Fixes/blob/f40e965bbe4133aef9e9b9eccabb2fbf0a34a9fb/src/World/sithWorld.c#L642)
covers compiled COG code, vertices, and selected template data, with an additional
MotS personality callback; it does not directly hash raw MAT or WAV payload bytes.
Checksum acceptance cannot certify matching rendering, sound IDs, gameplay, or
retail-peer compatibility. Adding executable COG code can change both checksum
and behavior. The retail executable's checksum was not disassembled or tested
here. Any future resource repair needs its own review and matching packages on
both peers.

Massassi supplies a [River Thrust COG attributed to Gandalv the Gray](https://www.massassi.net/cog/both.html),
with [public script source](https://www.massassi.net/cogfiles/both/riverthrust.cog).
That authentic named candidate is not bundled or inserted: its exact intended
historical revision for Caesar's Palace is unverified. A filename does not prove
that an optional Caesar resource pack existed. The original level readme also
restricts redistribution and reuse; this project distributes no Caesar assets.

## Transformation contract

- Preserve source JKL Version 1 geometry, UVs, adjoins, surface flags, normals,
  sector parameters, placements, frames, and environmental COG arguments.
- Expand each scalar JK surface-light value into equal mono, red, green, and blue
  values. Insert `-1` as each thing's MotS archlighting index and emit the empty
  archlighting section required by this format.
- Namespace JK resources and templates with `br_`, including typed COG template
  defaults and exposed template arguments, protecting native MotS resources.
- Use native MotS `walkplayer`, player/effect COGs, reviewed pickup bindings, and the 209 native
  templates from pinned multiplayer `k1.jkl`. Native preloads derive from those
  templates and active inventory, excluding unrelated K1 map event scripts.
- Retain reviewed original environment scripts and execution flags, with resource
  name changes and the explicit inventory adaptations documented here.
  Battleground's original `17a_Stream.cog` comes from `JK1.GOB`; its sixteen
  vectors, sixteen surface references, and speed remain unchanged.
- Preserve binary resource payloads exactly; rewrite filename references in
  textual resources. Generate a TYPE 2 single-level episode for deathmatch and
  custom maps, and TYPE 8 for the three CTF maps.

The intended fidelity is the original level environment with native MotS player,
weapon, Force and networking behavior, plus the pickup compatibility below. Exact original JK combat parity
is not established. Optional Force Throw/Lightning restoration is a separate
project; bridge conversion does not silently enable those powers or change their
controls.

### Script capacity and Force pickup compatibility

RC3 corrects a script-instance allocation error found while investigating
Canyon Oasis. Its original `World cogs 32` budget was not expanded when the
converter added MotS's native templates. Those templates consumed the available
instances, leaving later source templates without functioning scripts. WBW now
funds every added native binding, preserves the source map's spare budget, and
checks the final instance requirement independently. Canyon's corrected capacity
is 81, covering its 79 required instances with two slots to spare.

The audit also found Force-pickup behavior mismatches. Canyon's five Force Boosts
and two Surge pickups retain their original positions. They now use the native
neutral MotS pickup appearances: Force Boost for the five Boost locations, and
Force Surge for both original JK Surge locations. This change does not add or
relocate objects.

- Force Boost still grants +100 energy in multiplayer (+50 in single player),
  but uses MotS's active multiplayer maximum energy, inventory bin 69. The old
  rank-times-50 limit could reject a pickup below a persona's real maximum.
- Both original Surge variants now use MotS's working 20-second Force Surge effect
  through bin 64. MotS Force scripts do not use JK's separate Light Surge bin 65.
  Both locations inherit one controller, so either pickup renews the same timer.
  The refill respects the active maximum instead of potentially lowering energy.
- Native MotS pickup models replace the JK Force pickup appearances.
  Coordinates, authored respawn intervals and water flags stay intact.
  The generated episode contains uniquely named compatibility COGs;
  conversion does not replace the installed game scripts or add Force powers.
- The Force Boost script animates the native twinkle material used by its native
  pickup model. MotS's interface names these items **Force Boost** and **Force
  Surge**; its internal `darkside` template name is a legacy identifier, not an
  alignment restriction.

This follows the game's own level design. Native MotS Reactor and Tatooine
Homestead use the neutral Surge model and script even for placed pickups whose
internal template name is still `lightside`. WBW records the native template,
model and material hashes so the mapping can be reproduced from owned inputs.

WBW stores the source hashes and exact counted edits as recipe data and code.
The full scripts are extracted from the user's own MotS resource archive only
during conversion. No game scripts or converted archives are distributed with
the tool. The independent verifier reconstructs the expected scripts and checks
the native pickup model bindings as well as the unchanged placements and other
authored template fields.

Existing conversions need to be regenerated with RC4 (which includes the RC3
pickup correction and adds recipe tracking); updating the program
does not modify an already exported GOO. Select the affected map and use the
new result, with matching files for every multiplayer participant. An invisible
pickup still needs a runtime check: these changes alone do not prove
that an installation, mod override or rendering problem has been resolved.

Normal host-side respawn also requires the engine fork's MotS null-taker
acknowledgment fix. Native MotS pickup scripts call `TakeItem(item, -1)` and apply
their effects locally; an older host path rejected that sentinel and never
started the respawn timer. This is an engine correction in OpenJKDF2-MotS-Fixes,
separate from WBW's map recipes and application packages.

The engine corrections are published in the fork's
[host-respawn and first-person lighting fix](https://github.com/andreipemberton/OpenJKDF2-MotS-Fixes/commit/5fa4644d03080fef69d7137eaa2c8f295c47bd63).

### CTF-specific changes

The three CTF outputs retain their original TYPE 8 mode, team/flag scripts,
strings, scoring, callbacks, respawn logic, and map-specific environment scripts.
They make two narrow adaptations:

1. Exactly two team-entry saber grants in pinned `CTF_MAIN` change inventory bin
   `10` to native MotS saber bin `131`. Team, flag, and key bins `80`–`84` remain
   unchanged.
2. A `misc/items.dat` derived from native MotS changes bin `81`'s descriptor
   from `ysalamiri` to `redflag`, preserving its number, range, and `0x048` flags.
   Native red/gold flag icons are checked. Native regular ysalamiri remains bin
   `68`. The generated startup overlay must load this descriptor before inventory
   initialization; the episode-local copy is insufficient.

The dependency catalog excludes the separate KFY episode and its event scripts.
These recipes retain JK CTF logic; a TYPE 8 host-load result does not validate
team selection, captures, scoring, flag/key replication, costumes, or late joins.

The Arena of Dark and Light also retains one narrowly reviewed source omission:
the pinned original `shard0.3do` declares absent `00_glass.mat`, but its sole face
uses untextured geometry mode 3 and zero texture vertices. The source model hash
and exact reference are checked, and the absent material is namespaced. No
replacement texture is invented.

## Validation limits

Synthetic tests cover format and recipe invariants without retail assets.
`verify_retail.py` compares source-scene data using its own map selection table
and structural assertions, then checks two byte-identical rebuilds. Rebuilds use
the recipe implementation; they are reproducibility checks, not a second
independent converter. Neither tool launches the game.

Measured host runs establish load and advancing simulation for the tested
build/package combination. Full validation still requires traversal, collisions,
textures and lighting, environment switches/hazards, spawn/death/respawn, pickups,
weapons/force, and joined multiplayer peers. Dojo crates and CTF team/score/flag
behavior require their specific checks. Caesar additionally needs its actors,
traps, missing-resource behavior, and multiplayer glass triggers exercised.

The dependency scanner resolves literal references. It cannot establish computed
paths, every implicit dependency, or network behavior; hash pins and explicit
script sets bound the accepted inputs. Source and native template inheritance
are checked. The inherited native `item_heavy_explosive.cog` has an unusual
template default `EC.3do`, absent from the native K1 template table. That condition
is documented without inventing a replacement.

## Jedi High School recovery

The original **Jedi's High School 1.0**, by **PeD_HeAd**, was recovered on
2026-09-08 from the [public JKDF2.NET archive](https://www.jkdf2.net/JKBot/JKArchive/JKDF2/JKDF2/Game%20Files/jkmp/jhs.zip).
Its original readme is dated May 2, 1999. The ZIP contains `jhs.gob` and `JHS.txt`;
the ZIP SHA-256 is `a30e2b74db290b580effe442ac1345b9158a36b9803234a4a347a997039c0411`.
The earlier unsuccessful Massassi searches are superseded by this recovered package.

The `jhs` recipe preserves all 2,236 surfaces and 263 placed things. Its original
absent `minetrap.cog` and unused/untextured `00_glass.mat` references remain
explicitly absent under reserved names. Unreferenced scripts in the archive are
not activated. The readme's modification/distribution restrictions are retained
as provenance; generated assets remain private local outputs.

## Community RC recipes

See [COMMUNITY_RC1.md](COMMUNITY_RC1.md) for the fifteen recipes, their original
authors and download pages, per-map adaptations, and remaining gameplay checks.
The nine retail maps and two earlier community maps bring this RC to **26 maps**.

```powershell
python bridge.py list-community
python bridge.py convert-community --map jhs --level-archive 'D:\Downloads\jhs.zip' --jk-root $jkGameRoot --mots-root $motsGameRoot --output 'D:\Bridge Output\bridge-jhs-rc1.goo'
python verify_retail.py --community-key jhs --community-archive 'D:\Downloads\jhs.zip' --jk-root $jkGameRoot --mots-root $motsGameRoot --archive 'D:\Bridge Output\bridge-jhs-rc1.goo'
```

Only the original ZIP or embedded GOB revisions listed by the recipes are
accepted. Conversion reads original archives in memory and never executes their
contents. Source ZIP paths, duplicate names, CRCs, GOB bounds, and all pinned
input hashes are checked before a candidate is written.

Install the generated GOO in the `episode` directory of an OpenJKDF2 runtime using
owned MotS data. Launch **OpenJKDF2 with `-motsCompat`**, then host the converted
episode through **Multiplayer**. Do not launch the retail MotS executable.
For maps that generate a `bridge-<map>-startup` folder, place that entire folder
beside the runtime's `episode` and `resource` directories and add
`-path bridge-<map>-startup` when starting OpenJKDF2. The per-map startup GOO must
load before player, inventory and skin initialization. Every peer must use the
same converted episode and matching startup overlay. Use one selected map overlay
at a time; combining SBX, Manowars or other gameplay overlays needs a separate test.
Restart the game with the next map's matching startup overlay when changing
families, or restart without the previous overlay when the next map needs none.
Selecting another episode from the same running menu does not unload the old
player, inventory or skin overrides.

The catalog preserves exact original missing assets where reviewed. Purgatory's
`nat.mat` is used by one textured surface; Mos Espa's `00wall4_11.mat` is used by
eight textured surfaces. Those images are absent in the reviewed original packages
and owned JK resources. The converter preserves the engine's original material
fallback and reports it; it does not invent substitute artwork.

## Primary technical sources and credit

- [Massassi JKL format specification](https://www.massassi.net/jkspecs/jkl.htm).
- [SED scalar-color importer, pinned source](https://github.com/smlu/SED/blob/c3b6c0e59f192e96dc6df2daf698fb179e63603a/src/LEVEL_IO.INC#L322).
- [SED MotS surface writer](https://github.com/smlu/SED/blob/c3b6c0e59f192e96dc6df2daf698fb179e63603a/src/SAVEJKL.INC#L635),
  [thing writer](https://github.com/smlu/SED/blob/c3b6c0e59f192e96dc6df2daf698fb179e63603a/src/SAVEJKL.INC#L872),
  and [empty archlighting section](https://github.com/smlu/SED/blob/c3b6c0e59f192e96dc6df2daf698fb179e63603a/src/SAVEJKL.INC#L1098).
- [Historical first-hand conversion discussion](https://groups.google.com/g/alt.games.jedi-knight/c/uDyinDeq1xA).

SED source was read to establish file-format behavior; this project's Python
implementation is original. No editor executable was downloaded or run. Original
tooling by Andrei Pemberton, with Coda Lilitari. Original game, level, script, and
editor authors retain their respective credits and rights; attribution here does
not authorize redistribution of their assets.

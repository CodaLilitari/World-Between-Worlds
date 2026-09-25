# Validation record — 2026-09-08

## World Between Worlds workbench checkpoint

The **0.2.0-rc2** workbench source gate discovered **190 Python tests**. Using the
Windows build virtual environment, **177 passed and thirteen optional owned-archive
checks were skipped**. On Linux, **175 passed and fifteen were skipped**: the same
thirteen owned-data checks and two Windows-specific process tests. All **22 UI
source tests passed**. The separate Ninja Kage run enabled the owned inputs and
passed **42 tests with zero skips**. Release artifacts have their own packaging
and launch gates.

The updater and packaging gate's **47 tests passed on Windows**. The source launcher recognizes
the real interpreter child created by Windows virtual-environment Python, using
observed process ancestry while retaining version and loopback-URL checks.
Without that condition, both bundled and cached source-launch regressions fail.
A separate synthetic-app lifetime race was demonstrated under delayed ancestry
inspection; its fixture now waits for explicit parent acknowledgment. The old
fixed lifetime fails that regression. The corresponding Linux tests pass, with
the two Windows-only tests explicitly skipped. RC2 isolates the updater's
synthetic installed version and application root from the real checkout. Before
that test-fixture correction, bumping the application version to RC2 caused four
tests to exercise the wrong release path, including a real bundled app. No
production launcher change was required; the corrected full suites pass.

Ninja Kage remains a prototype. Its v4 maximum-mana correction passed a
**75.025-second** two-peer K1 initialization test on the older pinned 78c4
diagnostic executable: all **37 initialized host and 34 client samples** showed
rank 4, current mana 200 and maximum mana 200, with no input-provider activity.
All 66 descriptor bindings matched; clocks advanced and both peers connected.
The [sanitized record](https://github.com/andreipemberton/World-Between-Worlds/blob/v0.2.0-rc2/docs/validation/ninja-maxmana-20260908.json) pins the exact
archive, executable, source and parser fixture. It is repository-only, not bundled
in the application ZIPs; the plain-text app document retains the full external
release-tagged URL. Separate e9 production hosts
only established 30-second loading/simulation with rank-zero placeholders;
they did not pass positive-rank validation. The focused source gate passed
**42 Ninja tests and six catalog-selection tests**. Underfunded casts,
regeneration recovery, other ranks/personalities and current-production
positive-rank initialization remain unverified. The v3 action and grapple
results remain separate predecessor evidence. Native allocation/cycling still
omit Throw/Lightning, and the separate restoration experiment is excluded.
See [NINJA_KAGE.md](NINJA_KAGE.md) for exact limits.

A subsequent isolated Chrome test confirmed that Ninja Kage is selectable as a
prototype with no initial selection. A Canyon-only conversion generated no Ninja
files or startup overlay. Explicitly selecting Canyon and Ninja then reused the
unchanged Canyon output and created a separate Ninja folder with the exact
runtime-tested v3 archive hash. The Ninja-only recipe export contained one
asset-free recipe. All 112 baseline files retained their hashes; there were no
browser errors or external UI requests. This was a conversion test and did not
launch a game. The [selection evidence](docs/validation/ninja-selection-20260908.json)
records both jobs and the source hashes.

The actual browser UI passed seven additional checks in an isolated headless
Chrome session with zero browser errors: empty initial selection; dropdown and
checkbox multi-selection; persistent selection across filters; title search;
selected-only asset-free recipe export; recipe-detail display; and a narrow
viewport without horizontal overflow. All observed UI requests stayed on the
local application origin. An additional actual two-map UI conversion completed
Canyon Oasis and Jedi's High School through the job queue.

An explicit full selection then converted and independently verified **all 26
maps** through the same backend. The verification includes two repeat builds
with identical archive bytes, original binary-resource hashes, exact geometry,
lighting replication and typed COG argument checks. All **112 baseline game
files** retained their pre-run hashes. The
[public result record](https://github.com/andreipemberton/World-Between-Worlds/blob/main/docs/validation/map-regression-20260908.json)
pins every output and the source snapshot used. Structural verification did not
launch these newly generated copies; the earlier multiplayer host evidence
below remains a separate test.

The [six matched-camera screenshots](SCREENSHOTS.md) add rendering evidence for
Canyon Oasis, Jedi's High School and Nar Shaddaa. They show corresponding visible
geometry and materials in JK and MotS modes. Complete traversal and every
authored mechanism are not established by those static views.

A subsequent paired JHS test exercised one existing door and one existing
elevator through normal engine activation-message routing. Their authored COGs
opened and automatically closed the door, moved the elevator to its lower frame,
then returned it after the timer and reset the button. Both original JK and
converted MotS passed all 14 runtime gates and four full-XYZ endpoint checks in
separate 20-second multiplayer host runs. The elevator returned after 16.986
seconds in JK and 16.958 seconds in MotS; observation times are sampled, not
performance benchmarks. The [public action record](docs/validation/jhs-authored-actions-20260908.json)
pins the diagnostic executable, source archives, observations and exact limits.
This check did not cover player riding, obstructed movement, physical keyboard
activation or synchronization with another peer. No production engine change
was required, and both map archives and the retail baselines retained their hashes.

Release preparation also rejects a source checkout changed since app startup,
an original archive replaced during conversion, output directories overlapping
game or application files, and existing generated folders whose contents differ.
The replacement-archive test confirms no output or misleading receipt is
published. The updater stages verified versions separately, exercises newer
updater handoff, and falls back after failed startup; see
[packaging/USER_GUIDE.md](packaging/USER_GUIDE.md).

The historical records below retain the scope and counts of earlier map and
engine checkpoints. They do not imply broader coverage for Ninja Kage, whose
current prototype limits are recorded in [NINJA_KAGE.md](NINJA_KAGE.md).

The converter and independent verifier do not launch the game. Runtime observations
below come from the parent engineering task's isolated production-runtime harness;
the Dojo and Battleground result JSON files were subsequently read directly for
this record.

## Structural verification

Fifty-two synthetic unit tests pass after the stock, CTF startup and Caesar expansion. The independent verifier checks geometry/UVs,
adjoins, surface flags/topology/normals and exact lighting replication, sector
parameters, object placement/frames/flags, COG numeric/vector arguments, template
inheritance, original binary payload hashes, and two byte-identical rebuilds.

| Candidate | SHA-256 | Structural status |
|---|---|---|
| Valley v2 | `8a800f3063e2efb6950e38352d21cebdd04a3a6bfa884495c5fb7b421bbea377` | All ten verification families pass |
| Jedi Dojo v1 | `98cb6bc35269ea432d047e95251669a82fda98ff60b293b427baab882a44189c` | All ten verification families pass |
| Battleground Jedi v1 | `e96987f000915b1355185cfc340a1e8cd878c568068f4e0759e757b8e9ae3e8b` | All ten verification families pass |

Valley v1 is rejected development evidence because its colormap parser consumed
later geometry records. v2 fixes the boundary and has a regression test. Caesar's
earlier blanket dependency gate was superseded by the exact original-omission
audit and recipe documented in the expansion record below.

## Jedi Dojo multiplayer host observation

Evidence lane: `runtime-tests/baseline-bridge-dojo-v1-mp-02/result.json` in the
local audit package. The tested candidate hash is the Dojo hash listed above.
The executable hash was
`58a21e4922aaaa2aefc11c9aefbb20cb186651012c62342137dc76c1dd6a23d3`.

The harness invoked `-motsCompat -headless -autostart -mp -episode bridge-dojo-v1
-map br_dojo` with debug logging and verbose level 2. It requested 60 seconds and
recorded 60.19 seconds survived, with `survived_window=true`,
`simulation_advanced=true`, and no crash files. The final snapshot at 58.19 seconds
showed multiplayer active, `br_dojo.jkl` as the loaded world, a present local
player, and world clock 54,351 ms. The harness then terminated the process;
exit code 1 records that intentional termination, not a demonstrated normal game
shutdown. Startup string-count warnings remain in the debug log.

This establishes startup, level load, and advancing simulation as an actual MotS
multiplayer host for the measured window. It does not establish visual fidelity,
traversal/collision, all gameplay paths, crate damage/drop behavior, or two-peer
synchronization.

The parent also reported a 60-second Valley v2 multiplayer host run with an
advancing clock and no crash. That report remains distinct from the directly
inspected Dojo evidence above.

## Battleground Jedi multiplayer host observation

Evidence lane: `runtime-tests/baseline-bridge-battleground-v1-mp03/result.json` in
the local audit package. The tested candidate hash is the Battleground hash above.
The production executable hash was
`46082078c608a956e1012af3803fd89777e231fa6754efb078dacd0eb0c23165`.

The harness invoked `-motsCompat -headless -autostart -mp -episode
bridge-battleground-v1 -map br_battleground` with debug logging and verbose level
2. It requested 60 seconds and recorded 60.13 seconds survived, with
`survived_window=true`, `simulation_advanced=true`, and no crash files. The final
snapshot at 58.13 seconds showed multiplayer active, `br_battleground.jkl` as the
loaded world, a present local player, and world clock 56,866 ms. The harness then
terminated the process; exit code 1 records that intentional termination. Startup
string-count warnings remain in the debug log.

This establishes startup, level load, and advancing simulation as an actual MotS
multiplayer host for the measured window. It does not establish rendered river
animation or ambience, traversal/collision, gameplay paths, or two-peer
synchronization. No converter code or generated episode changed for this run.

## Remaining targeted checks

- Rendered environment, textures, lighting, traversal, and collision.
- Valley doors/elevator/ceiling; Battleground river texture motion and ambience.
- Spawn/death/respawn, every pickup, native weapons and force powers.
- Dojo's nine original wooden crates: lethal hit, subsequent hit, explosion,
  possible drops, and replication. The preserved original script's undeclared
  `totaldamage` behavior is documented in the README.
- A second peer, including movement, projectiles, pickups, custom COG state,
  joining/leaving, and synchronization.

No universal conversion, original-retail-MotS executable compatibility, full
Caesar/JHS playability, or mod-combination certification is implied by these results.

## Stock multiplayer expansion and Caesar v3

All nine base JK multiplayer maps build from the pinned owned installation:
six TYPE 2 deathmatch maps and three TYPE 8 CTF maps. Public `convert-stock --all`
builds separate episodes into a directory. Every stock output was rebuilt twice
byte-identically. The earlier Valley, Battleground and Dojo hashes remain unchanged.
All nine stock outputs and Caesar v3 passed the ten independent structural
verification families, including source COG argument types and exact unchanged
numeric/vector values. The verifier has its own original/target map mapping.

The seven newly added stock maps and final Caesar v3 each ran sequentially for
60 seconds in the production OpenJKDF2 MotS build whose SHA256 is
`46082078c608a956e1012af3803fd89777e231fa6754efb078dacd0eb0c23165`.
Each fresh lane contained one selected converted episode, native MotS resources,
and no gameplay mod. The harness checked MotS compatibility enabled, SP disabled,
multiplayer active, a local player, correct loaded world, advancing clock, input
hash stability, and no crash report. The complete 48-file MotS baseline remained
unchanged before and after each batch. The harness terminated each own process
after observation; exit code 1 is intentional termination, not normal shutdown.

| Candidate | SHA256 | Survived seconds | Final sampled game clock (ms) |
| --- | --- | ---: | ---: |
| Canyon Oasis v1 | `1da7d9c8bc1ee4630d54fb5125dd1da0a436656789a159d7da72d18c687bfae7` | 60.13 | 56,691 |
| Nar Shaddaa v1 | `0e6e1355955d83056e423e90a1d7dcef5cb00f18d2bf8688b7f00d7633582c86` | 60.13 | 56,874 |
| Bespin v1 | `c4a4d4ccc027427622b77052ba5fbee877bce9a2a7870dedb885016acf1fe733` | 60.13 | 56,893 |
| Blades of Death v1 | `ab1220d85a7253957fab73ebd01e67de4d8a6c8c586cb18f5233e320e2fd631b` | 60.12 | 56,741 |
| CTF The Duel v1 | `abbda835bf5143f82d91831ceb595e2a3f033eb18cb366503eab4c69e23c808a` | 60.13 | 56,806 |
| CTF The Arena of Dark and Light v1 | `d8d50a6e056be6f37607f64a5b90ef8c48c8ab8816787466b5636327955ae908` | 60.14 | 55,993 |
| CTF The Challenge at Nar Shaddaa v1 | `b4e9edf585ee9e3c57b27e291d64edbd9c0feafc66916749f135fcf875c4c910` | 60.12 | 56,661 |
| Caesar's Palace v3 | `2c72071a547bed9399414353c0bdec0c0c6beed9b7e70763e8947afa5576c469` | 60.13 | 56,594 |

The private evidence package retains `hosts-stock-dm-mp03.json`,
`hosts-stock-ctf-mp03.json`, every full per-lane `result.json`, and baseline
integrity manifests. Caesar's final lane is
`runtime-tests/baseline-bridge-caesars-v3-mp03`. The usual native string-count
warnings remain. These are loading/simulation observations; there was no rendered
traversal, peer session or exhaustive interaction test in this expansion.

An independent CTF review passed 12 structural/code checks per map. It confirmed
TYPE 8, original team/scoring flags and ordered bin 80-84 operations, two precise
saber grants changed to MotS bin 131, original respawn logic, episode strings,
the bin 81 HUD descriptor, and absence of KFY scripts. The Arena retains exactly
one original untextured-shard material omission, namespaced to prevent a native
MotS material from silently resolving it. Team entry/change, rendered HUD,
flag pickup/drop/return/capture, death/respawn, scoring and synchronization across
peers remain required before a CTF gameplay claim.

Caesar v3 contains 6,773 surfaces, 459 placed things, 243 COG instances and 1,142
resources. The exact eleven original missing filenames and allowed referrers
remain missing under their reserved names. The river instance retains all 50
arguments, civilian scripts remain namespaced, and one long flicker COG name is
shortened explicitly to fit the 31-byte limit. The only startup gameplay-code
change is the saber grant from 10 to 131; fists/Bryar already map through the
MotS API and current/automatic weapon-selection calls are unchanged. An
independent review passed 15 integration checks. The separate portable helper
tests reject altered hashes, omissions, referrers, resolved supposedly missing
scripts, and missing/duplicate saber-grant edits.

Caesar v1 (without the saber fix) and v2 (equivalent but unnecessarily explicit
fists/Bryar mappings) are superseded private development outputs. v1 also passed
a host smoke, which demonstrates why loading alone cannot certify behavior.
Only v3 is the current recipe. Traps, glass, actors, cameras, other interactions,
cosmetic appearance and peer synchronization remain explicit acceptance work.

The earlier JHS recovery gap was closed later on 2026-09-08: the original
PeD_HeAd version 1.0 ZIP was found in JKDF2.NET's public archive, verified, and
converted. See COMMUNITY_RC1.md for current results; the unsuccessful Massassi
and demo-release searches above are historical checks, not the current outcome.

## Required CTF startup overlay and active-descriptor verification

The first CTF host passes above checked episode loading and simulation, but the
episode-local `items.dat` had not become the active inventory table. The engine
initializes inventory before mounting the selected episode. That load-order gap
is corrected by a shared startup overlay, emitted automatically by `--all` and
individual CTF conversion commands. Existing episodes can obtain it with
`build-ctf-startup`. The episode archive bytes remain unchanged.

The `bridge-ctf-ui/bridge-ctf-ui.goo` overlay has SHA256
`3b16ae3206e2158b113116109d5ef7c05ff2a75e5a8d8c31ab964ea07199d45d`
and contains only the owned native `misc/items.dat` with descriptor 81 renamed to
`redflag`. Every host/client must mount it from process startup with
`-motsCompat -path bridge-ctf-ui`. The independent verifier now checks the
mandatory startup GOO as well as every stock episode, confirming that the single
descriptor name is its only native data edit.

All three CTF maps were then retested with the overlay, using the same pinned
production executable and a fresh native MotS lane per map. The observation
layout was compiled from the production headers with the production MinGW flags:
`sizeof(SithInventoryType)=168`, name offset4/length128, flags offset0, minimum132,
maximum136, COG pointer144, 200 entries. ReadProcessMemory inspected only the
agent-launched child processes; no test adapter was added to the engine.

| Final CTF run | Survived seconds | Final sampled clock (ms) | Active descriptor checks |
| --- | ---: | ---: | --- |
| The Duel + startup overlay | 60.13 | 56,484 | Passed |
| The Arena of Dark and Light + startup overlay | 60.13 | 56,725 | Passed |
| The Challenge at Nar Shaddaa + startup overlay | 60.14 | 56,821 | Passed |

Every active gameplay sample had `redflag` in bin81, flags `0x49`, range0..1,
and no COG pointer. Native bin68 ysalamiri, bin82 goldflag, bins83/84 red/gold keys,
and bin131 lightsaber retained their expected names, flags and ranges; observed
COG pointers were null for68/81/82 and present for83/84/131. The overlay was
mounted at resource directory0. All runs had MotS compatibility enabled,
SP disabled, multiplayer active, correct worlds, local players, advancing
simulation, unchanged inputs and no crash files. All 48 baseline files remained
hash-identical. The private evidence is `hosts-ctf-startup-mp03.json` plus the
per-lane results and `ctf-review/inventory-layout.json` provenance.

These reads prove the intended descriptors were active in the running production
engine. They do not establish actual HUD rendering, flag interactions, captures,
scoring or synchronization across peers; those acceptance checks remain open.

### Native MotS CTF episode and personality menus

A separate **4.622-second** native-menu replay completed with **15 actual
1280 × 960 framebuffer captures**. The unmodified host menu offered all three
converted TYPE 8 CTF episodes; its native OK handler returned each correct
episode and map, maximum rank 8, mode flags 144 and game-format argument 0.
The native character menus created and saved Jedi, Bounty Hunter, Scout and
Soldier characters, then reloaded all four through the actual character parser
using The Duel host menu's returned room fields. Native personality creation
assigned rank 7; the test did not set ranks, inventory or personality values.

The private diagnostic used exact production source base
`e9e293a7a98c9a665509af96f9a87a9ca2470996`, executable SHA256
`02ebed76650cf64ce90352a73c301dc1c0319921aab2464a9cf05b5daec2ab9f`,
and candidate-manifest SHA256
`cab09789ea99431b70294bfc03965d10b7f9bb6f58239e2c36ce16efefa3621f`.
Its added provider invoked normal in-process GUI handlers and captured its own
hidden window before native buffer swaps. Physical OS input was disabled. The
production host and character menu implementations were unchanged; this adds
no CTF menu feature to the released engine. The original baseline and diagnostic
runtime retained their hashes, and the owned child exited normally.

Two earlier private attempts remain preserved: one stopped because capture was
armed before a native repaint completed; another captured and saved the first
Jedi, then incorrectly treated the native nested-menu return value as failure.
The successful retry corrected those provider assumptions while retaining fresh
paint, native-result, backing-surface and menu-reference checks.

The [sanitized native-menu record](https://github.com/andreipemberton/World-Between-Worlds/blob/v0.2.0-rc2/docs/validation/ctf-native-menu-20260908.json)
pins the source, build, canonical episodes/overlay, raw observations, native MPC
files and images. It and the [representative screenshots](SCREENSHOTS.md) are
repository documentation, excluded from application packages. This was a GUI
test, with no listening game or gameplay simulation: CTF team entry, flag
pickup/drop/return/capture, scoring and gameplay across personalities remain
separate acceptance gates.


## Community RC1 expansion — final converted-v3

All fifteen community candidates pass independent source/structure verification
and match a completed 60-second OpenJKDF2 MotS multiplayer host run. The final
selected runs have no COG parser/unknown-verb/load errors in their stdout logs.
Every generated episode and required startup GOO matches both its manifest and
the actual tested lane. All 48 owned MotS baseline files remain unchanged.

The source-only test suite passes **80 tests**. All eleven earlier delivered
episodes still reproduce byte for byte; the existing CTF startup overlay also
passes. Community checks include fourteen verification families, plus a fifteenth
for each of the four mandatory startup overlays. Full source script reconstruction
checks every reviewed edit and the untouched text. These are independent
invariant checks and repeated builds, not an independently implemented converter.

Runtime03 is the previously tested COG-locality build (EXE SHA
`46082078c608a956e1012af3803fd89777e231fa6754efb078dacd0eb0c23165`).
Runtime04 adds the backpack fix from local source commit
`4dc57962e46a72662b59d36c30f15eacef6234b5` (EXE SHA
`eb1b61dfa98975a01a09249185396ef606eb26e402a80b6e3a3b38774c508176`).
Drazen and corrected Jawa were tested on 04; the other thirteen new families were
tested on 03. This is not a claim that every family has been retested on 04.

| Map | Surfaces / placed things | Final GOO SHA-256 | Host |
| --- | --- | --- | --- |
| Atlantis | 5153 / 212 | `50318501a7864d7fcad5ae0c98dff4052d583dce7be5be60b313a96cd23b513b` | 60.13s / runtime 03 |
| Death Star Arena | 7908 / 233 | `dc5e84ee257b4299f13a0d4865660a663f9c20559e1e672d815795caf5e40f50` | 60.12s / runtime 03 |
| Naboo | 2989 / 441 | `8f9bb38fa628ea525512202699488d7c73eed8e8f47b2293b3fc36a8e1ee0e08` | 60.14s / runtime 03 |
| Morpheus | 1000 / 81 | `b84a8bd1a5b1b6865c90b9bcf70ea5a6498b21f6b5f610c40dc8aafb6a3e2877` | 60.13s / runtime 03 |
| Duel Of The Fates S.E. | 2947 / 260 | `221d44164d7b625751475be15295c2c34b9d32aa7177c849fcc587a4a2857f6f` | 60.14s / runtime 03 |
| Jawa Dwelling SE | 5370 / 453 | `085ea93ca97e171f1263813a2311d5a862e0f607241347b3d2e75629e61808ca` | 60.14s / runtime 04 |
| The Mos Espa RPG | 2387 / 412 | `7a119a8a55ac5eca3e42d77e848abf14d3fc8ac90ac3800126e9666ae6b9c9cc` | 60.14s / runtime 03 |
| Area 21 | 31215 / 450 | `30677ec10bb002d126708202d3e6d6886da250107a13728bda2104847716810c` | 60.14s / runtime 03 |
| Stargate | 3536 / 117 | `93924e47292cb7757970d4254fe890e1f0dafde48f1059ad5c4f935ee46d3126` | 60.14s / runtime 03 |
| Drazen Isle | 30794 / 396 | `7ceb6e93f35ca8c3920ab91221efa882d760b7de93cadba834033c878c5467d2` | 60.14s / runtime 04 |
| Purgatory | 11699 / 451 | `3022645af741125d05421dba8975e4ebb0cc1b6fc7835946c1942c25c2c01b63` | 60.13s / runtime 03 |
| Courtyard | 2269 / 158 | `8431fa11cb14a6cb57bbf971b96410bc7b9c4fb33b9a8d3e6ac8c1374a0e1703` | 60.12s / runtime 03 |
| Shadow Caverns | 1664 / 131 | `77cc5161090621194148b01bc4b804c14e958d1fc7cbe507567ad5a4da3bc368` | 60.13s / runtime 03 |
| Deicide | 3739 / 91 | `84c9e2f0a4e5d9a8836cbf1ae4e3eb90aa9e6d7248e73db6f3ed4e52b5773cbc` | 60.13s / runtime 03 |
| Jedi's High School | 2236 / 263 | `6276dda2e731d4ff5c3570197086312be6fa0bee9754ae91d799af75501e774e` | 60.13s / runtime 03 |

Targeted observations read the running process through compiled ABI offsets:

- **Morpheus:** all reviewed numerical fields of the nine native weapon/explosion
  templates match the authored values, including Bryar damage 40/min 25, repeater
  velocity 16 and damage 25, and grenade damage 300/force 1000/range 2.
- **Jawa:** active inventory descriptor 129 has a nonnull
  `weap_concrifle_m.cog` and its live `fireWait` is approximately 0.1.
  The earlier v2 host survived but both concussion scripts failed to parse an
  inherited malformed print statement. V3 fixes the exact statement and passes
  the active-descriptor and clean-parser-log checks.
- **Stargate:** fists 121 are present and selected, weapon slots 122–140 are zero,
  ammunition 11/12/15/90/91/92 is zero, and battery 13 remains 75. These are observed
  inventory values, not an inference from the script text.
- **Drazen:** live map-item descriptors 43–50 contain the BACKPACKITEM flag;
  descriptor 81 is `redflag`. This establishes startup descriptor activation,
  not the full authored treasure quest or a rendered HUD screenshot.
- **Fates:** the exact mandatory skin-overlay GOO is mounted during the host
  run; all eleven source model replacements and their dependency data are
  independently checked. Rendered character appearance still needs visual QA.

Naboo's first core probe sampled GUI 5 with clock 0 before its player existed.
Its subsequent samples were normal. A fresh separate run passed a documented
post-initialization gate: GUI 5 with clock>0, first active sample within 15 seconds,
at least eight active samples, correct world/multiplayer/MotS/player state in all
of them, and advancing simulation. The initial failed classification remains in
the private evidence rather than being overwritten.

The backpack source regression passes 19,960 assertions, including 9,600 bin/slot/
descriptor cases and explicit rejection of the original slot-lookup mutant.
The earlier COG-locality regression still passes 30,766 assertions. The full
Windows x64 runtime builds, and all 1,145 tracked source/build files match its
recorded source commit after CRLF normalization. Packet tests exercise extracted
DSS item cases with stubbed tokens; full transport and generic packet-length
validation are outside those tests.

Remaining acceptance work includes rendered traversal, collision/lighting,
the original maps' traps and portals, complete treasure progression, actual
weapon firing cadence and balance, repeated death/drop/respawn, and joined-peer
synchronization. Headless host survival and loaded-state observations do not
certify all those behaviors. Gameplay overlays such as SBX/Manowars have not
been certified in combination with these fifteen conversions.

## Backpack production-runtime comparison

A private artificial COG fixture executed the real CreateBackpack and
PickupBackpack verbs in a MotS multiplayer host using the same converted Drazen
scene and startup overlay. It deliberately prepared a sole backpack entry with
inventory bin 43/value 1, cleared the player's copy, and performed pickup before
the next physics tick. It did not change inventory descriptor flags.

Two separate 45-second runs completed with advancing simulation, no crash files,
no visible own-process window, correct world/overlay, and unchanged baseline and
fixture hashes. The old runtime 03 returned **0**; corrected runtime 04 returned
**1**. Both the fixture's typed COG variables and the actual player inventory
agreed across multiple completed samples. This reproduces and resolves the
specific descriptor-lookup bug through production game functions.

The fixture is deliberately artificial. It does not certify the authored treasure
quest, physical touch pickup, death/drop timing, or two-peer replication. Its
first preparation used an unsupported diagnostic verb and an incorrect observer
name comparison; those rejected attempts are retained. The final fixture removes
the unsupported call, audits every invoked verb against the engine registrations,
and uses exact qualified COG identity and actual numeric type tags.

## RC3 Canyon Force pickup regression (2026-09-09)

The native-visual Canyon output has SHA-256
`cd5656b2c60beb50ae4d9a368405661af9d4a16c4d47f15eff0dde228e51be53`.
All nine stock maps plus Jedi's High School passed independent structural
verification and repeat-build byte equality with this recipe revision. Their
original object placements and authored template fields are preserved except
for the documented native Force pickup model/controller substitutions.

Canyon's map COG budget is now 81 for 79 required instances. The previous
budget of 32 left all seven source Force pickups without their COG bindings.
The new mapping uses native MotS Force Boost at all five Boost locations and
native Force Surge at both original JK Surge locations. The recipe pins the
owned native model, material, script and template sources.

A private diagnostic COG was added only to a scratch copy of this output. A
134-second OpenJKDF2 MotS multiplayer host run recorded 266 samples and passed
all 22 targeted checks. The fixture staged player positions and controlled
rank/energy preconditions, then exercised the game's actual movement, collision
and pickup scripts. It did not inject pickup messages. Observations included:

- All seven original pickups loaded with valid COG bindings and native models.
- Boosts added 100 energy above the old rank-based limit, clamped to the active
  400 maximum, and stayed available when the player was full or had zero capacity.
- Both Surge locations refilled energy and used MotS bin 64. Taking the second
  renewed the same controller's timer; the effect ended 20 seconds later. Bin 65
  remained inactive.
- The underwater Boost cases worked, native `00twinkle.mat` advanced through
  observed cels 0 through 10, and all six consumed pickups naturally respawned.
  The seventh stayed available after the full-energy rejection.

A separate reset-handler probe passed nine checks: sending the normal
`NEWPLAYER` message cleared the Surge state and its visual flag. This was a
message-handler test, not a played death and automatic respawn cycle.

The Windows engine executable used for these observations has SHA-256
`fd8ddfc23f09540068318bedcc3f08e5ce6b12ea5ee04ed3cf45fd8ed46b7873`.
It was built from fork commit `9510c4713aec475006d4aac8f2c417c2e66dfef0` plus
fixes for MotS host null-taker acknowledgment/respawn and first-person render-mode
selection. Those tested source changes are now published in fork commit
[`5fa4644`](https://github.com/andreipemberton/OpenJKDF2-MotS-Fixes/commit/5fa4644d03080fef69d7137eaa2c8f295c47bd63).
The engine remains separate from the WBW application package.
Extracted production-function regressions also passed, and removing each fix
reproduced its corresponding failed regression.

These runs establish the targeted pickup behavior in one hosted multiplayer
process. They do not establish human traversal, rendered appearance, normal
character-menu setup, a played death cycle or synchronization with a joined
peer. No rendered screenshot comparison is claimed for this test. Baseline
resources and the source conversion hashes stayed unchanged. The diagnostic
script and scratch conversion are private test artifacts and are not shipped
in WBW or in the normal converted map.

## RC4 recipe tracking and user workflow (2026-09-09)

RC4 adds independent per-recipe revisions, embedded metadata, versioned output
names, a read-only MotS folder scan, explicit native path selection and the
illustrated silent workbench. It retains the RC3 native Force-pickup correction.

The final Windows source suite ran **280 tests: 278 passed and two skipped**.
The skips were a Windows symlink-privilege fixture and a Windows virtual-environment
ancestry fixture. The UI suite passed **47 tests**. An earlier full run encountered
a Windows loopback connection abort in one HTTP boundary test; its focused retry
and the complete final suite passed. That first result remains in private QA records.

Four explicit recipes—Canyon Oasis, The Duel (stock CTF), Jedi's High School,
and Ninja Kage 7.0—passed real owned-input conversion and structural verification.
An exact repeat reused all four result directories, with **all 25 generated file
hashes unchanged**, including receipts and manifests. Their outputs stayed in
private local testing folders; no original or converted payload is published.

A separate **20-second production MotS multiplayer host** loaded the exact
`bridge-canyon_wbw_v1.goo` episode. All eight targeted checks passed: host survival,
MotS multiplayer mode, exact versioned episode, seven bound pickup COGs, absence
of a diagnostic COG, unchanged source/staged GOO, unchanged owned baseline, and
no visible window. Game time advanced from 1,956 to 18,507 milliseconds. Both
Surges shared their expected controller. Its game payload is byte-identical to
the RC3 Canyon payload whose pickup behavior is documented above; the added
metadata does not change its game-resource members. This host check used no
simulated OS input or staged player movement and captured no gameplay screenshot.

Scanning the four final result folders found five current archives (four primary
outputs and the CTF startup overlay), with no errors or warnings. A separate scan
of the older Canyon test installation reported one unversioned Canyon archive and
two unrecognized retail GOOs. Before/after hashes confirmed both scans were read-only.

Actual headless Chrome checks covered the local scanner, rendered original art,
desktop and 390-pixel mobile layouts, explicit selections, download-page links,
and native-picker response handling. Picker responses were mocked, so no native
dialog opened during unattended browser QA. The 20 library chooser tests also
passed on Windows and Linux using mocked dialogs/processes. Native runtime
bundling is a separate packaging check.

These checks do not add a claim of complete Ninja Kage gameplay, all-map traversal,
door/elevator behavior, joined-peer synchronization or a played death cycle.

## RC6 CTF presentation and launch review (September 25, 2026)

RC6 exposes the required CTF support mod in the picker, cards, queue, Details and
completed conversion results. Its notice applies to declared custom CTF entries
too, with separate instructions for custom systems; no custom CTF conversion is
enabled by this update. Browser inspection confirmed the stock CTF warning and
readable install/launch instructions. UI regressions cover both stock/custom
classifications, custom dependencies, successful results and failed conversions.

The three stock episode titles now begin `CTF - ` and their individual recipe
revisions advance to `wbw_v2`. A fresh hidden native-menu replay selected all
three generated payloads and returned their explicit CTF titles, correct worlds
and TYPE 8. That replay used the pinned diagnostic menu harness with legacy
filename aliases (payload bytes unchanged); it is distinct from production host
tests of the actual revisioned filenames. The relevant native menu source is
unchanged from the harness baseline. No engine CTF menu patch was made.

The [CTF review](docs/validation/CTF_REVIEW_2026-09-25.md) records exact build and
artifact identities, production-host results, historical lighting comparisons
and limits. Menu selection and passive host observations do not establish flag
pickup, return, capture, scoring or synchronization with a second player.

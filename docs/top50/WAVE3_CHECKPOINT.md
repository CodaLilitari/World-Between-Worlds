# September 20 continuation checkpoint

Development work resumed from the September 12 checkpoint. This is not a
release or completion of the requested 150-entry expansion.

The frozen queue remains **50 JK multiplayer levels, 50 singleplayer levels and
50 mods**. The current catalog has 52 entries overall. Within the frozen queue,
39 entries now have exact-input recipes, 38 are selectable prototypes or prior
entries, and 111 still lack recipes. Castle Conflict remains unavailable pending
delivery and qualification of its engine prerequisite.

| Category | Exact-input recipe | Selectable | No recipe yet |
| --- | ---: | ---: | ---: |
| Multiplayer | 29 | 28 | 21 |
| Singleplayer | 4 | 4 | 46 |
| Mods | 6 | 6 | 44 |

These counts are recipe coverage, not completed gameplay qualifications. The
[generated status report](current-recipe-status.json) identifies exact source
matches and runtime metadata. The three original intake inventories retain their
historical acquisition/review fields; they are not live support reports.

## New concrete work

- **The Massassi Temple Level Pack 3:** all eight worlds in the original cycle,
  exact author credits and notice, independently checked component union and
  resource ownership, and inspected initial JK/MotS views. Subway and Hoodwink
  also passed 45-second passive observations in each mode. Three original missing
  dependency edges remain explicitly scoped; source script quirks are preserved.
  Warehouse's converted initial view is warmer; the cause is not isolated.
  Gameplay, audible effects, map transitions and connected peers remain open.
  See the [pack review](MLP3_REVIEW.md) and [evidence](mlp3-evidence.json).
- **Canyon Stream:** exact recipe, two fresh identical builds, original omission
  scope controls, independent geometry/resource verification, paired initial JK
  and MotS views, and 45 seconds of advancing MotS MP host simulation. The
  missing original turret movement cue and authored script anomalies remain
  explicit. Dam, lifts, traps, water movement, respawn and second peer remain open.
- **Steal the Bottle:** exact recipe with one counted saber-bin compatibility
  edit, authored AI and ending preserved, two fresh identical builds, independent
  verification, paired initial views and 90 seconds of MotS SP simulation.
  Patrol, door, thrust/conveyor, ending, saves and traversal remain open.
- **Al's Star Wars Skin Pack:** full 135 authored registrations appended to all
  55 native MotS rows. Narrow source-pinned normalization handles 11 byte-identical
  duplicate directory pairs without relaxing the general archive parser. The
  original missing Jar Jar falling cue is retained under one exact omission
  rule; ten other original sound tokens newly resolve against MotS and their
  audible equivalence remains unresolved. Three explicit native MotS MP character
  selections rendered with the requested models and soundclasses. These are
  initial first-person captures, not proof of all 135 appearances or animation.
  Separate optional mod selection only.

The [level review](WAVE3_LEVEL_REVIEW.md) and
[level runtime receipt](wave3-level-runtime-evidence.json) distinguish each proof
dimension. The [skin review](ALS_SKIN_REVIEW.md) and
[skin runtime receipt](wave3-skin-runtime-evidence.json) retain the sound and
resource-capacity findings. No initial capture or idle simulation run proves a
playthrough.

## Integration and validation state

The earlier three-recipe source suite passed on Windows/Python 3.13.15 and Ubuntu/Python 3.14.4:
392 checks per platform, with 390 passing and two environment-specific skips.
Windows skipped a symlink-creation check because this process lacked the required
privilege and a virtual-environment ancestry check; Linux skipped two Windows-only
launcher checks. The tested source hashes stayed unchanged throughout both runs.
These source tests include the 41 SP checks and the 24 skin-adapter checks, with
negative controls against authored-behavior drift and broader omission waivers.

A repeated Windows failure exposed a real HTTP response race: rejecting a POST
before reading its separately transmitted body could abort the connection before
the client received the 403. Error responses now discard only a clearly framed
body of at most 128 KiB, with a total 0.5-second receive deadline. Authentication
and origin decisions still precede parsing and service actions. Regression tests
cover delayed bodies, invalid framing, time limits and absent service callbacks.
The earlier failed logs remain preserved; the final runs above include this fix.

The actual end-user service rebuilt all three recipes in fresh Windows processes
under hash seeds 1 and 999. All 22 result files match between those builds; fresh
Linux builds produced identical versioned game archives. Canyon's two original
notices are retained by that service, not merely by a private build script.
The read-only installation scanner recognizes all three staged archives as
current revision 1, with zero errors or changes to any of those 22 files. This
was an explicit private staging-tree scan, not a scan of a user's installation.

At that checkpoint, all 51 exported recipes and source locks matched the live catalog. An in-memory
source package passed full inspection with the previous checkpoint's updater,
including its explicit file allowlist and game-asset exclusions. It was not
published as a release. Exact output, package, test-log and receipt hashes are
in the [final validation record](wave3-validation.json).

All new recipes use revision `wbw_v1`. Their versioned output names and embedded
markers were checked through the actual service. Their canonical game payloads
match the separately recorded runtime-tested bytes. A source-lock change alone
does not mean a game-payload revision changed; runtime evidence binds the
canonical game payload separately from generated metadata.

## Next required work

The subsequent pack-omission extension is covered by a separate
[validation record](mp-pack-omission-validation.json). Windows and Linux each
ran 407 source tests: 405 passed and two environment-specific checks were
skipped. All four existing MP pack archives and manifests remain byte-identical
to the previous converter. The 51 source locks were regenerated; no existing
game-payload revision changed. The source package rebuilt identically in memory
and passed the preceding updater's inspection. This infrastructure change adds
no selectable recipe by itself.

The subsequent MLP3 catalog integration adds one prototype, revision `wbw_v1`.
Windows/Python 3.13.15 and Linux/Python 3.14.4 each ran 414 source tests: 412 passed
and two environment-specific checks were skipped. The actual service produced
the same versioned archive on both platforms; two fresh Windows hash seeds also
produced identical complete result folders. The read-only scanner recognizes the
output as current. All 52 source locks match the catalog. The
[MLP3 validation record](mlp3-validation.json) records package inspection and exact
hashes; no binary release or converted assets were published.

The [next highest-ranked missing-entry review](NEXT_ENTRY_REVIEW.md) records
original-engine comparisons and concrete source issues for MP, SP and mod
entries, with MLP3's subsequent promotion distinguished from the other intake work.

1. Progress the remaining 111 entries through exact conversion and appropriate
   MotS tests, including multiworld packs and all authored mod selections.
2. Add the missing gameplay proof for existing prototypes: ordinary control-driven
   doors/lifts, pickups and respawn, authored traps, SP goals and saves, full skin
   appearance/animation, map transitions and matched second peers.
3. Extend qualification of the separate engine's model and sound corrections.
   Both fixes are now pushed together at
   [69028bf3](https://github.com/CodaLilitari/OpenJKDF2-MotS-Fixes/commit/69028bf3088c9e3e3a83bc0cbb96cfb816c5acd8).
   The unchanged forward/reverse 32-appearance sequences select the correct
   models and soundclasses, with sound storage growing beyond the old 153-slot
   limit and no capacity rejection. All 6,366 linked event entries across six
   controls match their exact source definitions and WAV headers. See the
   [combined evidence](als-model-sound-growth-evidence.json). Audible effects,
   all 135 appearances, GUI, animation, saves, map transitions and peers remain
   open. The earlier material estimate was incorrect: live capacity is 1,288,
   not 644. Prior model-only and sound-failure receipts remain as baseline evidence.
4. Integrate and deliver the separate engine prerequisite for Castle, preserving
   the main engine checkout and unrelated worktrees. Converter changes stay here.

No original downloads, game/mod asset files or finished conversions belong in
GitHub. Approved documentation screenshots are the explicit exception. Private
builds, source-bearing audits and runtime directories stay outside this repo.
The stock JK campaign remains a separate future plan preserving both stories
with neutral MotS Force powers; it does not count toward these 150 entries.

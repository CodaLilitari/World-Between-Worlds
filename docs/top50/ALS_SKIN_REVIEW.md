# Al's Star Wars Skin Pack: exact optional prototype

[Original Massassi entry 997](https://www.massassi.net/levels/files/997.shtml), by
**Al MacDonald**. Recipe `mod-als-star-wars`, revision `wbw_v1`. This is an
explicitly selected mod, not a level dependency or automatic startup package.

The original table contains 28 stock JK registrations and 135 authored additions.
The recipe keeps all 55 native MotS registrations and appends those 135, producing
190 contiguous entries. Its two deliberate native-path overrides are
`misc/models.dat` and `ui/jkstrings.uni`. It introduces no COG, world, animation
or puppet override. Both original notices accompany the local output unchanged;
the source batch launcher is pinned but is never executed by WBW.

## Exact normalization and resource ownership

The source GOB contains 11 pairs of duplicate normalized material paths. Each
pair has identical payload bytes. A source-pinned operation validates the whole
archive, directory, pair membership, indices, offsets, lengths and hashes before
removing exactly the second directory entry. It preserves all payload bytes and
offsets at this normalization stage. The general archive parser is unchanged and
continues to reject unreviewed duplicates and malformed resource ranges.

Authored resources retain their directories with isolated `al_` basenames.
Counted filename edits reverse to the original source bytes. All 87 copied
owned-JK dependencies are independently reachable. The original unregistered
Luke Hoth model, unused materials and other leftovers remain isolated; no new
menu character or behavior is invented for them. Full ownership is recorded in
the local manifest. No source assets or completed conversion are distributed.

## Sound findings remain unresolved

Jar Jar's original soundclass requests `kennydead.wav` once for its falling
event. It is absent from the original pack and all eleven inspected owned
baseline archives. An exact source/output/event/hash rule preserves the missing
reference; a new missing sound or replacement voice fails verification. Source
inspection indicates the engine skips this event and retains the rest of the
soundclass. Silence has not been confirmed by an audible gameplay test, and a
quiet load log does not prove that every sound exists.

Ten other original sound tokens (`dv_*` and `KK600*`) were absent from the
inspected JK sources but now resolve through native MotS. The original notices
declare no extra sound or MotS dependency. Their event mappings, source hashes,
native paths and provider hashes are pinned in the recipe and local manifest.
**The intended voice equivalence is unproven.** This target behavior difference
appears in the catalog summary and generated README; it is not a same-name
compatibility assumption or a completed audio qualification.

## Bounded validation

Two fresh process builds under hash seeds 1 and 999 produced the same five files.
The canonical archive has 2,012 resources, 28,551,756 bytes, and SHA-256
`88211772487cd958f60629878568cdda9afdeb33c716f5854f02fd49b2fb48af`.
Independent checks verify all registrations, inverse source transformations,
owned dependency reachability, typed references and the two exact native overrides.
The adapter's 24 tests include duplicate, malformed-input, omission and notice
controls. Agent Han and Anime output bytes remain identical to the earlier adapter.

[Runtime evidence](wave3-skin-runtime-evidence.json) covers these three actual
selections on native MotS multiplayer `k1.jkl`, each in a fresh isolated process:

| Final row | Requested and observed model | Observed soundclass |
| ---: | --- | --- |
| 55 | `al_3po.3do` | `al_ky3po.snd` |
| 109 | `al_jarjar.3do` | `al_jarjar.snd` |
| 189 | `al_zuckuss.3do` | `al_kybossk.snd` |

All three rendered an initial frame, loaded the requested model/soundclass,
reported 18 hierarchy nodes, and exited successfully with no resource diagnostics.
The fixed first-person camera does not establish visible full-body appearance.
These are three direct MPC selections, not all 135 skins or a GUI browsing test.
The exact engine and payload hashes are retained in the receipt.

## Remaining gameplay and engine gates

The engine's model-selection table is dynamically allocated and can represent
190 correct rows. Its separate saved-character browser is capped at 32 MPC files;
direct `-character` autostart bypasses that enumeration and table membership, so
it cannot certify the GUI. GUI previews allocate and release their own resources.

Running-world caches have now produced a specific selection failure. An opt-in
private engine probe used the production MotS appearance function on the real
local player, requesting a reviewed set of 32 skins in the same native `k1`
world. It changed no game assets or allocation limits. Both forward and reversed
orders filled the **109-slot model pool** and failed on the eighteenth distinct
request. The function returned success, but substituted `kk.3do` / `ky.snd` for
the requested character. Each failing skin loaded correctly in its own fresh
process, and 32 repeated requests for one cached skin caused zero pool growth.
The [five-run capacity evidence](als-capacity-runtime-evidence.json) pins the
instrumented build, exact payload, requested/actual identities and counters.

**Correction to the earlier material estimate:** the live material allocation is
1,288, not 644. The earlier source review counted only one of two doublings of
the declared 322 slots. The failed forward run used 527 of those 1,288 slots;
it demonstrates model exhaustion, not material exhaustion. The probe deliberately
exited with status 7 after observing fallback; this was not a process crash.

The sound pool also reached 153/153, but individual sound-load results and audible
behavior were not measured. That remains an additional gate, not a confirmed
audio failure. These same-world appearance sequences are not simultaneous
32-player networking, GUI qualification, or a fix. An engine correction and
the corresponding regression runs remain required.

Required follow-ups include all authored selections, visible appearance and
animation, weapon attachment, affected sound events, death/respawn, normal GUI
selection, measured aggregate resource occupancy, matched peers and map changes.
Any demonstrated engine defect belongs in the separate engine fork. Do not
discard characters, stack unrelated overlays or rewrite native maps to conceal it.

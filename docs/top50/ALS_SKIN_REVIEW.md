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

Follow-up instrumentation now confirms a separate sound-loading failure at
**153/153 sound slots**. The diagnostic runs only after a cache miss and a
successful file-open, in the existing full-pool rejection branch. It does not
change allocation or playback. The second appearance in the forward sequence,
Bespin Chewbacca, already produces five failed sound loads while its requested
model and soundclass both match. The soundclass loader can skip failed sounds
and still report success for the class.

The [four-run sound evidence](als-sound-capacity-evidence.json) records 117
rejections across 25 existing WAVs in the forward sequence; 32 cached repeats
produce none. Bespin Chewbacca loads fresh without capacity rejection. Fresh
Muftak still has six initial sound rejections despite matching model/class and
exit status zero. Across both failing runs, 30 distinct rejected files were
verified in the exact overlay: five authored originals and 25 owned-JK
dependencies. These are distinct from Jar Jar's genuinely absent original WAV.

No audible playback was tested. These same-world appearance sequences are not
simultaneous 32-player networking, GUI qualification, or a fix. The separately
implemented model and sound corrections are recorded below; wider mod and
gameplay qualification remains required.

Required follow-ups include all authored selections, visible appearance and
animation, weapon attachment, affected sound events, death/respawn, normal GUI
selection, measured aggregate resource occupancy, matched peers and map changes.
Any demonstrated engine defect belongs in the separate engine fork. Do not
discard characters, stack unrelated overlays or rewrite native maps to conceal it.

## Model-storage correction in the engine fork

The separately reviewed [model fix](https://github.com/CodaLilitari/OpenJKDF2-MotS-Fixes/commit/bf7a46f8dc30ddc6fd4734326935a6ea07081ef7)
is now pushed on the engine fork's `codex/model-cache-growth` branch. It grows
the standalone engine's model store without moving loaded model headers or
their borrowed cache keys; the original-executable injection build retains its
contiguous layout. The [bounded runtime evidence](als-model-growth-evidence.json)
records both 32-selection sequences completing correctly, growing from 93/109
to 124/218 models. The cached and three fresh-selection controls also pass.
Native MotS Kyle/Mara and native JK initial-render controls passed separately.

That model-only checkpoint fixed the demonstrated model fallback while its
longer successful sequences still reported sound-load rejections. No updated
binary release, complete skin compatibility, audible playback, peer or save/load
qualification is claimed. Detailed source tests and remaining parser/cache
boundaries are documented in the engine commit.

## Combined model and sound correction

The [sound-storage correction](https://github.com/CodaLilitari/OpenJKDF2-MotS-Fixes/commit/69028bf3088c9e3e3a83bc0cbb96cfb816c5acd8)
is pushed on the engine fork's `codex/model-sound-cache-growth` branch, directly
on the model fix. It adds nonmoving sound-header pages, preserving pointers held
by soundclasses, the mixer, sectors and the cache. The engine's original layouts
remain unchanged; bounded IDs leave the signed `-1` sentinel unallocated.

The same forward and reverse sequences each select all 32 requested appearances
and finish at 124/218 models and 191/409 sounds, with no model, sound or material
capacity rejection. Cached repeats, three fresh selections and three separate
native JK/MotS initial-render controls also pass. Both storage fixtures pass
ASan/UBSan, including legacy behavior and deliberate mutation controls.

An independent comparator checked all 6,366 linked sound-event entries across
the six appearance runs against exact source SND rows, resolved WAV providers
and WAV headers. It checks ordering, flags, parameters, IDs and header fields;
every comparison passes with zero omission allowance. The forward and reverse
runs each cover 13 distinct soundclasses and 80 distinct sound IDs. Fifteen
deliberately invalid comparator inputs are rejected. The
[combined evidence receipt](als-model-sound-growth-evidence.json) binds these
results to the executable, source patch and exact per-run records.

This establishes sound-event/header loading for those controls, with null audio.
Audible output, PCM/backend execution, all 135 appearances, full-body animation,
GUI use, saves, map transitions and connected peers remain unqualified. Original
missing resources and native voice-content differences are separate findings.
No new game assets or binary release were published with this source checkpoint.

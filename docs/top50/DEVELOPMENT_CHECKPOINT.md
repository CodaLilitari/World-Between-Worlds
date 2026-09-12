# Top-50 expansion: development checkpoint

September 12, 2026. This is development work on `codex/massassi-top50`, not a
published release or a claim that all 150 requested entries are supported.

## Scope and current coverage

All 150 ranked original downloads were acquired privately and independently
rehashed: **486,655,537 bytes** across exactly 50 entries in each named Massassi
category. Source listings, attribution, download links and readme hashes are
recorded in the category inventories. Originals and their contents stay outside
this repository.

| Requested category | Original hashes recorded | Entries with exact-input recipes | Selectable entries | Entries without a recipe |
| --- | ---: | ---: | ---: | ---: |
| JK multiplayer levels | 50 | 26 | 25 | 24 |
| JK singleplayer levels | 50 | 2 | 2 | 48 |
| JK mods | 50 | 4 | 4 | 46 |
| Total | 150 | 32 | 31 | 118 |

Castle Conflict is the one matched but unavailable entry. A selectable
prototype still has the limits shown in its recipe; selection is not evidence
of a complete playthrough. Existing recipes outside these ranked categories
remain available. The complete WBW catalog has 45 entries: the earlier 27 plus
18 new entries, of which 17 are prototypes and Castle is unavailable.

Maintainers can refresh these counts with `python -B tools/top50_status.py`.
It matches the exact original hash and source listing, rather than matching a
title or treating a downloaded file as a supported recipe.

## New recipes and preservation decisions

- Multiplayer additions include Blue Rain, Goldeneye Facility, Egypt, 4H Gun
  Yard, Acid Storage Facility, 6000 Block, Gladiator, The Matrix, Bar and Grill,
  Heart of the Forest, Jedi Tower 2000 and Baron's Head at Night. Complete
  active episode rows are preserved for the multiworld packs. Orphan embedded
  worlds are inventoried separately, not silently promoted into playable rows.
- SP prototypes cover The Phantom Menace: Final Battle (Revised) and Legends
  of the Force: Darth Maul vs. Qui-Gon Jinn. Their authored episode progression,
  AI, cutscene scripts and SP Force behavior remain subject to their specific
  counted compatibility edits and preservation checks.
- New optional mod recipes cover Black and Yellow Flame Saber, the 16-bit Saber
  Pack and Agent Han Solo. They stay in Mods and are never implicitly selected
  with a level. Agent Han preserves all 55 native model registrations and adds
  one skin and label. Its only native-path overrides are the model registry
  and UI string table; its authored graphics/audio have isolated names within
  their original parent directories.

No global `z_jkdf2` asset dump is generated. Each episode remains self-contained
within its declared scope. A two-cohort archive audit covered all 18 new
profiles and found **zero unexpected active resource conflicts**. It separately
identified the declared saber-material and skin-registration overrides and
the native differences already present between MotS's own MP/base archives.
This does not certify loose-file precedence, persistent caches or peer checksums.

## Concrete bugs found

**Tiny animated MATs:** Castle Conflict exposed an engine loader bug. A valid
2-by-2, 8-bit image contains four packed bytes, while SDL allocates eight bytes
with padded rows. The old loader consumed padding from the file, misaligned the
next cel header and crashed. The unchanged Castle payload passed with the
isolated correction, as did Canyon Oasis and native MotS MP/SP controls.

The local engine fix is commit `f573653e34c6c862ec5c1cbf33c7cd9d4508646f` on
`codex/wbw-packed-material-rows`, based on `5fa4644d`. Synthetic packed-row tests
passed under ASan/UBSan and as a Windows console executable. The tested game
candidate replaced the material-loader object and relinked against the earlier
pinned runtime's objects/libraries; it was not a full current-engine rebuild.
Castle stays unavailable pending supported engine integration and retesting.

**Authored MP rank changes:** Heart and Tower change rank after native MotS has
cached its regeneration maximum. A controlled run without the correction
retained a zero cap and drained mana to zero despite rank 8. The final recipes
refresh the existing native controller only when its cached maximum is too low.
This avoids needlessly restarting its pulse on the original 15-second timer.
Live observations confirmed a 400 cap, the authored reset to 200 mana, then
increments of four per second. The original JK/native new-player order explains
the initial 400 mana. No global Force COG replacement was introduced.

**SP is different:** Native MotS recomputes the rank limit on each SP pulse, so
the MP rank workaround is not applied to the SP recipes. The engine also maps
ordinary weapon ordinals in `SetInv`/`ChangeInv`; only demonstrated incompatible
calls receive explicit edits. The native saber descriptor/ordinal distinction
is recorded per script.

**Installed recipe eligibility:** The scanner still identifies older or
unversioned archives belonging to an unavailable recipe, but no longer offers
an update that the conversion selector would reject.

## Evidence and limits

The final 332-test source suite passed on both Windows and Linux with the
private owned-game fixtures enabled; each platform skipped two inapplicable
or environment-dependent checks. The maintainer suite passed 22 tests, and
the UI suite passed 49. The exported 45-recipe catalog and CI template agree
with the runtime sources and packaging configuration.

[Reproducibility evidence](replay-evidence.json) records fresh builds of all
17 newly selectable recipes under Python hash seeds 1 and 999. All 101 output
files per run were identical, including notices, manifests and receipts. Their
canonical game payloads matched the earlier engine-tested candidates. Reuse
checks for the pack, SP and skin families recognized the existing output trees.
Independent Linux service conversions of 6000 Block, Phantom and Agent Han
produced the same stamped GOO bytes as Windows. No standalone binary or public
update was released from this checkpoint.

Final source files follow the repository's LF line-ending policy. Recipe locks,
both 17-recipe replays, the three-family reuse checks and the Windows/Linux
comparison were regenerated after normalization, so Git checkout normalization
does not silently change the recorded source fingerprints. Python syntax trees
and canonical game payloads were unchanged by this formatting correction.

The source package also passed the previous updater's full archive inspection.
It was built from 72 explicitly allowlisted files, with no game/archive payload
files, private absolute paths or unexpected embedded binary data. This package
check was performed in memory; it is not a published download.

[Development evidence](development-evidence.json) contains hashes, mode/world
checks, bounded runtime observations and the SED comparison. It contains no
original or converted game payloads. The recipe catalogs bind their runtime
evidence to canonical game payloads, independently of changing WBW metadata.

SED independently parsed nine selected converted worlds. Phantom, all four
Gladiator worlds and Acid passed its geometry validation. Castle and both
6000 Block variants retained exactly the same zero-length-edge findings as
their untouched originals: 1,404 for Castle and two per 6000 world, with no
added or removed findings. Those three are not labeled clean geometry passes.
No direct SED correction was used as an unrecorded recipe input.

The engine's current autostart path hardcodes Kyle. Agent Han's test therefore
establishes overlay loading, not selected-skin animation or appearance. Its
native skeleton/KEY checks and remaining baseline anomalies are detailed in
[the skin review](SKIN_REVIEW.md).

Follow-up [SP camera comparisons](SP_RENDERED_COMPARISONS.md) captured both new
SP prototypes in OpenJKDF2 JK and MotS modes using the same hidden-rendering
executable and cameras. The visible geometry, materials and lighting align in
the two inspected views. Their exact inputs, images and limitations are recorded
separately; these screenshots do not promote the recipes to full gameplay passes.

The remaining work includes 118 entries without recipes, the Castle engine
prerequisite, broader rendered comparisons, authored mechanics, SP objectives and
progression/save checks, skin selection and animation, respawn, same-process
transitions and matched second-peer tests. These dimensions are not implied by
successful structural verification or a hosted load test. KWP and Matrix's
specific unresolved dependencies remain documented in their review queues.

The [stock JK campaign plan](../STOCK_JK_CAMPAIGN_PLAN.md) remains separate:
preserve both authored stories with neutral MotS Force powers on either route.
It is planning only and contributes no enabled recipe or count to this work.

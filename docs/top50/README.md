# Massassi: 50 entries in each JKDF2 category

Andrei confirmed **50 per category** on September 12, 2026: 150 Massassi entries,
ranked by the download counts shown by the site's category listings. This is a
conversion project with separate intake, recipe and testing stages. A source
inventory is not a compatibility certification or a promise of an immediate
release.

See the [development checkpoint](DEVELOPMENT_CHECKPOINT.md) for current recipe
coverage, concrete fixes, test evidence and the work still pending.
The [remaining-source review](REMAINING_SOURCE_REVIEW.md) records individual
findings for all 118 entries still lacking recipes; it does not enable them.

| Category | Scope and frozen inventory |
| --- | --- |
| Jedi Knight Multiplayer Levels | [Multiplayer review queue](MP.md) · [metadata](mp.json) |
| Jedi Knight Single Player Levels | [Singleplayer review queue](SP.md) · [metadata](sp.json) |
| Jedi Knight Mods | [Mods review queue](MODS.md) · [metadata](mods.json) |

The ranking uses the exact named categories. Massassi lists JK CTF and Jedi
Knight Arena separately; they are not silently combined with this multiplayer
top 50. Existing WBW stock CTF recipes remain separate. Website download counts
are observations at the recorded snapshot time, not a quality ranking. Distinct
versions listed by Massassi remain distinct entries.

## What counts as a completed entry

1. Preserve the original listing, author attribution, download URL, archive
   hashes and original readme/terms evidence. The metadata stays in this repo;
   the downloaded files and extracted assets stay in the private workspace.
2. Inventory all archives, episode rows, worlds and required startup files. A
   pack is one ranked entry, but support must cover every active world and any
   dynamically referenced worlds. Report unused embedded worlds separately.
3. Review resource ownership, actual virtual paths, native MotS equivalents,
   authored replacements, startup binding and dynamic COG references using the
   [resource workflow](../RESOURCE_WORKFLOW.md). Shared basenames alone do not
   establish a collision.
4. Implement hash-pinned, counted WBW transformations. Any SED experiment must
   replay from the untouched originals through WBW. Rebuild in fresh directories
   and verify structure, resource ownership and deterministic output independently.
5. Test the correct target mode in OpenJKDF2 with MotS compatibility enabled.
   Report loading/simulation, rendering, authored mechanics, progression and
   multiplayer peer synchronization separately. A load smoke is not a playthrough.
6. Only then attach the supported recipe IDs and exact evidence to the inventory.
   New entries must never inherit historical runtime results from older recipes.

Mods stay in the Mods section and require an explicit selection. A mod with no
level is tested on a declared map rather than treated as a map itself. Native
MotS editions, if found, are documented as alternatives; their existence does
not silently remove an entry from the requested top 50.

Completed outputs stay local and self-contained in their declared episode or
startup scope. There is no automatic conversion of the entire queue, automatic
mod loading, shared global asset dump, or publication of game/mod payloads.

## Separate future work

Maintainers can run `python -B tools/top50_status.py` to validate the 50/50/50
ranking, attribution, source hashes and current exact-input recipe matches.
This report does not download, convert, install or launch anything; a matching
recipe is not a gameplay test result.

The [stock JKDF2 singleplayer campaign plan](../STOCK_JK_CAMPAIGN_PLAN.md) is
reserved work outside these 150 custom entries. It does not add an enabled
campaign recipe or interrupt this queue.

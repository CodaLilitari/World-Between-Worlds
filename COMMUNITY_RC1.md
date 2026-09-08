# Community recipes for 0.1.0-rc1

This source-only experimental RC adds fifteen original JK multiplayer maps to
the nine stock maps, Jedi Dojo and Caesar's Palace already supported. Conversion
is local, deterministic and restricted to reviewed original archive hashes.
Original authors remain credited below; no original or generated level assets
are included in the tool package. Coda Lilitari is a human-facing tooling credit,
not an invented GitHub account or a claim to authorship of the maps.

## Requested maps and recovered originals

| Recipe key | Original map / author | Original source |
| --- | --- | --- |
| `jhs` | Jedi's High School 1.0 — PeD_HeAd | [JKDF2.NET original ZIP](https://www.jkdf2.net/JKBot/JKArchive/JKDF2/JKDF2/Game%20Files/jkmp/jhs.zip) |
| `purgatory` | Purgatory — SM Sith Lord | [Massassi 1202](https://www.massassi.net/levels/files/1202.shtml) |
| `courtyard` | Courtyard — Adam (NOFpuXnk) Freeman | [Massassi 1122](https://www.massassi.net/levels/files/1122.shtml) |
| `shadow-caverns` | Shadow Caverns — NOFpuXnk | [Massassi 1169](https://www.massassi.net/levels/files/1169.shtml) |
| `deicide` | Deicide — NOFpuXnk | [Massassi 3082](https://www.massassi.net/levels/files/3082.shtml) |

The full current Massassi JK multiplayer catalog contained 1,289 distinct rows
at the audit. Three entries were attributed to NOFpuXnk or the verified Freeman
alias; the exact global author search agreed. This does not claim every map the
author ever made is still publicly archived.

JHS was found by following public directory listings into JKDF2.NET's `jkmp`
archive. ZIP CRC/path checks and the embedded GOB passed; its own readme identifies
PeD_HeAd, version 1.0, May 2, 1999. This supersedes the previous unsuccessful
Massassi-only recovery result. JHS is the actual recovered level, not a rebuilt
approximation or a different high-school map.

## Ten additional selections

These were chosen from Massassi's [top fifty JK multiplayer downloads](https://www.massassi.net/levels/jkmp/?sortby=dl_count&num=50),
snapshot 2026-09-08 14:35 UTC. Counts are historical snapshot values, not live
counters. Original descriptions, bundled notes, and twenty available primary
screenshots informed the selection; no preference here implies a completed
playthrough.

| Rank | Downloads | Recipe / map / original author | Conversion and gameplay focus |
| --- | ---: | --- | --- |
| 1 | 27,708 | `drazen-isle` — [Drazen Isle](https://www.massassi.net/levels/files/428.shtml), Jeff Walters | Large social environment, treasure maps and death/backpack transfer. |
| 3 | 18,528 | `duel-of-the-fates-se` — [Duel Of The Fates S.E.](https://www.massassi.net/levels/files/423.shtml), Hoth Rebel | Vertical reactor/hangar layout; eleven authored Episode I player-model overrides. |
| 4 | 16,185 | `morpheus` — [Morpheus](https://www.massassi.net/levels/files/216.shtml), bug | Jump pads, no-fall-damage surfaces, nine authored weapon/explosion template overrides. |
| 5 | 13,925 | `jawa-dwelling-se` — [Jawa Dwelling SE](https://www.massassi.net/levels/files/454.shtml), Red_0005 | Traps, secrets, embedded arenas and authored 0.1-second concussion-rifle fire wait. |
| 6 | 13,829 | `mos-espa-rpg` — [The Mos Espa RPG](https://www.massassi.net/levels/files/1087.shtml), Justin (Saber_Scorpion) Stebbins | Jobs, businesses and traversal; scope mods are recommendations, not a bundled hard dependency. |
| 8 | 11,416 | `atlantis` — [Atlantis](https://www.massassi.net/levels/files/135.shtml), bug | Ruined ocean architecture and force-dependent weapon access. |
| 11 | 10,392 | `area-21` — [Area 21](https://www.massassi.net/levels/files/1839.shtml), JeDak | Shared spawn hub, twenty portal routes and weapon-stripping areas. |
| 12 | 9,968 | `death-star-arena` — [Death Star Arena](https://www.massassi.net/levels/files/1251.shtml), Craig Urquhart | Large movie scenery with conventional corridor/hangar combat. |
| 13 | 9,149 | `naboo` — [Naboo](https://www.massassi.net/levels/files/1787.shtml), Ortheza | Original MotS-to-JK provenance; JK edition converted back, with the saber grant adapted. |
| 22 | 6,971 | `stargate` — [Stargate](https://www.massassi.net/levels/files/1242.shtml), JK_addict | Unarmed spawn, gate activation, teleportation and weapon removal/restoration. |

Chaos Eternal (#10) is deferred: its three-level cooperative campaign needs
objective, enemy synchronization and actual level-transition checks. It was not
flattened into a deathmatch map. Stargate takes that slot. Hoth Wars is a future
candidate, not part of this RC's accepted recipes.

## Reviewed adaptations and omissions

The normal conversion preserves geometry, object placement, original numeric
resource indices, scripts, COG execution flags and typed arguments. JK resources
receive reserved names; native MotS player, weapon, inventory and force behavior
is intentional except where a reviewed per-map rule preserves an authored change.

- **JHS:** three exact missing-reference edges remain absent: the unused world
  `00_glass.mat` declaration, the same untextured shard material, and the original
  argument-free `minetrap.cog` placement. Unreferenced jetpack/startup scripts stay
  inactive.
- **Purgatory:** absent `nat.mat` is used by one textured surface. The original
  missing `kk60008.wav` declarations/defaults are overridden in live placements.
  No replacement image or audio was invented, and the image's original contents
  are unknown. Purgatory is Massassi 1202; 2542 is Sith Mercenary Headquarters,
  whose historical comments discuss a Purgatory resource override.
- **Courtyard:** the original `MAX` actor template is undefined in the exact
  `EYE_ACTOR1` placement. The converter reserves the missing name and preserves
  the failed original lookup. JK1.GOB is needed for the original stream COG.
- **Mos Espa:** missing `00wall4_11.mat` is used by eight textured and four
  untextured surfaces. Original fallback behavior is preserved and reported.
- **Jawa:** its missing wall material is referenced only by a geometry-mode-zero
  face. A required startup overlay applies the authored rapid concussion firing
  rate to the native MotS weapon script. The world-local original weapon COG is
  retained; it alone would not change the inventory-bound weapon.
  Its original malformed `print "got conc";` diagnostic is repaired to a valid
  function call in both copies; the failed earlier parse is retained in the audit.
- **Duel of the Fates:** a required startup overlay supplies eleven original
  model replacements already selected by the native MotS model table, with their
  namespaced material dependencies. MotS's extra model choices remain available.
  One apparent missing COG name occurs only inside diagnostic printed text.
- **Morpheus:** nine reviewed source weapon/explosion field changes also apply to
  the templates actually spawned by native MotS weapons. Copying only namespaced
  JK templates would have left those weapons at native defaults. Native inheritance
  and unmodified fields are retained.
- **Area 21 / Stargate / Naboo / Drazen:** exact inventory adaptations distinguish
  JK's saber and bowcaster from MotS's actual weapon bins. Numeric mode arguments,
  force rank, mana and unrelated numbers are never globally rewritten.
- **Drazen backpack prerequisite:** use the fork's backpack fix, commit
  `4dc57962e46a72662b59d36c30f15eacef6234b5`. The original lookup checked a
  backpack slot's descriptor instead of the stored item bin. A private COG
  fixture reproduced a lost map item on the old engine and recovered it with
  the fix. The native contents array holds twelve entries; a full backpack can
  still exclude later items. Full treasure/death/peer behavior needs playtesting.

Original readmes and their differing modification/distribution restrictions are
recorded in the private audit. The tool emits private local candidates; this RC
does not grant redistribution rights over game data, authors' levels or artwork.

## Test scope

See VALIDATION.md for measured results and hashes. Structural verification checks
every surface, sector, vertex, UV, object, COG argument and template inheritance;
binary assets remain byte-identical to source, and exact script edits are checked.
Repeated builds verify determinism. Mandatory startup overlays are checked
separately because inventory/player initialization occurs before episode loading.

Headless multiplayer host runs verify the selected world, MotS mode, multiplayer
state, a local player, advancing simulation and absence of crash files during the
measured window. They do not establish rendered appearance, complete traversal,
combat balance, every trap/portal, repeated deaths or remote-peer synchronization.
Those are explicit acceptance tasks for playtesting, not inferred passes.

Use the OpenJKDF2 MotS compatibility executable and one selected startup overlay.
Restart with the matching overlay before switching map families; restart without
the previous overlay for maps that need none. Menu episode selection alone does
not reset global script, inventory and model overrides.
Retail MotS patches and MotS Enhanced are not part of these baseline conversions.
SBX and Manowars are separate gameplay-mod combinations and require one-at-a-time
tests with the converted maps before any combination compatibility claim.

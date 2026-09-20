# The Massassi Temple Level Pack 3

Recipe `mp-mlp3`, revision `wbw_v1`, is a **prototype** for the complete original
eight-map multiplayer pack. Select it under Levels, supply the exact original
[Massassi download](https://www.massassi.net/levels/files/1270.shtml), and convert
locally using owned JKDF2 and MotS installations. The generated archive is
`bridge-mp1270-pack_wbw_v1.goo`; it requires no startup overlay.

| Original world | Original author |
| --- | --- |
| Hoodwink | Stress |
| Dry Heat | NorthChaos |
| Hard Vacuum | Posse and Naythn of AE |
| Death's Dome | Justin "Juz" Stocks |
| Warehouse | Home_Sliced |
| Oy'glah'th | Freelancer |
| Subway Station | Jepman |
| Castle of Ice and Wind | bug |

The complete original episode order and cycle are preserved. Castle of Ice and
Wind is a different map from Castle Conflict. The original 6,876-byte notice is
retained unchanged, including each author's terms; WBW grants no redistribution
rights. No original archive, game resource or finished conversion is hosted here.

## Conversion and resource ownership

Each world passes an independent source-to-output reconstruction check before
the archive union is checked. That covers geometry, replicated light values,
placements, typed COG arguments, ordered template inheritance, reviewed native
MotS providers, namespaced dependencies, and exact source-pinned compatibility
edits. The complete union contains 914 resources. Two private builds produced
identical archives and manifests.

The source audit separately checked 164 runtime COG bindings against their exact
providers: the 28 distinct source scripts match owned JK originals, while output
gameplay bindings use reviewed native MotS controllers. Authored environment
scripts remain subject to the separate preservation checks. The Force-pickup
compatibility adapter is independently
checked, with native MotS visual resources and original pickup placements. An
unused original shield-shard COG is not imported. Resource paths and actual
resolved providers govern ownership; equal basenames alone do not prove overlap.

Three precisely scoped source dependency edges remain absent. Their full
referring paths, hashes and occurrence counts are checked from source and output
bytes. An output manifest cannot add exceptions, and neither a sibling map nor a
native fallback is allowed to silently fill one of these missing names.

## Preserved source limitations

- **Subway:** `subway_start.cog` is absent from the original and the pinned owned
  baselines. Both its script-table row and sole active instance remain represented
  by the exact omission rule. Its intended startup behavior is unknown.
- **Hoodwink:** the WAV `00electrexplo3.wav`, referenced by the world sound table
  and the authored sparks controller's default declaration, is absent. The placed
  controller instead supplies
  the existing `00rumbleamb01.wav`; this distinction is checked from source, not
  inferred from listening.
- **Dry Heat:** the authored comma-decimal vector token is preserved.
- **Castle of Ice and Wind:** the authored undeclared `dummy` symbol is preserved.

These caveats also appear in the generated README. They are not generalized
missing-resource waivers or speculative source repairs.

## Observed runtime and remaining tests

All eight unchanged original worlds rendered in OpenJKDF2 JK MP mode, and all
eight converted worlds rendered in MotS MP mode. The captures were inspected.
The converted initial loads reported no resource diagnostics, and isolated source
and staged inputs remained unchanged. The original Oy'glah'th capture used the
separately documented map-name gate patch to accept its authored apostrophes.

Hoodwink's paired initial images are pixel-identical. Warehouse's converted view
has a warmer color balance while retaining visible geometry and textures; its
mean absolute channel difference is about 3.502/255. The cause has not been
isolated. The other numeric image differences and all capture hashes are recorded
in [the evidence receipt](mlp3-evidence.json); exact visual parity is not claimed.

Subway and Hoodwink each also ran for 45 seconds in both original JK and converted
MotS MP modes, with advancing simulation and no reported resource errors. These
were hidden, passive runs with null audio. They do not establish audible effects,
movement, doors, elevators, pickups, authored traps, complete traversal, automatic
map transitions, connected-peer synchronization or retail-engine behavior.

The actual WBW service reproduced the same versioned archive on Windows and
Linux, matching the runtime-tested canonical payload. Two Windows hash seeds
produced identical complete result folders. Original notices and all caveats
were delivered, and the read-only scanner identified revision 1 as current
without changing staged files. [Source and service validation](mlp3-validation.json)
records the independent test and package gates. The catalog status remains
prototype until the missing gameplay evidence is established.

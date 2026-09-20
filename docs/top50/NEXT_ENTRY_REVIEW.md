# Next highest-ranked missing entries

September 20, 2026. These are source reviews and original-engine comparisons,
not new selectable conversions. Recipe coverage remains 38 of the frozen 150
entries, with 112 still lacking recipes. The separate stock campaign plan is
unchanged. Original downloads, source-bearing audits and all game assets stay
private; this document contains only findings and evidence hashes.

## Multiplayer: The Massassi Temple Level Pack 3

[Massassi entry 1270](https://www.massassi.net/levels/files/1270.shtml), rank 7,
by the contributors credited in its original notice. Original ZIP SHA-256:
`48a4e32e77be5d5e656eb1d222a937dd34ddbc9b8a9945da855fdfc5a2561bc1`.
The eight active worlds form a complete cycle. Any recipe must retain all eight,
their selection order, original authors, notices and authored environment scripts.

All eight unchanged worlds now have inspected initial captures in OpenJKDF2 JK
multiplayer mode. The first seven used the prior pinned capture build. The eighth,
`oy'glah'th.jkl`, exposed an overstrict filename check in the capture launcher.
A private engine change allows apostrophes in the map basename while retaining
the other filename/path checks. The exact authored world name then rendered;
no archive member, referring level or source resource was renamed.

The independent seven-image review is pinned by SHA-256
`16b792688830be17c9e4a6ebc5c9f20887b6ba6301b9d666501e0a3a2df4005e`.
The eighth capture receipt is
`2393cec5dd0b804a2beebd3e23e302687f7edb300c6f745dac9664c0de8b9b1a`,
using private executable
`bea87272173739fdcd27e67914b0c166535affe50ecc0cef01892d265f4e29e2`
and source patch
`4abd20ab0a205b272666adfb28bb1e05a95abbb64225bcb5a128b45d2a900a52`
over engine commit `28ec799f1dab3f3954b4d395d19711c2204c43b1`.
All captures used isolated inputs, hidden rendering and null audio; original and
staged hashes stayed unchanged. They establish initial rendering only.

Three source dependency edges remain unresolved:

- Subway's sole active COG instance references absent `subway_start.cog`.
  The script is missing from both the original and all nine pinned owned baseline
  archives; its notice specifies no external dependency. A rendered stairwell
  does not establish what the missing startup script should have done.
- Hoodwink's sound table contains absent `00electrexplo3.wav`.
- Its authored sparks controller also declares that sound as an exposed default,
  but the sole placed instance explicitly supplies existing `00rumbleamb01.wav`.
  That is a source argument finding, not an audible-event test.

The pack adapter currently rejects these omissions in both its per-world and
merged-output checks. Any extension needs exact referrer/hash/argument gates
and negative controls at both stages. Preserve the original vector-token and
undeclared-symbol findings for behavior comparison. No MotS conversion, complete
playthrough, connected-peer or retail-engine result is claimed.

## Singleplayer: Imperial Siege On Derra IV

[Massassi entry 6](https://www.massassi.net/levels/files/6.shtml), rank 2, by
Ryan Bickhart. Original ZIP SHA-256:
`e7faa8fdb059224b006a6a1542d6b6583c638a3d925c5de25ce02ea4ee328932`.
The unchanged original episode loaded and rendered its initial water corridor in
OpenJKDF2 JK singleplayer mode. The image was inspected; the capture used the
original spawn and unchanged isolated inputs with no visible owned window
observed. The private original-runtime summary is pinned by
`ce68c91fa75a26a48f8b65c637dd791cd74155313adfde2529c367ffd1e9f00d`.

A fresh 1,503-name source walk confirmed seven missing names, with exact hashes
for every discovered referring resource. Some are active sound defaults or
explicit sector/COG arguments. The missing `14awscrn.mat` is used by world surface
10162; its native MotS namesake is a candidate for an explicit reviewed binding.
It must not inherit an unused-material exception. The separate original glass
material finding concerns an unused world slot and an untextured shard.

The SP adapter needs narrowly reviewed missing-edge and native-provider handling
before this episode can become a recipe. Preserve the entire authored objective,
actor, inventory, rank/timer, camera and ending behavior. The initial original-JK
capture does not prove every missing reference resolves, and no converted or
retail-engine result has been produced.

## Mods: Saber Battle X — JK v3.1

[Massassi entry 1887](https://www.massassi.net/levels/files/1887.shtml), rank 1,
by ShadowX. Original ZIP SHA-256:
`50950b0c3a83dda972cb72c1dc85df96ea2248cb2daf88f09fc0ed2dc5272b2e`.
The paired comparison also verified the author's separate
[native MotS v3.0](https://www.massassi.net/levels/files/1866.shtml), ZIP SHA-256
`909ad10a6bbe3954e0e7c20f5d55094a5fb68708716866102d439d8aac339908`.
The asset-free comparison receipt regenerated identically, SHA-256
`555e79c8a8fc46ed83924bf9f327b532c5a3a27eb72bb0aef0a5b5f4b1aa620c`.

The native edition is useful author-port evidence, but cannot replace JK v3.1:

- All 151 JK selectable models use a 20-node rig. The native SBX edition also
  uses 20-node rigs, and all 105 shared KEY files are identical. Reducing them
  to native Kyle's 18 nodes would discard authored animation structure.
- Native saber mappings supply concrete ordinal/descriptor examples, but bonus
  Force powers, rank grants, costs, controls and targeting differ between versions.
- JK v3.1's inventory-based controls, Sith Talisman and Force pickup overrides
  require cooperating controller ports. Native v3.0 lacks those exact features
  and omits thirteen JK selectable characters.
- The native roster itself has a duplicated row identifier; it is comparison
  evidence, not an already validated replacement table.

A dedicated gameplay adapter must preserve JK v3.1's complete authored scope,
including its 151 selections, player/saber/Force/control scripts and SP campaign
hooks. Its exact malformed metadata path and two unused material declarations
have bounded repair proposals; no completed conversion or runtime qualification
exists yet. Keep this mod optional and separate from level conversions.

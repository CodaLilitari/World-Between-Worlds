# SBX JK 3.1 and its native MotS relative

Review date: September 12, 2026. These are source findings, not a new converted
SBX release or a gameplay acceptance result.

[Saber Battle X - JK v3.1](https://www.massassi.net/levels/files/1887.shtml) and
[Saber Battle X - MotS 3.0](https://www.massassi.net/levels/files/1866.shtml) are
both credited to ShadowX on Massassi and in their original manuals. The JK
ranking retains its own entry. A native MotS relative is useful comparison
material; it does not establish that the two versions behave identically.

The original archives were downloaded privately and hash-pinned:

| Original | ZIP SHA-256 | Game archive SHA-256 |
| --- | --- | --- |
| JK 3.1 | `50950b0c3a83dda972cb72c1dc85df96ea2248cb2daf88f09fc0ed2dc5272b2e` | `ad3df02e7bb2270ffb7997b57158e3d39f85b0bbabfaec43447cfc5f3f176833` |
| MotS 3.0 | `909ad10a6bbe3954e0e7c20f5d55094a5fb68708716866102d439d8aac339908` | `49c2d136cffb6b6108ea29165d1245262713a7ff9ace472654768ee0e3e0c449` |

All four JK and three MotS Word-document main text bodies were recovered
passively using the Microsoft MS-DOC character-piece structure, with lengths
checked against their declared main-body character counts. [The asset-free
receipt](sbx-manual-evidence.json) preserves document/extractor/text hashes and
piece offsets. It contains no original manual body, illustration or game asset.
Document formatting and embedded graphics were not rendered.

The main manuals' feature, credit and permission sections establish several
conversion decisions:

- JK 3.1 restores JK Force Throw and Speed while giving Push and Saber Throw
  separate bonus-power controls for characters with Jedi potential. Those are
  changes from earlier JK SBX versions. MotS already has native Push and Saber
  Throw slots; the native mod also changes MotS-only powers such as Far Sight,
  Projection and Chain Lightning. Reusing one version's Force table blindly
  would lose those distinctions.
- JK 3.1 moves field light, goggles, saber color, damage toggle and motion-trail
  toggle into item-inventory navigation. Evasion/kick, saber activation, stance,
  Push and Saber Throw remain separately controlled. The correct number/order of
  controls must come from the actual resulting item table.
- Authored saber replacements differ from an ordinary map conversion. Earlier
  JK SBX places the Sith saber in the crossbow slot and the long saber in the
  concussion slot. Native MotS SBX explicitly adds the Sith saber to its native
  bowcaster slot. The eventual comparison must inspect each native descriptor,
  secondary weapon and authored controller; Ninja Kage's rules are not a general
  SBX translator.
- JK 3.1 deliberately changes surge/boost behavior and adds the Sith Talisman.
  Those authored changes must not be overwritten by an ordinary-level pickup
  compatibility substitution.
- The author records 16-bit mipmap fixes, saber transparency limitations, save/load
  caveats, damage-toggle timing and remote blocking/lag issues. These define
  focused tests; reading the manual does not establish they are fixed in WBW or
  in the current engine fork.

The manuals include substantial third-party credits. The guide **Saber Fighting
101** is credited to **MOTL_Robinton, edited by ShadowX**. The primary SBX author
credits Glowsaber's creators, skin/model contributors and other source work;
the unchanged originals must accompany local conversion outputs rather than
reducing those credits to a single new author name.

Both primary manuals contain an author-stated permission for improvements or
feature inclusion with due credit, alongside conditions for distributing the
original package and its documentation. This is a record of what those sources
say, not a blanket conclusion about all underlying third-party rights. WBW's
distribution boundary remains unchanged: publish original tooling and exact
recipes; keep original and converted game/mod assets private and require the
user's own reviewed inputs.

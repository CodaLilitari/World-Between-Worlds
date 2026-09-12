# Reviewed optional multiplayer skins

These are source-specific conversion reviews, separate from engine, rendered
appearance and second-player acceptance. Downloaded skins, sound files, retail
dependencies and converted archives stay private. The converter contains only
the exact source locks and transformation instructions.

## Agent Han Solo

[Agent Han Solo, Massassi entry 681](https://www.massassi.net/levels/files/681.shtml)
is rank 48 in the pinned JK Mods snapshot. The page credits Agent Han Solo; the
original readme also credits Al Macdonald for the model used as its starting
point and identifies the Star Wars trilogy as the source of its voice clips.
The external readme and the archive's embedded readme are preserved in the local
conversion. This recipe does not grant permission to redistribute those assets.

Recipe `mod-agent-han` creates an optional, exclusive `wbw-agent-han` startup
overlay. It appends one MP skin to the **55 native MotS model registrations**.
All existing rows are preserved byte for byte; only the declared model count is
increased and the new registration appended. Native UI strings are preserved,
their message count updated, and a new `HA_AGENTHAN` display label added. The
original JK table's retail registrations are not copied over MotS's list.

The two intentional native-path overrides are `misc/models.dat` and
`ui/jkstrings.uni`. No inventory, weapon, Force, player COG, JKL, KEY or PUP is
replaced. The character is selected explicitly in multiplayer character setup.
Native persona selection remains an independent engine behavior: the current
model-list parser reads the index/model/soundclass fields, so the appended
fourth registration field is not evidence of persona enforcement.

The authored model, its 20 MATs, eight custom WAVs and soundclass retain their
parent directories. Their leaf names receive `ha_` prefixes and exact counted
references follow those changes. This avoids existing native loader/cache
aliases as well as native full-path overlaps. The six additional WAVs actually
needed from an owned JK sound archive are copied under the same namespace and
parent directories; other sound references use 28 explicitly pinned native MotS
WAVs. Binary materials and sound payloads are unchanged. Model geometry and rest
transforms are unchanged; only declared material references are rewritten.

There are two narrowly recorded source repairs. The GOB directory contains an
embedded `\readme.txt` entry, normalized to `readme.txt` before strict parsing,
with the entire original and normalized archive hashes pinned. One source
soundclass row uses the bare token `tud` while neighboring rows use `tud.wav`;
that exact counted row is changed to the existing, namespaced WAV. Neither
repair substitutes a newly invented asset.

Static checks compare all 18 authored model node identities and hierarchy links
against the native MotS Kyle model. The 63 KEY files named by native `ky.pup`
have pinned hashes and node lists. Three native KEYs (`kyfall.key`, `kyidle1b.key`
and `kysbsabr.key`) refer to node 18 beyond the stock 18-node Kyle hierarchy as
well. This is an existing baseline discrepancy, not a claim that every native
animation index lies in range. Matching hierarchy does not establish animated
poses, weapon attachment, texture appearance or remote-player behavior.

Two fresh builds produced identical complete output trees. An independent
verification pass reverses the declared model/soundclass edits to recover the
exact original source bytes, checks the complete output path set and native
tables, and validates typed material/sound references. Eight synthetic tests
exercise descriptor and payload tampering, unexpected providers, wrong inputs,
skeleton mismatches, token boundaries, unresolved bare sound references and
stage-relative output paths with exact on-disk readme preservation.
[The asset-free identity receipt](skin-replay-evidence.json) records the inputs,
outputs and explicit limits. Runtime and visual results must be reported on the
exact archive tested; this source review alone does not certify them.

Implementation: `skinmods_catalog.py`, `skinmods_converter.py` and
`test_skinmods_converter.py` in the repository root. The existing exact material
recipes remain in their separate adapter. A generic skin filename or a shared
author is not enough to opt an unreviewed package into this recipe.

## Matrix Skin Pack: source omissions remain open

[Matrix Skin Pack, Massassi entry 545](https://www.massassi.net/levels/files/545.shtml)
is rank 39. Its page lists Matrix__Apoc; its original readme also names Elyas
Machera. All nine supplied models were inventoried, including the unregistered
Luke model, rather than silently choosing only the first registered skin.

The registered `agent.3do` references `bond_hand.mat`, `bond_handi.mat` and
`bondsole.mat`, absent from the original package and both pinned games. The
unregistered Luke model also references missing Luke-head, hand, neck and sole
materials. One other referenced material exists only in owned JK retail.
Existing generic hand textures are not assumed to preserve those authored UVs.
No silent replacement or omission waiver has been accepted, and this pack has
no selectable conversion recipe yet.

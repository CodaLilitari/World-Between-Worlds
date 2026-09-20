# Imperial Siege On Derra IV: prototype review

`sp-imperial-siege`, revision `wbw_v1`, converts Ryan Bickhart's
[Imperial Siege On Derra IV](https://www.massassi.net/levels/files/6.shtml),
rank 2 in the frozen JK singleplayer queue. It remains a prototype with partial
resource closure. The converted opening scene renders and advances in
OpenJKDF2's MotS singleplayer mode; a complete mission playthrough is pending.

## Exact source and ownership

The recipe accepts original ZIP SHA-256
`e7faa8fdb059224b006a6a1542d6b6583c638a3d925c5de25ce02ea4ee328932`,
containing `impsiege.gob` SHA-256
`e375ccafde6119c4fab4b5c8fb12b90d0e327b2499c4dec0eb2e2fe773d57ea1`.
The sole world is `jkl/impsiege.jkl`; its exact world, original notice, owned
retail archives and referring resources are pinned in the recipe export.
Every generated result retains the original `impsiege.txt` notice verbatim.

The established SP adapter isolates required JK resources and templates, maps
reviewed player, Force and pickup controllers to native MotS resources, and
expands scalar lighting to the target format. The authored green-key and
blue/yellow wrench scripts remain from JK: a native namesake is not sufficient
evidence of equivalent behavior. In particular, MotS's wrench scripts introduce
mission dialogue and differ in inventory handling. The recipe preserves 88
source COGs and uses 29 reviewed native COG bindings.

One counted edit maps the startup saber grant from JK ordinal 10 to MotS
descriptor 131. Original objectives, actors, camera, rank/timer sequence and
ending behavior remain apart from the explicit resource/template renames and
documented native controller bindings. The authored duplicate alarm symbol in
the TIE-bay controller remains. No SED-only change is required to reproduce this
conversion, and the stock JK campaign remains a separate future plan.

## Original missing resources remain explicit

Seven original file names are absent across 14 referring-resource edges and
19 exact occurrences. These include two materials and five sounds. Exact
source hashes, token counts and contexts gate every omission; an added referrer
or unexpected provider fails validation. Missing files are not filled merely
because a native MotS resource has the same name.

The glass slot is unused by world surfaces, and its shard has one untextured
face. The separate `14awscrn.mat` reference belongs to surface 10162, whose
geometry mode is `NONE`; its presence does not establish a visible broken
screen. Native MotS supplies that material, but four used palette indices differ.
No appearance-equivalent substitution has been established, so it stays absent
under an isolated name. Potentially active missing sound defaults and explicit
COG arguments also remain disclosed in the generated README.

A distinct rule handles the original AT-ST script's missing local pilot
template, `atstdriver2T`. Only its exact declaration becomes `bs_atstdriver2t`;
the random branch predicate, explosion, spawn call and damage logic stay intact.
Source inspection predicts a failed creation and no pilot for that missing
default in both OpenJKDF2 modes. This branch has not been exercised in either
mode, and the prediction is not a retail runtime result. Unknown missing
templates, additional symbols, new providers and altered call contexts are
rejected; the file-omission rules grant no general template exception.

The independent checker verifies 3,720 resolved typed literals representing
2,212 distinct names, plus the exact approved omissions. This is **partial
resource closure**: computed or extensionless references, cached or loose
resources, external startup overlays and unexecuted branches remain outside it.

## Reproduction and runtime evidence

Two fresh private builds under different hash seeds produced the same canonical
GOO: 42,840,839 bytes, SHA-256
`76deef65de73582d1673cb8de5725e8c4fce59de79f972882be2fa9607887b11`.
Each passed separate-process verification with the builder disabled. Eighteen
mutated real candidate payloads were rejected. The four earlier SP recipes
retain their complete payload, manifest and verifier results. The final README
extension changes no game payload and leaves existing recipes' README bytes
unchanged when they have no additional source caveats.

The same private engine executable rendered both the untouched original in JK
SP mode and the candidate in MotS SP mode. Its SHA-256 is
`658ff65ebb6ddfc8feab5bc2721ee02fcbda5a97bd38cd62f43e7d3b630a28e6`;
the exact build and separate engine-fork source are recorded in the
[runtime evidence](imperial-siege-evidence.json). Both images were inspected:
the dark stone water corridor, arch and textures are visible. The images differ
slightly; neither pixel identity nor a cause for that difference is claimed.

Both modes then passed separate 45-second passive observations with advancing
simulation, unchanged inputs and baselines, no resource diagnostics and no
visible owned game window. Those observations used null audio and no movement
or other input. A successful opening does not test the missing-resource
locations or establish equivalent fallback behavior.

Full traversal, objectives, doors and lifts, item/Force behavior, combat and the
missing-pilot branch, saves, ending, audible effects and retail-engine parity
remain open. The [integrated service and source validation](imperial-siege-validation.json)
separately records the delivered revision marker, scanner and platform checks.

## Distribution boundary

This repository supplies the recipe, code and evidence metadata. It contains no
original archive, game/mod resource or finished conversion. Users supply the
exact original and their own installed games; outputs and their original notice
stay local. The tool's license does not relicense the level or authorize
redistributing its converted assets.

# Steal the Bottle: source and conversion review

This asset-free review records the September 20, 2026 integration and fresh
structural replay of `sp-steal-the-bottle`, revision 1. It covers Massassi
singleplayer entry 1046, rank 40 in the frozen queue, by Cave_Demon. The entry
remains a prototype; runtime and gameplay evidence belong to separate checks.

## Exact inputs and transformation

The recipe pins the original `STB.zip` SHA-256
`b90bf34284815bf493206eca685ef62c6a496b5c83cbeb1ab7fed5cc1c7a1307`, embedded
`STB.gob` SHA-256
`e542de3dd0dd293253a0735f303e8477a07f99b96027ee10db3a35e59b9855b1`, its sole
world `jkl/jksp1.jkl`, the original notice, six owned archives, 11 retained
source COGs and 16 source identities selected for native COG bindings.

One counted compatibility edit changes the startup saber grant from JK ordinal
10 to MotS descriptor 131. Other inventory operands, rank 0, authored Force
amount, the initial fall-through into `timer:` and the separately scheduled
15-second timer remain unchanged. The established SP adapter namespaces source
resources and templates, expands scalar surface lighting, and adds the needed
native template/resource preload closure. No new converter algorithm is needed.

Authored officer AI, drunken guard instincts, their soundclass and four custom
sounds remain under isolated `bs_` names. The officer AI differs from retail
`iodefault.ai`, so selecting the native namesake would lose authored behavior.
Text processing normalizes line endings and rewrites literal resource names;
the custom WAV bytes remain exact. The guards' lack of firing instincts is
authored behavior.

The bottle remains scenery. The source ends the level on crossing surface 682
from sector 82 into sector 83. All 42 placed things and the declared 242 thing
capacity remain; three tanks with sector -1 stay disabled. Bundled but unused
frame-patrol and four-stop elevator scripts remain outside the dependency closure.
Episode progression and goal strings are preserved byte-for-byte.

## Fresh replay and resource ownership

Two fresh private stages built from the untouched original using Python 3.13.15
and `PYTHONHASHSEED=999` and `1` produced identical bytes for all four emitted
files. Both archives passed a separate-process preservation verification with
the builder disabled. The raw output is also byte-identical to the reviewed
September 12 private candidate.

| Output | Bytes | SHA-256 |
| --- | ---: | --- |
| `wbw-sp-steal-bottle.goo` | 18,707,820 | `3bb3513a06144ccbf0de2384d4a5fe20d52711c39dc90ed5a0a03e3db086ce9b` |
| `manifest.json` | 482,668 | `eb0916ce1c0a7479966972a7339336addafd5b1647727cc52074c833e3cbbaa5` |
| `Boooooring.txt` | 4,470 | `a9687e07bff1220d97dfbe61dfbcb6ad37dfae6dede6729aa8dd44491f3dd5e9` |
| `README.txt` | 368 | `053b802db2e14884eb495bbc97fbe03c8a53e5f20d4475ee250646b339107ca7` |

The 738-entry archive contains the episode, authored strings, transformed world
and 735 dependency resources: 9 authored, 553 JK resource and 173 JK sound
resources. Each dependency has source identity, transformation, output hash and
referrers in the private manifest. There are no copied native episode resources
and no full-path overlaps with the pinned native resource or sound archives.
The intended profile is one selected converted episode plus the owned native
MotS base, with no startup overlay. Loose files, caches and other installed
episodes were outside this structural replay's mount evidence.

The independent verifier checked 2,107 typed literal references representing
1,466 distinct names through the exact loader directory choices. Computed or
extensionless references and runtime branches remain outside that result.

## Regression and remaining checks

All 41 tests in `test_sp_converter` passed with the four explicit private source
fixtures selected; none were skipped. Nine new contract/payload tests cover the
versioned episode name, exact saber edit and timer order, authored AI and speech,
COG arguments, ending condition, disabled things, native ownership and notices.
Mutation controls reject changed saber/rank, an invented `Return`, native AI
substitution, an added firing instinct, changed environmental or patrol arguments,
an altered ending surface, reenabled tanks and a JK pickup override.

The existing test that forbids repository output now derives that directory from
`sp_converter.__file__`, so a private test copy cannot test the wrong directory.
The shared versioned-name contract produces
`wbw-sp-steal-bottle_wbw_v1.goo`, within the 31-byte episode-stem limit.

Engine checks must separately establish initial inventory and Force behavior,
guard appearance/puppet and speech, officer patrol/death/drop, sector thrust,
surface motion, the active door, final crossing, save/load and a legitimate
playthrough. The author's report of odd-looking guards is an original finding;
comparison with the original is needed before calling that a conversion defect.
No SED correction, runtime result or gameplay completion is established here.

The original notice contains unresolved permission-template alternatives and
conflicting distribution text. Preserve its exact bytes locally and infer no
blanket redistribution permission. Original downloads, converted archives,
manifests containing asset paths and private source reviews stay outside this
repository. This recipe does not alter the separate stock JK campaign plan.

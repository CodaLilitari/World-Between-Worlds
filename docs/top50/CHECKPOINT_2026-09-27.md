# September 27 development checkpoint

This is a source-development checkpoint after **0.2.0-rc6**, not a new release or
an expansion of the supported catalog. RC6 remains the portable Windows/Linux
download. The catalog remains **53 records, 52 selectable**. Within the frozen
150-entry Massassi queue, 40 entries have exact-input recipes, 39 are selectable,
and 110 still lack recipes. Chaos Eternal and Dark Emperor II remain unregistered.

## Chaos Eternal: guarded original omissions

[Chaos Eternal](https://www.massassi.net/levels/files/328.shtml), by freddub,
is a three-world cooperative campaign. The converter now has a narrowly gated
implementation for its authored Force-rank startup profile and exact missing
template defaults. All 120 cooperative-AI placements are checked against pinned
originals and their complete 41-argument vectors. The sole placed missing
projectile argument is restricted to Club's original zero-range melee actor.
No projectile or actor template is invented to fill these original absences.

An independent checker reconstructs the complete AI script and placed arguments
from the originals, rejects unexpected template providers and checks the required
startup controller separately. The Force profile preserves the authored rank
1/2/4 assignments and timer, while synchronizing MotS's maximum-mana field and
recomputing its rank cap during the native controller's pulse. These are source
and structural checks, not proof of Force use or cooperative combat in-game.

The exact, asset-free [candidate specification](candidates/chaos-eternal.json)
is retained for development replay. It is **not registered in the catalog**.
Each of its three isolated component builds passed the independent verifier;
the complete pack build still fails the strict resource-union check. The first
conflict is `misc/pup/br_royalgrd.pup`: a model name inside an original comment is
rewritten only when that model is part of the selected world's dependency graph.
The same issue affects `misc/snd/br_icrpt.snd` and `misc/snd/br_stlaser.snd`.
These are the only three conflicting paths in the reviewed component union.
Their active contents are identical across worlds; restoring the exact source
comments in a diagnostic comparison also makes each complete file identical.
The pack merger correctly refuses to choose one provider silently. That
diagnostic is not an implemented conversion fix.

Next: review all conflicting shared resources, make any reference-normalization
change reproducible and independently verifiable, rebuild the complete campaign
twice, then test MotS Force use/regeneration, AI, death/respawn, the authored
transitions and matching multiplayer peers. Do not bypass the union rejection.

## Dark Emperor II: source review, no converted build

[Dark Emperor II: The Last of the Jedi](https://www.massassi.net/levels/files/3.shtml),
by Darth Maul, requires both a campaign archive and a startup patch. The bounded
review covered all 13 world files and 11 episode entries, including the secret
route and detached development files. Both archives match the frozen originals.

The adapter must preserve the authored launcher and toggleable Force powers
while retaining native MotS inventory. Eight dark-Jedi disarm controllers need
explicit weapon-ordinal and inventory-descriptor mappings: merely changing the
saber number leaves the MotS bowcaster path unsafe. Force progression needs its
own design because MotS changes the rank and allocation rules.

Three missing resources create eight reviewed omission edges: an unused material
table entry and two character sounds. These are original-source findings; no
replacement assets were invented. The next step is a source-locked two-package
adapter, followed by independent verification and SP gameplay tests covering
weapons, powers, story branches, objectives, saves and transitions. No Dark
Emperor II conversion or game launch occurred in this checkpoint.

## Regression and distribution boundary

All five existing multiplayer packs were rebuilt against the previous source
commit `e63b72acbd6c7f5c7d6b8287b52101a4dd35eeae`. Their complete game payloads,
canonical manifests, generated instructions and original notices are identical.
Existing map revisions therefore remain unchanged. Converter source locks were
regenerated; the stale Ninja Kage evidence link now matches the CodaLilitari
documentation link.

Validation at this checkpoint:

| Check | Result and boundary |
| --- | --- |
| Windows and WSL Linux source suites | 411 passed on each; 59 skipped for absent optional private fixtures/platform conditions. These are development interpreter runs, not new portable binary builds. |
| Chaos tests with exact owned inputs | All 15 passed, including 13 fixture tests skipped by the asset-free suite. Altered source, rules, generated scripts/arguments and unexpected template providers are rejected. The independent omission checker also passes with the builder disabled. |
| UI source tests | 53 passed. |
| Archive/profile and queue maintainer tests | 22 passed. |
| Five-pack original-input replay | All existing complete payloads, manifests, instructions and notices unchanged. |
| New in-game testing | None in this checkpoint; prior runtime evidence retains its original scope. |

The original inputs, resource excerpts, private audit outputs and generated game
archives remain local. This checkpoint publishes original tooling, exact recipe
instructions, tests and findings. Existing approved documentation images remain
permitted. A conversion recipe grants no redistribution rights to the underlying
games or add-ons.

The wider [remaining-work list](../releases/REMAINING_WORK_2026-09-20.md) still
applies. The stock JK campaign remains a separate future plan preserving both
authored story routes with neutral MotS Force powers. Work is paused at this
checkpoint after the requested GitHub, GitLab and portfolio updates.

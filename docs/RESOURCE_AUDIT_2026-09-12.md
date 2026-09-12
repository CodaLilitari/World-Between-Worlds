# WBW resource audit — September 12, 2026

The current recipe source rebuilt all **27 catalog entries** privately: 26 levels
and the separately selected Ninja Kage 7.0 prototype. All passed the existing
independent structural verifier. No unexpected native gameplay override paths
were found in the 26 declared level profiles, and no differing game-resource
bytes were found between a level episode and its own required startup overlay.
These are structural and archive comparisons, not new gameplay or two-client
parity tests.

## Decision

Keep each level's needed resources in its own episode archive, with its reviewed
internal directories and references. Andrei clarified that the storage cost is
trivial; a shared library would require additional reference rewriting for little
benefit. No shared `z_jkdf2` archive or broad renaming was introduced.

Matching basenames do not establish archive collisions. The audit uses the
complete normalized internal path and records whether providers can coexist in
the same declared launch profile. Different episode archives are not all mounted
together. Material/model resolver aliases and caches are a separate concern.

The reusable rules are in [RESOURCE_WORKFLOW.md](RESOURCE_WORKFLOW.md), enforced
as project working instructions by [AGENTS.md](../AGENTS.md). The local UI now
has distinct Levels and Mods navigation. Ninja remains explicitly selectable;
queueing/converting it neither launches it nor installs a startup override.

## Native MotS ownership

The native MotS concussion weapon controller is
`cog/weap_concrifle_m.cog`, registered by `misc/items.dat`. Ordinary converted
pickups use `cog/pow_concrifle_m.cog`; WBW does not import a JK firing controller
as the ordinary level default. Canyon's actual archive and template bindings
were checked. Source runtime selection is in `bridge.py:845–880`, dependency
resolution in `bridge.py:817–822,980–1005`, and independent reconstruction in
`verify_retail.py:423–565,622–646,743–763` at the RC4 baseline.

Intentional reviewed exceptions remain separate:

| Profile | Expected native gameplay/model override |
| --- | --- |
| Three stock CTF maps | `misc/items.dat` descriptor 81 name |
| Jawa Dwelling SE | `cog/weap_concrifle_m.cog`, two counted authored changes |
| Stargate | `cog/kyle_m.cog`, authored unarmed spawn behavior |
| Drazen Isle | `cog/kyle_m.cog` and `misc/items.dat`, treasure-map inventory behavior |
| Duel of the Fates SE | Eleven native player-model paths |
| Ninja Kage 7.0 | Separate gameplay mod with its own declared inventory, weapon, player, UI and asset changes; excluded from ordinary-level override approval |

Morpheus also preserves reviewed projectile-template changes. Force Boost and
Surge use the separately named, hash-pinned native-derived WBW compatibility
scripts. A controller with the right name alone is not proof that its bindings
or behavior are right; these distinctions remain in the recipe verifier.

The across-recipe inventory found **38 full-path different-byte overlaps** among
generic `br_` resources. That is a list of potential conflicts if those outputs
are combined, **not 38 active collisions**. An earlier basename-only count of 41
was corrected: three entries were in different internal directories (`sound/`
versus `voice/`) and do not qualify as full-path overlaps. Exact provider archive
hashes and member hashes are retained in the private audit inventory.

## Engine findings

Audited engine commit:
`5fa4644d03080fef69d7137eaa2c8f295c47bd63` in OpenJKDF2-MotS-Fixes.

- MotS mount discovery uses `.goo` (`src/engine_config.h:255`). The underlying
  container is shared with GOB, but a `.gob` filename is not discovered by these
  MotS mount paths. `z_` is not a portable priority rule: Windows enumeration is
  unsorted by the engine; POSIX uses alphabetical enumeration.
- Selecting an episode frees the previous episode mount (`src/Main/jkRes.c:82–114`).
  In archive-only lookup, `-path` precedes the selected episode, then mods/base
  resource archives. Loose-file behavior is different: the raw requested path
  is tried first, and later loose directories may supersede earlier archive
  matches (`jkRes.c:476–566`). This audit is not a scan of every user's loose files.
- Static inventory controllers bind before episode selection. COG/model/material
  caches can reuse earlier resources. Material loading tries `mat/<name>` then
  `3do/mat/<name>`; material/model cache insertion can shorten names. These typed
  resolver effects require separate observation, not a basename collision rule
  (`src/Main/jkHudInv.c:24–65,768–778`; `src/Cog/sithCog.c:619–671,1611–1641`;
  `src/World/sithMaterial.c:155–187`; `src/World/sithModel.c:89–125`).
- **Checksum mismatch rejection is compiled out** at `src/Dss/sithMulti.c:1159–1182`.
  An unequal checksum is logged, but the rejection packet/return are inside
  `#if 0`. A successful join is not evidence of matching gameplay data.
- World checksum coverage is limited to selected world/template/COG/persona
  data, not all archive contents. The compiled COG word count is passed as a byte
  count, another source concern (`src/World/sithWorld.c:642–675`;
  `src/Cog/sithCogParse.c:265–282`; `src/General/util.c:72–78`). Changing these
  legacy checksum semantics needs its own engine compatibility work and tests.
  No engine behavior was changed during this audit.

## SED and independent checks

SED package `0.4.0-mots.4-dev`, commit
`9de27d3d967752bfc0898603c2c8aa325f53ee04`, was checked against all **676** listed
package/artifact hashes. Its packaged agent independently extracted and validated
the RC4 Canyon JKL: **69 sectors, 644 surfaces, 66 things**, no structural issues
or preservation warnings. Original input hashes remained unchanged.

A pinned static snapshot resolved 134 visual resources and reported four
model-less ghost omissions. The camera was obstructed by the statically rendered
player model, so it is diagnostic evidence only, not a publicity or gameplay
comparison image. SED's basename fallback does not establish engine resolution;
its parser and snapshot do not run COGs or multiplayer.

No editor correction was needed. The workflow now requires any future SED edit
to be translated into an exact WBW transformation, rebuilt from untouched
originals, compared semantically and bytewise, and independently checked before
the affected recipe revision can ship.

## Remaining findings and claim limits

The second independent process replay exposed a metadata reproducibility defect:
Caesar's and JHS's known-omission entries came from unordered set iteration.
All 27 primary game archives matched, but four report/receipt files differed
only in ordering. Because existing-result reuse compares every generated file,
that could reject a valid previous conversion. The audit fix orders the report
traversal in `bridge.py`; it does not change game-resource bytes or authored
behavior. Exact source locks are regenerated when this converter source changes.
See the final validation record below for the completed replay checks.

1. **Duel of the Fates' startup overlay is broader than the player-model need.**
   Its matching episode shares 792 identical game-resource paths with it. This
   creates no differing-byte conflict inside its intended profile, but reusing
   the overlay with unrelated episodes can expose authored generic paths.
   Keep its explicit isolated launch instructions. Narrowing it needs a separate
   dependency and runtime check plus a recipe revision; no trim was guessed here.
2. The current literal dependency closure includes preload/template declarations
   and conservative native roots. It does not prove runtime reachability or every
   computed COG reference. The fresh manifest union contains 2,545 distinct owned
   JK retail source identities, 1,594 used only by custom-map closures. These
   explain why stock-only extraction is insufficient; they are not a proposal
   to copy all those resources into a shared pack.
3. `runtime_source_sha256` and `runtime_cog_exception_reasons` metadata are not
   independently enforced fields, although the enclosing original archives are
   hash-pinned and the actual generated edits are independently reconstructed.
   Future override-policy enforcement should bind expected provider/path/hash
   tuples explicitly, not treat descriptive metadata as an executable gate.
4. No new door/elevator traversal, complete pickup behavior, same-process map
   transition or two-peer tests were performed on these fresh outputs. Existing
   older runtime receipts retain their own exact scope; this audit does not
   upgrade them to complete library-wide compatibility.

Lily's requested technical review supported self-contained episodes and explicit
startup profiles. Adopted recommendations include testing with only declared
dependencies, predicting resource providers at each load stage, negative controls
for normalization/mismatched inputs, and comparing clean restarts with episode
switching. Her review treated the supplied engine facts as premises; it is
architectural feedback, not independent engine or runtime verification.

## Final validation record

- Existing Python suite: **280 run, 278 passed, two expected skips** (Windows
  symlink privilege and base-interpreter virtual-environment ancestry). The
  owned-input Ninja test was included.
- Archive auditor: **13 synthetic regressions passed**, plus an independent
  two-profile control distinguishing active, isolated-episode and isolated-startup
  overlaps. The native-resource plus RC4 Canyon archive comparison completed
  with no full-path review findings in that explicit archive scope.
- UI: **49 tests passed**. Actual local browser checks showed 26 entries in
  Levels and only Ninja in Mods; explicit queueing, switching sections and
  clearing the queue neither converted nor loaded anything. No native picker was
  opened, and the private temporary UI server was stopped afterward.
- Deterministic-report fix: Caesar's and JHS passed separate-process service
  tests with `PYTHONHASHSEED=1,2,3`. Seed 2 reused both existing same-parent
  results; seed 3 rebuilt to a fresh parent and matched all **10 generated files**,
  including reports and receipts. Pre-fix failed replay evidence is retained.
- The complete post-fix service run verified **all 27 recipes**. All **34 generated
  archives** have byte-identical non-marker resources and identical canonical
  game payloads before/after the fix. Only the inert `wbw/recipe.json` records
  changed to bind the updated source hashes; all map/mod revision numbers remain 1.
- Recipe locks were regenerated from the changed source; map recipe revisions
  stay at 1 because no gameplay/resource transformation changed. The source lock
  and tracking metadata reflect the new source hashes.
- The archive regression step is wired into the Windows/Linux release workflow
  and its identical source-package template. It was exercised locally; no remote
  workflow run, binary release or publication is claimed by this audit.

## Reusable archive audit

`tools/archive_audit.py` is a maintainer tool in the source checkout. It accepts
explicit native, episode and startup archives, emits paths/sizes/SHA-256s, and
distinguishes active from isolated profile overlaps. It reads no directories
automatically, modifies no inputs and outputs no extracted game payloads.
It does not model loose files, loader aliases/caches, actual mount precedence,
dependency closure or gameplay. Known valid WBW tracking metadata is reported
separately from game-resource overlaps.

```sh
python -B tools/archive_audit.py --native /owned/MotS/resource/JKMRES.GOO --episode /local/bridge-canyon_wbw_v1.goo --output /new/canyon-audit.json
python -B -m unittest discover -s tools -p "test_archive_audit.py"
node --test ui/test_ui.mjs
```

For multiple profiles, `--plan` accepts a JSON `archives` list of `path`, `role`
(`native`, `episode`, `startup`) and optional `profile`. One episode per profile;
native archives apply globally. A startup with no profile applies to every listed
episode, so use profile names for map-specific overlays. Repeated `--episode`
flags mean separate episode profiles, not a merged level set. Exit 0 means no
unresolved archive findings in the modeled scope; 1 requests review; 2 means an
invalid/incomplete audit. None is a runtime compatibility certificate.

Private evidence includes `fresh-audit-inputs.json`, `fresh-audit-results.json`,
`fresh-output-inventory.json`, `fresh-profile-cohorts.json`, the three specialist
reports and `sed-evidence/`. No game/mod assets, generated GOOs or private input
paths are included in this repository report. The app packaging allowlist is
unchanged; updated recipe source locks bind the deterministic-report fix.

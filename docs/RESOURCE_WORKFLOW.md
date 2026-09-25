# Resource ownership and reproducible recipe review

Status: project workflow adopted September 12, 2026. Applies to new recipes,
resource/controller changes, archive layout, startup overlays and release claims.
The current baseline is RC4, commit `2bbca928dd3b1c5999d09be1198997d85336cdb6`;
the engine audit baseline is `5fa4644d03080fef69d7137eaa2c8f295c47bd63`.
Recheck relevant source when either changes. This document specifies review
requirements; it is not a claim that every historical recipe meets every gate.

## Product and distribution boundary

WBW distributes instructions and original tooling. Users supply owned JK/MotS
archives and the reviewed original custom downloads. All extracted resources,
converted levels/mods and runtime evidence containing assets stay local. Approved
documentation screenshots and our original UI artwork are separate permissions.
Do not bundle assets merely because a dependency scan found them. Original
authors retain their credits and terms; a recipe is not a redistribution license.

Levels and Mods are separate navigation sections. Multiple explicit conversion
selections create separate results, not a combined runtime profile. Ninja Kage
7.0 is an optional gameplay-mod conversion, never an automatic level dependency.

## Ownership decisions

Record each output path's source archive hash, source path/hash, transformation,
output hash, reason it is needed, and intended scope. Classify it as follows:

| Resource role | Normal treatment | Required evidence |
| --- | --- | --- |
| Native MotS weapon, pickup, inventory or player binding | Reference the compatible native binding without copying a JK replacement | Actual native script/template/bin behavior; filename similarity alone is insufficient |
| Reviewed compatibility adaptation, such as Force pickups | Separately named native-derived controller with exact counted edits | Source hash, edit count, references, behavior and regression checks |
| JK retail dependency | Extract only the selected recipe's dependency closure from owned inputs | Root reference, transitive dependency chain, source identity, rewritten reference map |
| Author's map resource or environment COG | Preserve authored behavior; namespace references and apply only reviewed compatibility edits | Exact original revision, ownership and deliberate differences from retail |
| Intentional native-path override | Use the narrowest proven scope; a startup overlay only when binding/cache timing requires it | Explicit path, original native hash, replacement hash, reason, load stage, compatibility restrictions |
| Gameplay mod | Explicitly selected separate mod package | Its own inventory/skin/controller scope, dependencies and tested map/profile combinations |
| Reviewed missing original resource | Preserve only an exact documented omission waiver | Original missing reference and impact; no invented replacement or silent waiver |

Do not globally replace every COG with its MotS namesake. Doors, elevators,
traps, custom weapons and other authored behavior need semantic review. Ordinary
concussion pickups should bind MotS `pow_concrifle_m.cog` and its existing
`weap_concrifle_m.cog` inventory controller. Existing authored exceptions (for
example Jawa Dwelling's rapid-fire variant) require their declared overlay.

## Mount and collision audit

1. Pin the engine commit/build hash and launch mode. Test OpenJKDF2 in **MotS
   multiplayer** mode when that is the recipe's target.
2. Write the intended launch profile: one selected episode, the exact startup
   overlay if required, native resource archives, mounted mods, and loose files.
   Inventory case-normalized full virtual paths, not just basenames. Record
   archive order when it is controlled; flag unordered competing providers.
   Preserve original spelling in provenance and reject duplicate/ambiguous
   normalized entries. Predict the provider at each relevant loading phase;
   compare those predictions with engine observations when making runtime claims.
3. Check native-path overlaps, distinguishing identical redundant copies from
   differing replacements. An exact declared exception is reviewable; an
   unexpected replacement is a failed release gate. Do not rely on a broad
   `kind=mod` label to approve arbitrary overrides.
4. Compare paths among files that can be mounted at the same time. Also report
   latent conflicts if users combine outputs, clearly separated from conflicts
   in the intended profile. Two files in different episode archives do not by
   themselves establish an active collision.
5. Check pre-episode static inventory/COG binding and cached resource behavior.
   Inspect loose files explicitly: their lookup behavior can differ from archive
   precedence. Archive-only inventories do not certify the whole installation.
   Separately audit typed resolver/cache aliases: the audited material loader
   probes `mat/<name>` then `3do/mat/<name>`, and material/model insertion can
   store basenames. Such a cache or fallback interaction requires its own source
   and runtime evidence; it is not an archive full-path collision and does not
   make all matching basenames interchangeable.
6. Use `tools/archive_audit.py` for reproducible archive-only inventories and
   overlap reports. Its synthetic regression suite is included in the repository
   release workflow on Windows and Linux. It reads explicit files only and does not convert, install,
   launch or prove dependency closure. Record uninspected loose files as a limit.
7. Keep one selected episode and its matching required startup profile active.
   Do not place converted episodes in the global resource/mod directory or
   combine unrelated overlays. Restart when changing startup profiles so old
   static resources do not remain bound. This operational rule supplements the
   ownership audit; it cannot repair a broken conversion.

At the audited engine baseline, MotS directory mounts use `.goo`. `z_` is not an
ordering contract. Multiplayer checksum-mismatch rejection is compiled out;
successful joining is not a parity check. Even an enabled world checksum is
not a full hash of every asset or script source byte. Maintain independent
per-resource and launch-profile fingerprints.

## Shared-library decision

Current decision: retain self-contained selected episode archives and explicit
per-recipe startup overlays. Do not generate a global `z_jkdf2.gob` as a shortcut.
Current generic `br_` names contain different authored bytes between maps.
Andrei clarified that storage is a trivial cost here: merging or relocating
resources would require rewriting their referring levels, with little benefit.
Preserve the current internal directory structure and reviewed references. A
matching basename is not a collision; compare full paths and active scopes.

The following is a contingency only if a future request revives the library
idea, not a planned implementation or an audit prerequisite:

- Compute the union of **transitively needed owned JK retail sources** across
  reviewed level recipes, including retail resources used only by custom maps.
  Exclude authored replacements, mod assets, unrelated retail files and assets
  made unnecessary by native MotS substitutions. Keep dependency-chain evidence
  for every member. A source manifest union is only a candidate, not proof of
  the minimal final runtime closure.
- Deduplicate by source identity and final transformed bytes, not filename.
  Use a library namespace, preserve the engine's expected resource directories,
  and rewrite every relevant reference exactly. Audit filename length, case,
  dynamic strings, COG symbols, templates, models, puppets and soundclasses.
- Pin immutable library revision/content hash in each dependent map's metadata
  and instructions. Recipe updates must identify changed library dependencies.
  Existing maps keep their pinned library until explicitly updated.
- Test missing, wrong, duplicate and mixed library versions; stale loose files;
  authored overrides; mod isolation; load order; same-process map transitions;
  and two-client profile equality. Do not call a shared library safer merely
  because it is smaller or there is one copy of each basename.

## CTF recipe gate (stock and custom)

Review the actual episode TYPE and original controllers; a title or filename
alone does not establish CTF. Register reviewed CTF recipes with the `ctf`
gameplay tag so the picker, cards, queue, Details and result instructions show
the additional mod requirement for either stock or custom content. Preserve an
explicit CTF episode title visible in the native MotS host list.

Pin the exact required startup mod and install/launch instructions. Use
`bridge-ctf-ui` only after proving that the stock controller/inventory contract
applies; never attach it automatically to an unrelated custom CTF system.
For a different system, record its reviewed instructions as `ctf_instructions`
in the catalog row and ensure its converter generates or requires the stated
dependency. Do not enable an entry before that dependency is implemented.
Current community and pack intake rejects TYPE 8 until a reviewed CTF conversion
path is added; no custom CTF recipe is released by this UI change.

Test the generated level plus startup mod, including the native menu label and
mode selection, active red/gold flags and HUD bindings. Menu/host observations
are separate from flag pickup, return, capture, scoring and peer tests. Preserve
authored surface extra light and scalar intensities while expanding JK corner
lighting to MotS's on-disk interleaved A/R/G/B layout. Historical ports are useful
comparisons, not substitutes for owned originals or permission to redistribute.

## SED corrections must replay through WBW

SED can inspect originals and converted JKLs, validate modeled structures,
round-trip in a private scratch directory, or create a pinned static preview.
For each use, record SED commit, package/executable hash, exact command or
structured plan, source/archive hashes, output hashes and the result/limitations.

If an editor change reveals the desired fix:

1. Preserve the original input and make the experiment in private scratch space.
2. Save the exact SED edit plan or operation sequence and semantic before/after
   differences. Inspect unknown/opaque sections, COG text, indices, geometry,
   lights, flags, templates and resource paths; modeled counts alone are not a
   complete preservation check.
3. Implement the same narrow transformation in WBW with source hash gates,
   counted preconditions, exact reference rewrites and meaningful regression
   checks. Do not ship a binary patch containing game assets or treat the
   manually exported result as the new original.
4. Rebuild twice from the untouched originals in fresh directories. Compare all
   generated game payloads and manifests, then run the independent verifier.
   Account explicitly for metadata changes and bump affected recipe revisions.
5. Use SED again as an independent consumer, then run engine checks appropriate
   to the change. SED's exact-name/unique-basename fallback can make a preview
   succeed despite an engine path-resolution error; check full paths separately.

No direct editor correction is complete for WBW until this replay succeeds.

## Evidence and release gate

Keep a local audit receipt with tool versions, input/source/output hashes,
selected recipe IDs/revisions, expected overrides, profile, commands and
independent results. Publish an asset-free summary with source references and
specific open findings; keep payload-bearing evidence local.

Required review dimensions are separate:

- Deterministic conversion and independent structural/ownership verification.
- Resource closure and reference resolution under the intended engine profile.
  Use a clean profile containing only declared dependencies; unrelated installed
  maps, overlays or a shared union must not accidentally fill a missing reference.
  Exercise dynamic/constructed references, conditional COG branches, spawned
  entities, MP-only behavior and death/respawn where applicable. A literal graph
  or a trace of one exercised path does not prove every branch is covered.
- Static appearance/lighting with reproducible camera and explicit resources.
- Doors, elevators, pickups/respawn, inventory slots and authored COG behavior.
- Multiplayer host **and second peer** with equal resource/profile fingerprints,
  plus targeted differing-input controls. Record actual synchronization results.
- Same-process map changes versus a clean restart, especially for startup mods.

Run only the checks relevant to the proposed claim, and list pending dimensions.
Host survival, SED validation, a screenshot, a recipe SHA or a successful join
cannot substitute for the other dimensions. Engine fixes belong in the engine
fork; converter fixes and exact recipes belong here. Review final changes and
asset exclusions before updating the public release or the Massassi submission.

For each review, answer explicitly: **what was changed; why each resource is
present; what can override it; which checks ran on these exact bytes; what remains
unverified; and can WBW rebuild the correction from the original inputs?**

## Findings to retain from the top-50 expansion

- Inspect the actual engine verb before rewriting a numeric COG operand. MotS's
  `SetInv`/`ChangeInv` path translates ordinary weapon ordinals below 11 to
  inventory descriptors; `GetCurWeapon` still returns an ordinal. A blanket
  replacement of every matching number can break an already compatible call.
  The JK saber ordinal 10 needs a specific port because MotS's saber ordinal is
  11 and its descriptor is 131.
- Native MotS `force_well` recalculates the rank-based maximum on each SP pulse,
  but caches it during startup in MP. An authored MP script that changes rank
  afterward needs its own reviewed initialization handling. Check the original
  startup/new-player ordering, subsequent timers and regeneration cadence. Do
  not repeatedly restart the controller when its cached maximum already matches.
- A skin overlay mounting successfully does not prove that skin was selected.
  Ordinary autostart defaults to Kyle. The isolated engine branch now has a
  tested explicit MPC selection path; require its recorded executable and check
  the actual loaded model/soundclass. Historical tests without that selection
  remain overlay-load results only; see the second top-50 checkpoint.
  Preserve native registrations and inspect actual skeleton, KEY and resource
  bindings independently; shared directory names do not certify animation.
- When SED reports geometry problems, compare the untouched original and the
  converted world with the same pinned SED version. Retained original findings
  are different from conversion regressions, and neither is a clean geometry
  validation pass. Any proposed repair must be a separate exact recipe operation.

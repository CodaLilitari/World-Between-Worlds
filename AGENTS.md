# World Between Worlds project instructions

WBW is a recipe-book converter, separate from the OpenJKDF2-MotS-Fixes engine
fork and from optional gameplay mods. Read [the resource and recipe review
workflow](docs/RESOURCE_WORKFLOW.md) before changing a converter, recipe,
dependency resolver, archive layout, startup package, or release claim. The
workflow records Andrei's September 12, 2026 requirements and the source audit;
current user instructions remain authoritative.

- Publish original tooling, recipes, notices and approved documentation images.
  Never commit retail assets, custom level/mod asset files, downloaded originals,
  or generated game archives/conversions. Keep private evidence outside this repo.
- Keep Levels and Mods separate. Ninja Kage is an explicitly selectable mod
  conversion; do not implicitly select, combine, install, or load it with a map.
- Prefer native MotS gameplay bindings for ordinary maps where behavior matches.
  Preserve authored level behavior with explicit, counted, hash-pinned edits.
  Declare every native-path override and its intended startup scope.
- Audit actual simultaneous mounts and loose files. Separate installed episodes
  are not all mounted together. Do not assume `z_` controls precedence or use a
  successful join as evidence of equal resources. MotS archive mounts use `.goo`.
- Retain self-contained episode outputs. Andrei clarified that storage cost is
  trivial and merging paths would require rewriting the referring levels.
  Do not move generic `br_` resources or authored overrides into a global pack.
  Any future shared pack must contain only a reviewed minimal dependency union,
  use isolated names, and pin an immutable revision and content hash.
- SED is an inspection/prototyping aid. Every editor correction must become an
  exact WBW operation reproducible from the original inputs before release.
  No hand-edited final archive or unrecorded editor fix may become a recipe input.
- Keep structural, resource, rendering, gameplay, multiplayer and retail-parity
  evidence separate. Unresolved checks are open findings, never implied passes.
- Follow existing per-recipe revision tracking whenever game payload bytes or
  required runtime dependencies change. UI/docs or report-order-only edits do
  not bump map revisions; regenerate source locks when converter sources change.

Maintainer tools and workflow documents under `tools/` and `docs/` are source
checkout aids, not automatically part of the self-updating end-user package.
Review the explicit packaging allowlist and old-bootstrap contract before
adding them to a release payload.

The active [Massassi expansion queue](docs/top50/README.md) covers exactly 50
entries in each of the JK multiplayer, singleplayer and mod categories. A
download or structural inventory is not a supported conversion. Keep its
ranked input pins, recipe state and test evidence distinct. The
[stock JK campaign](docs/STOCK_JK_CAMPAIGN_PLAN.md) is a separate future plan:
preserve both authored story routes with MotS-neutral Force powers on either
route; do not count it toward the 150 custom entries or enable it prematurely.

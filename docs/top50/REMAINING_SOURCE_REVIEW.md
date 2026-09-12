# Source review of the 118 remaining entries

September 12, 2026. The remaining 24 MP levels, 48 SP levels and 46 mods now have
individual passive source reviews. **No additional recipe is enabled by this
review.** At that snapshot, conversion coverage was 32 exact-input matches, of
which 31 were selectable, across the 150-entry queue. The three candidates below
subsequently gained prototypes, bringing coverage to 35 exact-input matches and
34 selectable entries. The 118-entry metadata remains the original review
snapshot; [the development checkpoint](DEVELOPMENT_CHECKPOINT.md) tracks progress.

[The per-entry metadata](remaining-source-review.json) preserves rank, source
identity, original hash, candidate adapter and concrete review gates. It is a
reviewed subset of the private reports, excluding original source excerpts,
downloaded files and game resources. Full dependency chains and original notice
evidence stay private and are linked by report hashes.

## Coverage and limits

| Category | Entries reviewed | What the passive pass inspected |
| --- | ---: | --- |
| MP levels | 24 | 56 active worlds, seven orphan worlds and 43 retained notice files; exact episode rows and typed literal dependency chains |
| SP levels | 48 | 103 archive-local active-world records, including alternative/patch packages whose launch roles still need review; episode graphs, authored COGs/AI and typed resource/template declarations |
| Mods | 46 | 24,846 raw archive or mapped loose-file entries; controller, registration, native-path and source-directory findings |

These are source observations, not runtime failures or new supported-map counts.
Literal scans may include unused declarations and cannot prove constructed
references, conditional behavior, cache interactions, loose-file precedence or
peer agreement. Reused basenames are not treated as equivalent resources.
The exact original notices remain separate from any permission to distribute
generated assets.

Three SP packages remain opaque to the installed passive container reader:
The New Empire, The New Empire Part 2 and Arrow Thieves: Chapter 1. The DBZ and
Ghostbusters mod installers also remain opaque in this pass. None of their
downloaded executables was run. Escape From Mera Himbgie's original `prisons.gob`
was recovered from its CAB without executing setup; a future recipe needs a
pinned, reproducible decompression operation.

## Next bounded implementation candidates

| Candidate | Required work before selection |
| --- | --- |
| [DBZ: TDIR Tournament Level Pack](https://www.massassi.net/levels/files/1814.shtml) | Preserve all three active worlds and repair the duplicated episode row ID with an exact source-pinned operation. Keep the pack adapter's general duplicate rejection. The author says this level pack can work without TDIR; do not force-load the mod. |
| [Imperial Pumping Station](https://www.massassi.net/levels/files/1366.shtml) | Review and pin its 46 remaining source COGs, retain its non-Jedi protagonist and goals, and investigate the author's opening-camera issue. `stopbrief`/`briefstop` and an undeclared camera variable are source findings, not established fixes. |
| [Anime Characters Skin Pack](https://www.massassi.net/levels/files/684.shtml) | Add an exact loader for its original loose-ZIP directory instructions, namespace the 266 authored assets, append 15 skins to native MotS registrations, and verify transitive dependencies and actual selected-skin behavior. Existing skin adapters do not currently accept this source. |

These three now have exact recipes, independent verification and repeat builds.
DBZ's three worlds passed separate MP host checks, Imperial passed a bounded SP
simulation check, and all 15 Anime skins passed actual MotS MP model/soundclass
selection checks. [The second implementation batch](WAVE2_CHECKPOINT.md) records
the evidence and remaining gameplay/appearance/peer limits. The table preserves
the implementation requirements identified at the original review.

## Findings that affect implementation

- **The Death Star** has mixed JK-format geometry and MotS resource bindings.
  Of 116 distinct literal names unresolved against its selected JK profile,
  94 have exact native MotS candidates and 22 remain absent. A generic JK
  controller replacement would skip the required per-binding review.
- **Chaos Eternal** is a three-world cooperative mission. **Galactic Locations**
  has eleven active worlds, including bot variants. Their AI, objectives and
  transitions require more than a deathmatch pack conversion.
- **SS3 Death Match Levels** explicitly requires SS3 beta 9.0. A future recipe
  needs a separately selected, exact mod prerequisite; unrelated mods cannot
  silently supply its missing resources.
- **The Valley Battle** stores its active world as `jkl/valleybattle.gob` even
  though its contents are world text. The source is present; a reviewed path and
  episode-reference alias is needed.
- **Anime Characters** and **Medival Weapons** are loose distributions. Their
  original instructions place materials in different directories, `3do/mat/`
  and `mat/`. A generic flattening step would lose that distinction.
- Fourteen remaining mods have source archive-directory findings. Duplicate
  normalized entries need index/hash evidence and an exact resolution; the
  production archive reader must not silently adopt a global last-entry rule.
- **Advanced Grapple** and **Saber Blocking Plus** contain apparent undeclared
  variables; the latter also assigns a vector to a scalar. These are original
  script-review findings. **Sith Sabers S.E.** adds JK weapon ordinal 11, which
  needs explicit integration with MotS's existing saber slot.

The [resource workflow](../RESOURCE_WORKFLOW.md) governs each resulting change.
Any editor-assisted correction must replay through WBW from the untouched
originals. The separate stock campaign remains planning-only: both authored
stories, neutral MotS Force powers on either route.

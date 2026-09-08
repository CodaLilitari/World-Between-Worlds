# Ninja Kage 7.0 — MotS multiplayer prototype

World Between Worlds can build an **experimental local MotS conversion of ShadowX's Ninja Kage 7.0**. The recipe is still marked `prototype`. The corrected package has passed structural checks and real two-player MotS sessions, with bounded evidence for its weapons, handspring, kick and grappling-hook launch/detach. Live grapple attachment/pull, restored-Force allocation and visual fidelity remain open gates. Single-player campaigns and other MotS personalities are outside the reviewed scope.

The original package is a full startup mod: modeled Ninja To, shuriken, caltrops, kunai, grappling hook, jump/handspring, kick, custom Force scripts, skins, animations and sound. It contains no episode map geometry. Its `static.jkl` contains shared resource definitions and fifteen custom templates, so a map-surface lighting conversion is not applicable to this package itself.

## Original source and authorship

The primary source is [Massassi's Ninja Kage 7.0 listing](https://www.massassi.net/levels/files/1333.shtml), which identifies **ShadowX** and the **Jedi Knight Mod** category. Its [download page](https://www.massassi.net/levels/download/1333/) links to the [original `ninjakage_v7.zip`](https://www.massassi.net/media/levels/files/jkmod/ninjakage_v7.zip). The catalog dates the upload 7 January 2001; the included readme records creation on 25 December 2000.

| Original | Bytes | SHA256 |
|---|---:|---|
| `ninjakage_v7.zip` | 999,829 | `1d71863e564e75278eecd44244ef3a103692c49b4bf11fdbc2de591ccbf05764` |
| `Ninja Kage.gob` | 3,966,542 | `23bd8e18eae4df637a34ddf4f98ed3602c490de521e0cc147bf8e79bb9fe23af` |
| `Ninja Kage.txt` | 15,326 | `de4c8f16f3fe3b48f9b25f582f6760091fd9892e8bdf358145b698b2a270735c` |

The GOB has 311 entries, including 31 original COG scripts. The builder requires these exact source versions. One historical GOB directory entry begins with a root separator; only that complete hash-pinned GOB receives a narrowly defined virtual-name normalization in memory. General archive path checks remain strict.

ShadowX and the contributors named in the original readme retain their authorship. The readme permits credited modification/reuse while identifying borrowed components and their exceptions; this tool does not relicense their work. Generated local output retains the exact original readme when built from the ZIP. Converter source and source releases contain no original mod payloads, retail assets, complete original scripts, or original readme reproduction.

The converter and compatibility work are by Andrei Pemberton with Coda Lilitari. This is a human-facing credit, not an invented account or additional original-mod author.

The recovered package is explicitly a JK release. Contemporary comments on its original listing request a MotS version; current primary-source searches did not locate an authored MotS edition. That does not establish that no private or unindexed conversion ever existed.

## What the recipe preserves and changes

The recipe retains all 23 applicable original multiplayer COGs and the authored assets. Seven original campaign/actor scripts are excluded. The original JK player script is replaced by a native MotS player script with thirteen exact, counted adaptations that preserve Ninja Kage's kit, fall immunity, wall-stick behavior, transparent green blade materials, shields, goggles and weapon selection. Native MotS networking, cleanup, timers, extra weapon handling and personality parameters remain.

These distinctions are deliberate:

- Weapon inventory IDs and selection ordinals are different in MotS. The Ninja To is inventory **131**, but `GetCurWeapon` reports ordinal **11**. Dynamic weapon selection explicitly converts ordinals with `GetWeaponBin`.
- The five authored weapon COGs and both authored thermal pickup COGs use the corresponding native MotS `_m` entry names. Their original behavior remains, subject to exact slot corrections.
- Kunai/bin **124** keeps the authored maximum **200**, allowing the original starting grant of **50**. Native MotS's maximum of 30 would clamp that grant.
- Authored Force Push remains bin **27**, under the distinct `nk_force_push.cog` name. Native MotS Force Push/bin **38** and concussion rifle/bin **129** remain unchanged. No extra concussion weapon is added.
- Original Throw/bin **30**, Lightning/bin **32**, Hook/bin **116**, Jump/bin **117**, Kick/bin **118**, and the network helper/bin **119** are registered without renumbering native MotS inventory.
- All 29 authored models receive an explicit Jedi-personality column. The first reviewed setup is a fresh Jedi multiplayer character using the authored green saber materials.
- Authored string changes are merged into native MotS string tables. Native personality/UI keys remain, and the 25 hotkey labels follow the actual inventory enumeration.
- Both variants include the exact original JK Throw and Lightning HUD icons in 8-bit and 16-bit form. The verifier follows every active inventory descriptor's runtime-derived icon name, checks both depths and validates the required fallback/bracket bitmaps.
- The complete typed resource dependency set is preloaded in `static.jkl`. Native preload rows keep their order and indices; computed capacities accommodate the additional resources. The fifteen authored templates retain their parent order and fields. Their global `+sspks_blood` definition intentionally changes native map blood effects as part of the original full-mod behavior.

Native MotS damage multipliers, Force Defense, carbonite, flash, bubble effects, velocity/mana parameters and saber-only restrictions remain. These are MotS adaptation semantics; the tool does not claim identical JK-engine behavior.

## Local build and launch

Use the original Ninja Kage ZIP and clean, supported copies of both JK and MotS. The six normal pinned retail archives are sufficient; Ninja Kage does not require the JK single-player archive. Generated assets must remain outside the converter source directory.

The source API is available for explicit prototype evaluation:

```python
from pathlib import Path
import bridge
import ninja_converter

archives = bridge.pinned_archives(
    jk_root=Path(r"C:\Games\Jedi Knight"),
    mots_root=Path(r"C:\Games\Mysteries of the Sith"),
)
result = ninja_converter.build_to_directory(
    archives,
    Path(r"C:\Downloads\ninjakage_v7.zip"),
    Path(r"C:\GameConversions\NinjaKagePrototype"),
)
print(result["verification"])
```

Install the generated **entire `blackwing-ninja-kage` folder** beside the runtime's `resource/` and `episode/` folders. That stable internal folder name remains for recipe replay even though the converter is now called World Between Worlds. Launch the engine with:

```text
-motsCompat -path blackwing-ninja-kage
```

Select Multiplayer and use a fresh Jedi character with the authored model and green saber choice. Every peer must use the same startup mod. Restart without this `-path` before using another mod. Do not combine it with SBX, Manowars, or another startup/inventory overlay.

The Controls menu receives the correct labels. Its relevant action order is:

| Action | Inventory bin | Control function |
|---|---:|---|
| Authored Force Push | 27 | `ACTIVATE6` |
| Force Throw | 30 | `ACTIVATE9` |
| Direct Force Lightning | 32 | `ACTIVATE11` |
| Bacta | 40 | `ACTIVATE19` |
| IR Goggles | 41 | `ACTIVATE20` |
| Field Light | 42 | `ACTIVATE21` |
| Grappling Hook | 116 | `ACTIVATE22` |
| Jump/Handspring | 117 | `ACTIVATE23` |
| Kick | 118 | `ACTIVATE24` |

Native Restore Defaults assumes the normal twenty-action inventory. For this mod, explicitly bind **F2 to Field Light, F3 to IR Goggles, and F4 to Bacta**, then choose keys for the three new movement/attack actions. Existing user profiles are not silently rewritten.

Ordinary headless `-autostart -mp` uses the engine's dummy character path and does not load a Jedi MPC/PER merely because those files exist. A test must use the normal character-loading host/join flow before claiming a Jedi multiplayer result. Private test adapters are separate from the distributable converter and engine.

## Optional restored-Force allocation variant

The default prototype has Throw/Lightning descriptors and control labels, but ordinary native MotS allocation and power cycling omit bins 30 and 32. It therefore does **not** claim that those powers are selectable through the native allocation screen.

An explicit experimental build option, `force_ui=True`, supplies the resource contract for the separately reviewed restored-Force engine extension:

```python
result = ninja_converter.build_to_directory(
    archives, original_zip, fresh_output_directory, force_ui=True,
)
```

This variant changes the two internal descriptor names to `f_thr_r` and `f_lig_r`, adds local allocation-icon derivatives, and supplies the allocation hint strings. The original JK HUD icons are included in both variants. The original Ninja Kage Force COGs remain unchanged. No Force levels, extra stars or artificial starting powers are granted.

The engine extension implements allocation/category/refund behavior and power cycling for those opt-in descriptors. The current reviewed rebase has source patch SHA256 `c795ae75b86d9316cec91144f7f35c6689d11c579ca32c172f06afe946382cf4`; extracted native-function tests passed 947 assertions with undefined-behavior checks, and the complete Windows build passed. The variant requires an engine with that extension; putting the resource files into an ordinary engine does not add the missing UI logic.

The current v4 allocation icons preserve the original three 28×28 image states and duplicate the normal state as the fourth disabled-state placeholder required by MotS. Palette remapping and a proper disabled appearance are under review. Rendered layout, allocation, refunds, saves/reloads and power activation still require runtime/UI checks. A successful zero-allocation multiplayer session establishes descriptor compatibility, without establishing these UI or restored-power behaviors.

## Validation and remaining limits

The corrected default v3 produces **1,016 resources / 19,703,558 bytes**, SHA256 `50de33501041102606b5a6f879d61195d55c11898014e22e4d3148fbb133c6df`. The corrected optional Force v4 produces **1,018 resources / 19,710,411 bytes**, SHA256 `4fafc5c6cf194275cd36df496308c423a949cbb4ecfea66b90b6505ddfdc3462`. Each was assembled twice with identical bytes. These hashes describe these specific development artifacts; later recipe revisions require new verification.

The current Ninja test gate passed **43 tests**, including configured owned-asset integration and mutation tests. The independent verifier checks original assets, exact COG edits and untouched text, native inventory invariants, controls, models, static template/preload structure, imported resource hashes, dependency reachability, HUD bitmap closure and manifest contents. Structural verification alone does not certify parser execution or gameplay.

The initial default artifact failed real startup because it omitted four Throw/Lightning HUD icons. The native engine attempted to convert a missing bitmap. That failure was retained and the asset dependency repaired; it is not counted as a passing test. The corrected recipe also follows the native string parser's plain quote delimiters so the literal backslash key row is counted correctly and the final authored string is read. These corrections change only the four HUD resources and string table in the default variant, and only the string table in the prior optional variant.

Private tests used fresh Jedi MPC/PER characters, ordinary engine host/join initialization, two distinct connected peers, and input delivered through the loaded control mappings. The corrected default passed a **75.094-second idle session** and a **75.064-second action session**. The optional Force variant passed a **75.046-second idle session** with zero allocated powers. All 66 descriptor-bound COGs were loaded and validated during the initialized samples; no parser failure or crash was found in those runs, game clocks advanced, and the 48 clean baseline files retained their hashes.

The action session established the following bounded effects:

- Shuriken, caltrop and kunai selection/firing produced the corresponding live projectiles and consumed their authored ammunition. Both peers observed the weapon helper's network triggers.
- The stationary handspring produced its authored backward impulse; kick produced a transient punch projectile and returned its activation state to idle. These observations do not establish hit damage or every transient projectile.
- The standing Ninja To strike changed its authored attack state and saber flags. Rendered animation and collision damage were not measured.
- Grappling-hook launch and explicit detach changed the expected COG and inventory states. A live anchor and pull remain **unverified**. Follow-up normal aiming exposed a private observer defect: it treated the engine's highest occupied thing index as a count and omitted that final slot. The earlier apparent hook disappearance therefore does not establish destruction or invalid-handle pulling, and no gameplay-script repair is justified by that observation. The observer is being corrected for a new live-anchor test.

Four exact original missing-resource edges remain: `arimasen.wav` in the sword and Force Speed scripts, `shthrow.key` in the shuriken script, and `starm.3do` in an unused SP limb template. A separate pinned native script declares an absent `EC.3do` template but never uses that symbol; that unused declaration is retained. No replacement sound, animation, model or template is invented.

The original caltrop script contains assignment expressions where comparisons appear intended, and Force Pull has an inherited CTF-condition parenthesis issue. These are preserved and separately documented rather than silently attributed to the converter or declared parser failures.

Live grappling attachment/pull, restored-Force allocation and activation, combat damage, full remote visual replication, rendered appearance, sound, animation and per-map behavior remain runtime gates. A completed input schedule alone is not evidence that an ability worked. Single-player compatibility and other personalities are unverified.

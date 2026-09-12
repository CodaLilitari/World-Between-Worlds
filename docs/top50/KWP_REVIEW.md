# Killer's Weapons Pack: compatibility review in progress

Status, September 12, 2026: **incomplete, unselectable maintainer review**.
This is a plan and a reproducible weapon-controller edit audit, not a runnable
MotS conversion or a promise of gameplay compatibility.

The [Massassi original](https://www.massassi.net/levels/files/1060.shtml) is
ranked second in the captured JK Mods list. Its page lists ID_Junkguy; its
unchanged original readme credits **ID_Junkguy and ID_Matt**, with additional
credits to HOTS_Btrek and Deluxe_Six. WBW must retain those distinctions and the
original readme locally. The readme already reports camera/zoom problems after
falling or respawning. It does not grant a new redistribution license for a
converted asset package.

## Exact source and partial replay

| Input | SHA-256 |
| --- | --- |
| Original `kwp.zip`, 372,161 bytes | `517d742fe9822364a72e6be1da323ad23117c422cb163259e14f9533a3296126` |
| `KWP.gob`, 1,359,011 bytes, 70 entries | `18673aea67a633ea890d900049204818646eab5b4fa2b67d7e23ca6b3a7a9adc` |
| Original `readme.txt`, 4,328 bytes | `2175721920d2fc8d5fa41db3742843902e1327cde665c6cb5245f8a016f60e16` |

The maintainer command below accepts only this exact ZIP and its exact members.
It writes hashes and counted operations. An optional private script export is
an incomplete review artifact; it is never a GOO, install or launch action.

```powershell
python tools/kwp_review.py C:\Private\kwp.zip --report C:\Private\kwp-review.json --export-scripts C:\Private\kwp-script-review
python -m unittest tools.test_kwp_review -v
```

[The pinned weapon plan](kwp-weapon-plan.json) records 41 counted operations
across all ten authored weapon controllers. Five synthetic checks cover
descriptor translation, numeric boundaries, unchanged ammo/damage values,
unchanged network ordinals and failed edit preconditions. This does not validate
the COG compiler, inventory assembly or gameplay. The tool is maintained outside
the end-user updater payload.

## Weapon ordinals are different from inventory descriptors

| JK weapon | Planned MotS descriptor |
| --- | ---: |
| Fists 1 | 121 |
| Bryar 2 | 122 |
| Stormtrooper rifle 3 | 123 |
| Thermal detonator 4 | 124 |
| Crossbow 5 | 135 |
| Repeater 6 | 126 |
| Rail detonator 7 | 127 |
| Sequencer charge 8 | 128 |
| Concussion rifle 9 | 129 |
| Saber 10 | 131 |

The native table must remain the base. KWP's own ten authored weapon controllers
are intentional optional mod replacements for those descriptors. The extra
MotS weapons and their native flags/order must remain. This weapon-pack exception
does not change the ordinary-level rule: ordinary concussion pickups use the
native MotS controller.

Engine source audited at `b1be98bd4f170b5384cb71b15443a274aac6a937` distinguishes
these values in `src/Cog/sithCogFunction.c:1330`, `:1350`, `:1403` and `:1423`,
and `src/Gameplay/sithInventory.c:286` and `:311`:

- `GetCurWeapon` and `AutoSelectWeapon` return weapon **ordinals** in MotS.
- `GetWeaponBin` resolves an ordinal to an inventory descriptor.
- Weapon-selection functions automatically translate only values below eleven.
  An auto-selected MotS saber/crossbow therefore needs explicit descriptor
  resolution before selection.
- KWP's six trigger helpers use IDs 20/21, 30, 40/41, 60/61, 70/71 and 90/91.
  Their corresponding native weapon ordinals stay 2, 3, 4, 6, 7 and 9. The plan
  leaves those network IDs and expressions unchanged. It separately changes the
  saber predicate to a descriptor comparison and crossbow ownership to 135.

## Helper and hotkey collision

The original table assigns helper scripts to bins 116–121 and the grapple to
122. Original helper bins 120/121 and grapple 122 collide with MotS's native
none/fists/Bryar descriptors. The proposed exclusive-profile mapping is
116–121 to **141–146**, and grapple 122 to **147**.

The pinned native `JKMRES.GOO` inventory has no descriptors at 141–147. A literal
search across COG/DAT members in the pinned MotS resource, sound and stock-MP
archives found no references to those seven numbers. The engine enum ends
native weapon descriptors at 140, defines its hotkey offset at 150, and permits
200 bins (`src/types_enums.h:1053`–`:1084`, `src/engine_config.h:202`). A source
search through the inventory, COG, world, GUI and engine code found occurrences
of 141–147 only in unrelated GUI geometry/parser tables/collision sizing.

These findings support the candidate allocation for one exclusive KWP profile;
they do not prove all dynamic arithmetic or another mod avoids those bins.
Inventory initialization, save/load and two-peer behavior still need runtime
checks. The original player breathing logic also uses helper bin 117's activated
state: any native-player port must preserve that specific coupling at 142 or
explicitly justify a change. Do not silently apply Ninja Kage's helper layout.

## Native player and inventory port still required

The original `cog/kyle.cog` is largely a JK player copy. Replacing MotS's player
with it would discard native personality initialization, weapon handling,
carbonite effects, ysalamiri behavior and other native logic. The planned port
starts with hash-pinned native `cog/kyle_m.cog` and applies only independently
reviewed KWP deltas.

Known authored deltas include a 200-shield/battery initialization, physical/fall
damage immunity, an underwater breathing state and periodic battery behavior.
Native MP initialization runs after basic initialization and can reset shields
and inventories again, so editing only the common initializer is insufficient.
Respawn, scope reset, death, water and personality tests must check the final
state. The source's orphan flight variables/calls need an explicit resolution.

The native inventory merge must preserve KWP's authored ammo minima/maxima,
thermal/sequencer capacities, default fists/Bryar/saber ownership and selected
item limits, while keeping native MotS controls and unrelated descriptors.
The original JK Force table is not an instruction to add or replace MotS Force
powers. This is a weapons-mod port; any separate Force restoration is outside
this candidate. Retain native UI strings and add/change only authored strings,
the mapped weapon descriptions and the grapple's actual hotkey enumeration.

## Source defects and unresolved resources

These are findings in the untouched original, not silently accepted omissions.
Exact referrer hashes appear in the weapon plan or ranked source inventory.

| Source reference | Finding and practical consequence to check |
| --- | --- |
| `cog/kyle.cog` → `stop_engine` | Three calls, no matching local label. Requires an explicit source-repair decision before porting. |
| `cog/kyle.cog` → variable `water` | Assignment with no declaration in the script; its intended state is unresolved. |
| `cog/kyle.cog` → `breathe.wav`, `breathe2.wav` | Neither is in the mod or inspected owned JK/MotS archives. Breathing audio cannot be claimed preserved. |
| `cog/weap_repeater.cog` → `magtrommel.mat` | Missing named material is actively passed to `MaterialAnim`; requires compiler/resource/runtime diagnostics and a reviewed handling decision. |
| `jkl/static.jkl` → `null.snd` | Missing soundclass in a bullet-hole template; its loader behavior and spawned effect require testing. |
| `cog/taunt.cog` → `suckit.key` | Missing animation is passed to `PlayKey`; the script's actual inventory reachability is still being reviewed. |
| `cog/item_hook.cog` → four `.wav` placeholders | Several are passed to playback functions; they are not valid fully named sound dependencies. |
| `cog/weap_concrifle.cog`, `cog/weap_raildet.cog` → `.mat` placeholders | Both are passed to `MaterialAnim`; missing-resource behavior needs explicit handling. |
| `jkl/static.jkl` → `.snd` placeholder | Grapple soundclass is a placeholder; do not treat a filename scanner skipping it as resolved. |
| `jkl/static.jkl` template order | `+ulgflash` precedes its parent `_uexplosion`. An exact topological-order correction is needed for a standalone startup template assembly. |

The eventual recipe must derive its static pool from the native startup world,
retain all authored template behavior, resolve full typed resource paths and
declare required external template dependencies. It must not depend accidentally
on one MP level supplying another level's missing templates. Copies of native
gameplay controllers are not a substitute for that dependency review.

## Next acceptance gates

1. Complete exact native inventory/player/UI assembly and all placeholder,
   template-parent, template-reference and missing-resource decisions.
2. Produce a private candidate GOO and a per-entry provenance/override manifest;
   independently verify the exact path set and unchanged authored segments.
3. Rebuild twice from untouched inputs and compare every game payload.
4. Run a clean hidden native MotS MP host with only that candidate, examine COG
   and resource diagnostics, and exercise every weapon plus grapple and respawn.
5. Validate selected weapon appearance, scope/camera restoration, water/fall
   behavior and peer synchronization on more than one MP map.

Only then should the recipe enter the selectable Mods catalog with claims
limited to those completed checks. All source archives, original readmes,
review scripts containing game code and final converted archives remain private.

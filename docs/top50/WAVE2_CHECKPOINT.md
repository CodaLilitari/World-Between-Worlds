# Second implementation batch and pause checkpoint

Paused at Andrei's request on September 12, 2026. This is a development
checkpoint, not a release or a completed 150-entry compatibility claim.

The catalog contains **48 entries**. Within the requested frozen top 50 in each
Massassi category, **35 of 150 have exact-input recipes, 34 are selectable, and
115 lack recipes**. Castle Conflict remains unavailable pending delivery of its
engine prerequisite. Existing entries outside these categories remain separate.

## Added recipes

| Entry | Conversion and bounded engine evidence | Still open |
| --- | --- | --- |
| [DBZ: TDIR Tournament Level Pack](https://www.massassi.net/levels/files/1814.shtml) | All three active worlds preserved; one exact duplicate episode-row identifier repaired. Separate 30-second MotS MP hosts passed for all three worlds, with advancing simulation and no resource diagnostics. No TDIR mod is required or loaded. | Appearance comparisons, pickups/respawn, mechanics and matched peers. |
| [Imperial Pumping Station](https://www.massassi.net/levels/files/1366.shtml) | Non-Jedi protagonist, original goals and authored scripts preserved. Compatible ordinary pickups use native MotS controllers; isolated JK wrench controllers avoid introducing unrelated MotS dialogue. A 90-second MotS SP load/simulation check passed without resource diagnostics. | Opening camera, pumps, gates, reactor, escape, progression and save/load. |
| [Anime Characters Skin Pack](https://www.massassi.net/levels/files/684.shtml) | Exact loose-ZIP directory instructions retained; 15 skins appended to 55 native registrations. All 15 actual MotS MP selections loaded the requested model and soundclass, each with 18 hierarchy nodes and no resource diagnostics. | Visible full-body comparison, animation, audible sound, weapon attachment, respawn and peers. |

The skin recipe preserves the original `3do/mat/` parent directory and uses an
isolated namespace. Its two intentional native-path overrides are
`misc/models.dat` and `ui/jkstrings.uni`. The dependency audit found exactly two
owned JK soundclasses and 55 WAVs needed to preserve the authored voice bindings;
all 57 were independently reachable. No COG, world, KEY or PUP override is added.
The pack is a separately selected mod, never an implicit level dependency.

Original notices and authorship remain intact in local outputs. Tooling and
recipes contain no original downloads, extracted assets or finished conversions.
A recipe and its compatibility work do not confer asset redistribution rights.

## Validation recorded

[Runtime evidence](wave2-runtime-evidence.json) and
[replay/package evidence](wave2-validation.json) contain asset-free hashes and
bounded results. Two fresh final service runs under Python hash seeds 1 and 999
produced **21 identical output files per run** across the three recipes, including
notices, manifests and receipts. Independent Linux conversions produced the same
versioned GOO bytes as Windows. Canonical game payloads still match the tested
candidates after adding runtime evidence to the recipe metadata.

The exact three-profile archive audit found zero unexpected active resource
conflicts. It separately identified the two skin registry/UI overrides and
three differences between MotS's own episode and base archives. This audit does
not prove loose-file, persistent-cache or peer equality.

The source suite examined 355 tests on Windows and Linux. Windows initially
skipped 15; all 13 omitted owned Ninja Kage payload tests passed in a targeted
follow-up, leaving two environment-specific skips. Linux passed with two skips.
A later 73-test integration check passed 72 tests and hit one Windows socket
abort in an unchanged HTTP API test; that exact test passed immediately in
isolation. No product change was made to conceal that transient result.

All 48 exported recipes agree with live catalog generation. The source package
passed the updater from `5ad34e5` in memory: 72 allowlisted files, no added package
members or game assets. No release binary, release ZIP or automatic update was
published from this checkpoint.

## Separate engine work

The engine branch `codex/wbw-agent-validation` contains the packed-MAT-row fix
and explicit multiplayer autostart character selection. Character selection
uses the native MPC path and host rank limits. Capture receipts report both the
requested and actually loaded model, addressing the previous hardcoded-Kyle
testing limitation. The default-Kyle and out-of-range rank controls passed.

The selected-skin suite used candidate executable SHA-256
`0247daaac30347f7b85552de615d9db499faa0fb5ea2a9fd9b92157f557e5e60`.
The committed-source build at engine commit
`28ec799f1dab3f3954b4d395d19711c2204c43b1` has executable SHA-256
`4b208d7455223e1d6dd059938cb9c128b2dc4d97ff76ca1f00c891cc24ffdf94`.
It independently passed a Rei selection capture and a 30-second Castle Conflict
MotS MP check, with zero resource diagnostics and advancing simulation in Castle.
All current engine translation units were rebuilt against a copied private
dependency cache. This is not a claim of rebuilding every third-party dependency.

The capture camera still follows ordinary first-person body visibility rules.
Its frames verify rendering and actual selection, not a visible full-body skin
comparison. The inherited MPC reader's malformed-bin and header-token handling
also needs a separate hardening pass; the current tests use complete pinned
fixtures. The engine branch has not been merged into a released prerequisite.

## Resume here

1. Resume the **115 entries without recipes**: 23 MP, 47 SP and 45 mods. The
   original [remaining-source snapshot](REMAINING_SOURCE_REVIEW.md) supplies
   individual source gates; use the live status tool for updated counts.
2. Review the private **Steal the Bottle** and **Canyon Stream** candidates before
   integrating them. They are not catalog entries at this checkpoint. Steal
   preserves authored AI and its surface-crossing ending, with one reviewed
   saber-bin edit. Canyon retains a documented original missing turret sound;
   it must not be mislabeled unused or silently replaced. Their private handoffs
   retain exact source pins, operations, test state and unfinished work.
3. Complete gameplay and comparison checks for the selectable prototypes:
   doors/lifts, hazards, pickups and respawn, SP objectives and saves, actual
   skin appearance/animation, map transitions and matched second-peer behavior.
4. Integrate and deliver the engine prerequisite, then retest Castle and update
   its eligibility. Preserve the main fork checkout and unrelated worktrees.
5. Improve the capture/control interface for reproducible full-body and gameplay
   inspection, and harden the inherited MPC reader. Keep engine code in the fork
   and recipe transformations in WBW.
6. Rebuild release packages and review documentation only after those support
   gates are met. Keep all game/mod assets and generated conversions local.

The [stock JK campaign](../STOCK_JK_CAMPAIGN_PLAN.md) remains a separate future
plan: preserve both authored light-side and dark-side story routes while using
MotS's neutral Force system on either route. It is outside these 150 entries.

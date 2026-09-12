# Future plan: stock Jedi Knight campaign in MotS

Requested September 12, 2026. **Planning only; no campaign conversion is enabled.**
This is separate from the active Massassi top-50-per-category project.

The requested behavior is that choosing the dark-side or light-side route must
not determine whether the campaign can be played through WBW in MotS. Andrei
confirmed: **preserve both authored story routes, with MotS's neutral Force
powers on either route.** The exact route-selection UI
is a future design decision; do not silently remove a route or invent a merged
story to avoid implementing progression.

## Conversion work to plan

- Inventory the owned JKDF2 campaign's complete episode graph, both route
  branches, transitions, goals, cutscene triggers and supporting resources.
  Preserve the authored narrative and record any behavior that needs a semantic
  port. MotS availability must not be gated by JK's light/dark alignment.
- Separate story branch state from Force availability, rank, star allocation,
  mana limits and inventory state. Audit the actual campaign and native MotS
  controllers before deciding which values to retain or translate. Do not reuse
  multiplayer mana adjustments in singleplayer without evidence.
- Resolve weapon ordinal/bin differences, authored boss and player scripts,
  AI, mission items and any JK-specific Force behavior. Missing Force powers
  remain a separate mod project unless a mission specifically requires a
  reviewed compatibility implementation.
- Preserve complete episode progression and save/restore behavior. Review
  transitions in the same process as well as fresh starts; cached startup
  inventory and model bindings can differ from a direct map launch.
- Extract only the required dependencies from the user's owned installation.
  Record exact recipes and original/output hashes; do not distribute retail
  assets, copied cutscenes, or finished campaign archives. An external video
  dependency must be declared and checked rather than silently omitted.

## Acceptance matrix

Both story routes must be independently selectable/playable according to the
eventual route design, with MotS-neutral Force rules on either route. Test the
branch decision, every progression edge, mission objectives, relevant Force
interactions, bosses, death/respawn and save/restore. Include a normal campaign
start and direct diagnostic starts, and distinguish actual rendered gameplay
from headless loading tests. Check that changing Force allocation does not
accidentally change the intended story route.

Before enabling this recipe, publish an asset-free description of the final
route behavior and its limitations, and associate every result with the exact
recipe revision and engine build. Planning this work does not certify either
retail parity or a complete campaign playthrough.

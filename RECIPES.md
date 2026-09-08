# How a conversion is saved and replayed

World Between Worlds accepts reviewed original versions. It does not ask an AI model to
reconstruct a conversion when the user clicks a map. The work for each supported
map/mod is already executable code and pinned recipe data in the release.

`recipes.json` is the published asset-free snapshot of those recipe locks. The
workbench's Details view and Export selected recipes expose the same records.
They include the source ZIP/GOB/world hashes, declared dependency and script
sets, counted edits, reviewed original omissions, native overrides, and the
SHA-256 hashes of the converter modules that implement shared transformations.
The module hashes matter: a rule plus its versioned implementation defines the
conversion more precisely than a prose description alone.

The converter resolves needed resources from the selected original archive and
the user's owned JK/MotS installations. Its maps use explicit override order,
safe archive paths, namespaced resources/template names and individually reviewed
inventory/COG adjustments. It will reject an unreviewed original hash, an edit
anchor whose occurrence count changed, or an unexpected unresolved dependency.
Known original omissions are narrow named exceptions with recorded evidence;
there is no general ignore-missing switch.

Each generated result includes:

- The converted GOO and its member/source manifest.
- Any startup overlay required before inventory/player/model initialization.
- `blackwing-recipe.json`: the exact recipe lock used for that conversion.
- `blackwing-receipt.json`: the lock, original/owned input hashes, generated-file
  hashes and independent structural verification result.

The receipts are local artifacts. The application package contains no retail
or original community asset payloads, and Export selected recipes contains no
generated GOO. Repeating a conversion with the same recipe implementation and
matching inputs must produce identical game archive bytes. Different converter
versions can have different receipt/recipe hashes even if a particular map's
game bytes remain unchanged.

The recipes use separate paths for stock maps, custom map episodes and startup
gameplay mods. A mod such as Ninja Kage has no fictitious level added to it.
Multiple selected results stay separate; selecting multiple recipes never means
loading their gameplay overlays together.

Maintainers regenerate the published catalog after the final source changes:

```text
python packaging/export_catalog.py --output recipes.json
```

That command exports metadata only. It does not convert all maps or read game
assets. Actual conversion still requires an explicit selection and local inputs.

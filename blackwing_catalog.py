"""Selectable reviewed recipes and asset-free, reproducible recipe exports."""
import hashlib
import json
from pathlib import Path

import bridge
import custom_registry
import blackwing_revisions
import recipe_adapters
from blackwing_version import VERSION, TITLE, REPOSITORY

SOURCE_ROOT = Path(__file__).resolve().parent
ENGINE_MODULES = ('bridge.py', 'gob.py', 'caesars_audit.py', 'custom_registry.py',
                  'community_runtime.py', 'custom_catalog.py', 'author_catalog.py',
                  'jhs_catalog.py', 'massassi_mp_catalog.py', 'verify_retail.py', 'ninja_catalog.py',
                  'ninja_converter.py',
                  'recipe_adapters.py', 'mods_catalog.py', 'mods_converter.py',
                  'mp_pack_catalog.py', 'mp_pack_converter.py', 'sp_catalog.py', 'sp_converter.py',
                  'skinmods_catalog.py', 'skinmods_converter.py',
                  'blackwing_catalog.py', 'blackwing_service.py', 'blackwing_revisions.py')
MAP_RUNTIME = {
    'scope': 'Historical 60-second MotS multiplayer host with advancing simulation',
    'status': 'prior-recipe-host-tested',
    'full_gameplay': False,
    'note': 'These host runs predate RC3 script-capacity/pickup changes. Test each new output; host survival is separate from authored mechanics and two-peer playtesting.',
}
UNTESTED_RUNTIME = {
    'scope': 'New recipe; no runtime evidence supplied',
    'status': 'not-run',
    'full_gameplay': False,
    'note': 'Structural verification is separate from rendering, gameplay and peer testing.',
}
# Historical evidence belongs to these exact recipe families. A new catalog
# entry must never inherit it merely by going through the same converter.
HISTORICAL_COMMUNITY_IDS = frozenset({
    'drazen-isle', 'duel-of-the-fates-se', 'jawa-dwelling-se', 'stargate',
    'jhs', 'purgatory', 'atlantis', 'death-star-arena', 'naboo', 'morpheus',
    'mos-espa-rpg', 'area-21', 'courtyard', 'shadow-caverns', 'deicide',
})


def jsonable(value):
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(item) for item in value]
    if isinstance(value, set):
        return sorted(jsonable(item) for item in value)
    return value


def canonical(value):
    return json.dumps(jsonable(value), ensure_ascii=False, sort_keys=True,
                      separators=(',', ':')).encode('utf-8')


def source_hashes():
    return {name: hashlib.sha256((SOURCE_ROOT / name).read_bytes()).hexdigest()
            for name in ENGINE_MODULES if (SOURCE_ROOT / name).is_file()}


LOADED_SOURCE_HASHES = source_hashes()


def require_consistent_sources():
    if source_hashes() != LOADED_SOURCE_HASHES:
        raise ValueError('Tool files changed after startup. Restart World Between Worlds before exporting or converting recipes.')


def recipes():
    rows = []
    for key, spec in bridge.STOCK_MAPS.items():
        is_ctf = spec.get('episode_type') == 8
        rows.append(dict(id=key, title=spec['title'], kind='vanilla',
                         gameplay=['mp', 'ctf'] if is_ctf else ['mp'],
                         author='LucasArts', source_url='', archive_hint='',
                         requires_archive=False, status='verified',
                         summary='Extracts this original multiplayer map and its required assets from your JK installation.',
                         startup_overlay=bridge.CTF_STARTUP_FOLDER if is_ctf else None,
                         runtime_test=dict(MAP_RUNTIME)))
    for key, title, author, url, hint in (
        ('dojo', 'Jedi Dojo', 'Tee', 'https://www.massassi.net/levels/files/429.shtml', 'dojo.zip or dojo.gob'),
        ('caesars', "Caesar's Palace", 'WAR_Shockwave', 'https://www.massassi.net/levels/files/1400.shtml', 'caesars.zip or caesars.gob'),
    ):
        rows.append(dict(id=key, title=title, author=author, source_url=url,
                         kind='custom', gameplay=['mp'], archive_hint=hint,
                         requires_archive=True, status='verified', startup_overlay=None,
                         summary='Replays the reviewed original map conversion with locally extracted dependencies.',
                         runtime_test=dict(MAP_RUNTIME)))
    for key, spec in custom_registry.entries().items():
        overlay = bool(spec.get('native_cog_edits') or spec.get('native_resource_overrides') or spec.get('native_text_edits'))
        # startup_files is authoritative. These four reviewed families currently
        # have inventory, player or model changes that must load before an episode.
        overlay = overlay or key in {'drazen-isle', 'duel-of-the-fates-se', 'jawa-dwelling-se', 'stargate'}
        notes = spec.get('notes', [])
        summary = notes[0] if isinstance(notes, list) and notes else 'Reviewed original map with local dependency extraction and preserved authored environment scripts.'
        rows.append(dict(id=key, title=spec['title'], author=spec['author'],
                         source_url=spec['source_url'], kind='custom',
                         gameplay=['mp', 'saber'] if spec.get('episode_type') == 16 else ['mp'],
                         archive_hint=spec.get('gob_member', key + '.zip'),
                         requires_archive=True, status=spec.get('catalog_status', 'verified'), summary=summary,
                         startup_overlay='bridge-' + spec['tag'] + '-startup' if overlay else None,
                         runtime_test=dict(spec.get('runtime_test', MAP_RUNTIME if key in HISTORICAL_COMMUNITY_IDS else UNTESTED_RUNTIME))))
    # A gameplay mod is a startup package, never a fictitious map episode.
    try:
        import ninja_converter
    except ModuleNotFoundError as exc:
        if exc.name != 'ninja_converter':
            raise
    else:
        if hasattr(ninja_converter, 'catalog_entry'):
            rows.append(ninja_converter.catalog_entry())
    rows.extend(recipe_adapters.catalog_entries())
    if len(rows) != len({row['id'] for row in rows}):
        raise ValueError('Duplicate recipe ID across converter families.')
    for row in rows:
        key = row['id']
        row['revision'] = blackwing_revisions.revision(key)
        row['revision_label'] = 'wbw_v' + str(row['revision'])
        if key in bridge.STOCK_MAPS:
            legacy = bridge.stock_output_name(key)
        elif key in custom_registry.entries():
            legacy = custom_registry.output_name(key)
        elif recipe_adapters.for_recipe(key):
            legacy, = row['legacy_filenames']
        else:
            legacy = {'dojo': 'bridge-dojo-v1.goo', 'caesars': 'bridge-caesars-v3.goo',
                      'ninja-kage': 'blackwing-ninja-kage.goo'}[key]
        row['legacy_filenames'] = [legacy]
        row['output_filename'] = blackwing_revisions.versioned_name(legacy, row['revision'])
    return rows


def catalog():
    return dict(version=VERSION, title=TITLE, repository=REPOSITORY,
                recipes=recipes(), default_selection=[],
                navigation={'kinds': ['vanilla', 'custom', 'mod'],
                            'gameplay': ['mp', 'ctf', 'saber', 'sp']},
                premise='Recipes and original tooling only. Required game and level assets are read from your own local files.',
                unsupported='Only listed, reviewed archive revisions are accepted. Empty categories have no released recipes.')


def selection(ids):
    if not isinstance(ids, list) or not ids or any(not isinstance(key, str) for key in ids):
        raise ValueError('Choose at least one specific map or mod.')
    known = {row['id']: row for row in recipes()}
    if len(ids) != len(set(ids)):
        raise ValueError('Each recipe may be selected only once.')
    if len(ids) > len(known) or any(key not in known for key in ids):
        raise ValueError('The selection contains an unknown recipe.')
    if any(known[key]['status'] not in {'verified', 'supported', 'ready', 'available', 'prototype'} for key in ids):
        raise ValueError('The selection contains an unavailable recipe.')
    return [known[key] for key in ids]


def recipe_details(key):
    require_consistent_sources()
    matches = [row for row in recipes() if row['id'] == key]
    if len(matches) != 1:
        raise ValueError('Unknown recipe.')
    row = matches[0]
    adapter = recipe_adapters.for_recipe(key)
    if key in bridge.STOCK_MAPS:
        spec = bridge.STOCK_MAPS[key]
    elif key in custom_registry.entries():
        spec = custom_registry.entries()[key]
    elif key == 'dojo':
        spec = dict(zip_sha256=bridge.DOJO_ZIP_SHA256, gob_sha256=bridge.DOJO_GOB_SHA256,
                    source_cogs=bridge.DOJO_COGS, transformation='bridge.recipe(dojo=original)')
    elif key == 'caesars':
        spec = dict(zip_sha256=bridge.CAESARS_ZIP_SHA256, gob_sha256=bridge.CAESARS_GOB_SHA256,
                    source_cogs=bridge.CAESARS_COGS, transformation='bridge.recipe(caesars=original)',
                    behavior='One counted saber grant 10 -> 131; exact reviewed omissions; long-name alias.')
    elif adapter:
        spec = adapter.recipe_details(key)
    else:
        import ninja_converter
        spec = ninja_converter.recipe_details()
    result = dict(schema='blackwing.recipe-lock.v1', version=VERSION,
                  recipe_revision=row['revision'], revision_label=row['revision_label'],
                  entry=row, recipe=jsonable(spec), engine_source_sha256=source_hashes(),
                  retail_archive_sha256=bridge.HASHES,
                  optional_archive_sha256={'jksp': bridge.JKSP_SHA256, 'jkctf': bridge.JKCTF_SHA256,
                                           'motssp': bridge.MOTSSP_SHA256},
                  force_pickup_compatibility=(dict(
                      revision='mots-force-pickups-v2-native-visuals',
                      bindings=bridge.FORCE_PICKUP_BINDINGS,
                      sources=bridge.FORCE_PICKUP_SOURCES,
                      native_visuals=bridge.FORCE_PICKUP_VISUALS,
                      native_template_world_sha256=bridge.FORCE_PICKUP_NATIVE_WORLD_SHA256,
                      scope='Map runtime bindings only; no separate Force-power mod or Ninja selection',
                      edits='Counted native COG edits use maxmana bin69 in MP; both source surge kinds inherit one renewable native bin64 timer controller and native mana1.3do visual; Force Boost uses native dark.3do with native 00twinkle.mat animation; placements and respawn remain')
                      if row['kind'] != 'mod' and 'mp' in row['gameplay'] else None),
                  map_cog_instance_budget=(
                      'Maximum of original declared capacity plus added native template bindings plus shared-controller allocation, and final world COG rows plus all explicit template/placed-thing COG assignments; inventory uses the static world'
                      if row['kind'] != 'mod' and 'mp' in row['gameplay'] else None),
                  shared_transformations=[
                      'Hash-gate input archives and the exact source world/script set.',
                      'Resolve the literal dependency graph from the selected map/mod and owned archives.',
                      'Namespace reviewed map assets and template references, preserving original geometry.',
                      'Expand JK scalar vertex lighting to MotS A/R/G/B components.',
                      'Use reviewed MotS weapon/inventory bindings and exact counted per-recipe COG edits.',
                      'Emit deterministic archives, required startup overlays and source/output hash manifests.',
                      'Verify generated structure independently; this does not run the game.',
                  ],
                  assets_included=False)
    if spec.get('mode') == 'exact-material-repack-v1':
        result['shared_transformations'] = [
            'Hash-gate the exact original ZIP, all members and reviewed native material targets.',
            'Preserve all authored payload bytes and complete virtual paths.',
            'Rebuild the archive for an explicit, separate MotS startup mod.',
            'Preserve original notices beside the locally generated output.',
            'Verify the exact member set, native registration and post-write bytes.',
        ]
    elif adapter and adapter.__name__ == 'skinmods_converter':
        result['shared_transformations'] = [
            'Hash-gate the original skin archive, exact path repairs and required owned resources.',
            'Preserve authored geometry and resources with counted reference and namespace edits.',
            'Retain every native MotS skin registration and append the reviewed skin and UI label.',
            'Check native skeleton and animation dependencies without replacing gameplay scripts.',
            'Build an explicit optional startup mod; animated appearance and peer checks remain separate.',
        ]
    elif 'sp' in row['gameplay']:
        result['shared_transformations'] = [
            'Hash-gate the complete original episode and owned JK/MotS singleplayer sources.',
            'Preserve reviewed episode progression, authored AI, objectives and cutscene logic.',
            'Apply explicit counted compatibility edits and preserve native SP Force semantics.',
            'Namespace reviewed dependencies and expand scalar lighting to MotS components.',
            'Rebuild and independently verify every world and its resource closure.',
        ]
    result['recipe_sha256'] = hashlib.sha256(canonical(result)).hexdigest()
    return result


def export_plan(ids):
    rows = selection(ids)
    return dict(schema='blackwing.selection.v1', version=VERSION,
                repository=REPOSITORY, assets_included=False,
                recipes=[recipe_details(row['id']) for row in rows])

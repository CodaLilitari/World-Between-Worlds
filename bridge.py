"""Original, deliberately bounded JK multiplayer -> OpenMotS local recipe.

Accepted conversions are nine hash-pinned retail multiplayer maps and Jedi Dojo.
Caesar's Palace preserves its independently audited original omissions.
This is a structural prototype; a successful build is not a gameplay pass.
"""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import re
import zipfile
import custom_registry
import community_runtime

from gob import ArchiveError, Gob, build_gob
from caesars_audit import legacy_omission_waiver, waived_output_reference, static_usage

HASHES = {
    'jkmp': '27a4b3642e0965753232f35b1e8e846c91df1eca1da77398b5efda66ca369a2e',
    'jkres': 'c75f7d5211bdd2e07a3af6a987c718037e8f0fd6909018ddb4327137bf3a7ebf',
    'jksnd': '6c6d51eca9c85dffe7dce9b449642a052f055352e3f817abf03b465da861aafd',
    'motsmp': '92e3895aa5ae179861f8174dd23c03506acad270916c7f58b7b8f260d7a36bcd',
    'motsres': 'fa615eafa30114afd5e38369d790e721df56ce9a4ef62b66f34fc41b7c048a12',
    'motssnd': 'b80029082c93c7c47fd886ab659f41b5318fed1fa34b173cf5fd1bb7226d3462',
}
PATHS = {
    'jkmp': 'jkdf2-steam-clean/Episode/JK1MP.GOB',
    'jkres': 'jkdf2-steam-clean/Resource/Res2.gob',
    'jksnd': 'jkdf2-steam-clean/Resource/Res1hi.gob',
    'motsmp': 'mots-retail-clean/episode/JKM_MP.GOO',
    'motsres': 'mots-retail-clean/resource/JKMRES.GOO',
    'motssnd': 'mots-retail-clean/resource/JKMSNDLO.GOO',
}
JKSP_SHA256 = '41591e570d5a2173873465e4c061e61edb5efea9883533ed70d78b3a81a10e46'
JKSP_PATH = 'jkdf2-steam-clean/Episode/JK1.GOB'
JKCTF_SHA256 = 'da98fe3fc769168f1bb562cc1f6532560b12d8e920fd6c34586d69b424b5b1fc'
JKCTF_PATH = 'jkdf2-steam-clean/Episode/JK1CTF.GOB'
EXTENSIONS = 'mat|cmp|3do|key|pup|snd|cog|wav|spr|par|ai'
FILE_REF = re.compile(r'(?<![\w.~&])([\w+.~&-]+\.(?:' + EXTENSIONS + r'))(?![\w.~&])', re.I)
TEXT_EXTENSIONS = {'.jkl', '.3do', '.pup', '.snd', '.cog', '.spr', '.par', '.ai'}
TABLES = ('sounds', 'materials', 'colormaps', 'aiclasses', 'models', 'sprites',
          'keyframes', 'puppets', 'soundclasses', 'scripts')
ENVIRONMENT_COGS = {'00_door.cog', '00_elev_switch2.cog', '00_slideceiling.cog'}
EXPECTED_COGS = {
    'kyle.cog', 'pow_bacta.cog', 'pow_shields.cog', 'pow_supershield.cog',
    'pow_mana.cog', 'pow_revive.cog', 'pow_vest.cog', 'pow_darkside.cog',
    'pow_lightside.cog', 'class_sequencer.cog', '00_smoketrail.cog',
    'pow_saber.cog', '00_desttrail.cog', 'pow_backpack.cog', 'pow_bryar.cog',
    'pow_strifle.cog', 'pow_single_thermal.cog', 'pow_crossbow.cog',
    'pow_repeater.cog', 'pow_railgun.cog', 'pow_single_sequencer.cog',
    'pow_concrifle.cog', *ENVIRONMENT_COGS,
}
BATTLEGROUND_COGS = set('''kyle.cog pow_health.cog pow_bacta.cog pow_darkside.cog
pow_lightside.cog pow_mana.cog class_sequencer.cog 00_smoketrail.cog pow_saber.cog
00_desttrail.cog pow_backpack.cog pow_bryar.cog pow_strifle.cog pow_single_thermal.cog
pow_crossbow.cog pow_repeater.cog pow_railgun.cog pow_single_sequencer.cog
pow_concrifle.cog 00_slideceiling.cog 17a_stream.cog 00_playambient.cog'''.split())
# Exact world and script-set hashes gate these individually reviewed recipes.
# Environment scripts retain their source code and explicit execution flags;
# template defaults and filename references are namespaced, never replaced.
STOCK_MAPS = {
    'nar-shaddaa': {
        'world': 'jkl/m2.jkl', 'tag': 'narshaddaa',
        'title': 'Nar Shaddaa Loading Terminal',
        'sha256': '938f8a892bcdc90a7f54f25aed4fd58baba750293c5d01ac2dec68ef170eef9a',
        'scripts_sha256': '0af8497f76a836305bfbebccc8670918fa3c5b1bdb23164f2c26f1a42b0b223e',
        'environment': '00_conveyor.cog 00_door.cog 00_elev_switch.cog 00_randomambient.cog 00_twoonebee.cog m2_dettrap.cog m2_ffieldswitch.cog m2_turrettrap.cog xtank3.cog',
    },
    'bespin': {
        'world': 'jkl/m4.jkl', 'tag': 'bespin', 'title': 'Bespin Mining Station',
        'sha256': '150eda1c2e6c7f316c8b76a0f2f060ce5d49dcc9ae24bb43e4fb42a5df20d89c',
        'scripts_sha256': 'd2467e6c0e48b61a02453f42a6ef6c9d8e54f549f102f27167ed82a0901d5825',
        'environment': '00_door.cog 00_elev_switch2.cog 00_forcefield.cog 00_matanim.cog 00_surfanim.cog m4_reactorthrust.cog xtank3.cog',
    },
    'blades-of-death': {
        'world': 'jkl/m5.jkl', 'tag': 'blades', 'title': 'Blades of Death',
        'sha256': '61713ac79aa60bba1b558f8457a1351f720b076c242469110975ac26b2dcff38',
        'scripts_sha256': 'bb83329b7b1786fba26bffe6e3dba5e4d351a370f73add0b0d605c85c32e0dcd',
        'environment': 'm5_antigrav.cog m5_autodoor.cog m5_convbelt.cog m5_fandamage.cog m5_flashingredlight.cog m5_healingsector.cog m5_surfanim.cog',
    },
    'canyon-oasis': {
        'world': 'jkl/m10.jkl', 'tag': 'canyon', 'title': 'Canyon Oasis',
        'sha256': '87bb3e919ee1f3749595f1ee37965bc083dbb866148775fd64280b0170926ecc',
        'scripts_sha256': '44414ca8418f235c2334ad4b26031280a4ff988d8a289688fd490b785205a09e',
        'environment': '00_conveyor.cog 00_lightning.cog 00_playambient.cog 00_slideceiling.cog',
    },
    'valley': {
        'world': 'jkl/m_boss15.jkl', 'tag': 'valley',
        'title': 'The Valley of the Jedi Tower', 'episode_title': 'Valley',
        'sha256': '1f8502deba0220a3f39a2a3fb2f638ecf71b214f127b74d47ac482194e907458',
        'scripts_sha256': '1f9a7a3d572bf682e8696cacb9d3bed6d4e75e97597712dcb7fcf7d5bf3211bb',
        'environment': '00_door.cog 00_elev_switch2.cog 00_slideceiling.cog',
    },
    'battleground': {
        'world': 'jkl/m_boss17.jkl', 'tag': 'battleground', 'title': 'Battleground Jedi',
        'sha256': '5c0795709ff3f2da525d0ad9ce4a3e41b13445febc1b5f88f727c864b606349f',
        'scripts_sha256': 'eccda0df0e36a4b29d6ec44d7b282790a34b221700f996ba2641222b2aa04dc9',
        'environment': '00_playambient.cog 00_slideceiling.cog 17a_stream.cog',
        'requires_jksp': True,
    },
    'ctf-duel': {
        'world': 'jkl/c1.jkl', 'tag': 'ctf_duel', 'title': 'The Duel',
        'archive': 'jkctf', 'episode_type': 8,
        'sha256': '349fb5beffba7c84fd573fe1184f3fbb569d4fcdad07d2d9b26fcb8afdb849e0',
        'scripts_sha256': 'ceec3b488cc9286c272be53dc1ebd6c4154f495627cb239d7a5d3bb57fb4dfea',
        'environment': 'c1_ambientwindsound.cog c1_ctfcallback.cog c1_secretelev.cog c1_slideskies.cog ctf_displayscore.cog ctf_iconsclient.cog ctf_main.cog ctf_respawn.cog ctf_safeentry.cog',
    },
    'ctf-arena': {
        'world': 'jkl/c2.jkl', 'tag': 'ctf_arena', 'title': 'The Arena of Dark and Light',
        'archive': 'jkctf', 'episode_type': 8,
        'sha256': 'bc9975eb3c93ee45e83928307d27dfd5d8f94ad4eea3216fa3fecf784e593ade',
        'scripts_sha256': '5a764a43a6b962b392bd1ce3bbf2bba92022b3911ceb69286278d509d532c8be',
        'environment': '00_breakinglamps.cog c2_ambientwindsound.cog c2_breakingglass.cog c2_breakingglassclient.cog c2_dualforcefield.cog c2_killingfloor.cog c2_movingplatform.cog c2_mtrigelev.cog c2_simpleforcefield.cog ctf_displayscore.cog ctf_iconsclient.cog ctf_main.cog ctf_respawn.cog ctf_safeentry.cog',
        'source_omissions': [{
            'name': '00_glass.mat', 'referrer': '3do/shard0.3do',
            'referrer_sha256': 'f0b4102b3ba378913b6d16ee585baab2d14f46f9ae4ae293a1c24b9f2369f44d',
            'untextured_3do': True,
            'reason': 'Original missing sole material slot; the one face is geo3 and has zero texture vertices. Preserve omission, not a substitute texture.',
        }],
    },
    'ctf-challenge': {
        'world': 'jkl/c3.jkl', 'tag': 'ctf_challenge', 'title': 'The Challenge at Nar Shaddaa',
        'archive': 'jkctf', 'episode_type': 8,
        'sha256': 'b4d804591cebebbd59f05ad42a8e059178dc468e24172bd6bc5b7d6ba1c2f0a7',
        'scripts_sha256': '83452416ceb2638649e4080f3fb59e1ede3fe565db721f0bc0f98485fb900b55',
        'environment': '00_breakinglampx.cog c3_ambienttechsound.cog c3_ambientwindsound.cog c3_autodoor.cog c3_cameraff.cog c3_detonators.cog c3_dualelev.cog c3_elevswitch.cog c3_fanspuzzle.cog c3_forcefield.cog c3_killingfloor.cog c3_largelevel.cog c3_largelevelsrv.cog c3_movingplatform.cog c3_mtrigelev.cog c3_sascolored.cog c3_sasneutral.cog c3_switchdoor.cog c3_turrets.cog ctf_displayscore.cog ctf_doorgold.cog ctf_doorred.cog ctf_iconsclient.cog ctf_keygold.cog ctf_keyred.cog ctf_keysclient.cog ctf_main.cog ctf_respawn.cog ctf_safeentry.cog',
    },
}


def stock_selector(value):
    """Accept stable recipe keys, source JKL names, and exact retail titles."""
    selected = value.strip().lower()
    for key, spec in STOCK_MAPS.items():
        if selected in {key, spec['tag'], spec['title'].lower(),
                        spec['world'], Path(spec['world']).name,
                        Path(spec['world']).stem}:
            return key
    raise RecipeError('Unsupported stock map: ' + value)


def stock_output_name(key):
    spec = STOCK_MAPS[key]
    return 'bridge-' + spec['tag'] + ('-v2.goo' if key == 'valley' else '-v1.goo')


CAESARS_GOB_SHA256 = '56393dc8b9c855e06799650d08dfe24268344d1fe3f6972140e2525ac3a4e3f0'
CAESARS_ZIP_SHA256 = 'b7a9f16b9141a4ef56c97784ef5a49914655a87ad6db59a2014429ee6ffe5fbd'
DOJO_GOB_SHA256 = '6ce07727918159fefd9f5cb8728bf4a618263a44d3a414fa365ea26c35954910'
DOJO_ZIP_SHA256 = '27f6a44f209cdc8fcebfe0fffd3230b2e7cbc1cf5982ef07133b10bdc70bc4da'
DOJO_COGS = set('''00_desttrail.cog 00_smoketrail.cog actor_wc.cog class_sequencer.cog
kyle.cog levelstart.cog pow_backpack.cog pow_bacta.cog pow_battery.cog pow_bryar.cog
pow_concrifle.cog pow_crossbow.cog pow_energy.cog pow_health.cog pow_power.cog
pow_railgun.cog pow_repeater.cog pow_shields.cog pow_single_sequencer.cog
pow_single_thermal.cog pow_smbkpk.cog pow_strifle.cog'''.split())
CAESARS_COGS = set('''00_breakingglass.cog 00_conveyor.cog 00_desttrail.cog 00_generator2.cog
00_matanim.cog 00_sectorliteanimflicker2.cog 00_slideceiling.cog 00_smoketrail.cog
00_turrettrap.cog actor_bt.cog actor_mn.cog actor_pf.cog actor_pm.cog bcc.cog bcs.cog
caesars_start.cog class_sequencer.cog destruct.cog grenade.cog hemlos_door.cog
kyle.cog levelstart.cog lightswitch.cog m2_ffieldswitch.cog mdm04_slashgrate.cog
pow_backpack.cog pow_bacta.cog pow_battery.cog pow_bryar.cog pow_concrifle.cog
pow_crossbow.cog pow_darkside.cog pow_energy.cog pow_goggles.cog pow_health.cog
pow_lightside.cog pow_power.cog pow_powerboost.cog pow_railcharges.cog pow_railgun.cog
pow_repeater.cog pow_revive.cog pow_sequencer.cog pow_shields.cog pow_single_sequencer.cog
pow_single_thermal.cog pow_smbkpk.cog pow_stbkpk.cog pow_strifle.cog pow_supershield.cog
pow_thermal.cog pow_vest.cog raildet.cog redcamera.cog riverthrust.cog scream.cog
seqcharge.cog textvoice.cog toucmelv.cog turret.cog wavcons.cog'''.split())


class RecipeError(ValueError):
    pass


def open_caesars(path):
    path = Path(path)
    if path.stat().st_size > 20_000_000:
        raise RecipeError('Unsupported Caesar archive size')
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest == CAESARS_GOB_SHA256:
        return Gob(data, str(path))
    if digest != CAESARS_ZIP_SHA256:
        raise RecipeError('Unsupported Caesar archive hash')
    from io import BytesIO
    from gob import resource_name
    with zipfile.ZipFile(BytesIO(data)) as archive:
        names = [resource_name(item.filename) for item in archive.infolist()]
        if len(names) != len(set(names)) or set(names) != {'credits.doc', 'credits.txt', 'readme.txt', 'caesars.gob'}:
            raise RecipeError('Unexpected Caesar ZIP directory')
        if archive.testzip() is not None:
            raise RecipeError('Caesar ZIP CRC failure')
        data = archive.read('caesars.gob')
    if hashlib.sha256(data).hexdigest() != CAESARS_GOB_SHA256:
        raise RecipeError('Unexpected embedded Caesar GOB hash')
    return Gob(data, str(path) + ':caesars.gob')


def open_dojo(path):
    path = Path(path)
    if path.stat().st_size > 1_000_000:
        raise RecipeError('Unsupported Jedi Dojo archive size')
    data = path.read_bytes(); digest = hashlib.sha256(data).hexdigest()
    if digest == DOJO_GOB_SHA256:
        return Gob(data, str(path))
    if digest != DOJO_ZIP_SHA256:
        raise RecipeError('Unsupported Jedi Dojo archive hash')
    from io import BytesIO
    from gob import resource_name
    with zipfile.ZipFile(BytesIO(data)) as archive:
        names = [resource_name(item.filename) for item in archive.infolist()]
        if len(names) != len(set(names)) or len(names) != 2 or 'dojo.gob' not in names:
            raise RecipeError('Unexpected Jedi Dojo ZIP directory')
        if archive.testzip() is not None:
            raise RecipeError('Jedi Dojo ZIP CRC failure')
        entry = next(item.filename for item in archive.infolist() if item.filename.lower() == 'dojo.gob')
        data = archive.read(entry)
    if hashlib.sha256(data).hexdigest() != DOJO_GOB_SHA256:
        raise RecipeError('Unexpected embedded Jedi Dojo GOB hash')
    return Gob(data, str(path) + ':dojo.gob')


def audit_caesars(archives, caesars):
    if caesars.sha256 != CAESARS_GOB_SHA256:
        raise RecipeError('Unsupported Caesar archive hash')
    source = Catalog([('caesars', caesars)] + [(key, archives[key]) for key in ('jkmp', 'jkres', 'jksnd')])
    target = Catalog([(key, archives[key]) for key in ('motsmp', 'motsres', 'motssnd')])
    pending = deque([('jkl/caesars.jkl', name) for name in sorted(references(text(caesars.read('jkl/caesars.jkl'))))])
    missing = {}; seen = set()
    while pending:
        referrer, name = pending.popleft()
        if name not in source.by_name:
            missing.setdefault(name, {'referrers': [], 'owned_mots_candidate': name in target.by_name})['referrers'].append(referrer)
            continue
        if name in seen:
            continue
        seen.add(name)
        _, path, archive = source.get(name)
        if Path(name).suffix in TEXT_EXTENSIONS:
            pending.extend((path, item) for item in sorted(references(text(archive.read(path)))))
    try:
        waiver = legacy_omission_waiver(caesars, archives, missing)
    except ValueError as error:
        raise RecipeError(str(error)) from error
    return {'status': 'reviewed-original-omissions-preserved', 'source_sha256': caesars.sha256,
            'resolved_resource_count': len(seen), 'missing_original_dependencies': missing,
            'reviewed_legacy_omission_waiver': waiver, 'static_usage': static_usage(caesars),
            'recovered_candidate': {'name': 'riverthrust.cog', 'url': 'https://www.massassi.net/cogfiles/both/riverthrust.cog',
                                    'sha256': '0476afe206a9a529804b30473fa7b23ce0b3c5ea21cc09bb2b4898c0aba1169b',
                                    'limitation': 'Authentic named source, exact intended historical revision unverified.'},
            'limitation': 'An owned MotS filename match is a candidate, not automatic proof of the intended asset. No placeholders are generated.'}


def template_defaults(value, names):
    return re.sub(r'(^\s*template\s+\w+\s*=\s*)([^\s]+)',
                  lambda m: m.group(1) + names.get(m.group(2).lower(), m.group(2)),
                  value, flags=re.M | re.I)


def exposed_symbols(cog):
    m = re.search(r'^\s*symbols\s*$(.*?)^\s*end\s*$', active_lines(cog), re.M | re.I | re.S)
    if not m:
        raise RecipeError('COG symbols block not found')
    return [line.split()[0].lower() for line in m.group(1).splitlines()
            if line.strip() and line.split()[0].lower() != 'message'
            and not re.search(r'\blocal\b', line, re.I)]


def rewrite_cog_template_arguments(value, catalog, template_names, *, missing_cogs=(), missing_templates=()):
    rows = []
    used_missing = set()
    for row in records(value, 'cogs'):
        tokens = row.split()
        if tokens[1].lower() in missing_cogs:
            if tokens[1].lower() in catalog.by_name:
                raise RecipeError('Reviewed absent COG unexpectedly resolved')
            rows.append(' '.join(tokens))
            continue
        _, path, archive = catalog.get(tokens[1])
        types = exposed_symbols(text(archive.read(path)))
        symbols_block = re.search(r'^\s*symbols\s*$(.*?)^\s*end\s*$', active_lines(text(archive.read(path))), re.M | re.I | re.S)
        symbol_names = [line.split()[1].split('=')[0].lower() for line in symbols_block.group(1).splitlines()
                        if line.strip() and line.split()[0].lower() != 'message' and not re.search(r'\blocal\b', line, re.I)]
        if len(tokens) - 2 > len(types):
            raise RecipeError(f'Too many COG placement arguments: {tokens[0]} {tokens[1]}')
        for index, kind in enumerate(types[:len(tokens) - 2]):
            if kind == 'template':
                token = tokens[index + 2].lower()
                if token not in template_names and token != '-1':
                    matching = [i for i, rule in enumerate(missing_templates) if rule['row'] == tokens[0]
                                and rule['cog'].lower() == tokens[1].lower() and rule['name'].lower() == token
                                and rule['symbol'].lower() == symbol_names[index] and rule.get('reason')]
                    if len(matching) != 1 or 'br_' + token in template_names.values():
                        raise RecipeError(f'Undefined external template {token}')
                    used_missing.add(matching[0])
                    tokens[index + 2] = 'br_' + token
                    continue
                tokens[index + 2] = template_names.get(token, token)
        rows.append(' '.join(tokens))
    if used_missing != set(range(len(missing_templates))):
        raise RecipeError('Reviewed missing template argument did not match original placement')
    return replace_block(value, 'cogs', rows, int(block(value, 'cogs').group(2)))


def text(data):
    return data.decode('cp1252').replace('\r', '')


def active_lines(value):
    return '\n'.join(line.split('#', 1)[0].split('//', 1)[0] for line in value.splitlines())


def references(value):
    """Literal filename references only; computed COG paths are not inferred."""
    return set(m.group(1).lower() for m in FILE_REF.finditer(active_lines(value)))


def block(value, label):
    pattern = re.compile(r'(^World ' + re.escape(label) + r'\s+(\d+)[^\n]*\n)(.*?)(?=^(?:World\s|Section:\s|end\b)|\Z)', re.I | re.M | re.S)
    m = pattern.search(value)
    if not m:
        raise RecipeError(f'Missing World {label} block')
    return m


def records(value, label):
    return [line.strip() for line in block(value, label).group(3).splitlines()
            if line.strip() and not line.lstrip().startswith('#')]


def replace_block(value, label, rows, capacity=None):
    m = block(value, label)
    return value[:m.start()] + f'World {label} {capacity if capacity is not None else len(rows)}\n' + '\n'.join(rows) + '\n' + value[m.end():]


def expand_surface_lighting(value):
    """Preserve all pre-intensity tokens and replicate each JK scalar as A,R,G,B."""
    start = re.search(r'^World surfaces\s+(\d+)\s*$', value, re.M | re.I)
    if not start:
        raise RecipeError('Missing surfaces')
    lines = value[start.end():].splitlines(keepends=True)
    wanted = int(start.group(1)); seen = 0
    for index, line in enumerate(lines):
        if seen == wanted:
            break
        tokens = line.split('#', 1)[0].split()
        if not tokens or not re.fullmatch(r'\d+:', tokens[0]):
            continue
        if len(tokens) < 10 or int(tokens[0][:-1]) != seen:
            raise RecipeError('Malformed/nonsequential surface record')
        n = int(tokens[9]); prefix = 10 + n
        if len(tokens) != prefix + n:
            raise RecipeError('Recipe requires scalar JK surface lighting')
        if not all(re.fullmatch(r'-?\d+,-?\d+', token) for token in tokens[10:prefix]):
            raise RecipeError('Malformed surface vertex pair')
        for token in tokens[prefix:]:
            float(token)
        lines[index] = '\t'.join(tokens[:prefix] + [x for token in tokens[prefix:] for x in [token] * 4]) + '\n'
        seen += 1
    if seen != wanted:
        raise RecipeError('Truncated surfaces')
    return value[:start.end()] + ''.join(lines), seen


def convert_things(value, template_names):
    rows = []
    for line in records(value, 'things'):
        tokens = line.split()
        if len(tokens) < 10 or not re.fullmatch(r'\d+:', tokens[0]):
            raise RecipeError('Malformed thing')
        if len(tokens) > 10 and '=' not in tokens[10]:
            raise RecipeError('Already has MotS archlighting or unsupported thing layout')
        for token in tokens[3:9]:
            float(token)
        int(tokens[9])
        old = tokens[1].lower()
        if old not in template_names:
            raise RecipeError(f'Undefined scene template {old}')
        tokens[1] = 'walkplayer' if old == 'walkplayer' else template_names[old]
        tokens.insert(10, '-1')
        rows.append(' '.join(tokens))
    return replace_block(value, 'things', rows, int(block(value, 'things').group(2))), len(rows)


class Catalog:
    def __init__(self, archives):
        self.by_name = {}
        self.ambiguous = set()
        for label, archive in archives:
            for path in archive.entries:
                basename = Path(path).name.lower()
                if basename in self.by_name:
                    old_label, old_path, old_archive = self.by_name[basename]
                    if old_archive.read(old_path) != archive.read(path):
                        # Archive order is explicit override precedence; paths sharing
                        # a basename in a single archive must not be guessed.
                        if old_label == label:
                            self.ambiguous.add(basename)
                    continue
                self.by_name[basename] = (label, path, archive)

    def get(self, name):
        if name.lower() in self.ambiguous:
            raise RecipeError(f'Ambiguous resource basename: {name}')
        try:
            return self.by_name[name.lower()]
        except KeyError as exc:
            raise RecipeError(f'Unresolved literal dependency: {name}') from exc


def owned_file(root, relative):
    """Resolve legacy archive spelling on case-sensitive Linux installations.

    Components must be unique even on a case-sensitive filesystem. This does
    not relax content hashes or search outside the user-selected game root.
    """
    current = Path(root)
    for part in Path(relative).parts:
        if part in ('', '.', '..') or '/' in part or '\\' in part:
            raise RecipeError('Invalid owned archive relative path')
        matches = [path for path in current.iterdir() if path.name.casefold() == part.casefold()]
        if len(matches) != 1:
            raise RecipeError('Missing or ambiguous owned archive component: ' + part)
        current = matches[0]
    return current


def pinned_archives(baselines=None, *, jk_root=None, mots_root=None, include_jksp=False, include_jkctf=False):
    if baselines is None and (jk_root is None or mots_root is None):
        raise RecipeError('Supply --jk-root and --mots-root, or the legacy --baselines layout')
    if baselines is not None and (jk_root is not None or mots_root is not None):
        raise RecipeError('Do not mix --baselines with --jk-root/--mots-root')
    found = {}
    requested = dict(PATHS)
    if include_jksp:
        requested['jksp'] = JKSP_PATH
    if include_jkctf:
        requested['jkctf'] = JKCTF_PATH
    for key, rel in requested.items():
        if baselines is None:
            _, local_rel = rel.split('/', 1)
            path = owned_file(jk_root if key.startswith('jk') else mots_root, local_rel)
        else:
            path = Path(baselines) / rel
        archive = Gob.open(path)
        if archive.sha256 != ({'jksp': JKSP_SHA256, 'jkctf': JKCTF_SHA256}.get(key) or HASHES[key]):
            raise RecipeError(f'Unsupported source hash for {key}; no output generated')
        found[key] = archive
    return found


def reviewed_source_omission(name, referrer, catalog, rules):
    """Accept only a named, hash-audited original missing reference edge."""
    for rule in rules:
        if name != rule['name'] or referrer != rule['referrer']:
            continue
        label, path, archive = catalog.get(Path(referrer).name)
        data = archive.read(path)
        if path != referrer or hashlib.sha256(data).hexdigest() != rule['referrer_sha256']:
            raise RecipeError('Source omission referrer hash mismatch: ' + referrer)
        if rule.get('untextured_3do'):
            value = active_lines(text(data))
            face = re.search(r'^\s*FACES\s+1\s*$(.*?)^\s*FACE NORMALS', value, re.M | re.I | re.S)
            row = face.group(1).split() if face else []
            if (not re.search(r'^\s*MATERIALS\s+1\s*$', value, re.M | re.I)
                    or not re.search(r'^\s*TEXTURE VERTICES\s+0\s*$', value, re.M | re.I)
                    or len(row) < 8 or row[1] != '0' or row[3] != '3'):
                raise RecipeError('Reviewed untextured material usage changed')
        return {**rule, 'source_archive': label, 'output_name': 'br_' + name,
                'output_referrer': path.rsplit('/', 1)[0] + '/br_' + Path(path).name}
    raise RecipeError(f'Unresolved literal dependency: {name} (from {referrer})')


def adapt_ctf_saber_grants(value):
    """Two reviewed CTF team-entry saber grants move from JK bin10 to MotS131."""
    result, count = re.subn(r'\bSetInv\(player, 10, 1\);', 'SetInv(player, 131, 1);', value)
    if count != 2:
        raise RecipeError('CTF saber-grant source changed; expected two exact calls')
    return result


def adapt_caesars_start(value):
    """Fix the saber grant; fists/Bryar and weapon-selection modes already map."""
    pattern = r'(\bSetInv\(\s*player\s*,\s*)10(\s*,\s*1\s*\))'
    value, count = re.subn(pattern, lambda m: m.group(1) + '131' + m.group(2), value, flags=re.I)
    if count != 1:
        raise RecipeError(f'Expected one original Caesar saber grant for bin 10; found {count}')
    return value


def ctf_items_dat(value):
    """Keep native MotS gameplay; restore the CTF red-flag HUD descriptor only."""
    result, count = re.subn(r'^(ysalamiri)(\s+81\s+0\s+1\s+0x048\s*)$',
                            r'redflag\2', value, flags=re.M)
    if count != 1:
        raise RecipeError('Unexpected MotS bin81 descriptor')
    return result


CTF_STARTUP_FOLDER = 'bridge-ctf-ui'
CTF_STARTUP_ARCHIVE = 'bridge-ctf-ui.goo'


def ctf_startup_candidate(archives):
    """Startup resource directory zero must supply items before episode selection."""
    for key in ('motsres', 'motssnd'):
        if archives[key].sha256 != HASHES[key]:
            raise RecipeError('Unsupported CTF startup input hash: ' + key)
    source = archives['motsres'].read('misc/items.dat')
    items = ctf_items_dat(text(source)).encode('cp1252')
    icons = {}
    for name in ('icredfl8.bm', 'icredfl16.bm', 'icgoldf8.bm', 'icgoldf16.bm'):
        path = 'ui/bm/' + name
        icons[path] = hashlib.sha256(archives['motssnd'].read(path)).hexdigest()
    output = Gob(build_gob({'misc/items.dat': items}))
    manifest = {
        'recipe': 'ctf-startup-ui-v1', 'required_for': ['ctf-duel', 'ctf-arena', 'ctf-challenge'],
        'inputs': {key: archives[key].sha256 for key in ('motsres', 'motssnd')},
        'source_items_sha256': hashlib.sha256(source).hexdigest(),
        'transformation': 'Only native MotS inventory descriptor81: ysalamiri -> redflag; flags/range/other rows unchanged.',
        'native_icons_sha256': icons, 'output': output.inventory(),
        'required_launch_arguments': ['-motsCompat', '-path', CTF_STARTUP_FOLDER],
        'load_order': 'Main_ParseCmdLine -> jkRes_Startup(-path directory0) -> static.jkl -> jkHudInv_InitItems; episode selection occurs later.',
        'limitation': 'The copy of items.dat inside a CTF episode is insufficient for startup initialization. Every host/client must use this overlay from process launch.',
    }
    return output.data, manifest


def ctf_startup_files(data, manifest):
    digest = hashlib.sha256(data).hexdigest()
    instructions = f'''CTF startup overlay (shared by all three bridge CTF episodes)

This generated archive contains owned MotS items.dat with only descriptor81
renamed from ysalamiri to redflag. It must be mounted BEFORE inventory startup.
The episode-local copy alone is insufficient. Keep this asset package local.

1. Use a clean, separate MotS runtime with the supported native resource files.
2. Copy the whole {CTF_STARTUP_FOLDER} directory beside that runtime's resource
   and episode directories. Keep only {CTF_STARTUP_ARCHIVE}, its manifest, and
   this README in it. Do not combine it with SBX, Manowar, KFY or another mod.
3. Copy the selected converted CTF GOO(s) to that runtime's episode directory.
4. From the runtime working directory start the engine with these arguments:
      -motsCompat -path {CTF_STARTUP_FOLDER}
   Then select the desired CTF episode in Multiplayer. Every client must launch
   with the same overlay too. Restart without -path before playing other modes.

For explicit multiplayer autostart, append the selected row's arguments:
  The Duel:
    -autostart -mp -episode bridge-ctf_duel-v1 -map br_ctf_duel.jkl
  The Arena of Dark and Light:
    -autostart -mp -episode bridge-ctf_arena-v1 -map br_ctf_arena.jkl
  The Challenge at Nar Shaddaa:
    -autostart -mp -episode bridge-ctf_challenge-v1 -map br_ctf_challenge.jkl
Use the actual GOO stem if you chose a different episode output filename.

The relative -path value above deliberately contains no spaces and stays below
the engine's fixed path buffers. Quoting a spaced absolute -path is unreliable
because Main_ParseCmdLine tokenizes whitespace. The runtime path itself may
contain spaces: set the working directory separately from command arguments.

Do not leave loose misc/items.dat overrides in the runtime, resource directory,
or selected episode subdirectory: jkRes_FileOpen can prefer such files. Do not
add other GOO files or loose resources to this overlay directory. Native icons
icredfl8/16 and icgoldf8/16 come from the pinned JKMSNDLO.GOO resource archive.

Verify the overlay GOO before use:
  SHA256 {digest}
Its only internal member must be misc/items.dat. The manifest records all input
and member hashes. Structural startup packaging does not certify team selection,
flag pickup/drop/return, captures/scoring, HUD rendering, or network replication.
'''
    return {CTF_STARTUP_ARCHIVE: data,
            'bridge-ctf-ui.manifest.json': (json.dumps(manifest, indent=2) + '\n').encode('utf-8'),
            'README.txt': instructions.encode('utf-8')}


def check_ctf_startup_directory(path, files):
    """Allow exact reuse for separate CTF conversions, never mixed mod contents."""
    path = Path(path)
    if path.resolve().is_relative_to(Path(__file__).resolve().parent):
        raise RecipeError('Generated game assets must stay outside the source project')
    if path.exists():
        if (not path.is_dir() or {item.name for item in path.iterdir()} != set(files)
                or any(not (path / name).is_file() or (path / name).read_bytes() != data
                       for name, data in files.items())):
            raise RecipeError('CTF startup directory exists with different or extra contents: ' + str(path))


def write_ctf_startup(path, data, manifest):
    path = Path(path)
    files = ctf_startup_files(data, manifest)
    check_ctf_startup_directory(path, files)
    reused = path.exists()
    if not reused:
        path.mkdir(parents=True)
        for name, payload in files.items():
            with (path / name).open('xb') as out:
                out.write(payload)
        check_ctf_startup_directory(path, files)
    return {'directory': str(path), 'archive': str(path / CTF_STARTUP_ARCHIVE),
            'sha256': hashlib.sha256(data).hexdigest(), 'reused_identical': reused,
            'required_launch_arguments': manifest['required_launch_arguments']}


def recipe(archives, *, caesars=None, dojo=None, stock_map='valley', community=None, community_key=None):
    """Generate bytes in memory. Asset bytes never become part of tool source."""
    for key, expected in HASHES.items():
        if key not in archives or archives[key].sha256 != expected:
            raise RecipeError(f'Unsupported source hash for {key}')
    stock_map = stock_selector(stock_map)
    spec = STOCK_MAPS[stock_map]
    if (community is None) != (community_key is None):
        raise RecipeError('Community conversion requires both original archive and recipe key')
    if sum(item is not None for item in (caesars, dojo, community)) > 1:
        raise RecipeError('Select one custom level')
    if community is not None:
        spec = custom_registry.entries()[custom_registry.select(community_key)]
        if community.sha256 != spec['gob_sha256']:
            raise RecipeError('Unreviewed community GOB hash')
    is_ctf = spec.get('episode_type') == 8
    if is_ctf and ('jkctf' not in archives or archives['jkctf'].sha256 != JKCTF_SHA256):
        raise RecipeError('CTF requires the pinned JK1CTF.GOB')
    if spec.get('requires_jksp'):
        if caesars is not None or dojo is not None:
            raise RecipeError('Select either a stock map or a custom level')
        if 'jksp' not in archives or archives['jksp'].sha256 != JKSP_SHA256:
            raise RecipeError('Battleground Jedi requires the pinned JK1.GOB for original 17a_Stream.cog')
    if caesars is not None and dojo is not None:
        raise RecipeError('Select one custom level')
    custom = caesars if caesars is not None else dojo if dojo is not None else community
    if custom is not None and stock_map != 'valley':
        raise RecipeError('Select either a stock map or a custom level')
    tag = 'caesars' if caesars is not None else 'dojo' if dojo is not None else spec['tag']
    source = Catalog(([(tag, custom)] if custom is not None else []) +
                     ([('jkctf', archives['jkctf'])] if is_ctf else []) +
                     [(key, archives[key]) for key in ('jkmp', 'jkres', 'jksnd')] +
                     ([('jksp', archives['jksp'])] if spec.get('requires_jksp') else []))
    target = Catalog([(key, archives[key]) for key in ('motsmp', 'motsres', 'motssnd')])
    if caesars is not None and caesars.sha256 != CAESARS_GOB_SHA256:
        raise RecipeError('Unsupported Caesar GOB hash')
    caesars_waiver = None
    if caesars is not None:
        audit = audit_caesars(archives, caesars)
        caesars_waiver = audit['reviewed_legacy_omission_waiver']
    if dojo is not None and dojo.sha256 != DOJO_GOB_SHA256:
        raise RecipeError('Unsupported Jedi Dojo GOB hash')
    source_world = spec['world'] if community is not None or custom is None else 'jkl/' + tag + '.jkl'
    original_bytes = custom.read(source_world) if custom else archives[spec.get('archive', 'jkmp')].read(source_world)
    if (custom is None or community is not None) and hashlib.sha256(original_bytes).hexdigest() != spec['sha256']:
        raise RecipeError('Unexpected stock world hash; requires separate semantic review')
    original = text(original_bytes)
    native = text(archives['motsmp'].read('jkl/k1.jkl'))
    if not re.search(r'^Version\s+1\s*$', original, re.I | re.M):
        raise RecipeError('Unsupported source JKL version')
    scripts = {re.sub(r'^\d+:\s*', '', line).lower() for line in records(original, 'scripts')}
    if custom is not None and community is None and scripts != (CAESARS_COGS if caesars else DOJO_COGS):
        raise RecipeError('Unexpected script set; requires separate semantic review')
    if (custom is None or community is not None) and hashlib.sha256('\n'.join(sorted(scripts)).encode()).hexdigest() != spec['scripts_sha256']:
        raise RecipeError('Unexpected stock script set; requires separate semantic review')

    runtime_cogs = {cog for cog in scripts if cog.startswith('pow_') or cog in
                    {'kyle.cog', 'class_sequencer.cog', '00_smoketrail.cog', '00_desttrail.cog'}}
    if community is not None:
        runtime_cogs = set(spec['runtime_cogs'].split()) if isinstance(spec['runtime_cogs'], str) else set(spec['runtime_cogs'])
        for cog, expected in spec.get('cog_sha256', {}).items():
            _, path, archive = source.get(cog)
            if hashlib.sha256(archive.read(path)).hexdigest() != expected:
                raise RecipeError('Unreviewed original COG hash: ' + cog)
    environment_cogs = scripts - runtime_cogs
    if community is not None:
        reviewed = set(spec['environment'].split()) if isinstance(spec['environment'], str) else set(spec['environment'])
        if not environment_cogs <= reviewed:
            raise RecipeError('Unreviewed community environmental COG set')
        environment_cogs = reviewed
    if custom is None and environment_cogs != set(spec['environment'].split()):
        raise RecipeError('Unreviewed stock environmental COG set')
    template_names = {line.split()[0].lower(): spec.get('template_aliases', {}).get(line.split()[0].lower(), 'br_' + line.split()[0].lower())
                      for line in records(original, 'templates')}
    if len(set(template_names.values())) != len(template_names):
        raise RecipeError('Namespaced template aliases collide')

    substitutions = {}
    for cog in sorted(runtime_cogs):
        adapted = cog[:-4] + '_m.cog'
        selected = adapted if adapted in target.by_name else cog
        target.get(selected)
        substitutions[cog] = selected

    # Resolve the complete literal resource graph of this pinned world and its
    # reviewed environmental COGs. Player/pickup/effect COGs remain native MotS.
    pending = deque((source_world, name) for name in sorted(references(original)))
    pending.extend((source_world, Path(rule['source_path']).name) for rule in spec.get('native_resource_overrides', {}).values())
    resources = {}; inventory = []; visited = set(); name_map = dict(substitutions)
    if caesars_waiver:
        name_map.update(caesars_waiver['name_map'])
    accepted_omissions = []
    while pending:
        referrer, name = pending.popleft()
        if name not in source.by_name and name not in substitutions:
            if caesars_waiver and name in caesars_waiver['original_referrers']:
                if referrer not in caesars_waiver['original_referrers'][name]:
                    raise RecipeError('Unreviewed Caesar missing-resource edge: ' + referrer + ' -> ' + name)
                continue
            omission = reviewed_source_omission(name, referrer, source, spec.get('source_omissions', []))
            if community is not None:
                omission['output_name'] = spec.get('resource_aliases', {}).get(name, 'br_' + name)
                omission['output_referrer'] = ('jkl/br_' + tag + '.jkl' if referrer == source_world else
                    referrer.rsplit('/', 1)[0] + '/' + spec.get('resource_aliases', {}).get(Path(referrer).name, 'br_' + Path(referrer).name))
            name_map[name] = omission['output_name']
            if omission not in accepted_omissions:
                accepted_omissions.append(omission)
            continue
        if name in visited or name in substitutions:
            continue
        visited.add(name)
        label, path, archive = source.get(name)
        if name.endswith('.cog') and name not in environment_cogs:
            raise RecipeError(f'Unreviewed source COG: {name}')
        # This authored 29-byte COG name cannot take the normal prefix under the
        # engine's 31-byte limit. Keep a single explicit alias in this pinned map.
        renamed = 'br_sectorliteanimflicker2.cog' if caesars and name == '00_sectorliteanimflicker2.cog' else 'br_' + name
        renamed = spec.get('resource_aliases', {}).get(name, renamed)
        if len(renamed.encode('cp1252')) > 31:
            raise RecipeError(f'Legacy resource identifier would exceed 31 bytes: {renamed}')
        if renamed in name_map.values():
            raise RecipeError('Namespaced resource aliases collide: ' + renamed)
        name_map[name] = renamed
        data = archive.read(path)
        resources[path.rsplit('/', 1)[0] + '/' + renamed] = data
        inventory.append({'source_archive': label, 'source_path': path,
                          'source_sha256': hashlib.sha256(data).hexdigest(),
                          'output_name': renamed})
        if Path(name).suffix in TEXT_EXTENSIONS:
            pending.extend((path, ref) for ref in sorted(references(text(data)) - visited))

    def rename_refs(value):
        return FILE_REF.sub(lambda m: name_map.get(m.group(1).lower(), m.group(1)), value)

    for path, data in list(resources.items()):
        if Path(path).suffix in TEXT_EXTENSIONS:
            original_name = next(item['source_path'].rsplit('/', 1)[-1] for item in inventory if item['output_name'] == Path(path).name)
            transformed_resource = rename_refs(custom_registry.apply_cog_edits(text(data), spec.get('cog_edits', {}).get(original_name, [])))
            if path.endswith('.cog'):
                if is_ctf and Path(path).name == 'br_ctf_main.cog':
                    transformed_resource = adapt_ctf_saber_grants(transformed_resource)
                if caesars and Path(path).name == 'br_caesars_start.cog':
                    transformed_resource = adapt_caesars_start(transformed_resource)
                defaults = re.findall(r'^\s*template\s+\w+\s*=\s*([^\s]+)', active_lines(transformed_resource), flags=re.M | re.I)
                unknown = [name for name in defaults if name.lower() not in template_names and name != '-1']
                if unknown:
                    raise RecipeError(f'Undefined source COG template defaults in {path}: {unknown}')
                transformed_resource = template_defaults(transformed_resource, template_names)
            resources[path] = transformed_resource.encode('cp1252')
    missing_cogs = {name for name in caesars_waiver['name_map'] if name.endswith('.cog')} if caesars_waiver else set()
    missing_cogs.update(item['name'] for item in accepted_omissions if item['name'].endswith('.cog'))
    transformed = rename_refs(rewrite_cog_template_arguments(original, source, template_names,
                                                             missing_cogs=missing_cogs, missing_templates=spec.get('missing_template_arguments', [])) if custom or is_ctf else original)
    transformed, surface_count = expand_surface_lighting(transformed)

    source_templates = records(transformed, 'templates')
    template_names = {line.split()[0].lower(): spec.get('template_aliases', {}).get(line.split()[0].lower(), 'br_' + line.split()[0].lower()) for line in source_templates}
    if any(len(n) > 31 for n in template_names.values()):
        raise RecipeError('Namespaced template exceeds 31 characters')
    new_templates = []
    for line in source_templates:
        words = line.split(None, 2)
        if len(words) < 2:
            raise RecipeError('Malformed template')
        words[0] = template_names[words[0].lower()]
        words[1] = template_names.get(words[1].lower(), words[1])
        if len(words) == 3:
            words[2] = re.sub(r'(?<==)([^\s()]+)', lambda m: template_names.get(m.group(1).lower(), m.group(1)), words[2])
        new_templates.append(' '.join(words))
    transformed, thing_count = convert_things(transformed, template_names)
    native_templates = records(native, 'templates')
    native_templates, native_template_edits = community_runtime.patch_native_templates(
        native_templates, records(original, 'templates'), spec.get('native_template_overrides', {}), name_map)
    transformed = replace_block(transformed, 'templates', native_templates + new_templates)

    # Build native runtime dependencies from templates and the active inventory,
    # excluding K1's unrelated map event scripts and unused preload declarations.
    native_queue = deque(sorted(references('\n'.join(native_templates)) |
                                references(text(archives['motsres'].read('misc/items.dat'))) |
                                set(substitutions.values())))
    native_seen = set()
    native_imports = []
    native_dependency_source = Catalog([('converted', Gob(build_gob(resources)))] +
                                       [(key, archives[key]) for key in ('motsmp', 'motsres', 'motssnd')]) if native_template_edits else target
    while native_queue:
        name = native_queue.popleft()
        if name in native_seen:
            continue
        native_seen.add(name)
        label, path, archive = native_dependency_source.get(name)
        data = archive.read(path)
        if label == 'motsmp':
            resources[path] = data
            native_imports.append({'source_path': path, 'sha256': hashlib.sha256(data).hexdigest()})
        if Path(name).suffix in TEXT_EXTENSIONS:
            native_queue.extend(sorted(references(text(data)) - native_seen))

    # Preserve original numeric table indices, then append native dependencies.
    table_counts = {}
    table_extensions = dict(zip(TABLES, ('.wav', '.mat', '.cmp', '.ai', '.3do',
                                         '.spr', '.key', '.pup', '.snd', '.cog')))
    for label in TABLES:
        old_rows = records(transformed, label)
        indexed = label != 'sounds'
        native_values = [name + (' 1 1' if label == 'materials' else '')
                         for name in sorted(native_seen) if Path(name).suffix == table_extensions[label]]
        next_index = max((int(row.split(':', 1)[0]) + 1 for row in old_rows), default=0) if indexed else len(old_rows)
        rows = old_rows + ([f'{next_index + i}: {row}' for i, row in enumerate(native_values)] if indexed else native_values)
        capacity = next_index + len(native_values)
        transformed = replace_block(transformed, label, rows, capacity)
        table_counts[label] = capacity
    if re.search(r'^Section:\s*ARCHLIGHTING', transformed, re.I | re.M):
        raise RecipeError('Unexpected source archlighting')
    transformed += '\nSection: ARCHLIGHTING\nNum ArchObjects 0\nend\n'
    output_world = 'br_' + tag
    resources['jkl/' + output_world + '.jkl'] = transformed.encode('cp1252')
    episode_title = "Caesar's Palace" if caesars else 'Jedi Dojo by Tee' if dojo else spec.get('episode_title', spec['title'])
    episode_type = spec.get('episode_type', 2) if custom is None or community is not None else 2
    resources['episode.jk'] = (f'"JK {episode_title} - MotS bridge prototype"\nTYPE {episode_type}\nSEQ 1\n10: 1 1 LEVEL {output_world}.jkl 0 0 10 10\nend\n').encode('cp1252')
    stock_title = spec['title']
    if community is not None:
        strings = text(custom.read('misc/cogstrings.uni')) if 'misc/cogstrings.uni' in custom.entries else f'MSGS 1\n"{Path(source_world).stem.upper()}" 0 "{stock_title}"\nEND\n'
        strings = re.sub(r'"' + re.escape(Path(source_world).stem) + r'"', '"BR_' + tag.upper() + '"', strings, flags=re.I)
        resources['misc/cogstrings.uni'] = strings.encode('cp1252')
    else:
        resources['misc/cogstrings.uni'] = (text(custom.read('misc/cogstrings.uni')).replace('"' + tag.upper(), '"BR_' + tag.upper()).encode('cp1252') if custom else f'MSGS 1\n"BR_{tag.upper()}" 0 "{stock_title} (JK bridge prototype)"\nEND\n'.encode('cp1252'))
    if is_ctf:
        strings = text(archives['jkctf'].read('misc/cogstrings.uni'))
        strings = re.sub(r'"' + Path(source_world).stem.upper() + r'"', '"BR_' + tag.upper() + '"', strings)
        resources['misc/cogstrings.uni'] = strings.encode('cp1252')
        resources['misc/items.dat'] = ctf_items_dat(text(archives['motsres'].read('misc/items.dat'))).encode('cp1252')
        for icon in ('icredfl8.bm', 'icredfl16.bm', 'icgoldf8.bm', 'icgoldf16.bm'):
            target.get(icon)  # Runtime derives these names from items.dat.

    # Check output/native literal resource closure, never silently omit misses.
    output = Gob(build_gob(resources))
    available = Catalog([('output', output), ('motsmp', archives['motsmp']),
                         ('motsres', archives['motsres']), ('motssnd', archives['motssnd'])])
    if caesars_waiver:
        unexpected_resolved = set(caesars_waiver['intentionally_absent_names']) & available.by_name.keys()
        if unexpected_resolved:
            raise RecipeError('Original Caesar omissions unexpectedly resolved: ' + ', '.join(sorted(unexpected_resolved)))
    resolved_omissions = {item['output_name'] for item in accepted_omissions} & available.by_name.keys()
    if resolved_omissions:
        raise RecipeError('Reviewed original omissions unexpectedly resolved: ' + ', '.join(sorted(resolved_omissions)))
    missing = []; unexpected_missing = []
    for path in resources:
        if Path(path).suffix in TEXT_EXTENSIONS:
            for ref in references(text(resources[path])):
                if ref not in available.by_name:
                    omission = next((item for item in accepted_omissions
                                     if item['output_referrer'] == path and item['output_name'] == ref), None)
                    item = {'source': path, 'reference': ref}
                    if omission is not None or (caesars_waiver and waived_output_reference(ref, path, caesars_waiver)):
                        item['reviewed_original_omission'] = True
                    else:
                        unexpected_missing.append(item)
                    missing.append(item)
                else:
                    available.get(ref)
    if unexpected_missing:
        raise RecipeError('Output unresolved literal references: ' + json.dumps(unexpected_missing))
    manifest = {'recipe': 'community-' + spec['key'] + '-rc1' if community is not None else 'caesars-original-omissions-v3' if caesars else 'jedi-dojo-v1' if dojo else f'retail-{stock_map}-v1', 'status': 'structurally-built-gameplay-unverified',
                'inputs': {k: {'sha256': a.sha256} for k, a in archives.items()},
                'scene': {'surfaces': surface_count, 'placed_things': thing_count,
                          'native_templates': len(native_templates), 'namespaced_jk_templates': len(new_templates)},
                'tables': table_counts, 'runtime_cog_substitutions': substitutions,
                'native_runtime_dependency_count': len(native_seen),
                'native_episode_resource_imports': native_imports,
                'explicit_behavior_omissions': [],
                'custom_level_input_sha256': custom.sha256 if custom else None,
                'source_resource_graph': sorted(inventory, key=lambda i: i['source_path']),
                'literal_dependencies_unresolved': missing,
                'reviewed_source_omissions': accepted_omissions,
                'reviewed_caesars_legacy_omissions': caesars_waiver,
                'caesars_transforms': ({'weapon_grants': 'One CAESARS_START saber grant10 ->131; original fists1/Bryar2 already ordinal-map to MotS121/122',
                                        'long_cog_alias': '00_sectorliteanimflicker2.cog -> br_sectorliteanimflicker2.cog',
                                        'legacy_omissions': 'Exact eleven original missing names/referrers preserved; no replacement assets'} if caesars else None),
                'stock_world': source_world if custom is None else None,
                'episode_type': episode_type,
                'ctf_transforms': ({'saber_grants': 'Two CTF_MAIN team-entry grants: bin10 ->131',
                                    'team_flag_key_bins': '80-84 unchanged',
                                    'hud': 'Native items.dat bin81 name restored to redflag; mandatory shared startup overlay must load through -path bridge-ctf-ui before inventory initialization. Episode-local copy alone is insufficient.',
                                    'required_startup_overlay': CTF_STARTUP_FOLDER + '/' + CTF_STARTUP_ARCHIVE,
                                    'mode': 'TYPE8 and original CTF scripts/strings/callbacks retained; no KFY script loaded'} if is_ctf else None),
                'limitations': ['OpenMotS gameplay and network behavior require runtime validation.',
                                'Literal filename scanner cannot certify computed COG or template dependencies.',
                                'Native MotS player, weapon, pickup and force semantics are intentional.',
                                'Only the selected hash-pinned map and archive revisions are accepted.'],
                'output': output.inventory()}
    if community is not None:
        manifest['community_source'] = {field: spec[field] for field in ('key', 'title', 'author', 'source_url', 'gob_sha256', 'world', 'sha256')}
        manifest['community_cog_edits'] = spec.get('cog_edits', {})
        manifest['community_notes'] = spec.get('notes', [])
        manifest['native_template_edits'] = native_template_edits
        startup = community_runtime.startup_files(spec, target, source, resources, name_map, rename_refs)
        if startup:
            startup_archive = Gob(startup['data'])
            startup_catalog = Catalog([('startup', startup_archive), ('episode', output)] +
                                      [(key, archives[key]) for key in ('motsmp', 'motsres', 'motssnd')])
            for path in startup_archive.entries:
                if Path(path).suffix in TEXT_EXTENSIONS:
                    for ref in references(text(startup_archive.read(path))):
                        if ref not in startup_catalog.by_name and any(item['output_referrer'] == path and item['output_name'] == ref for item in accepted_omissions):
                            continue
                        startup_catalog.get(ref)
            manifest['required_startup_overlay'] = {key: value for key, value in startup.items() if key != 'data'}
            manifest['required_startup_overlay']['sha256'] = hashlib.sha256(startup['data']).hexdigest()
            # Kept out of serializable reports by the writer. The generated
            # startup GOO is emitted next to the selected episode, never in source.
            manifest['_startup_data'] = startup['data']
    return output.data, manifest


def check_output_path(path):
    path = Path(path)
    if path.exists() or path.with_suffix('.manifest.json').exists():
        raise RecipeError('Output or manifest exists; choose a fresh path: ' + str(path))
    if path.resolve().is_relative_to(Path(__file__).resolve().parent):
        raise RecipeError('Generated game assets must stay outside the source project')


def write_candidate(path, data, manifest):
    manifest = dict(manifest)
    startup_data = manifest.pop('_startup_data', None)
    if startup_data is not None:
        startup = manifest['required_startup_overlay']
        folder = path.parent / startup['folder_name']
        files = {startup['archive_name']: startup_data,
                 'README.txt': (f"Required startup overlay for {manifest['community_source']['title']}.\n"
                                f"Place this folder in the OpenJKDF2 MotS root; launch with -motsCompat -path {folder.name}.\n"
                                "Select the converted episode in Multiplayer. Use this overlay alone.\n"
                                "Restart the game with the matching overlay when changing map families; restart without it for maps that need none.\n"
                                "Every peer must use identical generated episode and startup files.\n").encode('utf-8')}
        if folder.exists():
            if not folder.is_dir() or {p.name for p in folder.iterdir()} != set(files) or any((folder / name).read_bytes() != value for name, value in files.items()):
                raise RecipeError('Existing community startup folder differs from candidate')
        else:
            folder.mkdir(parents=True)
            for name, value in files.items():
                with (folder / name).open('xb') as out:
                    out.write(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as out:
        out.write(data)
    if Gob.open(path).data != data:
        raise ArchiveError('Post-write archive verification failed')
    with path.with_suffix('.manifest.json').open('x', encoding='utf-8') as out:
        json.dump(manifest, out, indent=2)
    return {'output': str(path), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest(), 'scene': manifest['scene'],
            'status': manifest['status']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('list-community', help='List hash-pinned community recipe keys and original sources')
    scan = sub.add_parser('inventory'); scan.add_argument('archive', type=Path)
    startup = sub.add_parser('build-ctf-startup', help='Build the mandatory shared startup overlay for existing CTF episodes')
    startup.add_argument('--mots-root', type=Path, required=True)
    startup.add_argument('--output', type=Path, required=True, help='Output overlay directory; install as bridge-ctf-ui in the runtime')
    for command in ('convert-stock', 'convert-valley', 'convert-battleground', 'convert-caesars', 'convert-dojo', 'audit-caesars', 'convert-community'):
        convert = sub.add_parser(command)
        convert.add_argument('--baselines', type=Path, help='Optional legacy lab layout')
        convert.add_argument('--jk-root', type=Path, help='Owned Jedi Knight installation directory')
        convert.add_argument('--mots-root', type=Path, help='Owned Mysteries of the Sith installation directory')
        if command != 'audit-caesars':
            convert.add_argument('--output', type=Path, required=True)
        if command in ('convert-caesars', 'convert-dojo', 'audit-caesars', 'convert-community'):
            convert.add_argument('--level-archive', type=Path, required=True, help='Original custom level ZIP or GOB')
        if command == 'convert-community':
            convert.add_argument('--map', type=custom_registry.select, required=True, help='Reviewed key from list-community')
        if command == 'convert-stock':
            selection = convert.add_mutually_exclusive_group(required=True)
            selection.add_argument('--map', type=stock_selector,
                                   help='Recipe key, exact title, or source JKL: ' + ', '.join(STOCK_MAPS))
            selection.add_argument('--all', action='store_true',
                                   help='Build every supported stock map; --output names a directory')
    args = parser.parse_args()
    if args.command == 'list-community':
        print(json.dumps([{field: spec[field] for field in ('key', 'title', 'author', 'source_url')}
                          for spec in custom_registry.entries().values()], indent=2)); return
    if args.command == 'inventory':
        print(json.dumps(Gob.open(args.archive).inventory(), indent=2)); return
    if args.command == 'build-ctf-startup':
        archives = {key: Gob.open(args.mots_root / PATHS[key].split('/', 1)[1])
                    for key in ('motsres', 'motssnd')}
        print(json.dumps(write_ctf_startup(args.output, *ctf_startup_candidate(archives)), indent=2)); return
    if args.command == 'audit-caesars':
        print(json.dumps(audit_caesars(pinned_archives(args.baselines, jk_root=args.jk_root, mots_root=args.mots_root), open_caesars(args.level_archive)), indent=2)); return
    if args.command == 'convert-stock':
        selected = list(STOCK_MAPS) if args.all else [args.map]
        paths = [args.output / stock_output_name(key) if args.all else args.output for key in selected]
        for path in paths:
            check_output_path(path)
        archives = pinned_archives(args.baselines, jk_root=args.jk_root, mots_root=args.mots_root,
                                   include_jksp=any(STOCK_MAPS[key].get('requires_jksp') for key in selected),
                                   include_jkctf=any(STOCK_MAPS[key].get('archive') == 'jkctf' for key in selected))
        # Preflight every recipe before writing any candidate. Archive I/O errors
        # can still leave completed files; existing outputs are never overwritten.
        candidates = [recipe(archives, stock_map=key) for key in selected]
        startup_data = None
        if any(STOCK_MAPS[key].get('episode_type') == 8 for key in selected):
            startup_path = (args.output if args.all else args.output.parent) / CTF_STARTUP_FOLDER
            startup_data = ctf_startup_candidate(archives)
            check_ctf_startup_directory(startup_path, ctf_startup_files(*startup_data))
        # Emit mandatory startup assets before the episode archives. A successful
        # CTF conversion therefore always has its shared, verified launch overlay.
        startup_result = write_ctf_startup(startup_path, *startup_data) if startup_data else None
        results = [write_candidate(path, data, manifest)
                   for path, (data, manifest) in zip(paths, candidates)]
        for key, result in zip(selected, results):
            if STOCK_MAPS[key].get('episode_type') == 8:
                result['required_startup_overlay'] = startup_result
        print(json.dumps(results if args.all else results[0], indent=2)); return
    check_output_path(args.output)
    community_spec = custom_registry.entries()[args.map] if args.command == 'convert-community' else None
    data, manifest = recipe(pinned_archives(args.baselines, jk_root=args.jk_root, mots_root=args.mots_root,
                                           include_jksp=args.command == 'convert-battleground' or bool(community_spec and community_spec.get('requires_jksp'))),
                            caesars=open_caesars(args.level_archive) if args.command == 'convert-caesars' else None,
                            dojo=open_dojo(args.level_archive) if args.command == 'convert-dojo' else None,
                            community=custom_registry.open_original(args.level_archive, args.map) if community_spec else None,
                            community_key=args.map if community_spec else None,
                            stock_map='battleground' if args.command == 'convert-battleground' else 'valley')
    print(json.dumps(write_candidate(args.output, data, manifest), indent=2))


if __name__ == '__main__':
    try:
        main()
    except (RecipeError, ArchiveError, OSError, ValueError) as exc:
        import sys
        print(f'error: {exc}', file=sys.stderr)
        raise SystemExit(2)

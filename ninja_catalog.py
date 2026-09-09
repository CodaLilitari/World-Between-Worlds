"""Source-only Ninja Kage metadata and surgical MotS adaptation anchors.

Original mod/assets remain ShadowX and credited contributors' work. The builder
reads user-provided originals; this module contains no original asset payloads.
"""

STATUS = 'prototype'
RECIPE = 'ninja-kage-7.0-mots-mp-prototype-4-maxmana'
PREVIOUS_RUNTIME_TEST = {
    'status': 'bounded-mp-pass',
    'artifact_sha256': '50de33501041102606b5a6f879d61195d55c11898014e22e4d3148fbb133c6df',
    'game': 'MotS', 'mode': 'multiplayer', 'personality': 'Jedi', 'map': 'k1.jkl',
    'peers': 2, 'idle_seconds': 75.094, 'basic_action_seconds': 75.064,
    'grapple_seconds': 75.056, 'descriptor_cog_bindings_checked': 66,
    'effects': ['weapon selection and ammunition/projectile response',
                'authored weapon helper network triggers', 'standing Ninja To attack state',
                'stationary handspring impulse', 'kick activation and punch projectile',
                'live wall-stopped grapple, pull and normal detach'],
    'limits': ['No complete combat, rendering, sound or remote visual equivalence claim.',
               'Single-player and other personalities unreviewed.',
               'Authored Throw/Lightning allocation and activation remain separate conversion gates.'],
}
RUNTIME_TEST = {
    'status': 'bounded-native-initialization-pass',
    'recipe': RECIPE,
    'artifact_sha256': 'f65bded1d3db64602e8cc25a7c96a6e7c2328b2de33bedc7808f27295488806d',
    'game': 'MotS', 'mode': 'multiplayer', 'personality': 'Jedi', 'map': 'k1.jkl',
    'peers': 2, 'idle_seconds': 75.025,
    'initialized_samples': {'host': 37, 'client': 34},
    'observed_amounts': {'rank_bin20': 4, 'current_mana_bin14': 200, 'maximum_mana_bin69': 200},
    'engine': {'kind': 'older-private-diagnostic', 'base_commit': None,
               'exe_sha256': '78c4ac380c55da5c8bf0e36f82c147bdcfef16576a192eb775f2cf4f81006ad0',
               'current_production_positive_rank_validated': False},
    'full_gameplay': False,
    'evidence': {'url': 'https://github.com/andreipemberton/World-Between-Worlds/blob/v0.2.0-rc2/docs/validation/ninja-maxmana-20260908.json',
                 'bundled': False,
                 'sha256': '4fef964e4fc08b71264d88fe10b6023d6efcc6a85aab4d8446c78c1e800453cc'},
    'limits': ['Initialization only, with input disabled and zero allocated powers.',
               'Current e9 production positive-rank initialization remains unverified.',
               'Underfunded casts, regeneration recovery, other ranks and personalities remain unverified.',
               'Throw/Lightning allocation and activation remain separate conversion gates.'],
    'predecessor': PREVIOUS_RUNTIME_TEST,
}
REQUIRED_HUD_ICONS = ('icf_thr8.bm', 'icf_thr16.bm', 'icf_lig8.bm', 'icf_lig16.bm')
NORMALIZED_GOB_SHA256 = 'c9f001461ad37e1f3030b2b2d05db8fa591717880e908089d6932cd2e3e443ee'
NATIVE_UNUSED_TEMPLATE = {
    'path': 'cog/item_heavy_explosive.cog',
    'sha256': 'bd79f7ddbfb7adbd564c4c6538709471fec8f89b7ea0fb87dc459c220acd8aeb',
    'symbol': 'explosive_tpl', 'name': 'EC.3do',
    'reason': 'Pinned native bin53 script declares this missing template but never reads the symbol in code.',
}

SPEC = {'id': 'ninja-kage',
 'title': 'Ninja Kage 7.0',
 'author': 'ShadowX',
 'source_url': 'https://www.massassi.net/levels/files/1333.shtml',
 'download_url': 'https://www.massassi.net/media/levels/files/jkmod/ninjakage_v7.zip',
 'archive_hint': 'ninjakage_v7.zip',
 'zip_sha256': '1d71863e564e75278eecd44244ef3a103692c49b4bf11fdbc2de591ccbf05764',
 'gob_sha256': '23bd8e18eae4df637a34ddf4f98ed3602c490de521e0cc147bf8e79bb9fe23af',
 'gob_member': 'Ninja Kage.gob',
 'readme_member': 'Ninja Kage.txt',
 'readme_sha256': 'de4c8f16f3fe3b48f9b25f582f6760091fd9892e8bdf358145b698b2a270735c',
 'original_member_count': 311,
 'startup_overlay': 'blackwing-ninja-kage',
 'cog_sha256': {'cog/weap_thermdet.cog': 'd110b07df1fee73d64b9d6549654934f6f91962815990b12c88ae5259244bd28',
                'cog/weap_strifle.cog': 'ac76a24e516543475a68e3b560f79ef8bfe3d422c4ea3838160fd7d9a6f0e2fb',
                'cog/weap_saber.cog': 'f4fd0edfd535437624c5f416ad3eee4453c2c65712f49b54f792d4060457a884',
                'cog/weap_fists.cog': '26773a16d4f2b0e43dbf49de211b311faf4bd6b913252769c4cbd0618a527e27',
                'cog/weap_bryar.cog': 'b1f2a61d8e6f657382299d337ed5b4f844eb09c3681883a0972052c58a99b606',
                'cog/pow_thermal.cog': '3de5ac22db9b8c9cc331aca4b7bc80fc65973d1fa60dbadad88a73e24904f775',
                'cog/pow_single_thermal.cog': 'a09fd988eca7b910f107288992e1e933f5173cc49f140f6b212893faaef9dd7d',
                'cog/kyle.cog': '07282d51a984f082a857b5a36d223b4a61594a11d5f5b34b862ed1d60f3fe1b0',
                'cog/kick.cog': '8aaf87edf0f2b76bb9a42e067f4b579128d958e3e99c2fdaae93665063820bcb',
                'cog/jattack.cog': 'c1fc522d9459f12d70565bce3bf21fe1eb0a48a6b536cb181b8a8a1e5a3a0d5c',
                'cog/item_irgoggles.cog': '49b74f5d9361270f6a203be1fd73ba5c567f4bf45fc958ef918df6a6e650c420',
                'cog/item_hook.cog': 'a94c491ff0cab2a971f9afebbb3c0dca5559dddfe05ce799a0cf53411657ccc1',
                'cog/force_well.cog': '04b8567af599b3b7eb92a1b2cc5ec3f0d2a0e11e56dba0137a8779217fcd1830',
                'cog/force_throw.cog': '3f90ec34f453adc99e00ab84b15126e510b24d46fa53294b633dc9fd00e61f2f',
                'cog/force_speed.cog': '7cb377b718f857346cde86657b41fe2ab91a40d597fa73b908aa6927c4a3d4c4',
                'cog/force_seeing.cog': '8b7a4cd496e8b44109aaad1003cf6450005174cdddee8bd4357c909b64c91890',
                'cog/force_push.cog': '04c963b392eb0939936e7b645614511b6e2df1ada6fa12569ebd00be198f972e',
                'cog/force_pull.cog': '1b5a0f45e526fff99103ad0b4a2a450a7004384a95e69ad50ba1a02b5cde2dd9',
                'cog/force_persuasion.cog': '39733cf7d0078f909251abd9ada4a1238dd049973d007988b9b85540b5ba42ac',
                'cog/force_lightning.cog': 'b429cbf59de6c68fd490de4d14040086d31877278cdb9365dfac51e62082c4a8',
                'cog/force_heal.cog': 'ee4fc16a674ebf3519d6a9753838b1d3a774064ea71a66e2c43e74b7f87401e6',
                'cog/force_grip.cog': '8fde515e6164e8b66b2b79b531ee83cb4692ea0eb17fa1bcc96649dde4f48616',
                'cog/force_destruction.cog': 'f66ffba3203a45fb14da5ba36b2a42d6f37e0c50f186784760f98fbb969938b4',
                'cog/client_weapons.cog': '4ec18951ffba210805c391684cb63b5adfecfa964ead0427b2ef256740341822',
                'cog/actor_st.cog': 'f0e352eed06de9a19ad99e063f6cb0e7ec887bd41840f3adc71fd9f3c841abf8',
                'cog/21_endlevel.cog': 'b7df7f9622faf081748e19ed7a7e8fd48d47004e2a221084a89ac1f433c246cd',
                'cog/20_endlevel.cog': 'ac5d1a352b6c8a1dad9c24dbfa440d95ade40ac0392d6d07b0829a05fde80db3',
                'cog/19b_endlevel.cog': '85948303eb7f5f7bd97f5d2b5e7be7b6308558638738a0c7b28c90edfb240310',
                'cog/19a_endlevel.cog': 'f39d5b57152dee052534a23566ec41393f0e5c8367797df59e6a70db56d85815',
                'cog/18_endelev.cog': 'e930041e572a397819041fe1aea24158b6d92254f58f5125eb2ea1630094297b',
                'cog/17a_endlevel.cog': 'f26f30440dff05ca19e1e8c957b0a56215a7e435ce85201570849bb9b4c1a151'}}

# Native MotS descriptor IDs. Weapon selection ordinals remain distinct.
WEAPON_BINS = {0: 120, 1: 121, 2: 122, 3: 123, 4: 124, 5: 135,
               6: 126, 7: 127, 8: 128, 9: 129, 10: 131}
WEAPON_ALIASES = {f'weap_{name}.cog': f'weap_{name}_m.cog'
                  for name in ('fists', 'bryar', 'strifle', 'thermdet', 'saber')}
SCRIPT_ALIASES = {'force_push.cog': 'nk_force_push.cog',
                  'pow_thermal.cog': 'pow_thermal_m.cog',
                  'pow_single_thermal.cog': 'pow_single_thermal_m.cog', **WEAPON_ALIASES}
EXCLUDED_SP_SCRIPTS = ('17a_endlevel.cog', '18_endelev.cog', '19a_endlevel.cog',
                       '19b_endlevel.cog', '20_endlevel.cog', '21_endlevel.cog', 'actor_st.cog')

# Original omissions are retained, never filled with invented substitute assets.
ORIGINAL_MISSING = {
    ('cog/weap_saber.cog', 'arimasen.wav'): 'Original silent mount/dismount/hum resource is absent.',
    ('cog/force_speed.cog', 'arimasen.wav'): 'Original force-speed loop resource is absent.',
    ('cog/weap_bryar.cog', 'shthrow.key'): 'Original shuriken throw keyframe is absent.',
    ('jkl/static.jkl', 'starm.3do'): 'Original +stormlimb1 model is absent; SP dismemberment is outside this prototype.',
}
ORIGINAL_COG_EDITS = {
 'force_well.cog': [{'count': 1,
                     'old': 'startup:\n   player = GetLocalPlayerThing();\n',
                     'new': 'startup:\n   player = GetLocalPlayerThing();\n'
                            '   SetInv(player, 69, GetInv(player, 20) * 50);\n',
                     'reason': 'Initialize native MotS maximum-mana bin69 to the original Ninja '
                               'rank*50 limit. Preserve current mana, rank*2 regeneration each '
                               'second, the original clamp, and all authored power costs.'}],
 'pow_single_thermal.cog': [{'count': 2,
                             'new': 'GetCurWeapon(player) == 11',
                             'old': 'GetCurWeapon(player) == 10',
                             'reason': 'Preserve both auto-pickup and auto-reload saber protection '
                                       'checks using MotS saber ordinal11.'}],
 'pow_thermal.cog': [{'count': 2,
                      'new': 'GetCurWeapon(player) == 11',
                      'old': 'GetCurWeapon(player) == 10',
                      'reason': 'Preserve both auto-pickup and auto-reload saber protection checks '
                                'using MotS saber ordinal11.'},
                     {'count': 1,
                      'new': 'GetWeaponPriority(player, GetWeaponBin(GetCurWeapon(player)), 0)',
                      'old': 'GetWeaponPriority(player, GetCurWeapon(player), 0)',
                      'reason': 'GetWeaponPriority accepts actual bins once ordinal>=11; preserve '
                                'native saber/extra-weapon priority lookup.'}],
 'weap_bryar.cog': [{'count': 1,
                     'new': 'SelectWeapon(player, GetWeaponBin(AutoSelectWeapon(player, 1)));',
                     'old': 'SelectWeapon(player, AutoSelectWeapon(player, 1));',
                     'reason': 'AutoSelectWeapon returns a MotS ordinal; preserve choice but '
                               'translate it before selecting bins beyond the old0..10 '
                               'compatibility range.'}],
 'weap_saber.cog': [{'count': 1,
                     'new': 'SetCurWeapon( player, 131 );',
                     'old': 'SetCurWeapon( player, 10 );',
                     'reason': 'NK sword is native inventory131; raw10 would select native '
                               'EWEB130, and raw11 would address ammo11.'},
                    {'count': 1,
                     'new': 'GetInv(player, 131)',
                     'old': 'GetInv(player, 10)',
                     'reason': 'Read NK sword ownership from native inventory131.'},
                    {'count': 1,
                     'new': 'GetCurWeapon(player) == 11',
                     'old': 'GetCurWeapon(player) == 10',
                     'reason': 'GetCurWeapon returns ordinal11 for native inventory131.'}],
 'weap_strifle.cog': [{'count': 1,
                       'new': 'SelectWeapon(player, GetWeaponBin(AutoSelectWeapon(player, 1)));',
                       'old': 'SelectWeapon(player, AutoSelectWeapon(player, 1));',
                       'reason': 'AutoSelectWeapon returns a MotS ordinal; preserve choice but '
                                 'translate it before selecting bins beyond the old0..10 '
                                 'compatibility range.'}],
 'weap_thermdet.cog': [{'count': 1,
                        'new': 'SelectWeapon(player, GetWeaponBin(AutoSelectWeapon(player, 1)));',
                        'old': 'SelectWeapon(player, AutoSelectWeapon(player, 1));',
                        'reason': 'AutoSelectWeapon returns a MotS ordinal; preserve choice but '
                                  'translate it before selecting bins beyond the old0..10 '
                                  'compatibility range.'}]}
NATIVE_PLAYER_SHA256 = '0513bfc43369262d458f90babbcedb66f6be2f5eecce25c59ecc4f7f298b2f95'
PLAYER_COG_EDITS = [{'old': 'tip_mat=saberorange0.mat',
  'new': 'tip_mat=sabergreen0.mat',
  'count': 1,
  'reason': 'Native startup installs orange saber materials, but the authored NK README specifies '
            'that only its green materials are transparent. Resolve this basename to the authored '
            'NK green material.'},
 {'old': 'side_mat=saberorange1.mat',
  'new': 'side_mat=sabergreen1.mat',
  'count': 1,
  'reason': 'Preserve the authored invisible green energy blade around the modeled Ninja To; '
            'retain the native saber setup dimensions and impact templates.'},
 {'old': '   damage = GetParam(0);',
  'new': '   damage = GetParam(0);\n'
         '\n'
         '   // Ninja Kage: ignore falling damage, as in the authored player script.\n'
         '   if(damageType == 64)\n'
         '   {\n'
         '      ReturnEx(0);\n'
         '      Return;\n'
         '   }',
  'count': 1,
  'reason': 'Preserve Ninja Kage exact damage-type-64 immunity; retain native damage, carbonite, '
            'network and multiplier handling for other types.'},
 {'old': '         force_blinding = 1;',
  'new': '         force_blinding = 0;',
  'count': 1,
  'reason': 'Preserve the sole authored change to the JK blinding receiver. This unusual zero is '
            'inherited behavior, not a new fix.'},
 {'old': '   if(GetInv(player, 60) < 100) SetInv(player, 60, 100);',
  'new': '   if(GetInv(player, 60) < 100) SetInv(player, 60, 200);',
  'count': 1,
  'reason': 'Preserve authored minimum shield initialization: below 100 becomes 200.'},
 {'old': '   SetInv(player, 121, 1.0);\n   SetInv(player, 122, 1.0);\n   SetInv(player, 131, 1.0);',
  'new': '   SetInv(player, 121, 1.0);\n'
         '   SetInv(player, 122, 1.0);\n'
         '   SetInv(player, 123, 1.0);\n'
         '   SetInv(player, 124, 50.0);\n'
         '   SetInv(player, 131, 1.0);',
  'count': 1,
  'reason': 'Preserve authored fists, shuriken, caltrops, 50 kunai and Ninja To grants using '
            'native weapon bins.'},
 {'old': '   if(GetInv(player, 11) < 50) SetInv(player, 11, 50.0);',
  'new': '   if(GetInv(player, 11) < 75) SetInv(player, 11, 75.0);',
  'count': 1,
  'reason': 'Preserve minimum 75 metal alloy ammo; bin 11 is ammo and must not become a weapon '
            'bin.'},
 {'old': '   // IR Goggles\n'
         '   if(GetInv(player, 41))\n'
         '      SetInvAvailable(player, 41, 1);\n'
         '   else\n'
         '      SetInvAvailable(player, 41, 0);\n'
         '   SetInvActivated(player, 41, 0);',
  'new': '   // Ninja Kage gives IR goggles at every initialization.\n'
         '   SetInv(player, 41, 1);\n'
         '   SetInvAvailable(player, 41, 1);\n'
         '   SetInvActivated(player, 41, 0);',
  'count': 1,
  'reason': 'Preserve authored unconditional goggles grant and availability, with explicit '
            'equivalent control flow.'},
 {'old': '   jkEndTarget();',
  'new': '   // Ninja Kage wall-stick physics attribute.\n'
         '   SetPhysicsFlags(player, 0x80);\n'
         '\n'
         '   jkEndTarget();',
  'count': 1,
  'reason': 'Preserve authored player wall-stick attribute; native enum 0x80 is WALLSTICK, not '
            'flight.'},
 {'old': '   // Make these available if they were initialized to non-zero',
  'new': '   // Ninja Kage authored MP loadout, after native parameter initialization.\n'
         '   // Keep native additional weapon definitions, timers and network behavior.\n'
         '   for (i = 122; i <= 140; i = i + 1)\n'
         '      SetInv(player, i, 0);\n'
         '   SetInv(player, 121, 1.0);\n'
         '   SetInv(player, 122, 1.0);\n'
         '   SetInv(player, 123, 1.0);\n'
         '   SetInv(player, 124, 50.0);\n'
         '   SetInv(player, 131, 1.0);\n'
         '   SetInv(player, 11, 75.0);\n'
         '   SetInv(player, 12, 0.0);\n'
         '   SetInv(player, 15, 10.0);\n'
         '   SetInv(player, 40, 0);\n'
         '   SetInvAvailable(player, 40, 0);\n'
         '   SetInv(player, 41, 1);\n'
         '   SetInvAvailable(player, 41, 1);\n'
         '   SetInv(player, 60, 200);\n'
         '\n'
         '   // Make these available if they were initialized to non-zero',
  'count': 1,
  'reason': 'Ensure native spawn parameters do not erase the authored MP kit. Extra native weapons '
            'remain defined and usable when picked up; no stock spawn weapon silently replaces NK '
            'kit.'},
 {'old': '   SelectWeapon(player, jkGetMultiParam(1));\n'
         '   SetCurInvWeapon(player, jkGetMultiParam(1));',
  'new': '   primaryWeapon = GetWeaponBin(AutoSelectWeapon(player, 1));\n'
         '   SelectWeapon(player, primaryWeapon);\n'
         '   SetCurInvWeapon(player, primaryWeapon);',
  'count': 1,
  'reason': 'Preserve NK automatic spawn selection using authored priorities while translating the '
            'returned MotS ordinal into a real inventory bin. Reuse native unused primaryWeapon '
            'local.'},
 {'old': '   SetTimerEx(0.5, 2001, jkGetMultiParam(1), 0);',
  'new': '   SetTimerEx(0.5, 2001, primaryWeapon, 0);',
  'count': 1,
  'reason': 'Retain native delayed weapon-mount repair with the same selected NK inventory bin.'},
 {'old': '      curWeapon = GetCurWeapon(player);',
  'new': '      curWeapon = GetCurWeapon(player);\n'
         '\n'
         '      // Bound the native 21-entry pickup array; retain NK saber immunity.\n'
         '      if((curWeapon <= 0) || (curWeapon > 20) || (curWeapon == 5) || (curWeapon == 11)) '
         'Return;',
  'count': 1,
  'reason': 'Avoid an invalid ordinal indexing contiguous tpl[0..20], exclude undefined native '
            'placeholder 5, and preserve NK always-unpullable Ninja To. Keep native '
            'extra-weapon/EWEB/scope handling.'}]

KNOWN_GAPS = [
    'V4 maximum-mana initialization passed a 75.025-second rank 4 two-peer idle test on the older pinned diagnostic; current e9 positive-rank initialization, underfunded casts and regeneration recovery remain unverified. V3 action/grapple evidence is a separate predecessor record.',
    'This prototype targets a fresh Jedi multiplayer character; other personalities and single-player are unreviewed.',
    'Original Force Throw/bin30 and Lightning/bin32 have descriptors and hotkeys, but native MotS allocation/cycling excludes them.',
    'Native Restore Defaults assumes 20 hotkeys; explicitly bind F2 Field Light/ACTIVATE21, F3 IR Goggles/ACTIVATE20 and F4 Bacta/ACTIVATE19 for this 25-action mod.',
    'Original missing sounds/keyframe/model remain absent; no replacement artwork or audio is fabricated.',
    'Original caltrop script uses assignment where comparison appears intended in its one/two-ammo branches; behavior remains to be tested.',
    'Do not combine this startup mod with SBX, Manowars, other startup overlays, or independently modified inventory tables.',
    'Per-map template behavior, combat, sound, animations, remote replication and visuals remain unverified.',
    'The authored global +sspks_blood template overrides same-named native map blood effects, as a full-mod gore change.',
]

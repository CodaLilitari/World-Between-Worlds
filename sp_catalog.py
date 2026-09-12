"""Explicit source-locked SP pilots; no game assets are embedded."""

RECIPES = {'sp-phantom-menace-final-battle': {'entry': {'id': 'sp-phantom-menace-final-battle',
                                              'title': 'The Phantom Menace: Final Battle (Revised)',
                                              'author': 'Darth Maul',
                                              'kind': 'custom',
                                              'gameplay': ['sp'],
                                              'status': 'prototype',
                                              'source_url': 'https://www.massassi.net/levels/files/23.shtml',
                                              'revision': 1,
                                              'requires_archive': True,
                                              'archive_hint': 'ep1end.zip',
                                              'summary': 'Experimental complete single-player episode: '
                                                         'authored duel, ally, AI and scripted scenes '
                                                         'retained; full gameplay validation pending.',
                                              'startup_overlay': None,
                                              'runtime_test': {'status': 'bounded-load-smoke-pass',
                                                               'seconds': 45,
                                                               'mode': 'MotS singleplayer',
                                                               'full_gameplay': False},
                                              'legacy_filenames': ['wbw-sp-ep1final.goo'],
                                              'required_owned_archives': ['jksp', 'motssp']},
                                    'zip_sha256': '1e9bb4ec7ffef3e122c431a824af772815958788a05818136b1f576bf06a3b0d',
                                    'archives': [{'member': 'ep1end.gob',
                                                  'sha256': '061db9c426368b5ebb1c9513f8161ca7b2c3f3a7666af4e16a68246a32d09c4d',
                                                  'role': 'episode'}],
                                    'readmes': [{'path': 'ep1end_auth.txt',
                                                 'bytes': 4745,
                                                 'sha256': 'd0174f127a2592242e9e462c753d9b3928cb0f741c7bbdd40586a2232536ad71'}],
                                    'worlds': {'jkl/untitled.jkl': 'b36a150bfec5a2260376d54f401e4701ed3b229c64a3b9e87a5636654d9064b0'},
                                    'episode_rows': [['10:',
                                                      '1',
                                                      '1',
                                                      'LEVEL',
                                                      'Untitled.jkl',
                                                      '0',
                                                      '0',
                                                      '-1',
                                                      '-1']],
                                    'native_world': 'jkl/s1l1_rebelbase.jkl',
                                    'owned_hashes': {'jkres': 'c75f7d5211bdd2e07a3af6a987c718037e8f0fd6909018ddb4327137bf3a7ebf',
                                                     'jksnd': '6c6d51eca9c85dffe7dce9b449642a052f055352e3f817abf03b465da861aafd',
                                                     'jksp': '41591e570d5a2173873465e4c061e61edb5efea9883533ed70d78b3a81a10e46',
                                                     'motsres': 'fa615eafa30114afd5e38369d790e721df56ce9a4ef62b66f34fc41b7c048a12',
                                                     'motssnd': 'b80029082c93c7c47fd886ab659f41b5318fed1fa34b173cf5fd1bb7226d3462',
                                                     'motssp': '08e5717915c8fc37bab80b8ffd5e7e1fb0ff2817fe48cb151884c5bf8639a66a'},
                                    'native_cog_bindings': {'00_desttrail.cog': '00_desttrail.cog',
                                                            '00_smoketrail.cog': '00_smoketrail.cog',
                                                            'class_sequencer.cog': 'class_sequencer.cog',
                                                            'kyle.cog': 'kyle_m.cog',
                                                            'pow_backpack.cog': 'pow_backpack_m.cog',
                                                            'pow_bryar.cog': 'pow_bryar_m.cog',
                                                            'pow_concrifle.cog': 'pow_concrifle_m.cog',
                                                            'pow_crossbow.cog': 'pow_crossbow_m.cog',
                                                            'pow_railgun.cog': 'pow_railgun_m.cog',
                                                            'pow_repeater.cog': 'pow_repeater_m.cog',
                                                            'pow_single_sequencer.cog': 'pow_single_sequencer_m.cog',
                                                            'pow_single_thermal.cog': 'pow_single_thermal_m.cog',
                                                            'pow_strifle.cog': 'pow_strifle_m.cog'},
                                    'native_binding_source_sha256': {'pow_single_sequencer.cog': '2777cacb7aceff81128cbf8b432cda15a32557f716cabe2ff6111183c79b965e',
                                                                     'pow_backpack.cog': '7bacc8efb06a8d6b71ab3780f2ab6302ad1c63d245bd9524c0b89258053b08ed',
                                                                     'pow_repeater.cog': '83505b4b4620ce33e494caab76769e59a9ececceaeef161122ab64dc3861feb6',
                                                                     '00_smoketrail.cog': '2a990da3d41131bca2d1481562592742e5f8c543ac846dd95311a361189c7bbf',
                                                                     'pow_strifle.cog': 'edddcde2521e57fcf7d3c8c6e83ec25b7085d6230c4e09cf1387091f08697a73',
                                                                     '00_desttrail.cog': '6c56bf2f756cd63625443d5fa76f8d72521c1f19ed9b61a7ce6252b1ecc00c48',
                                                                     'class_sequencer.cog': '7a057711f1e6fb33e1a7b410d657738531c5b6664af3259dad3ab16c4b30cae5',
                                                                     'pow_crossbow.cog': 'e5dfce5f5f394b670ac2a7a9d2c569085127b1857bc52b3859475ae10b285f85',
                                                                     'pow_railgun.cog': '4dd2252dde766ad47c9e89a1bb59e009431c7c3838e98cd703bbc4332a5d26bc',
                                                                     'pow_concrifle.cog': 'a762451646e8598bc64afc70c6ef5054e434dda6da5a4d5f735c13fef00de011',
                                                                     'kyle.cog': 'cf68cc4754acd78d2d84297eb6d05df80d0e8e265fa5d5a902b7101f8e523955',
                                                                     'pow_single_thermal.cog': 'fbf8c39c853bf5e9a60cf3016bba7a39936c136552ce094b80c872d205c811cf',
                                                                     'pow_bryar.cog': 'd533156b8283c2c21f44355f7146192df873f5806499cc57fb9fbfa838a2a169'},
                                    'source_cog_sha256': {'00_deathfloor2.cog': '5c117e1dfc723e45c02eff4e7fb854577c210e95f423bc3fc1ae0af0686f310b',
                                                          '03_aiturnenemy.cog': '6a5c57a3757158d34562aaff03ece779a0389d802189048d8ac8acd653fcbc64',
                                                          '03_aiturnplay.cog': '73a45e12fb234aa40af20d17b664749afdd424268454dbb748d006bd2542b2bf',
                                                          'darkjedi_maul.cog': 'b4a8cb999c69cd61eb890dc68c55c23b9ea03f611baf90da52a09e93a1134219',
                                                          'darkjedi_quigonjinn.cog': '54f5a21094b38c06d73b2578f7b3c8223340ac9aea641595a4b1277672edd8c1',
                                                          'duel_intro.cog': 'a1a739648d3694e26986768c7c4ff0935d5dcecf4899463af19ad8001a97786d',
                                                          'hhpyaaaaaak.cog': 'acec962645aee7ef2108f09af5dbb59053b51408c718ab24caa825165dbc4d14',
                                                          'testtest.cog': '078b4613eb7402167655ab538422f83a5335858a8e25918ee0a1f92c83115bf4',
                                                          'untitled_start.cog': '59672f6d5c3721aee5d55ffea167fb349d8786bf9fd4fb77ccf6ec4c107fadab',
                                                          'usuckhenry1.cog': '378b5ef68117cf5606699ce9b333f415b3b272eec4beed3c41c0abf910f7ca27',
                                                          'usuckhenry2.cog': '2979e3568c56b71414b2c9bfdff6313b907c7c085b8308746279cca09fbe2c04'},
                                    'verbatim_paths': ['misc/cogstrings.uni'],
                                    'output_filename': 'wbw-sp-ep1final.goo',
                                    'cog_edits': {'untitled_start.cog': [{'old': 'SetInv(player, 10, 1);',
                                                                          'new': 'SetInv(player, 131, 1);',
                                                                          'count': 1,
                                                                          'reason': 'Grant native MotS saber '
                                                                                    'descriptor131; preserve '
                                                                                    'authored saber-only '
                                                                                    'start.'}],
                                                  'darkjedi_maul.cog': [{'old': '(GetCurWeapon(victim) != '
                                                                                '10)',
                                                                         'new': '(GetCurWeapon(victim) != '
                                                                                '11)',
                                                                         'count': 1,
                                                                         'reason': 'Native MotS saber is '
                                                                                   'weapon ordinal11; '
                                                                                   'preserve saber exclusion '
                                                                                   'from Force Pull.'}],
                                                  'darkjedi_quigonjinn.cog': [{'old': '(GetCurWeapon(victim) '
                                                                                      '!= 10)',
                                                                               'new': '(GetCurWeapon(victim) '
                                                                                      '!= 11)',
                                                                               'count': 1,
                                                                               'reason': 'Native MotS saber '
                                                                                         'is weapon '
                                                                                         'ordinal11; '
                                                                                         'preserve saber '
                                                                                         'exclusion from '
                                                                                         'Force Pull.'}]},
                                    'readme_source_defects': ['Ally falling can suppress a scripted message.',
                                                              'Rare boss falling can make original '
                                                              'completion impossible.'],
                                    'native_template_omissions': {'cog/item_heavy_explosive.cog': {'sha256': 'bd79f7ddbfb7adbd564c4c6538709471fec8f89b7ea0fb87dc459c220acd8aeb',
                                                                                                   'name': 'ec.3do',
                                                                                                   'reason': 'Native '
                                                                                                             'original '
                                                                                                             'declares '
                                                                                                             'an '
                                                                                                             'unused '
                                                                                                             'explosive_tpl '
                                                                                                             'template '
                                                                                                             'whose '
                                                                                                             'value '
                                                                                                             'is '
                                                                                                             'a '
                                                                                                             'model '
                                                                                                             'filename; '
                                                                                                             'symbol '
                                                                                                             'never '
                                                                                                             'read '
                                                                                                             'by '
                                                                                                             'code. '
                                                                                                             'Preserve '
                                                                                                             'exact '
                                                                                                             'native '
                                                                                                             'script.'}}},
 'sp-maul-vs-qui-gon': {'entry': {'id': 'sp-maul-vs-qui-gon',
                                  'title': 'Legends of the Force: Darth Maul vs. Qui-Gon Jinn',
                                  'author': 'BoBo Fett',
                                  'kind': 'custom',
                                  'gameplay': ['sp'],
                                  'status': 'prototype',
                                  'source_url': 'https://www.massassi.net/levels/files/26.shtml',
                                  'revision': 1,
                                  'requires_archive': True,
                                  'archive_hint': 'MaulJinn.zip',
                                  'summary': 'Experimental complete single-player duel: Qui-Gon player, '
                                             'double-bladed Maul, landing sequence and Force grants '
                                             'retained; full gameplay validation pending.',
                                  'startup_overlay': None,
                                  'runtime_test': {'status': 'bounded-load-smoke-pass',
                                                   'seconds': 30,
                                                   'mode': 'MotS singleplayer',
                                                   'full_gameplay': False},
                                  'legacy_filenames': ['wbw-sp-mauljinn.goo'],
                                  'required_owned_archives': ['jksp', 'motssp'],
                                  'massassi_id': 26},
                        'zip_sha256': '61ed86d2ba4c0ea5bb2fdd7f2eae5e9459618ce4550d7debb8d8f6424559942e',
                        'archives': [{'member': 'MaulJinn.gob',
                                      'sha256': '868524accb6f1b7e73f46761705da71673520d8989406591b4d5d5e845bc79fc',
                                      'role': 'episode'}],
                        'readmes': [{'path': 'MaulJinn.txt',
                                     'bytes': 5825,
                                     'sha256': '970b4d25a17e12a8d3d1ba831551afd64d8aa6ca85375e853ae10df8346ca3bc'}],
                        'worlds': {'jkl/zela_duel.jkl': '4d5909a7ff3e21319b4bd7c6df20778b18b3c58eaa5bc51be22176b90b3519f7'},
                        'episode_rows': [['11:', '1', '2', 'LEVEL', 'zela_duel.jkl', '21', '31', '-1', '-1']],
                        'native_world': 'jkl/s1l1_rebelbase.jkl',
                        'owned_hashes': {'jkres': 'c75f7d5211bdd2e07a3af6a987c718037e8f0fd6909018ddb4327137bf3a7ebf',
                                         'jksnd': '6c6d51eca9c85dffe7dce9b449642a052f055352e3f817abf03b465da861aafd',
                                         'jksp': '41591e570d5a2173873465e4c061e61edb5efea9883533ed70d78b3a81a10e46',
                                         'motsres': 'fa615eafa30114afd5e38369d790e721df56ce9a4ef62b66f34fc41b7c048a12',
                                         'motssnd': 'b80029082c93c7c47fd886ab659f41b5318fed1fa34b173cf5fd1bb7226d3462',
                                         'motssp': '08e5717915c8fc37bab80b8ffd5e7e1fb0ff2817fe48cb151884c5bf8639a66a'},
                        'native_cog_bindings': {'00_desttrail.cog': '00_desttrail.cog',
                                                '00_smoketrail.cog': '00_smoketrail.cog',
                                                'class_sequencer.cog': 'class_sequencer.cog',
                                                'kyle.cog': 'kyle_m.cog',
                                                'pow_backpack.cog': 'pow_backpack_m.cog',
                                                'pow_bryar.cog': 'pow_bryar_m.cog',
                                                'pow_concrifle.cog': 'pow_concrifle_m.cog',
                                                'pow_crossbow.cog': 'pow_crossbow_m.cog',
                                                'pow_railgun.cog': 'pow_railgun_m.cog',
                                                'pow_repeater.cog': 'pow_repeater_m.cog',
                                                'pow_single_sequencer.cog': 'pow_single_sequencer_m.cog',
                                                'pow_single_thermal.cog': 'pow_single_thermal_m.cog',
                                                'pow_strifle.cog': 'pow_strifle_m.cog',
                                                'pow_mana.cog': 'pow_mana.cog',
                                                'pow_power.cog': 'pow_power_m.cog',
                                                'pow_bacta.cog': 'pow_bacta.cog',
                                                'pow_battery.cog': 'pow_battery_m.cog',
                                                'pow_health.cog': 'pow_health.cog',
                                                'pow_shields.cog': 'pow_shields.cog'},
                        'native_binding_source_sha256': {'00_desttrail.cog': '6c56bf2f756cd63625443d5fa76f8d72521c1f19ed9b61a7ce6252b1ecc00c48',
                                                         '00_smoketrail.cog': '2a990da3d41131bca2d1481562592742e5f8c543ac846dd95311a361189c7bbf',
                                                         'class_sequencer.cog': '7a057711f1e6fb33e1a7b410d657738531c5b6664af3259dad3ab16c4b30cae5',
                                                         'kyle.cog': 'cf68cc4754acd78d2d84297eb6d05df80d0e8e265fa5d5a902b7101f8e523955',
                                                         'pow_backpack.cog': '7bacc8efb06a8d6b71ab3780f2ab6302ad1c63d245bd9524c0b89258053b08ed',
                                                         'pow_bryar.cog': 'd533156b8283c2c21f44355f7146192df873f5806499cc57fb9fbfa838a2a169',
                                                         'pow_concrifle.cog': 'a762451646e8598bc64afc70c6ef5054e434dda6da5a4d5f735c13fef00de011',
                                                         'pow_crossbow.cog': 'e5dfce5f5f394b670ac2a7a9d2c569085127b1857bc52b3859475ae10b285f85',
                                                         'pow_railgun.cog': '4dd2252dde766ad47c9e89a1bb59e009431c7c3838e98cd703bbc4332a5d26bc',
                                                         'pow_repeater.cog': '83505b4b4620ce33e494caab76769e59a9ececceaeef161122ab64dc3861feb6',
                                                         'pow_single_sequencer.cog': '2777cacb7aceff81128cbf8b432cda15a32557f716cabe2ff6111183c79b965e',
                                                         'pow_single_thermal.cog': 'fbf8c39c853bf5e9a60cf3016bba7a39936c136552ce094b80c872d205c811cf',
                                                         'pow_strifle.cog': 'edddcde2521e57fcf7d3c8c6e83ec25b7085d6230c4e09cf1387091f08697a73',
                                                         'pow_mana.cog': 'f7253958c01e90bfc99d162ec0af0c2cc819e561c817165bcf434dadb776a30a',
                                                         'pow_power.cog': '073756cb1b74cc2f84393215297cbd6f5e739d15972c283afcccd2130ebb5061',
                                                         'pow_bacta.cog': '8b420d7556d92a9f2bcfbb99aeac690e85d7beb54baa7f7e7321f4121b090d56',
                                                         'pow_battery.cog': 'd5580c827623ee20f6ef0e235c4b9f1dccff38a0ed4a50bb77392d59fbd4e9eb',
                                                         'pow_health.cog': '764f213b0dfb0623fecef59f46850fc37c5a0e4e0599f15411d35ee4b6ffb011',
                                                         'pow_shields.cog': '8d515630da6ac31126decd4ca8c94ef840c42edc1110ef102e5f48530d88e8ad'},
                        'source_cog_sha256': {'actor_r5.cog': '951038f3cc815d72725b4ec01ad0c125ae4d5aaee09e73695c65193ccca1d174',
                                              'duel_control.cog': '04c90df598725e425fe88cfe6eda3256a4d4360643d22326bf4ed5a2176cc726',
                                              'duel_start.cog': 'f89d9dd1463f32d315d229f3df7fec53188cee2ba91096bb2d53de3a3a1fde00',
                                              'darkjedi_maul.cog': '5c07ac4bffb3ace79120ebdb190ecfdcfc2b6da62437d35f3302ae54bd3a5676',
                                              'duel_intro.cog': '1dffc2697dfb3f3588642e99184e1e79c5e062dd1653e9f7194ccf41e9ecf515',
                                              'actor_r2.cog': '3075923b616221e6ec03a5f6665626d7da821519cd58042b4175694e74665829'},
                        'verbatim_paths': ['misc/cogstrings.uni'],
                        'output_filename': 'wbw-sp-mauljinn.goo',
                        'cog_edits': {'duel_start.cog': [{'old': 'SetInv(player, 10, 1);',
                                                          'new': 'SetInv(player, 131, 1);',
                                                          'count': 1,
                                                          'reason': 'Native MotS saber descriptor is131; '
                                                                    'source10 otherwise selects EWEB.'}],
                                      'darkjedi_maul.cog': [{'old': '(GetCurWeapon(victim) != 10)',
                                                             'new': '(GetCurWeapon(victim) != 11)',
                                                             'count': 1,
                                                             'reason': 'Native MotS saber ordinal is11; '
                                                                       'preserve authored exclusion from '
                                                                       'Force Pull.'}]},
                        'readme_source_defects': [],
                        'native_template_omissions': {'cog/item_heavy_explosive.cog': {'sha256': 'bd79f7ddbfb7adbd564c4c6538709471fec8f89b7ea0fb87dc459c220acd8aeb',
                                                                                       'name': 'ec.3do',
                                                                                       'reason': 'Native '
                                                                                                 'original '
                                                                                                 'declares '
                                                                                                 'an unused '
                                                                                                 'explosive_tpl '
                                                                                                 'template '
                                                                                                 'whose '
                                                                                                 'value is a '
                                                                                                 'model '
                                                                                                 'filename; '
                                                                                                 'symbol '
                                                                                                 'never read '
                                                                                                 'by code. '
                                                                                                 'Preserve '
                                                                                                 'exact '
                                                                                                 'native '
                                                                                                 'script.'}},
                        'semantic_notes': ['Source rank7/current mana200 and Force grants21,22,24,27,31 '
                                           'remain unchanged; native SP cap follows rank*50.',
                                           'SetInv/ChangeInv map ordinary weapon ordinals below11 to native '
                                           'descriptors in the MotS engine; no redundant numeric rewrites.',
                                           'Original player model/maxhealth150, enemy saber flags0x5/0x15, '
                                           'antigravity logic, landing cutscene and autosave retained.',
                                           'Source episode row11 has original level number2 and progression '
                                           'grants21/31; entire row retained.',
                                           'Native mana boost uses the SP rank cap and50-mana grant; no MP '
                                           'bin69 override.']}}

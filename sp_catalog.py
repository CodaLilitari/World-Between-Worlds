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

# Exact original and retail pins; no authored asset payloads.
RECIPES['sp-imperial-pumping-station'] = {'entry': {'id': 'sp-imperial-pumping-station',
           'title': 'Imperial Pumping Station',
           'author': 'Mike Hamilton (Mangore Kiramin)',
           'kind': 'custom',
           'gameplay': ['sp'],
           'status': 'prototype',
           'source_url': 'https://www.massassi.net/levels/files/1366.shtml',
           'revision': 1,
           'requires_archive': True,
           'archive_hint': 'mk_ips.zip',
           'summary': 'Experimental Corbit infiltration mission with authored pumps, reactor '
                      'objectives and escape sequence retained; full gameplay validation pending.',
           'startup_overlay': None,
           'runtime_test': {'status': 'bounded-load-smoke-pass',
                            'mode': 'MotS singleplayer',
                            'seconds': 90,
                            'full_gameplay': False,
                            'world': 'mk_ips.jkl',
                            'engine_sha256': 'fd8ddfc23f09540068318bedcc3f08e5ce6b12ea5ee04ed3cf45fd8ed46b7873',
                            'payload_sha256': 'b25f60de9c1d337a85416100cc61fb8c27e0bca8966f045867f689cc4763e30b',
                            'evidence_report_sha256': '6a2bdeb9ae9b040b8a5f82bba723e3fdadbe3556e18a3454f80db3ae7109af8a',
                            'note': 'Loading and advancing simulation; authored camera, pumps, '
                                    'goals and escape require gameplay testing.'},
           'legacy_filenames': ['wbw-sp-pumping-station.goo'],
           'required_owned_archives': ['jksp', 'motssp'],
           'massassi_id': 1366},
 'zip_sha256': 'bf5a4ba8fff45e6b1efcee887fa5db56571380c730ca791347e03cfd0b5d2e04',
 'archives': [{'member': 'mk_ips.gob',
               'sha256': '995137bbeea54f0f79daa542e960355e365dafb24433c930a4bbb110e9e11126',
               'role': 'episode'}],
 'readmes': [{'path': 'mk_ips.txt',
              'bytes': 5004,
              'sha256': 'b980ce6ba31f4cc71f4e1f20018dc6f365b79ae543ee5d1a803cc8b49f47bc8b'}],
 'worlds': {'jkl/mk_ips.jkl': 'dce8aeac74eaa1d05df3002ced4af83461266f6e6580db97f68dbc5179fff301'},
 'episode_rows': [['10:', '1', '1', 'LEVEL', 'mk_ips.jkl', '0', '0', '-1', '-1']],
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
                         'pow_bacta.cog': 'pow_bacta.cog',
                         'pow_battery.cog': 'pow_battery_m.cog',
                         'pow_bryar.cog': 'pow_bryar_m.cog',
                         'pow_concrifle.cog': 'pow_concrifle_m.cog',
                         'pow_crossbow.cog': 'pow_crossbow_m.cog',
                         'pow_drailgun.cog': 'pow_drailgun_m.cog',
                         'pow_drepeater.cog': 'pow_drepeater_m.cog',
                         'pow_dstrifle.cog': 'pow_dstrifle_m.cog',
                         'pow_energy.cog': 'pow_energy_m.cog',
                         'pow_health.cog': 'pow_health.cog',
                         'pow_power.cog': 'pow_power_m.cog',
                         'pow_railcharges.cog': 'pow_railcharges_m.cog',
                         'pow_railgun.cog': 'pow_railgun_m.cog',
                         'pow_repeater.cog': 'pow_repeater_m.cog',
                         'pow_revive.cog': 'pow_revive.cog',
                         'pow_sequencer.cog': 'pow_sequencer_m.cog',
                         'pow_shields.cog': 'pow_shields.cog',
                         'pow_single_sequencer.cog': 'pow_single_sequencer_m.cog',
                         'pow_single_thermal.cog': 'pow_single_thermal_m.cog',
                         'pow_smbkpk.cog': 'pow_smbkpk_m.cog',
                         'pow_strifle.cog': 'pow_strifle_m.cog',
                         'pow_thermal.cog': 'pow_thermal_m.cog',
                         'pow_vest.cog': 'pow_vest.cog'},
 'native_binding_source_sha256': {'00_desttrail.cog': '6c56bf2f756cd63625443d5fa76f8d72521c1f19ed9b61a7ce6252b1ecc00c48',
                                  '00_smoketrail.cog': '2a990da3d41131bca2d1481562592742e5f8c543ac846dd95311a361189c7bbf',
                                  'class_sequencer.cog': '7a057711f1e6fb33e1a7b410d657738531c5b6664af3259dad3ab16c4b30cae5',
                                  'kyle.cog': 'cf68cc4754acd78d2d84297eb6d05df80d0e8e265fa5d5a902b7101f8e523955',
                                  'pow_backpack.cog': '7bacc8efb06a8d6b71ab3780f2ab6302ad1c63d245bd9524c0b89258053b08ed',
                                  'pow_bacta.cog': '8b420d7556d92a9f2bcfbb99aeac690e85d7beb54baa7f7e7321f4121b090d56',
                                  'pow_battery.cog': 'd5580c827623ee20f6ef0e235c4b9f1dccff38a0ed4a50bb77392d59fbd4e9eb',
                                  'pow_bryar.cog': 'd533156b8283c2c21f44355f7146192df873f5806499cc57fb9fbfa838a2a169',
                                  'pow_concrifle.cog': 'a762451646e8598bc64afc70c6ef5054e434dda6da5a4d5f735c13fef00de011',
                                  'pow_crossbow.cog': 'e5dfce5f5f394b670ac2a7a9d2c569085127b1857bc52b3859475ae10b285f85',
                                  'pow_drailgun.cog': '2812ae55d215dde58d7551a844c0bb4c09a93f446579bb41a7022dcabc2ec166',
                                  'pow_drepeater.cog': '95eafcf256cbe99aa92df0cc668490ccc41988caed79871532a290935e6ffc87',
                                  'pow_dstrifle.cog': '483513c35d918b1344e558f4da3adf5d67f13ec5382f010686a3fe455e2088b2',
                                  'pow_energy.cog': '1bcd549121e3e9afd5ebe2bbe4b509d6d022265eee3239a164f3a7816bf10d8f',
                                  'pow_health.cog': '764f213b0dfb0623fecef59f46850fc37c5a0e4e0599f15411d35ee4b6ffb011',
                                  'pow_power.cog': '073756cb1b74cc2f84393215297cbd6f5e739d15972c283afcccd2130ebb5061',
                                  'pow_railcharges.cog': '18e5b0cf2ee4cc133582ba8879577f060b06c8eeda22d63bbc401deb998f57e3',
                                  'pow_railgun.cog': '4dd2252dde766ad47c9e89a1bb59e009431c7c3838e98cd703bbc4332a5d26bc',
                                  'pow_repeater.cog': '83505b4b4620ce33e494caab76769e59a9ececceaeef161122ab64dc3861feb6',
                                  'pow_revive.cog': '6904811bf2f22d8fbfde1c206ec8f1c0da2ed66f4217312fa31c934f52f3214e',
                                  'pow_sequencer.cog': '0f5b9acde5776625fd32f7d7582c4676dfc3b64cf784614fcd69733bcd324392',
                                  'pow_shields.cog': '8d515630da6ac31126decd4ca8c94ef840c42edc1110ef102e5f48530d88e8ad',
                                  'pow_single_sequencer.cog': '2777cacb7aceff81128cbf8b432cda15a32557f716cabe2ff6111183c79b965e',
                                  'pow_single_thermal.cog': 'fbf8c39c853bf5e9a60cf3016bba7a39936c136552ce094b80c872d205c811cf',
                                  'pow_smbkpk.cog': '60411d9c952634486dac6629db2f40fefb28af0389281208e3534c1b76c97c31',
                                  'pow_strifle.cog': 'edddcde2521e57fcf7d3c8c6e83ec25b7085d6230c4e09cf1387091f08697a73',
                                  'pow_thermal.cog': '962d2fb78f1e818439056039b76573f69ec50b0ffcea442cecedb05783290f3b',
                                  'pow_vest.cog': 'd3550f626554565280f3fa30bbc4c0c5b9032caad6f6d5fed47e16732efe2d5f'},
 'source_cog_sha256': {'00_bloodtrail.cog': '90a071f66f7cc620215f8444e037ff47e062ad4c48e599b9823b2a251b5e1031',
                       '00_conveyor.cog': '3abb561d6e05c98340993d7c299e6b680ac9785c032d6af4c405f1c2200fad0b',
                       '00_door.cog': 'a07fb10fadbc81bf4a970cd4ced495240ccfa86f35e3f9de954729d65cbfba5a',
                       '00_doorlocked1side.cog': 'd3e1098c3584de1e778b55a84042a0817f239dd6340a212abc8f322c647128c3',
                       '00_doorswitch.cog': '2da57ded50d3fc5b938b62c01dea38e55171ad246f58f11379c234d3be0aee06',
                       '00_elev_switch.cog': 'c1e492ba2c3b8cc0399f777e8a61338e4a1f9aed816ab3e62974e8b92d2adcc3',
                       '00_generator.cog': 'a764810a081562dcbd245688842a384414f1d147bc4af267cffa56adba954c5c',
                       '00_secretareas.cog': '8658ceb5cd8c0b6785e92423134f7de086f073f62fa455dd782e6d579b3bdf38',
                       '00_sectorthrust.cog': '6d63da50cef46ca9279d1acd957d464ebfceda257b995bdaa4b009c13efa7b47',
                       '00_simple_elev.cog': '9d805c389b73c88f8da803517007395a121c29b5625ce1758b940d394317ba4c',
                       '00_slideceiling.cog': '3d7103359ab74f5b7732445b96477896637121cf8b1600ae8985eb02407b0135',
                       'actor_atst.cog': '80d5d53eaa92d8af0434a8f692114287548448f8a44511fe9d1a051f22ab04b2',
                       'actor_cr.cog': '4a75eba98f0b7ec24d8487031cb4bf75039afc56da5f7d9a986c4d71d29f6a3e',
                       'actor_cs.cog': '3b2d4afc49c0440c2cb1e997a0415c1f260545808e97b78f73843bc2a9bebf44',
                       'actor_i2.cog': '84f9e5851295560c3d0ec64e284e252427ee1bea37f374391251199d5a85c79e',
                       'actor_ic.cog': '325d6426b148240d176c3656796bb637c7f4a75eaa47e51e90cf27a3c4ea52f0',
                       'actor_io.cog': '7766f0e5756ecd78d1e1921b73b35dae0912ad6a7005e03209e076b986a28a69',
                       'actor_pd.cog': 'eae2b9e4c34d56325f461d6ad60cc1af7f7c5fb8107b3769d851ef2ec8e8563e',
                       'actor_s3.cog': 'bda9a2c4a16ceff79b30d4f57bf0c28253631dd41f53195fb6588c1b662dc93a',
                       'actor_sd.cog': '8cacfeb14da68155c2166f28a046974d4e03f29ce6b00ff13cd3d0bd4688f213',
                       'actor_st.cog': 'b2b27471f59972e928746f57442bc40e0a29b3080b0433713d56bfdfd19ed1d5',
                       'actor_ug.cog': 'f25482a492accb4eba11a372309b2a4294777dbf18cae883625509c7c52e908c',
                       'destthing.cog': 'd734b825a820b3115b8f05aa74f56c66109cf572c677abe9cfbfcf679699f061',
                       'elev_doors_trig.cog': 'd03dba27279912420c253addace0c27b509413817ffd9a4d69af46efd3a8e74c',
                       'elev_squad.cog': 'edd1a71c5bb60665bed42cd33b584dc52b60f2b04d52d9c3f5014fb4ccac0f53',
                       'ffield2switch.cog': '1201d938867b24b808820bfe014a826acdd48de504555ce63bafe58ec2ef472c',
                       'installation_goals.cog': '03bc534f94cb0e64badd8cd280657bb03f99c0fcf85640cbef10ff84181699e9',
                       'installation_start.cog': '130cac6bc4292c7827d7dd930fcabd1feaf0393c8a384c2837ce72a9f6e7988a',
                       'lock_door.cog': '7dcd84485e366cbc3b87465f00097c344fa82aeff9bdef6b7b7096cf6b9e0657',
                       'movepipes.cog': 'c8798e41998ec6c67fb6da25cb1dbc412744943e824f9a85bc3c096f296cd7ff',
                       'pow_drailgun.cog': '2812ae55d215dde58d7551a844c0bb4c09a93f446579bb41a7022dcabc2ec166',
                       'pow_drepeater.cog': '95eafcf256cbe99aa92df0cc668490ccc41988caed79871532a290935e6ffc87',
                       'pow_dstrifle.cog': '483513c35d918b1344e558f4da3adf5d67f13ec5382f010686a3fe455e2088b2',
                       'pow_energy.cog': '1bcd549121e3e9afd5ebe2bbe4b509d6d022265eee3239a164f3a7816bf10d8f',
                       'pow_railcharges.cog': '18e5b0cf2ee4cc133582ba8879577f060b06c8eeda22d63bbc401deb998f57e3',
                       'pow_revive.cog': '6904811bf2f22d8fbfde1c206ec8f1c0da2ed66f4217312fa31c934f52f3214e',
                       'pow_sequencer.cog': '0f5b9acde5776625fd32f7d7582c4676dfc3b64cf784614fcd69733bcd324392',
                       'pow_smbkpk.cog': '60411d9c952634486dac6629db2f40fefb28af0389281208e3534c1b76c97c31',
                       'pow_thermal.cog': '962d2fb78f1e818439056039b76573f69ec50b0ffcea442cecedb05783290f3b',
                       'pow_vest.cog': 'd3550f626554565280f3fa30bbc4c0c5b9032caad6f6d5fed47e16732efe2d5f',
                       'pow_wrenchblue.cog': '4c0df23370a90e93733233f5f5459c4285760eb851d577e5475442471606edbc',
                       'pow_wrenchyellow.cog': 'b4ef1fd8983f589054c05fbf87385bb88cada101c595b9fec38d020b58129123',
                       'pumpcontrol.cog': '8582ed6a4a1948a92754cab59fe3c870dda86b3c28e9c98026c5825d1a464f5e',
                       'sect_squad.cog': '15f0cba507e03fc9dcbd63235d7f6ce62a38c3b874595f55ea95bde8f7a34485',
                       'shotgrate.cog': 'fc9bd992a65baa6e8bd5b3e27a670e85e28f957cabdeb8512b8f675dd37c7e33',
                       'watergate.cog': '1381b0bcf1f646c5b0ff9b8f15165e3dcdd432407628a78a19b92095f3b5ad48'},
 'verbatim_paths': ['misc/cogstrings.uni'],
 'output_filename': 'wbw-sp-pumping-station.goo',
 'cog_edits': {},
 'readme_source_defects': ['Author reports an occasional opening-camera malfunction; abort/reload '
                           'was the original workaround. Cause and gameplay remedy remain '
                           'unverified.'],
 'native_template_omissions': {'cog/item_heavy_explosive.cog': {'sha256': 'bd79f7ddbfb7adbd564c4c6538709471fec8f89b7ea0fb87dc459c220acd8aeb',
                                                                'name': 'ec.3do',
                                                                'reason': 'Native original '
                                                                          'declares an unused '
                                                                          'explosive_tpl template '
                                                                          'whose value is a model '
                                                                          'filename; symbol never '
                                                                          'read by code. Preserve '
                                                                          'exact native script.'}},
 'semantic_notes': ['Preserve Corbit as a non-Jedi protagonist: authored rank0, ordinary '
                    'weapon/ammo grants and all goals remain unchanged.',
                    'The MotS engine maps ordinary weapon ordinals below11 in inventory verbs; no '
                    'blanket numeric rewrite or new Force powers.',
                    'The lexer creates undeclared identifiers as zero-valued symbols, so briefstop '
                    'and old_camera are accepted; the unused stopbrief declaration is not a proven '
                    'camera defect. No speculative COG repair.',
                    'Original Urban Commando model and materials credited to Christopher Merkel '
                    'are extracted locally and namespaced; no model or other game assets ship with '
                    'WBW.',
                    'Keep the original introduction, pumps, gates, reactor charge, shuttle escape '
                    'and objective/briefing strings; no authored scene or gameplay loop was '
                    'removed.',
                    'All46 remaining original COG sources were reviewed and pinned: ten ordinary '
                    'pickup controllers now bind native MotS versions;36 retain their original '
                    'behavior under isolated names.',
                    'Native dropped-weapon, ammo, thermal/sequencer, revive and vest bindings '
                    'retain MotS inventory/alternate-mode behavior, including native damageable '
                    'ammunition pickups; no replacement native controller files are emitted.',
                    'Keep isolated JK blue/yellow wrench controllers: native MotS namesakes add '
                    'Duncan dialogue and subtitle side effects belonging to another mission. '
                    'Preserve original key bins49/50 and authored gate checks.']}

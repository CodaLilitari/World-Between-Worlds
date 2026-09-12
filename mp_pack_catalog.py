"""Hash-pinned reviewed MP episodes, complete active worlds and source-only instructions."""

PACKS = {'mp-6000-block': {'tag': 'mp323',
                   'title': '6000 Block',
                   'author': 'Brian Lozier',
                   'source_url': 'https://www.massassi.net/levels/files/323.shtml',
                   'download_url': 'https://www.massassi.net/media/levels/files/jkmp/6000.zip',
                   'massassi_id': 323,
                   'download_rank': 27,
                   'zip_sha256': '87c8073de0a5bd3176d6147959967f95b3dbd32ace06fd226d17cc0be87567b8',
                   'gob_sha256': '562263b1619e079812c2a2df66176df292ef05f7fb42924cc2d2baa81d5d533c',
                   'gob_member': '6000.gob',
                   'episode_sha256': '5ca96bfb9ab9d55f34b94a630796d146227c07724f292a34270b6f059475e3d3',
                   'episode_rows': [{'line': 10,
                                     'disc': 1,
                                     'level': 1,
                                     'type': 'LEVEL',
                                     'world': 'jkl/6000_saber.jkl',
                                     'lightpow': 0,
                                     'darkpow': 0,
                                     'goto_a': 11,
                                     'goto_b': -1,
                                     'world_spec': 'sabers'},
                                    {'line': 11,
                                     'disc': 0,
                                     'level': 2,
                                     'type': 'LEVEL',
                                     'world': 'jkl/6000_guns.jkl',
                                     'lightpow': 0,
                                     'darkpow': 0,
                                     'goto_a': 10,
                                     'goto_b': -1,
                                     'world_spec': 'guns'}],
                   'world_specs': {'sabers': {'tag': 'mp323_s',
                                              'title': '6000 Block',
                                              'author': 'Brian Lozier',
                                              'source_url': 'https://www.massassi.net/levels/files/323.shtml',
                                              'download_url': 'https://www.massassi.net/media/levels/files/jkmp/6000.zip',
                                              'massassi_id': 323,
                                              'download_rank': 27,
                                              'zip_sha256': '87c8073de0a5bd3176d6147959967f95b3dbd32ace06fd226d17cc0be87567b8',
                                              'gob_sha256': '562263b1619e079812c2a2df66176df292ef05f7fb42924cc2d2baa81d5d533c',
                                              'gob_member': '6000.gob',
                                              'world': 'jkl/6000_saber.jkl',
                                              'sha256': 'b5848d8c0f46deb3169d409cea6b46633b4ddbcf7da060a60a6f59a374638b22',
                                              'scripts_sha256': 'd1850fa877b91fe34c317a5630ca6b502b2a2b5974dbb6d50f3689103b1cf7a9',
                                              'episode_type': 2,
                                              'runtime_cogs': '00_desttrail.cog 00_smoketrail.cog '
                                                              'class_sequencer.cog kyle.cog '
                                                              'pow_backpack.cog pow_bacta.cog '
                                                              'pow_bryar.cog pow_concrifle.cog '
                                                              'pow_crossbow.cog pow_health.cog '
                                                              'pow_mana.cog pow_railgun.cog '
                                                              'pow_repeater.cog pow_shields.cog '
                                                              'pow_single_sequencer.cog '
                                                              'pow_single_thermal.cog '
                                                              'pow_strifle.cog',
                                              'runtime_source_sha256': {'00_desttrail.cog': '6c56bf2f756cd63625443d5fa76f8d72521c1f19ed9b61a7ce6252b1ecc00c48',
                                                                        '00_smoketrail.cog': '2a990da3d41131bca2d1481562592742e5f8c543ac846dd95311a361189c7bbf',
                                                                        'class_sequencer.cog': '7a057711f1e6fb33e1a7b410d657738531c5b6664af3259dad3ab16c4b30cae5',
                                                                        'kyle.cog': 'cf68cc4754acd78d2d84297eb6d05df80d0e8e265fa5d5a902b7101f8e523955',
                                                                        'pow_backpack.cog': '7bacc8efb06a8d6b71ab3780f2ab6302ad1c63d245bd9524c0b89258053b08ed',
                                                                        'pow_bacta.cog': '8b420d7556d92a9f2bcfbb99aeac690e85d7beb54baa7f7e7321f4121b090d56',
                                                                        'pow_bryar.cog': 'd533156b8283c2c21f44355f7146192df873f5806499cc57fb9fbfa838a2a169',
                                                                        'pow_concrifle.cog': 'a762451646e8598bc64afc70c6ef5054e434dda6da5a4d5f735c13fef00de011',
                                                                        'pow_crossbow.cog': 'e5dfce5f5f394b670ac2a7a9d2c569085127b1857bc52b3859475ae10b285f85',
                                                                        'pow_health.cog': '764f213b0dfb0623fecef59f46850fc37c5a0e4e0599f15411d35ee4b6ffb011',
                                                                        'pow_mana.cog': 'f7253958c01e90bfc99d162ec0af0c2cc819e561c817165bcf434dadb776a30a',
                                                                        'pow_railgun.cog': '4dd2252dde766ad47c9e89a1bb59e009431c7c3838e98cd703bbc4332a5d26bc',
                                                                        'pow_repeater.cog': '83505b4b4620ce33e494caab76769e59a9ececceaeef161122ab64dc3861feb6',
                                                                        'pow_shields.cog': '8d515630da6ac31126decd4ca8c94ef840c42edc1110ef102e5f48530d88e8ad',
                                                                        'pow_single_sequencer.cog': '2777cacb7aceff81128cbf8b432cda15a32557f716cabe2ff6111183c79b965e',
                                                                        'pow_single_thermal.cog': 'fbf8c39c853bf5e9a60cf3016bba7a39936c136552ce094b80c872d205c811cf',
                                                                        'pow_strifle.cog': 'edddcde2521e57fcf7d3c8c6e83ec25b7085d6230c4e09cf1387091f08697a73'},
                                              'environment': '00_particlethrust.cog',
                                              'cog_sha256': {'00_particlethrust.cog': 'de7e19b35d78ddf337fe6cb028ca67a6bb555d6792fb91370a86c5866de0c6e4'},
                                              'requires_jksp': False,
                                              'source_omissions': [],
                                              'resource_aliases': {},
                                              'cog_edits': {},
                                              'native_cog_edits': {},
                                              'native_template_overrides': {},
                                              'native_resource_overrides': {},
                                              'readme_provenance': [{'path': '6000_readme.txt',
                                                                     'sha256': '9eb397b432ce412da39d957e7666d3a5415257267b4c76dac828065f1f15472f',
                                                                     'bytes': 4716}],
                                              'notes': ['Source review: preserve the authored '
                                                        'particle/thrust COG with its local '
                                                        'particle template references. The script '
                                                        'does not alter inventory, weapon slots or '
                                                        'player classes.',
                                                        'This is one reviewed world of the '
                                                        'original two-world 6000 Block release; '
                                                        'expose the complete pack only after both '
                                                        'active episode rows are assembled and '
                                                        'verified.'],
                                              'runtime_test': {'status': 'not-run-on-this-output',
                                                               'full_gameplay': False,
                                                               'note': 'Source review and '
                                                                       'independent structural '
                                                                       'conversion only; engine '
                                                                       'host and two-peer gameplay '
                                                                       'checks remain pending.'},
                                              'runtime_gates': ['Open the converted episode in a '
                                                                'clean MotS multiplayer profile '
                                                                'with only its declared '
                                                                'dependencies.',
                                                                'Check original pickup placement '
                                                                'and native MotS inventory '
                                                                'bindings, authored '
                                                                'doors/lifts/hazards where '
                                                                'present, then matched second-peer '
                                                                'behavior.']},
                                   'guns': {'tag': 'mp323_g',
                                            'title': '6000 Block',
                                            'author': 'Brian Lozier',
                                            'source_url': 'https://www.massassi.net/levels/files/323.shtml',
                                            'download_url': 'https://www.massassi.net/media/levels/files/jkmp/6000.zip',
                                            'massassi_id': 323,
                                            'download_rank': 27,
                                            'zip_sha256': '87c8073de0a5bd3176d6147959967f95b3dbd32ace06fd226d17cc0be87567b8',
                                            'gob_sha256': '562263b1619e079812c2a2df66176df292ef05f7fb42924cc2d2baa81d5d533c',
                                            'gob_member': '6000.gob',
                                            'world': 'jkl/6000_guns.jkl',
                                            'sha256': '19c496a563ebb3ff24c388ec1de64221a38c8a0131f0eb4fa7f548f52665ed1d',
                                            'scripts_sha256': 'd8e7b1bdbadca153191fd6f339a85344c67f1b057cac9529cb7ea4bbb3218ea4',
                                            'episode_type': 2,
                                            'runtime_cogs': '00_desttrail.cog 00_smoketrail.cog '
                                                            'class_sequencer.cog kyle.cog '
                                                            'pow_backpack.cog pow_bacta.cog '
                                                            'pow_bryar.cog pow_concrifle.cog '
                                                            'pow_crossbow.cog pow_energy.cog '
                                                            'pow_health.cog pow_mana.cog '
                                                            'pow_power.cog pow_railcharges.cog '
                                                            'pow_railgun.cog pow_repeater.cog '
                                                            'pow_sequencer.cog pow_shields.cog '
                                                            'pow_single_sequencer.cog '
                                                            'pow_single_thermal.cog '
                                                            'pow_strifle.cog',
                                            'runtime_source_sha256': {'00_desttrail.cog': '6c56bf2f756cd63625443d5fa76f8d72521c1f19ed9b61a7ce6252b1ecc00c48',
                                                                      '00_smoketrail.cog': '2a990da3d41131bca2d1481562592742e5f8c543ac846dd95311a361189c7bbf',
                                                                      'class_sequencer.cog': '7a057711f1e6fb33e1a7b410d657738531c5b6664af3259dad3ab16c4b30cae5',
                                                                      'kyle.cog': 'cf68cc4754acd78d2d84297eb6d05df80d0e8e265fa5d5a902b7101f8e523955',
                                                                      'pow_backpack.cog': '7bacc8efb06a8d6b71ab3780f2ab6302ad1c63d245bd9524c0b89258053b08ed',
                                                                      'pow_bacta.cog': '8b420d7556d92a9f2bcfbb99aeac690e85d7beb54baa7f7e7321f4121b090d56',
                                                                      'pow_bryar.cog': 'd533156b8283c2c21f44355f7146192df873f5806499cc57fb9fbfa838a2a169',
                                                                      'pow_concrifle.cog': 'a762451646e8598bc64afc70c6ef5054e434dda6da5a4d5f735c13fef00de011',
                                                                      'pow_crossbow.cog': 'e5dfce5f5f394b670ac2a7a9d2c569085127b1857bc52b3859475ae10b285f85',
                                                                      'pow_energy.cog': '1bcd549121e3e9afd5ebe2bbe4b509d6d022265eee3239a164f3a7816bf10d8f',
                                                                      'pow_health.cog': '764f213b0dfb0623fecef59f46850fc37c5a0e4e0599f15411d35ee4b6ffb011',
                                                                      'pow_mana.cog': 'f7253958c01e90bfc99d162ec0af0c2cc819e561c817165bcf434dadb776a30a',
                                                                      'pow_power.cog': '073756cb1b74cc2f84393215297cbd6f5e739d15972c283afcccd2130ebb5061',
                                                                      'pow_railcharges.cog': '18e5b0cf2ee4cc133582ba8879577f060b06c8eeda22d63bbc401deb998f57e3',
                                                                      'pow_railgun.cog': '4dd2252dde766ad47c9e89a1bb59e009431c7c3838e98cd703bbc4332a5d26bc',
                                                                      'pow_repeater.cog': '83505b4b4620ce33e494caab76769e59a9ececceaeef161122ab64dc3861feb6',
                                                                      'pow_sequencer.cog': '0f5b9acde5776625fd32f7d7582c4676dfc3b64cf784614fcd69733bcd324392',
                                                                      'pow_shields.cog': '8d515630da6ac31126decd4ca8c94ef840c42edc1110ef102e5f48530d88e8ad',
                                                                      'pow_single_sequencer.cog': '2777cacb7aceff81128cbf8b432cda15a32557f716cabe2ff6111183c79b965e',
                                                                      'pow_single_thermal.cog': 'fbf8c39c853bf5e9a60cf3016bba7a39936c136552ce094b80c872d205c811cf',
                                                                      'pow_strifle.cog': 'edddcde2521e57fcf7d3c8c6e83ec25b7085d6230c4e09cf1387091f08697a73'},
                                            'environment': '00_particlethrust.cog',
                                            'cog_sha256': {'00_particlethrust.cog': 'de7e19b35d78ddf337fe6cb028ca67a6bb555d6792fb91370a86c5866de0c6e4'},
                                            'requires_jksp': False,
                                            'source_omissions': [],
                                            'resource_aliases': {},
                                            'cog_edits': {},
                                            'native_cog_edits': {},
                                            'native_template_overrides': {},
                                            'native_resource_overrides': {},
                                            'readme_provenance': [{'path': '6000_readme.txt',
                                                                   'sha256': '9eb397b432ce412da39d957e7666d3a5415257267b4c76dac828065f1f15472f',
                                                                   'bytes': 4716}],
                                            'notes': ['Source review: preserve the authored '
                                                      'particle/thrust COG with its local particle '
                                                      'template references. The script does not '
                                                      'alter inventory, weapon slots or player '
                                                      'classes.',
                                                      'This is one reviewed world of the original '
                                                      'two-world 6000 Block release; expose the '
                                                      'complete pack only after both active '
                                                      'episode rows are assembled and verified.'],
                                            'runtime_test': {'status': 'not-run-on-this-output',
                                                             'full_gameplay': False,
                                                             'note': 'Source review and '
                                                                     'independent structural '
                                                                     'conversion only; engine host '
                                                                     'and two-peer gameplay checks '
                                                                     'remain pending.'},
                                            'runtime_gates': ['Open the converted episode in a '
                                                              'clean MotS multiplayer profile with '
                                                              'only its declared dependencies.',
                                                              'Check original pickup placement and '
                                                              'native MotS inventory bindings, '
                                                              'authored doors/lifts/hazards where '
                                                              'present, then matched second-peer '
                                                              'behavior.']}},
                   'notes': ['Both active original episode rows are required; no unlisted physical '
                             'worlds exist.',
                             'Source terms require preserving authorship and README; this '
                             'source-only recipe grants no redistribution rights.'],
                   'runtime_test': {'status': 'exact-payload-host-smoke-passed',
                                    'scope': '30-second hidden MotS multiplayer host per active '
                                             'world',
                                    'full_gameplay': False,
                                    'worlds': [{'case': 'mp-6000-block-sabers-v1',
                                                'world': 'br_mp323_s.jkl',
                                                'duration_seconds': 30,
                                                'runtime_sha256': 'fd8ddfc23f09540068318bedcc3f08e5ce6b12ea5ee04ed3cf45fd8ed46b7873',
                                                'tested_archive_sha256': 'ea5c0aeb975086a5b38ba9f41d7f0d042f6979b2943e55eeef7e67bcc324e103',
                                                'payload_sha256': '602e1dc29cacd01f0306a1334ec147ae944efd7afc897c3cc900897ad7771a40',
                                                'evidence_report_sha256': '213b918046259194ea6e53414e265499c6fba37593179b979dc16e6719bd497d'},
                                               {'case': 'mp-6000-block-guns-v1',
                                                'world': 'br_mp323_g.jkl',
                                                'duration_seconds': 30,
                                                'runtime_sha256': 'fd8ddfc23f09540068318bedcc3f08e5ce6b12ea5ee04ed3cf45fd8ed46b7873',
                                                'tested_archive_sha256': 'ea5c0aeb975086a5b38ba9f41d7f0d042f6979b2943e55eeef7e67bcc324e103',
                                                'payload_sha256': '602e1dc29cacd01f0306a1334ec147ae944efd7afc897c3cc900897ad7771a40',
                                                'evidence_report_sha256': 'cd80af68e1e9a1094437fca508b9b1d2771d22e646448b2508c50ae7ffa176ea'}],
                                    'note': 'Correct MotS multiplayer mode and selected world, '
                                            'advancing simulation, and zero resource diagnostics. '
                                            'This evidence is bound to the canonical game payload; '
                                            'metadata markers may differ. Rendering, authored '
                                            'mechanics and two-peer synchronization are not '
                                            'established.'},
                   'catalog_status': 'prototype'},
 'mp-gladiator': {'key': 'mp-gladiator',
                  'tag': 'mp168',
                  'title': 'Gladiator',
                  'author': 'Daniel Yost',
                  'source_url': 'https://www.massassi.net/levels/files/168.shtml',
                  'download_url': 'https://www.massassi.net/media/levels/files/jkmp/gladiator.zip',
                  'massassi_id': 168,
                  'download_rank': 49,
                  'zip_sha256': 'b99fa725513c81834b3708719ee9a7335c677ecfe3fd28be866921c9e2cfe725',
                  'gob_sha256': 'ab1a34e0505891295e9c23abcc22d0998af98fa756360b85d34da075a4a1cab6',
                  'gob_member': 'Gladiator.gob',
                  'episode_sha256': '756c9ab603c3bba3119bcd51681347e76a8066618d106fe9256e60efbdaa858b',
                  'episode_rows': [{'line': 10,
                                    'disc': 1,
                                    'level': 1,
                                    'type': 'LEVEL',
                                    'world': 'jkl/gladiator.jkl',
                                    'lightpow': 0,
                                    'darkpow': 0,
                                    'goto_a': 12,
                                    'goto_b': -1,
                                    'world_spec': 'arena'},
                                   {'line': 12,
                                    'disc': 0,
                                    'level': 3,
                                    'type': 'LEVEL',
                                    'world': 'jkl/gladiatorreeyee.jkl',
                                    'lightpow': 0,
                                    'darkpow': 0,
                                    'goto_a': 11,
                                    'goto_b': -1,
                                    'world_spec': 'reeyees'},
                                   {'line': 11,
                                    'disc': 0,
                                    'level': 2,
                                    'type': 'LEVEL',
                                    'world': 'jkl/gladiatorpig.jkl',
                                    'lightpow': 0,
                                    'darkpow': 0,
                                    'goto_a': 13,
                                    'goto_b': -1,
                                    'world_spec': 'gamorreans'},
                                   {'line': 13,
                                    'disc': 0,
                                    'level': 2,
                                    'type': 'LEVEL',
                                    'world': 'jkl/gladiatorkell.jkl',
                                    'lightpow': 0,
                                    'darkpow': 0,
                                    'goto_a': -1,
                                    'goto_b': -1,
                                    'world_spec': 'kelldragons'}],
                  'world_specs': {'arena': {'tag': 'mp168_a',
                                            'title': 'Gladiator',
                                            'author': 'Daniel Yost',
                                            'source_url': 'https://www.massassi.net/levels/files/168.shtml',
                                            'download_url': 'https://www.massassi.net/media/levels/files/jkmp/gladiator.zip',
                                            'massassi_id': 168,
                                            'download_rank': 49,
                                            'zip_sha256': 'b99fa725513c81834b3708719ee9a7335c677ecfe3fd28be866921c9e2cfe725',
                                            'gob_sha256': 'ab1a34e0505891295e9c23abcc22d0998af98fa756360b85d34da075a4a1cab6',
                                            'gob_member': 'Gladiator.gob',
                                            'world': 'jkl/gladiator.jkl',
                                            'sha256': 'f8c47010ed591dcaa682ca012cb775854665b09028abde20d353ab9f01d1df37',
                                            'scripts_sha256': '4da88cf2e855d66efbc313f8befe4dd4c622ca66ca64893f1374bf0af81cdb8d',
                                            'episode_type': 2,
                                            'runtime_cogs': '00_desttrail.cog 00_smoketrail.cog '
                                                            'class_sequencer.cog kyle.cog '
                                                            'pow_backpack.cog pow_bryar.cog '
                                                            'pow_concrifle.cog pow_crossbow.cog '
                                                            'pow_energy.cog pow_health.cog '
                                                            'pow_power.cog pow_powerboost.cog '
                                                            'pow_railcharges.cog pow_railgun.cog '
                                                            'pow_repeater.cog pow_sequencer.cog '
                                                            'pow_single_sequencer.cog '
                                                            'pow_single_thermal.cog '
                                                            'pow_strifle.cog pow_thermal.cog '
                                                            'pow_vest.cog',
                                            'runtime_source_sha256': {'00_desttrail.cog': '6c56bf2f756cd63625443d5fa76f8d72521c1f19ed9b61a7ce6252b1ecc00c48',
                                                                      '00_smoketrail.cog': '2a990da3d41131bca2d1481562592742e5f8c543ac846dd95311a361189c7bbf',
                                                                      'class_sequencer.cog': '7a057711f1e6fb33e1a7b410d657738531c5b6664af3259dad3ab16c4b30cae5',
                                                                      'kyle.cog': 'cf68cc4754acd78d2d84297eb6d05df80d0e8e265fa5d5a902b7101f8e523955',
                                                                      'pow_backpack.cog': '7bacc8efb06a8d6b71ab3780f2ab6302ad1c63d245bd9524c0b89258053b08ed',
                                                                      'pow_bryar.cog': 'd533156b8283c2c21f44355f7146192df873f5806499cc57fb9fbfa838a2a169',
                                                                      'pow_concrifle.cog': 'a762451646e8598bc64afc70c6ef5054e434dda6da5a4d5f735c13fef00de011',
                                                                      'pow_crossbow.cog': 'e5dfce5f5f394b670ac2a7a9d2c569085127b1857bc52b3859475ae10b285f85',
                                                                      'pow_energy.cog': '1bcd549121e3e9afd5ebe2bbe4b509d6d022265eee3239a164f3a7816bf10d8f',
                                                                      'pow_health.cog': '764f213b0dfb0623fecef59f46850fc37c5a0e4e0599f15411d35ee4b6ffb011',
                                                                      'pow_power.cog': '073756cb1b74cc2f84393215297cbd6f5e739d15972c283afcccd2130ebb5061',
                                                                      'pow_powerboost.cog': '1dd3214a7c95a9c88f32c0710747648aefcc54495d666496cbfeae697aa085d8',
                                                                      'pow_railcharges.cog': '18e5b0cf2ee4cc133582ba8879577f060b06c8eeda22d63bbc401deb998f57e3',
                                                                      'pow_railgun.cog': '4dd2252dde766ad47c9e89a1bb59e009431c7c3838e98cd703bbc4332a5d26bc',
                                                                      'pow_repeater.cog': '83505b4b4620ce33e494caab76769e59a9ececceaeef161122ab64dc3861feb6',
                                                                      'pow_sequencer.cog': '0f5b9acde5776625fd32f7d7582c4676dfc3b64cf784614fcd69733bcd324392',
                                                                      'pow_single_sequencer.cog': '2777cacb7aceff81128cbf8b432cda15a32557f716cabe2ff6111183c79b965e',
                                                                      'pow_single_thermal.cog': 'fbf8c39c853bf5e9a60cf3016bba7a39936c136552ce094b80c872d205c811cf',
                                                                      'pow_strifle.cog': 'edddcde2521e57fcf7d3c8c6e83ec25b7085d6230c4e09cf1387091f08697a73',
                                                                      'pow_thermal.cog': '962d2fb78f1e818439056039b76573f69ec50b0ffcea442cecedb05783290f3b',
                                                                      'pow_vest.cog': 'd3550f626554565280f3fa30bbc4c0c5b9032caad6f6d5fed47e16732efe2d5f'},
                                            'environment': '',
                                            'cog_sha256': {},
                                            'requires_jksp': False,
                                            'source_omissions': [],
                                            'resource_aliases': {},
                                            'cog_edits': {},
                                            'native_cog_edits': {},
                                            'native_template_overrides': {},
                                            'native_resource_overrides': {},
                                            'readme_provenance': [{'path': 'Gladiator.txt',
                                                                   'sha256': '5cee07bf8ab36d18cbc641cf0896dca60a84162ecdd24b38d63942f99a84e716',
                                                                   'bytes': 4034}],
                                            'notes': ['Source review: preserve the authored '
                                                      'multiplayer enemy generator and source '
                                                      'actor damage, death-drop and Force-skill '
                                                      'callback behavior. Callback message IDs 24, '
                                                      '31 and 34 are also present in native MotS '
                                                      'actor scripts and are not inventory slots '
                                                      'to remap.',
                                                      'The original pack contains an ordinary '
                                                      'arena plus ReeYees, Gamorrean and Kell '
                                                      'Dragon variants. Source generator '
                                                      'visibility/spawn limits and no-gun '
                                                      'placements are retained; AI behavior and '
                                                      'two-peer synchronization require runtime '
                                                      'testing.'],
                                            'runtime_test': {'status': 'not-run-on-this-output',
                                                             'full_gameplay': False,
                                                             'note': 'Source review and '
                                                                     'independent structural '
                                                                     'conversion only; engine host '
                                                                     'and two-peer gameplay checks '
                                                                     'remain pending.'},
                                            'runtime_gates': ['Open the converted episode in a '
                                                              'clean MotS multiplayer profile with '
                                                              'only its declared dependencies.',
                                                              'Check original pickup placement and '
                                                              'native MotS inventory bindings, '
                                                              'authored doors/lifts/hazards where '
                                                              'present, then matched second-peer '
                                                              'behavior.'],
                                            'key': 'mp-gladiator-arena'},
                                  'reeyees': {'tag': 'mp168_r',
                                              'title': 'Gladiator',
                                              'author': 'Daniel Yost',
                                              'source_url': 'https://www.massassi.net/levels/files/168.shtml',
                                              'download_url': 'https://www.massassi.net/media/levels/files/jkmp/gladiator.zip',
                                              'massassi_id': 168,
                                              'download_rank': 49,
                                              'zip_sha256': 'b99fa725513c81834b3708719ee9a7335c677ecfe3fd28be866921c9e2cfe725',
                                              'gob_sha256': 'ab1a34e0505891295e9c23abcc22d0998af98fa756360b85d34da075a4a1cab6',
                                              'gob_member': 'Gladiator.gob',
                                              'world': 'jkl/gladiatorreeyee.jkl',
                                              'sha256': 'cd41c00e3ba99b242aa0928033ea1e90568c62ff3707dfdb9b1d639790169c1b',
                                              'scripts_sha256': '2c1d821376ccd797026a86680bd33b91f00e452d655ccb8b76813cc107292058',
                                              'episode_type': 2,
                                              'runtime_cogs': '00_desttrail.cog 00_smoketrail.cog '
                                                              'class_sequencer.cog kyle.cog '
                                                              'pow_backpack.cog pow_bryar.cog '
                                                              'pow_concrifle.cog pow_crossbow.cog '
                                                              'pow_dstrifle.cog pow_energy.cog '
                                                              'pow_health.cog pow_power.cog '
                                                              'pow_powerboost.cog '
                                                              'pow_railcharges.cog pow_railgun.cog '
                                                              'pow_repeater.cog pow_sequencer.cog '
                                                              'pow_single_sequencer.cog '
                                                              'pow_single_thermal.cog '
                                                              'pow_strifle.cog pow_thermal.cog '
                                                              'pow_vest.cog',
                                              'runtime_source_sha256': {'00_desttrail.cog': '6c56bf2f756cd63625443d5fa76f8d72521c1f19ed9b61a7ce6252b1ecc00c48',
                                                                        '00_smoketrail.cog': '2a990da3d41131bca2d1481562592742e5f8c543ac846dd95311a361189c7bbf',
                                                                        'class_sequencer.cog': '7a057711f1e6fb33e1a7b410d657738531c5b6664af3259dad3ab16c4b30cae5',
                                                                        'kyle.cog': 'cf68cc4754acd78d2d84297eb6d05df80d0e8e265fa5d5a902b7101f8e523955',
                                                                        'pow_backpack.cog': '7bacc8efb06a8d6b71ab3780f2ab6302ad1c63d245bd9524c0b89258053b08ed',
                                                                        'pow_bryar.cog': 'd533156b8283c2c21f44355f7146192df873f5806499cc57fb9fbfa838a2a169',
                                                                        'pow_concrifle.cog': 'a762451646e8598bc64afc70c6ef5054e434dda6da5a4d5f735c13fef00de011',
                                                                        'pow_crossbow.cog': 'e5dfce5f5f394b670ac2a7a9d2c569085127b1857bc52b3859475ae10b285f85',
                                                                        'pow_dstrifle.cog': '483513c35d918b1344e558f4da3adf5d67f13ec5382f010686a3fe455e2088b2',
                                                                        'pow_energy.cog': '1bcd549121e3e9afd5ebe2bbe4b509d6d022265eee3239a164f3a7816bf10d8f',
                                                                        'pow_health.cog': '764f213b0dfb0623fecef59f46850fc37c5a0e4e0599f15411d35ee4b6ffb011',
                                                                        'pow_power.cog': '073756cb1b74cc2f84393215297cbd6f5e739d15972c283afcccd2130ebb5061',
                                                                        'pow_powerboost.cog': '1dd3214a7c95a9c88f32c0710747648aefcc54495d666496cbfeae697aa085d8',
                                                                        'pow_railcharges.cog': '18e5b0cf2ee4cc133582ba8879577f060b06c8eeda22d63bbc401deb998f57e3',
                                                                        'pow_railgun.cog': '4dd2252dde766ad47c9e89a1bb59e009431c7c3838e98cd703bbc4332a5d26bc',
                                                                        'pow_repeater.cog': '83505b4b4620ce33e494caab76769e59a9ececceaeef161122ab64dc3861feb6',
                                                                        'pow_sequencer.cog': '0f5b9acde5776625fd32f7d7582c4676dfc3b64cf784614fcd69733bcd324392',
                                                                        'pow_single_sequencer.cog': '2777cacb7aceff81128cbf8b432cda15a32557f716cabe2ff6111183c79b965e',
                                                                        'pow_single_thermal.cog': 'fbf8c39c853bf5e9a60cf3016bba7a39936c136552ce094b80c872d205c811cf',
                                                                        'pow_strifle.cog': 'edddcde2521e57fcf7d3c8c6e83ec25b7085d6230c4e09cf1387091f08697a73',
                                                                        'pow_thermal.cog': '962d2fb78f1e818439056039b76573f69ec50b0ffcea442cecedb05783290f3b',
                                                                        'pow_vest.cog': 'd3550f626554565280f3fa30bbc4c0c5b9032caad6f6d5fed47e16732efe2d5f'},
                                              'environment': '00_bloodtrail.cog actor_rb.cog '
                                                             'enemygenmp.cog',
                                              'cog_sha256': {'00_bloodtrail.cog': '90a071f66f7cc620215f8444e037ff47e062ad4c48e599b9823b2a251b5e1031',
                                                             'actor_rb.cog': '348a5e64126e73eef896548cd12c41cc3ee7cc9833e62f9b2388520553d1f546',
                                                             'enemygenmp.cog': '2cffad0fc3d0ea138a8f97b8f63b0572fff02e0748c49faf27ff984c50eecdfa'},
                                              'requires_jksp': False,
                                              'source_omissions': [],
                                              'resource_aliases': {'stlaser.snd': 'br_mp168_r_stlaser.snd'},
                                              'cog_edits': {},
                                              'native_cog_edits': {},
                                              'native_template_overrides': {},
                                              'native_resource_overrides': {},
                                              'readme_provenance': [{'path': 'Gladiator.txt',
                                                                     'sha256': '5cee07bf8ab36d18cbc641cf0896dca60a84162ecdd24b38d63942f99a84e716',
                                                                     'bytes': 4034}],
                                              'notes': ['Source review: preserve the authored '
                                                        'multiplayer enemy generator and source '
                                                        'actor damage, death-drop and Force-skill '
                                                        'callback behavior. Callback message IDs '
                                                        '24, 31 and 34 are also present in native '
                                                        'MotS actor scripts and are not inventory '
                                                        'slots to remap.',
                                                        'The original pack contains an ordinary '
                                                        'arena plus ReeYees, Gamorrean and Kell '
                                                        'Dragon variants. Source generator '
                                                        'visibility/spawn limits and no-gun '
                                                        'placements are retained; AI behavior and '
                                                        'two-peer synchronization require runtime '
                                                        'testing.'],
                                              'runtime_test': {'status': 'not-run-on-this-output',
                                                               'full_gameplay': False,
                                                               'note': 'Source review and '
                                                                       'independent structural '
                                                                       'conversion only; engine '
                                                                       'host and two-peer gameplay '
                                                                       'checks remain pending.'},
                                              'runtime_gates': ['Open the converted episode in a '
                                                                'clean MotS multiplayer profile '
                                                                'with only its declared '
                                                                'dependencies.',
                                                                'Check original pickup placement '
                                                                'and native MotS inventory '
                                                                'bindings, authored '
                                                                'doors/lifts/hazards where '
                                                                'present, then matched second-peer '
                                                                'behavior.'],
                                              'key': 'mp-gladiator-reeyees'},
                                  'gamorreans': {'tag': 'mp168_g',
                                                 'title': 'Gladiator',
                                                 'author': 'Daniel Yost',
                                                 'source_url': 'https://www.massassi.net/levels/files/168.shtml',
                                                 'download_url': 'https://www.massassi.net/media/levels/files/jkmp/gladiator.zip',
                                                 'massassi_id': 168,
                                                 'download_rank': 49,
                                                 'zip_sha256': 'b99fa725513c81834b3708719ee9a7335c677ecfe3fd28be866921c9e2cfe725',
                                                 'gob_sha256': 'ab1a34e0505891295e9c23abcc22d0998af98fa756360b85d34da075a4a1cab6',
                                                 'gob_member': 'Gladiator.gob',
                                                 'world': 'jkl/gladiatorpig.jkl',
                                                 'sha256': '3418e4ba97ac38ac814f3cac063cf27ba7519f61eb162b938a01cdd3a4012b24',
                                                 'scripts_sha256': '72cd0fb814d6c95119d16c7bd2122e39dc9aa4adfb39b843eca5e2e34d5d4e77',
                                                 'episode_type': 2,
                                                 'runtime_cogs': '00_desttrail.cog '
                                                                 '00_smoketrail.cog '
                                                                 'class_sequencer.cog kyle.cog '
                                                                 'pow_backpack.cog pow_bacta.cog '
                                                                 'pow_bryar.cog pow_concrifle.cog '
                                                                 'pow_crossbow.cog pow_health.cog '
                                                                 'pow_railgun.cog pow_repeater.cog '
                                                                 'pow_single_sequencer.cog '
                                                                 'pow_single_thermal.cog '
                                                                 'pow_strifle.cog',
                                                 'runtime_source_sha256': {'00_desttrail.cog': '6c56bf2f756cd63625443d5fa76f8d72521c1f19ed9b61a7ce6252b1ecc00c48',
                                                                           '00_smoketrail.cog': '2a990da3d41131bca2d1481562592742e5f8c543ac846dd95311a361189c7bbf',
                                                                           'class_sequencer.cog': '7a057711f1e6fb33e1a7b410d657738531c5b6664af3259dad3ab16c4b30cae5',
                                                                           'kyle.cog': 'cf68cc4754acd78d2d84297eb6d05df80d0e8e265fa5d5a902b7101f8e523955',
                                                                           'pow_backpack.cog': '7bacc8efb06a8d6b71ab3780f2ab6302ad1c63d245bd9524c0b89258053b08ed',
                                                                           'pow_bacta.cog': '8b420d7556d92a9f2bcfbb99aeac690e85d7beb54baa7f7e7321f4121b090d56',
                                                                           'pow_bryar.cog': 'd533156b8283c2c21f44355f7146192df873f5806499cc57fb9fbfa838a2a169',
                                                                           'pow_concrifle.cog': 'a762451646e8598bc64afc70c6ef5054e434dda6da5a4d5f735c13fef00de011',
                                                                           'pow_crossbow.cog': 'e5dfce5f5f394b670ac2a7a9d2c569085127b1857bc52b3859475ae10b285f85',
                                                                           'pow_health.cog': '764f213b0dfb0623fecef59f46850fc37c5a0e4e0599f15411d35ee4b6ffb011',
                                                                           'pow_railgun.cog': '4dd2252dde766ad47c9e89a1bb59e009431c7c3838e98cd703bbc4332a5d26bc',
                                                                           'pow_repeater.cog': '83505b4b4620ce33e494caab76769e59a9ececceaeef161122ab64dc3861feb6',
                                                                           'pow_single_sequencer.cog': '2777cacb7aceff81128cbf8b432cda15a32557f716cabe2ff6111183c79b965e',
                                                                           'pow_single_thermal.cog': 'fbf8c39c853bf5e9a60cf3016bba7a39936c136552ce094b80c872d205c811cf',
                                                                           'pow_strifle.cog': 'edddcde2521e57fcf7d3c8c6e83ec25b7085d6230c4e09cf1387091f08697a73'},
                                                 'environment': 'actor_gg.cog enemygenmp.cog',
                                                 'cog_sha256': {'actor_gg.cog': 'eaac3e09a98dd2728add870d3aaf155ef8cc3651b79a0f6df5b2dc80128e1209',
                                                                'enemygenmp.cog': '2cffad0fc3d0ea138a8f97b8f63b0572fff02e0748c49faf27ff984c50eecdfa'},
                                                 'requires_jksp': False,
                                                 'source_omissions': [],
                                                 'resource_aliases': {},
                                                 'cog_edits': {},
                                                 'native_cog_edits': {},
                                                 'native_template_overrides': {},
                                                 'native_resource_overrides': {},
                                                 'readme_provenance': [{'path': 'Gladiator.txt',
                                                                        'sha256': '5cee07bf8ab36d18cbc641cf0896dca60a84162ecdd24b38d63942f99a84e716',
                                                                        'bytes': 4034}],
                                                 'notes': ['Source review: preserve the authored '
                                                           'multiplayer enemy generator and source '
                                                           'actor damage, death-drop and '
                                                           'Force-skill callback behavior. '
                                                           'Callback message IDs 24, 31 and 34 are '
                                                           'also present in native MotS actor '
                                                           'scripts and are not inventory slots to '
                                                           'remap.',
                                                           'The original pack contains an ordinary '
                                                           'arena plus ReeYees, Gamorrean and Kell '
                                                           'Dragon variants. Source generator '
                                                           'visibility/spawn limits and no-gun '
                                                           'placements are retained; AI behavior '
                                                           'and two-peer synchronization require '
                                                           'runtime testing.'],
                                                 'runtime_test': {'status': 'not-run-on-this-output',
                                                                  'full_gameplay': False,
                                                                  'note': 'Source review and '
                                                                          'independent structural '
                                                                          'conversion only; engine '
                                                                          'host and two-peer '
                                                                          'gameplay checks remain '
                                                                          'pending.'},
                                                 'runtime_gates': ['Open the converted episode in '
                                                                   'a clean MotS multiplayer '
                                                                   'profile with only its declared '
                                                                   'dependencies.',
                                                                   'Check original pickup '
                                                                   'placement and native MotS '
                                                                   'inventory bindings, authored '
                                                                   'doors/lifts/hazards where '
                                                                   'present, then matched '
                                                                   'second-peer behavior.'],
                                                 'key': 'mp-gladiator-gamorreans'},
                                  'kelldragons': {'tag': 'mp168_k',
                                                  'title': 'Gladiator',
                                                  'author': 'Daniel Yost',
                                                  'source_url': 'https://www.massassi.net/levels/files/168.shtml',
                                                  'download_url': 'https://www.massassi.net/media/levels/files/jkmp/gladiator.zip',
                                                  'massassi_id': 168,
                                                  'download_rank': 49,
                                                  'zip_sha256': 'b99fa725513c81834b3708719ee9a7335c677ecfe3fd28be866921c9e2cfe725',
                                                  'gob_sha256': 'ab1a34e0505891295e9c23abcc22d0998af98fa756360b85d34da075a4a1cab6',
                                                  'gob_member': 'Gladiator.gob',
                                                  'world': 'jkl/gladiatorkell.jkl',
                                                  'sha256': '64915c1850c6a26e51aefe81fef3fab9de6735710600d3503bbc07e525d9f51d',
                                                  'scripts_sha256': 'd4945ea49d2b5849837e65665633efb6ddc82942690f94d0e24eff8e51463a38',
                                                  'episode_type': 2,
                                                  'runtime_cogs': '00_desttrail.cog '
                                                                  '00_smoketrail.cog '
                                                                  'class_sequencer.cog kyle.cog '
                                                                  'pow_backpack.cog pow_bryar.cog '
                                                                  'pow_concrifle.cog '
                                                                  'pow_crossbow.cog pow_health.cog '
                                                                  'pow_railgun.cog '
                                                                  'pow_repeater.cog '
                                                                  'pow_shields.cog '
                                                                  'pow_single_sequencer.cog '
                                                                  'pow_single_thermal.cog '
                                                                  'pow_strifle.cog',
                                                  'runtime_source_sha256': {'00_desttrail.cog': '6c56bf2f756cd63625443d5fa76f8d72521c1f19ed9b61a7ce6252b1ecc00c48',
                                                                            '00_smoketrail.cog': '2a990da3d41131bca2d1481562592742e5f8c543ac846dd95311a361189c7bbf',
                                                                            'class_sequencer.cog': '7a057711f1e6fb33e1a7b410d657738531c5b6664af3259dad3ab16c4b30cae5',
                                                                            'kyle.cog': 'cf68cc4754acd78d2d84297eb6d05df80d0e8e265fa5d5a902b7101f8e523955',
                                                                            'pow_backpack.cog': '7bacc8efb06a8d6b71ab3780f2ab6302ad1c63d245bd9524c0b89258053b08ed',
                                                                            'pow_bryar.cog': 'd533156b8283c2c21f44355f7146192df873f5806499cc57fb9fbfa838a2a169',
                                                                            'pow_concrifle.cog': 'a762451646e8598bc64afc70c6ef5054e434dda6da5a4d5f735c13fef00de011',
                                                                            'pow_crossbow.cog': 'e5dfce5f5f394b670ac2a7a9d2c569085127b1857bc52b3859475ae10b285f85',
                                                                            'pow_health.cog': '764f213b0dfb0623fecef59f46850fc37c5a0e4e0599f15411d35ee4b6ffb011',
                                                                            'pow_railgun.cog': '4dd2252dde766ad47c9e89a1bb59e009431c7c3838e98cd703bbc4332a5d26bc',
                                                                            'pow_repeater.cog': '83505b4b4620ce33e494caab76769e59a9ececceaeef161122ab64dc3861feb6',
                                                                            'pow_shields.cog': '8d515630da6ac31126decd4ca8c94ef840c42edc1110ef102e5f48530d88e8ad',
                                                                            'pow_single_sequencer.cog': '2777cacb7aceff81128cbf8b432cda15a32557f716cabe2ff6111183c79b965e',
                                                                            'pow_single_thermal.cog': 'fbf8c39c853bf5e9a60cf3016bba7a39936c136552ce094b80c872d205c811cf',
                                                                            'pow_strifle.cog': 'edddcde2521e57fcf7d3c8c6e83ec25b7085d6230c4e09cf1387091f08697a73'},
                                                  'environment': 'actor_kd.cog enemygenmp.cog',
                                                  'cog_sha256': {'actor_kd.cog': '26460ded9177e10ef6a145e6f87b0683307b9bf50d9d8264b5c140feabb771bf',
                                                                 'enemygenmp.cog': '2cffad0fc3d0ea138a8f97b8f63b0572fff02e0748c49faf27ff984c50eecdfa'},
                                                  'requires_jksp': False,
                                                  'source_omissions': [],
                                                  'resource_aliases': {},
                                                  'cog_edits': {},
                                                  'native_cog_edits': {},
                                                  'native_template_overrides': {},
                                                  'native_resource_overrides': {},
                                                  'readme_provenance': [{'path': 'Gladiator.txt',
                                                                         'sha256': '5cee07bf8ab36d18cbc641cf0896dca60a84162ecdd24b38d63942f99a84e716',
                                                                         'bytes': 4034}],
                                                  'notes': ['Source review: preserve the authored '
                                                            'multiplayer enemy generator and '
                                                            'source actor damage, death-drop and '
                                                            'Force-skill callback behavior. '
                                                            'Callback message IDs 24, 31 and 34 '
                                                            'are also present in native MotS actor '
                                                            'scripts and are not inventory slots '
                                                            'to remap.',
                                                            'The original pack contains an '
                                                            'ordinary arena plus ReeYees, '
                                                            'Gamorrean and Kell Dragon variants. '
                                                            'Source generator visibility/spawn '
                                                            'limits and no-gun placements are '
                                                            'retained; AI behavior and two-peer '
                                                            'synchronization require runtime '
                                                            'testing.'],
                                                  'runtime_test': {'status': 'not-run-on-this-output',
                                                                   'full_gameplay': False,
                                                                   'note': 'Source review and '
                                                                           'independent structural '
                                                                           'conversion only; '
                                                                           'engine host and '
                                                                           'two-peer gameplay '
                                                                           'checks remain '
                                                                           'pending.'},
                                                  'runtime_gates': ['Open the converted episode in '
                                                                    'a clean MotS multiplayer '
                                                                    'profile with only its '
                                                                    'declared dependencies.',
                                                                    'Check original pickup '
                                                                    'placement and native MotS '
                                                                    'inventory bindings, authored '
                                                                    'doors/lifts/hazards where '
                                                                    'present, then matched '
                                                                    'second-peer behavior.'],
                                                  'key': 'mp-gladiator-kelldragons'}},
                  'notes': ['Complete four-world original episode, including all actor variants; '
                            'no unlisted physical worlds.',
                            'The source enemy generator references an unassigned squadmaker COG '
                            'after deaths; original source behavior is preserved and needs '
                            'explicit AI respawn testing.',
                            'Exact ReeYees-only stlaser.snd alias avoids one differing full-path '
                            'resource: an original commented sound reference is namespaced only '
                            'when that world imports the referenced sound. The byte-equality union '
                            'guard remains strict.'],
                  'runtime_test': {'status': 'exact-payload-host-smoke-passed',
                                   'scope': '30-second hidden MotS multiplayer host per active '
                                            'world',
                                   'full_gameplay': False,
                                   'worlds': [{'case': 'mp-gladiator-arena-v1',
                                               'world': 'br_mp168_a.jkl',
                                               'duration_seconds': 30,
                                               'runtime_sha256': 'fd8ddfc23f09540068318bedcc3f08e5ce6b12ea5ee04ed3cf45fd8ed46b7873',
                                               'tested_archive_sha256': 'ecb6a00a444b4bfaf04af6b2624b3d2241eb640e5c93a853429e58effedbe4c9',
                                               'payload_sha256': 'ee827a4243fcd886803266f9db123f6ecbe09b71360a9c45bbc327ee8904c378',
                                               'evidence_report_sha256': '1f879c97bbdce6ce9733e03ac5570fe0dbbb4069c1e32ca798399875cb855e05'},
                                              {'case': 'mp-gladiator-ree-v1',
                                               'world': 'br_mp168_r.jkl',
                                               'duration_seconds': 30,
                                               'runtime_sha256': 'fd8ddfc23f09540068318bedcc3f08e5ce6b12ea5ee04ed3cf45fd8ed46b7873',
                                               'tested_archive_sha256': 'ecb6a00a444b4bfaf04af6b2624b3d2241eb640e5c93a853429e58effedbe4c9',
                                               'payload_sha256': 'ee827a4243fcd886803266f9db123f6ecbe09b71360a9c45bbc327ee8904c378',
                                               'evidence_report_sha256': '61be67e2ffd5e601ac4fb79d65cf6c1cdb9e3eb9ffb42715284bc1a101add4b5'},
                                              {'case': 'mp-gladiator-gam-v1',
                                               'world': 'br_mp168_g.jkl',
                                               'duration_seconds': 30,
                                               'runtime_sha256': 'fd8ddfc23f09540068318bedcc3f08e5ce6b12ea5ee04ed3cf45fd8ed46b7873',
                                               'tested_archive_sha256': 'ecb6a00a444b4bfaf04af6b2624b3d2241eb640e5c93a853429e58effedbe4c9',
                                               'payload_sha256': 'ee827a4243fcd886803266f9db123f6ecbe09b71360a9c45bbc327ee8904c378',
                                               'evidence_report_sha256': '15e9355e1796920bd759ef921f1a1b10878ca3c48072588a8bfac7d147abeb0e'},
                                              {'case': 'mp-gladiator-kell-v1',
                                               'world': 'br_mp168_k.jkl',
                                               'duration_seconds': 30,
                                               'runtime_sha256': 'fd8ddfc23f09540068318bedcc3f08e5ce6b12ea5ee04ed3cf45fd8ed46b7873',
                                               'tested_archive_sha256': 'ecb6a00a444b4bfaf04af6b2624b3d2241eb640e5c93a853429e58effedbe4c9',
                                               'payload_sha256': 'ee827a4243fcd886803266f9db123f6ecbe09b71360a9c45bbc327ee8904c378',
                                               'evidence_report_sha256': 'b08794c719d2d96db5cf679b0316897924d01afd66243a9f6b0255bc60d35b42'}],
                                   'note': 'Correct MotS multiplayer mode and selected world, '
                                           'advancing simulation, and zero resource diagnostics. '
                                           'This evidence is bound to the canonical game payload; '
                                           'metadata markers may differ. Rendering, authored '
                                           'mechanics and two-peer synchronization are not '
                                           'established.'},
                  'catalog_status': 'prototype'},
 'mp-the-matrix': {'key': 'mp-the-matrix',
                   'tag': 'mp267',
                   'title': 'The Matrix',
                   'author': 'Daniel Yost',
                   'source_url': 'https://www.massassi.net/levels/files/267.shtml',
                   'download_url': 'https://www.massassi.net/media/levels/files/jkmp/matrixlvl.zip',
                   'massassi_id': 267,
                   'download_rank': 44,
                   'zip_sha256': 'c0fad067971d87345be02562614dde1e8bf0df45cb6d82ddf3b900bcdeaa7626',
                   'gob_sha256': '1a084b4acb9fa91e8ef1bcaaf6803ca5236ad19a93885e90f1e8b9ffd7e0c7d0',
                   'gob_member': 'matrix.gob',
                   'episode_sha256': '229c2834f87373cff3096af64e899e0943ecfe7faee7ea1cc1eb6becfb2009a3',
                   'episode_rows': [{'line': 12,
                                     'disc': 2,
                                     'level': 1,
                                     'type': 'LEVEL',
                                     'world': 'jkl/matrix.jkl',
                                     'lightpow': 26,
                                     'darkpow': 31,
                                     'goto_a': -1,
                                     'goto_b': -1,
                                     'world_spec': 'matrix'}],
                   'world_specs': {'matrix': {'tag': 'mp267',
                                              'title': 'The Matrix',
                                              'author': 'Daniel Yost',
                                              'source_url': 'https://www.massassi.net/levels/files/267.shtml',
                                              'download_url': 'https://www.massassi.net/media/levels/files/jkmp/matrixlvl.zip',
                                              'massassi_id': 267,
                                              'download_rank': 44,
                                              'zip_sha256': 'c0fad067971d87345be02562614dde1e8bf0df45cb6d82ddf3b900bcdeaa7626',
                                              'gob_sha256': '1a084b4acb9fa91e8ef1bcaaf6803ca5236ad19a93885e90f1e8b9ffd7e0c7d0',
                                              'gob_member': 'matrix.gob',
                                              'world': 'jkl/matrix.jkl',
                                              'sha256': '7da00d8579216febabb1b51f95db418a5d1fd8b059e055fb06667dd5fcc9ff15',
                                              'scripts_sha256': '2aac0b4eac77685d2de944f22fe0e55d680a9840cbfdb68ebefe88981641a1de',
                                              'episode_type': 2,
                                              'runtime_cogs': '00_desttrail.cog 00_smoketrail.cog '
                                                              'class_sequencer.cog kyle.cog '
                                                              'pow_backpack.cog pow_bryar.cog '
                                                              'pow_concrifle.cog pow_crossbow.cog '
                                                              'pow_energy.cog pow_health.cog '
                                                              'pow_power.cog pow_railcharges.cog '
                                                              'pow_railgun.cog pow_repeater.cog '
                                                              'pow_shields.cog '
                                                              'pow_single_sequencer.cog '
                                                              'pow_single_thermal.cog '
                                                              'pow_strifle.cog',
                                              'runtime_source_sha256': {'00_desttrail.cog': '6c56bf2f756cd63625443d5fa76f8d72521c1f19ed9b61a7ce6252b1ecc00c48',
                                                                        '00_smoketrail.cog': '2a990da3d41131bca2d1481562592742e5f8c543ac846dd95311a361189c7bbf',
                                                                        'class_sequencer.cog': '7a057711f1e6fb33e1a7b410d657738531c5b6664af3259dad3ab16c4b30cae5',
                                                                        'kyle.cog': 'cf68cc4754acd78d2d84297eb6d05df80d0e8e265fa5d5a902b7101f8e523955',
                                                                        'pow_backpack.cog': '7bacc8efb06a8d6b71ab3780f2ab6302ad1c63d245bd9524c0b89258053b08ed',
                                                                        'pow_bryar.cog': 'd533156b8283c2c21f44355f7146192df873f5806499cc57fb9fbfa838a2a169',
                                                                        'pow_concrifle.cog': 'a762451646e8598bc64afc70c6ef5054e434dda6da5a4d5f735c13fef00de011',
                                                                        'pow_crossbow.cog': 'e5dfce5f5f394b670ac2a7a9d2c569085127b1857bc52b3859475ae10b285f85',
                                                                        'pow_energy.cog': '1bcd549121e3e9afd5ebe2bbe4b509d6d022265eee3239a164f3a7816bf10d8f',
                                                                        'pow_health.cog': '764f213b0dfb0623fecef59f46850fc37c5a0e4e0599f15411d35ee4b6ffb011',
                                                                        'pow_power.cog': '073756cb1b74cc2f84393215297cbd6f5e739d15972c283afcccd2130ebb5061',
                                                                        'pow_railcharges.cog': '18e5b0cf2ee4cc133582ba8879577f060b06c8eeda22d63bbc401deb998f57e3',
                                                                        'pow_railgun.cog': '4dd2252dde766ad47c9e89a1bb59e009431c7c3838e98cd703bbc4332a5d26bc',
                                                                        'pow_repeater.cog': '83505b4b4620ce33e494caab76769e59a9ececceaeef161122ab64dc3861feb6',
                                                                        'pow_shields.cog': '8d515630da6ac31126decd4ca8c94ef840c42edc1110ef102e5f48530d88e8ad',
                                                                        'pow_single_sequencer.cog': '2777cacb7aceff81128cbf8b432cda15a32557f716cabe2ff6111183c79b965e',
                                                                        'pow_single_thermal.cog': 'fbf8c39c853bf5e9a60cf3016bba7a39936c136552ce094b80c872d205c811cf',
                                                                        'pow_strifle.cog': 'edddcde2521e57fcf7d3c8c6e83ec25b7085d6230c4e09cf1387091f08697a73'},
                                              'environment': '',
                                              'cog_sha256': {},
                                              'requires_jksp': False,
                                              'source_omissions': [],
                                              'resource_aliases': {},
                                              'cog_edits': {},
                                              'native_cog_edits': {},
                                              'native_template_overrides': {},
                                              'native_resource_overrides': {},
                                              'readme_provenance': [{'path': 'Matrix.txt',
                                                                     'sha256': '2a4bcda3a019b485da9fd89e5dc5f943f76ad61e566a6a90f780927c94f6a10a',
                                                                     'bytes': 2553}],
                                              'notes': ['Source review: the only active original '
                                                        'episode world has no environmental COGs '
                                                        'or authored runtime replacements. '
                                                        'Preserve sector gravity, underwater '
                                                        'shaft, original placements and native '
                                                        'MotS pickup bindings.',
                                                        'Eleven unlisted source worlds are not '
                                                        'part of the selected Matrix episode. '
                                                        'There are no authored active-world COGs '
                                                        'that dynamically load them.'],
                                              'runtime_test': {'status': 'not-run-on-this-output',
                                                               'full_gameplay': False,
                                                               'note': 'Source review and '
                                                                       'independent structural '
                                                                       'conversion only; engine '
                                                                       'host and two-peer gameplay '
                                                                       'checks remain pending.'},
                                              'runtime_gates': ['Open the converted episode in a '
                                                                'clean MotS multiplayer profile '
                                                                'with only its declared '
                                                                'dependencies.',
                                                                'Check original pickup placement '
                                                                'and native MotS inventory '
                                                                'bindings, authored '
                                                                'doors/lifts/hazards where '
                                                                'present, then matched second-peer '
                                                                'behavior.'],
                                              'key': 'mp-the-matrix-matrix'}},
                   'catalog_status': 'prototype',
                   'notes': ['Preserve the original single active row, including its unusual '
                             'row12/CD2/Force26,31 metadata and terminal transitions. OpenJKDF2 '
                             'jkMain_EndLevel applies these legacy Force awards only when '
                             'Main_bMotsCompat is false; the MotS port retains the source metadata '
                             'without adding powers.',
                             'All eleven unlisted physical JKLs remain documented as orphan source '
                             'content, not additional playable maps.'],
                   'runtime_test': {'status': 'exact-payload-host-smoke-passed',
                                    'scope': '30-second hidden MotS multiplayer host per active '
                                             'world',
                                    'full_gameplay': False,
                                    'worlds': [{'case': 'mp-the-matrix-v1',
                                                'world': 'br_mp267.jkl',
                                                'duration_seconds': 30,
                                                'runtime_sha256': 'fd8ddfc23f09540068318bedcc3f08e5ce6b12ea5ee04ed3cf45fd8ed46b7873',
                                                'tested_archive_sha256': '99c555ac7d475a4dc05114c35441378847a050011ef965ca8829260022a14c1a',
                                                'payload_sha256': 'c2c5985f3921fa908bfbc9a9475615d70e16ad82bd17b5084c63ae20a2878608',
                                                'evidence_report_sha256': '02f1c4f2879a1496d49ab5f03a240c0fb7be6f9fee8b3e80a4bfdbefd825a62b'}],
                                    'note': 'Correct MotS multiplayer mode and selected world, '
                                            'advancing simulation, and zero resource diagnostics. '
                                            'This evidence is bound to the canonical game payload; '
                                            'metadata markers may differ. Rendering, authored '
                                            'mechanics and two-peer synchronization are not '
                                            'established.'}}}


# Source-only recipe for the complete three-world standalone tournament pack.
PACKS['mp-dbz-tdir-tournament'] = {'title': 'DBZ: TDIR Tournament Level Pack',
 'author': 'ctsketch and Ubuu aka iostream',
 'source_url': 'https://www.massassi.net/levels/files/1814.shtml',
 'download_url': 'https://www.massassi.net/media/levels/files/jkmp/dbztdirtm.zip',
 'massassi_id': 1814,
 'download_rank': 42,
 'zip_sha256': '6c4cbb9db2992c2be5945186776072d4e392631260aaeb607597bbdff0ab596a',
 'gob_sha256': '89d29eee0adb82b5d8a6a303293cca23bfbc3421178b6ce3b18ad53fc2fe417c',
 'gob_member': 'DBZTDIR_TM.gob',
 'tag': 'mp1814',
 'episode_sha256': 'df9b4e3dd3be1f0bde11bf60991703c86dde644e642fefa299ebc333410fc46e',
 'episode_rows': [{'line': 10,
                   'disc': 1,
                   'level': 1,
                   'type': 'LEVEL',
                   'world': 'jkl/cellarena.jkl',
                   'lightpow': 0,
                   'darkpow': 0,
                   'goto_a': -1,
                   'goto_b': -1,
                   'world_spec': 'cell'},
                  {'line': 11,
                   'disc': 0,
                   'level': 2,
                   'type': 'LEVEL',
                   'world': 'jkl/budoukai.jkl',
                   'lightpow': 0,
                   'darkpow': 0,
                   'goto_a': -1,
                   'goto_b': -1,
                   'world_spec': 'budoukai'},
                  {'line': 11,
                   'disc': 0,
                   'level': 2,
                   'type': 'LEVEL',
                   'world': 'jkl/heaventourney.jkl',
                   'lightpow': 0,
                   'darkpow': 0,
                   'goto_a': -1,
                   'goto_b': -1,
                   'world_spec': 'heaven'}],
 'episode_row_repairs': [{'row_index': 2,
                          'old_line': 11,
                          'new_line': 12,
                          'row_sha256': '3c41e1db2d62419b98a60998fedb166ba0d0df9f916401858f1a68006c248da0',
                          'count': 1,
                          'reason': 'The third terminal row repeats row11. No episode branch '
                                    'refers to row11 or row12 and no authored COG exists; only its '
                                    'duplicate line identifier becomes12. Keep level2, order, CD, '
                                    'Force fields, filenames and labels.'}],
 'world_specs': {'cell': {'title': 'DBZ: TDIR Tournament Level Pack',
                          'author': 'ctsketch and Ubuu aka iostream',
                          'source_url': 'https://www.massassi.net/levels/files/1814.shtml',
                          'download_url': 'https://www.massassi.net/media/levels/files/jkmp/dbztdirtm.zip',
                          'massassi_id': 1814,
                          'download_rank': 42,
                          'zip_sha256': '6c4cbb9db2992c2be5945186776072d4e392631260aaeb607597bbdff0ab596a',
                          'gob_sha256': '89d29eee0adb82b5d8a6a303293cca23bfbc3421178b6ce3b18ad53fc2fe417c',
                          'gob_member': 'DBZTDIR_TM.gob',
                          'tag': 'mp1814_c',
                          'world': 'jkl/cellarena.jkl',
                          'sha256': '460c0481d8e16729562548a964d6667f3c4f69983bd983523c9885488409808f',
                          'scripts_sha256': '7bc1df0d6594fee753f5cab363ccdfb2d2db479e0e7b67ef4ea15af3d91347d7',
                          'episode_type': 2,
                          'runtime_cogs': '00_desttrail.cog 00_smoketrail.cog class_sequencer.cog '
                                          'kyle.cog pow_backpack.cog pow_bryar.cog '
                                          'pow_concrifle.cog pow_crossbow.cog pow_railgun.cog '
                                          'pow_repeater.cog pow_single_sequencer.cog '
                                          'pow_single_thermal.cog pow_strifle.cog',
                          'runtime_source_sha256': {'00_desttrail.cog': '6c56bf2f756cd63625443d5fa76f8d72521c1f19ed9b61a7ce6252b1ecc00c48',
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
                                                    'pow_strifle.cog': 'edddcde2521e57fcf7d3c8c6e83ec25b7085d6230c4e09cf1387091f08697a73'},
                          'environment': '',
                          'cog_sha256': {},
                          'requires_jksp': False,
                          'source_omissions': [],
                          'resource_aliases': {},
                          'cog_edits': {},
                          'native_cog_edits': {},
                          'native_template_overrides': {},
                          'native_resource_overrides': {},
                          'readme_provenance': [{'path': 'readme.txt',
                                                 'sha256': '2b6dc26d0befc556c8a5def4a4d0dd3639bd9b214cf97efe772853ce33133f20',
                                                 'bytes': 4929}],
                          'notes': ['Original archive has no authored COG files and this world has '
                                    'no placed COG instances. All13 script-table controllers are '
                                    'hash-pinned stock JK player, trail, weapon or pickup '
                                    'controllers; ordinary gameplay uses the reviewed native MotS '
                                    'bindings.',
                                    'Preserve authored geometry, things, flags, UVs and world '
                                    'physics with existing exact MotS format/lighting expansion '
                                    'and local dependency namespacing. No TDIR mod, skin, Force or '
                                    'startup overlay is installed.',
                                    'This world is part of the complete three-world DBZ: TDIR '
                                    'Tournament pack. Original notice is retained unchanged; '
                                    'source wording is not a redistribution license.'],
                          'runtime_test': {'status': 'pack-host-smoke-recorded',
                                           'full_gameplay': False,
                                           'note': 'Evidence is attached to the final complete '
                                                   'pack; component output alone was not hosted.'},
                          'runtime_gates': ['Open all3 original worlds through their retained '
                                            'episode order in clean OpenJKDF2 MotS multiplayer.',
                                            'Check native MotS weapon pickup slots, ammo, player '
                                            'spawn/respawn, source geometry/lighting appearance '
                                            'and matched second-peer behavior.']},
                 'budoukai': {'title': 'DBZ: TDIR Tournament Level Pack',
                              'author': 'ctsketch and Ubuu aka iostream',
                              'source_url': 'https://www.massassi.net/levels/files/1814.shtml',
                              'download_url': 'https://www.massassi.net/media/levels/files/jkmp/dbztdirtm.zip',
                              'massassi_id': 1814,
                              'download_rank': 42,
                              'zip_sha256': '6c4cbb9db2992c2be5945186776072d4e392631260aaeb607597bbdff0ab596a',
                              'gob_sha256': '89d29eee0adb82b5d8a6a303293cca23bfbc3421178b6ce3b18ad53fc2fe417c',
                              'gob_member': 'DBZTDIR_TM.gob',
                              'tag': 'mp1814_b',
                              'world': 'jkl/budoukai.jkl',
                              'sha256': '76e766c3bf0747df0eecfad6b2d5892eeef26da50b9c53d516f45ed02335a946',
                              'scripts_sha256': '7bc1df0d6594fee753f5cab363ccdfb2d2db479e0e7b67ef4ea15af3d91347d7',
                              'episode_type': 2,
                              'runtime_cogs': '00_desttrail.cog 00_smoketrail.cog '
                                              'class_sequencer.cog kyle.cog pow_backpack.cog '
                                              'pow_bryar.cog pow_concrifle.cog pow_crossbow.cog '
                                              'pow_railgun.cog pow_repeater.cog '
                                              'pow_single_sequencer.cog pow_single_thermal.cog '
                                              'pow_strifle.cog',
                              'runtime_source_sha256': {'00_desttrail.cog': '6c56bf2f756cd63625443d5fa76f8d72521c1f19ed9b61a7ce6252b1ecc00c48',
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
                                                        'pow_strifle.cog': 'edddcde2521e57fcf7d3c8c6e83ec25b7085d6230c4e09cf1387091f08697a73'},
                              'environment': '',
                              'cog_sha256': {},
                              'requires_jksp': False,
                              'source_omissions': [],
                              'resource_aliases': {},
                              'cog_edits': {},
                              'native_cog_edits': {},
                              'native_template_overrides': {},
                              'native_resource_overrides': {},
                              'readme_provenance': [{'path': 'readme.txt',
                                                     'sha256': '2b6dc26d0befc556c8a5def4a4d0dd3639bd9b214cf97efe772853ce33133f20',
                                                     'bytes': 4929}],
                              'notes': ['Original archive has no authored COG files and this world '
                                        'has no placed COG instances. All13 script-table '
                                        'controllers are hash-pinned stock JK player, trail, '
                                        'weapon or pickup controllers; ordinary gameplay uses the '
                                        'reviewed native MotS bindings.',
                                        'Preserve authored geometry, things, flags, UVs and world '
                                        'physics with existing exact MotS format/lighting '
                                        'expansion and local dependency namespacing. No TDIR mod, '
                                        'skin, Force or startup overlay is installed.',
                                        'This world is part of the complete three-world DBZ: TDIR '
                                        'Tournament pack. Original notice is retained unchanged; '
                                        'source wording is not a redistribution license.'],
                              'runtime_test': {'status': 'pack-host-smoke-recorded',
                                               'full_gameplay': False,
                                               'note': 'Evidence is attached to the final complete '
                                                       'pack; component output alone was not '
                                                       'hosted.'},
                              'runtime_gates': ['Open all3 original worlds through their retained '
                                                'episode order in clean OpenJKDF2 MotS '
                                                'multiplayer.',
                                                'Check native MotS weapon pickup slots, ammo, '
                                                'player spawn/respawn, source geometry/lighting '
                                                'appearance and matched second-peer behavior.']},
                 'heaven': {'title': 'DBZ: TDIR Tournament Level Pack',
                            'author': 'ctsketch and Ubuu aka iostream',
                            'source_url': 'https://www.massassi.net/levels/files/1814.shtml',
                            'download_url': 'https://www.massassi.net/media/levels/files/jkmp/dbztdirtm.zip',
                            'massassi_id': 1814,
                            'download_rank': 42,
                            'zip_sha256': '6c4cbb9db2992c2be5945186776072d4e392631260aaeb607597bbdff0ab596a',
                            'gob_sha256': '89d29eee0adb82b5d8a6a303293cca23bfbc3421178b6ce3b18ad53fc2fe417c',
                            'gob_member': 'DBZTDIR_TM.gob',
                            'tag': 'mp1814_h',
                            'world': 'jkl/heaventourney.jkl',
                            'sha256': '93cd60422f5d611f5e21d326774ebc94a243d5c7ad8613b3b501adefba815e8e',
                            'scripts_sha256': '7bc1df0d6594fee753f5cab363ccdfb2d2db479e0e7b67ef4ea15af3d91347d7',
                            'episode_type': 2,
                            'runtime_cogs': '00_desttrail.cog 00_smoketrail.cog '
                                            'class_sequencer.cog kyle.cog pow_backpack.cog '
                                            'pow_bryar.cog pow_concrifle.cog pow_crossbow.cog '
                                            'pow_railgun.cog pow_repeater.cog '
                                            'pow_single_sequencer.cog pow_single_thermal.cog '
                                            'pow_strifle.cog',
                            'runtime_source_sha256': {'00_desttrail.cog': '6c56bf2f756cd63625443d5fa76f8d72521c1f19ed9b61a7ce6252b1ecc00c48',
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
                                                      'pow_strifle.cog': 'edddcde2521e57fcf7d3c8c6e83ec25b7085d6230c4e09cf1387091f08697a73'},
                            'environment': '',
                            'cog_sha256': {},
                            'requires_jksp': False,
                            'source_omissions': [],
                            'resource_aliases': {},
                            'cog_edits': {},
                            'native_cog_edits': {},
                            'native_template_overrides': {},
                            'native_resource_overrides': {},
                            'readme_provenance': [{'path': 'readme.txt',
                                                   'sha256': '2b6dc26d0befc556c8a5def4a4d0dd3639bd9b214cf97efe772853ce33133f20',
                                                   'bytes': 4929}],
                            'notes': ['Original archive has no authored COG files and this world '
                                      'has no placed COG instances. All13 script-table controllers '
                                      'are hash-pinned stock JK player, trail, weapon or pickup '
                                      'controllers; ordinary gameplay uses the reviewed native '
                                      'MotS bindings.',
                                      'Preserve authored geometry, things, flags, UVs and world '
                                      'physics with existing exact MotS format/lighting expansion '
                                      'and local dependency namespacing. No TDIR mod, skin, Force '
                                      'or startup overlay is installed.',
                                      'This world is part of the complete three-world DBZ: TDIR '
                                      'Tournament pack. Original notice is retained unchanged; '
                                      'source wording is not a redistribution license.'],
                            'runtime_test': {'status': 'pack-host-smoke-recorded',
                                             'full_gameplay': False,
                                             'note': 'Evidence is attached to the final complete '
                                                     'pack; component output alone was not '
                                                     'hosted.'},
                            'runtime_gates': ['Open all3 original worlds through their retained '
                                              'episode order in clean OpenJKDF2 MotS multiplayer.',
                                              'Check native MotS weapon pickup slots, ammo, player '
                                              'spawn/respawn, source geometry/lighting appearance '
                                              'and matched second-peer behavior.']}},
 'catalog_status': 'prototype',
 'notes': ["Cell's Game Arena, Budoukai and Heaven's Tournament are all active; no physical source "
           'world is omitted. No TDIR gameplay mod is required or automatically loaded.',
           'OpenJKDF2 episode branches resolve lineNum while multiplayer selection identifies '
           'filenames. All six original goto fields are-1; exactly the later duplicate row '
           'identifier11 is renamed12. Preserve the separate repeated level2 column and all '
           'title/loading values.',
           'Original README credits Ubuu/iostream, ctsketch and the TDIR crew. It contains '
           'contradictory distribution boilerplate; preserve its exact bytes locally and make no '
           'asset redistribution claim.'],
 'runtime_test': {'status': 'exact-payload-host-smoke-passed',
                  'scope': '30-second hidden MotS multiplayer host per active world',
                  'full_gameplay': False,
                  'worlds': [{'case': 'mp-dbz1814-c-v1',
                              'world': 'br_mp1814_c.jkl',
                              'mode': 'mp',
                              'duration_seconds': 30,
                              'runtime_sha256': 'fd8ddfc23f09540068318bedcc3f08e5ce6b12ea5ee04ed3cf45fd8ed46b7873',
                              'tested_archive_sha256': '3d75d6bb748ec02d0a082332c8366388712997218de99a8bed4088303584521a',
                              'payload_sha256': '3d75d6bb748ec02d0a082332c8366388712997218de99a8bed4088303584521a',
                              'evidence_report_sha256': 'ff2b8a48e973cbb73baa38c0b7f6110e5bacfb69995a03eb781263e0cd00c92b',
                              'gates': {'survived_requested_window': True,
                                        'observed_expected_mode': True,
                                        'expected_episode_world': True,
                                        'simulation_advanced': True,
                                        'inputs_and_staged_files_unchanged': True,
                                        'baseline_unchanged': True,
                                        'no_visible_window': True,
                                        'no_harness_error': True},
                              'resource_diagnostic_count': 0},
                             {'case': 'mp-dbz1814-b-v1',
                              'world': 'br_mp1814_b.jkl',
                              'mode': 'mp',
                              'duration_seconds': 30,
                              'runtime_sha256': 'fd8ddfc23f09540068318bedcc3f08e5ce6b12ea5ee04ed3cf45fd8ed46b7873',
                              'tested_archive_sha256': '3d75d6bb748ec02d0a082332c8366388712997218de99a8bed4088303584521a',
                              'payload_sha256': '3d75d6bb748ec02d0a082332c8366388712997218de99a8bed4088303584521a',
                              'evidence_report_sha256': 'd0201380d490c7468a3d7d16de3f7afbaeb9ba6607e4a63b17ec3f0dcdcb4f13',
                              'gates': {'survived_requested_window': True,
                                        'observed_expected_mode': True,
                                        'expected_episode_world': True,
                                        'simulation_advanced': True,
                                        'inputs_and_staged_files_unchanged': True,
                                        'baseline_unchanged': True,
                                        'no_visible_window': True,
                                        'no_harness_error': True},
                              'resource_diagnostic_count': 0},
                             {'case': 'mp-dbz1814-h-v1',
                              'world': 'br_mp1814_h.jkl',
                              'mode': 'mp',
                              'duration_seconds': 30,
                              'runtime_sha256': 'fd8ddfc23f09540068318bedcc3f08e5ce6b12ea5ee04ed3cf45fd8ed46b7873',
                              'tested_archive_sha256': '3d75d6bb748ec02d0a082332c8366388712997218de99a8bed4088303584521a',
                              'payload_sha256': '3d75d6bb748ec02d0a082332c8366388712997218de99a8bed4088303584521a',
                              'evidence_report_sha256': 'b84af04d0a6c8c5dfe0506c4d46ab5abeb0dee1417587915e63bb558d76a4622',
                              'gates': {'survived_requested_window': True,
                                        'observed_expected_mode': True,
                                        'expected_episode_world': True,
                                        'simulation_advanced': True,
                                        'inputs_and_staged_files_unchanged': True,
                                        'baseline_unchanged': True,
                                        'no_visible_window': True,
                                        'no_harness_error': True},
                              'resource_diagnostic_count': 0}],
                  'note': 'Loading and advancing simulation only; rendering, mechanics, respawn '
                          'and peers remain open.'}}

"""Hash-pinned local conversion specifications for Purgatory and NOFpuXnk maps.

Original source-only metadata; no game or level resource bytes are included.
Audit: current Massassi catalogue plus each original ZIP/readme, 2026-09-08.
All 1,289 JK MP catalogue rows yielded three verified NOFpuXnk author entries:
Courtyard (Adam (NOFpuXnk) Freeman), Shadow Caverns, and Deicide.
Keep original readmes with locally generated assets; publication rights differ.
These are conversion specifications, not gameplay or visual parity certificates.
"""

CATALOG = {'purgatory': {'tag': 'purgatory',
               'title': 'Purgatory',
               'author': 'SM Sith Lord',
               'source_url': 'https://www.massassi.net/levels/files/1202.shtml',
               'download_url': 'https://www.massassi.net/media/levels/files/jkmp/purgatory.zip',
               'zip_sha256': 'd58c89afcb75820da23cd3844890f8fca589d12ea2ee4cc341f1597d84db6a2d',
               'gob_sha256': '49f7365b31f5169b5fc02262bd243989b027c0e0a7535abfc56e436197693a4c',
               'gob_member': 'purgatory.gob',
               'world': 'jkl/purgatory.jkl',
               'sha256': '27b4b50513ba34b6d9229e5e68ed5406424cb79d4a716059c7bff6a1dd6b5188',
               'scripts_sha256': '60e8c36c7f0c479c1cb4a0879f42a0354579bc88382a31d0d39d90381b3fd589',
               'episode_type': 2,
               'runtime_cogs': '00_desttrail.cog 00_smoketrail.cog class_sequencer.cog kyle.cog '
                               'pow_backpack.cog pow_bacta.cog pow_bryar.cog pow_concrifle.cog '
                               'pow_crossbow.cog pow_darkside.cog pow_energy.cog pow_health.cog '
                               'pow_lightside.cog pow_mana.cog pow_power.cog pow_powerboost.cog '
                               'pow_railcharges.cog pow_railgun.cog pow_repeater.cog pow_revive.cog '
                               'pow_single_sequencer.cog pow_single_thermal.cog pow_strifle.cog '
                               'pow_supershield.cog pow_vest.cog',
               'environment': '00_door.cog 00_elev_switch.cog 00_hidethings.cog 00_lightning.cog '
                              '00_sectordamage.cog 00_sectorthrust.cog 00_slideceiling.cog autodoor.cog '
                              'bts_2door_cli.cog bts_2door_srv.cog lightswitch.cog mines.cog niceday.cog '
                              'nteleport.cog pitenter.cog purgatory_start2.cog purgcamera.cog purgdoor.cog '
                              'random_teleport2.cog scream.cog scrolltexture.cog switch_door.cog '
                              'text_voice.cog tmptrap.cog togglecam.cog xtank4.cog xtank4rd.cog',
               'requires_jksp': False,
               'cog_sha256': {'00_desttrail.cog': '6c56bf2f756cd63625443d5fa76f8d72521c1f19ed9b61a7ce6252b1ecc00c48',
                              '00_door.cog': 'a07fb10fadbc81bf4a970cd4ced495240ccfa86f35e3f9de954729d65cbfba5a',
                              '00_elev_switch.cog': 'c1e492ba2c3b8cc0399f777e8a61338e4a1f9aed816ab3e62974e8b92d2adcc3',
                              '00_hidethings.cog': '6c1f7a34622e26212ca50038bfba98b70dac284bccbd6311d4ed00c7c760471f',
                              '00_lightning.cog': 'cc0ec0e7a4d1e01c775d512b203824a1abd43bf33487c637da4bbeb176be32c4',
                              '00_sectordamage.cog': '301f17f82d92578b686008af8d87f266e6d762166c042a97d7f428a82b1eefde',
                              '00_sectorthrust.cog': '6d63da50cef46ca9279d1acd957d464ebfceda257b995bdaa4b009c13efa7b47',
                              '00_slideceiling.cog': '3d7103359ab74f5b7732445b96477896637121cf8b1600ae8985eb02407b0135',
                              '00_smoketrail.cog': '2a990da3d41131bca2d1481562592742e5f8c543ac846dd95311a361189c7bbf',
                              'autodoor.cog': '3fbcf9ebe3090226bf8fa449b7d879c2820ce2e36db0383d66b1ef00b8e1a236',
                              'bts_2door_cli.cog': '837e3b912ec14e91788059584b2badaf6b83a100eef44f26a865effeb6625cf0',
                              'bts_2door_srv.cog': 'f0577cd020504d53cc2836f3c66dc3f898400ec6416b9d263914d28945e9679d',
                              'class_sequencer.cog': '7a057711f1e6fb33e1a7b410d657738531c5b6664af3259dad3ab16c4b30cae5',
                              'kyle.cog': 'cf68cc4754acd78d2d84297eb6d05df80d0e8e265fa5d5a902b7101f8e523955',
                              'lightswitch.cog': '2ffe47b8e2f135f5cf8168f11b7a31775daca8e5ca4876c94030acf71e7141b0',
                              'mines.cog': 'a38fc96eb46744cb19bd4f980f8640237a2f25df70a192529efad2e6a134bc70',
                              'niceday.cog': '5824492cbcee7967530a3b4d8de2a8de2307cbd603da0496432f3613f5bc5979',
                              'nteleport.cog': '47f8813b07898fbc2197d0c86c5451ac2c3c2ae7e9382a85cb2eb1ad34437ab4',
                              'pitenter.cog': 'aec01e1ba9e3c3bf4ea0bbbb1e0a24e8191e7a00ca3e8d99df03104a3459d744',
                              'pow_backpack.cog': '7bacc8efb06a8d6b71ab3780f2ab6302ad1c63d245bd9524c0b89258053b08ed',
                              'pow_bacta.cog': '8b420d7556d92a9f2bcfbb99aeac690e85d7beb54baa7f7e7321f4121b090d56',
                              'pow_bryar.cog': 'd533156b8283c2c21f44355f7146192df873f5806499cc57fb9fbfa838a2a169',
                              'pow_concrifle.cog': 'a762451646e8598bc64afc70c6ef5054e434dda6da5a4d5f735c13fef00de011',
                              'pow_crossbow.cog': 'e5dfce5f5f394b670ac2a7a9d2c569085127b1857bc52b3859475ae10b285f85',
                              'pow_darkside.cog': '739d2bd52cd1ad550178805a780db8095a1a34bb5d366c41d5871995b069c504',
                              'pow_energy.cog': '1bcd549121e3e9afd5ebe2bbe4b509d6d022265eee3239a164f3a7816bf10d8f',
                              'pow_health.cog': '764f213b0dfb0623fecef59f46850fc37c5a0e4e0599f15411d35ee4b6ffb011',
                              'pow_lightside.cog': 'a5f632793d2366554dd40d6cefeadba3e111a7f52b3b626c3a53c698cb84abf3',
                              'pow_mana.cog': 'f7253958c01e90bfc99d162ec0af0c2cc819e561c817165bcf434dadb776a30a',
                              'pow_power.cog': '073756cb1b74cc2f84393215297cbd6f5e739d15972c283afcccd2130ebb5061',
                              'pow_powerboost.cog': '1dd3214a7c95a9c88f32c0710747648aefcc54495d666496cbfeae697aa085d8',
                              'pow_railcharges.cog': '18e5b0cf2ee4cc133582ba8879577f060b06c8eeda22d63bbc401deb998f57e3',
                              'pow_railgun.cog': '4dd2252dde766ad47c9e89a1bb59e009431c7c3838e98cd703bbc4332a5d26bc',
                              'pow_repeater.cog': '83505b4b4620ce33e494caab76769e59a9ececceaeef161122ab64dc3861feb6',
                              'pow_revive.cog': '6904811bf2f22d8fbfde1c206ec8f1c0da2ed66f4217312fa31c934f52f3214e',
                              'pow_single_sequencer.cog': '2777cacb7aceff81128cbf8b432cda15a32557f716cabe2ff6111183c79b965e',
                              'pow_single_thermal.cog': 'fbf8c39c853bf5e9a60cf3016bba7a39936c136552ce094b80c872d205c811cf',
                              'pow_strifle.cog': 'edddcde2521e57fcf7d3c8c6e83ec25b7085d6230c4e09cf1387091f08697a73',
                              'pow_supershield.cog': '73d88c22033240be74810cb8457fd94834a7d3aa35065a102312f4289730d004',
                              'pow_vest.cog': 'd3550f626554565280f3fa30bbc4c0c5b9032caad6f6d5fed47e16732efe2d5f',
                              'purgatory_start2.cog': 'cd6744e5c458475e4cd406d11076c2d74b38618c6763e1c7379169741e397a54',
                              'purgcamera.cog': '7d53b5cff09a4293e8333ddb9b6b1382d037c9fdae4f3590e09e578bd7e131c6',
                              'purgdoor.cog': 'ab08228f492b6d75edb828a4ee72e0a894cda65b82ec7be07b3f7724c8d871ef',
                              'random_teleport2.cog': '551a57e1a41f10be9c7500bf5df074a3a45bbce3b157ddeec4a9fd79e5643479',
                              'scream.cog': 'b81c83fd75df5cce64c9add719002ec2bcbe53ca3123edcafa0ee602d2745cb2',
                              'scrolltexture.cog': '5a3b7e2b29f71d3bbd5d4a50d2fb58114d012da3fa37a5ad5cd09907c86902f6',
                              'switch_door.cog': '7c7207d45f9abc2261c50fe4886b6dc58effcb52f78c86a6003a5b6c22968c80',
                              'text_voice.cog': '5824492cbcee7967530a3b4d8de2a8de2307cbd603da0496432f3613f5bc5979',
                              'tmptrap.cog': 'f8bf0339ad51d0f4466effc56463364d95e138ffc98f1fff3bc4b6ebfc99b4b7',
                              'togglecam.cog': '4483cab8190386c3a736074b5457ad24e5680bb8b21587df36eebdb8602a8685',
                              'xtank4.cog': '8c4e0711fe15256c93a709f55192eddbc070d5999e8fc48d19595a86e54958ca',
                              'xtank4rd.cog': '2ef6e12f2b1dd3bfa7f6e4a4f437ab10c2a3fd2a7241eaf6cd6352ac2c3639f6'},
               'source_omissions': [{'name': 'kk60008.wav',
                                     'referrer': 'cog/niceday.cog',
                                     'referrer_sha256': '5824492cbcee7967530a3b4d8de2a8de2307cbd603da0496432f3613f5bc5979',
                                     'reason': 'Original absent sound table/default entry. All three placed '
                                               'text/voice instances override the default with available '
                                               'SCREEM3.WAV, SCARY3.WAV or I00BO03Z.WAV. Preserve absence '
                                               'rather than supply a guessed sound.'},
                                    {'name': 'kk60008.wav',
                                     'referrer': 'cog/text_voice.cog',
                                     'referrer_sha256': '5824492cbcee7967530a3b4d8de2a8de2307cbd603da0496432f3613f5bc5979',
                                     'reason': 'Original absent sound table/default entry. All three placed '
                                               'text/voice instances override the default with available '
                                               'SCREEM3.WAV, SCARY3.WAV or I00BO03Z.WAV. Preserve absence '
                                               'rather than supply a guessed sound.'},
                                    {'name': 'kk60008.wav',
                                     'referrer': 'jkl/purgatory.jkl',
                                     'referrer_sha256': '27b4b50513ba34b6d9229e5e68ed5406424cb79d4a716059c7bff6a1dd6b5188',
                                     'reason': 'Original absent sound table/default entry. All three placed '
                                               'text/voice instances override the default with available '
                                               'SCREEM3.WAV, SCARY3.WAV or I00BO03Z.WAV. Preserve absence '
                                               'rather than supply a guessed sound.'},
                                    {'name': 'nat.mat',
                                     'referrer': 'jkl/purgatory.jkl',
                                     'referrer_sha256': '27b4b50513ba34b6d9229e5e68ed5406424cb79d4a716059c7bff6a1dd6b5188',
                                     'reason': 'Original absent material301 on textured geo4 '
                                               'surface7404/sector749; preserve its original '
                                               'missing-material fallback without inventing or bundling '
                                               'optional artwork.'}],
               'resource_aliases': {},
               'cog_edits': {}},
 'courtyard': {'tag': 'courtyard',
               'title': 'Courtyard',
               'author': 'Adam (NOFpuXnk) Freeman',
               'source_url': 'https://www.massassi.net/levels/files/1122.shtml',
               'download_url': 'https://www.massassi.net/media/levels/files/jkmp/courtyard.zip',
               'zip_sha256': 'c0a13e6a6ead717eaa7bf3b96f41dcc60fda6ee15f382975c63cc5c8cf8b5109',
               'gob_sha256': '408e9a44df3b1ded8abe7b7a49c530b68704671415dd823595078782047ec724',
               'gob_member': 'courtyard.gob',
               'world': 'jkl/courtyard.jkl',
               'sha256': '6c1208570c656ddf838505a08db1d8611274fc516ed928996d5c17c878c002be',
               'scripts_sha256': 'fb061f01f7264e8714a091b3bf79fd7b7a8fed287e6849de4093aa467ce28fe9',
               'episode_type': 2,
               'runtime_cogs': '00_desttrail.cog 00_smoketrail.cog class_sequencer.cog kyle.cog '
                               'pow_backpack.cog pow_bacta.cog pow_bryar.cog pow_concrifle.cog '
                               'pow_crossbow.cog pow_health.cog pow_lightside.cog pow_mana.cog pow_power.cog '
                               'pow_powerboost.cog pow_railcharges.cog pow_railgun.cog pow_repeater.cog '
                               'pow_sequencer.cog pow_shields.cog pow_single_sequencer.cog '
                               'pow_single_thermal.cog pow_strifle.cog pow_supershield.cog pow_thermal.cog',
               'environment': '17a_stream.cog courtyard_start.cog eye_actor1.cog',
               'requires_jksp': True,
               'cog_sha256': {'00_desttrail.cog': '6c56bf2f756cd63625443d5fa76f8d72521c1f19ed9b61a7ce6252b1ecc00c48',
                              '00_smoketrail.cog': '2a990da3d41131bca2d1481562592742e5f8c543ac846dd95311a361189c7bbf',
                              '17a_stream.cog': 'daf2ca0bc289a36dcba895fb027cf9912204f81af62d5f0658a5aae9de3cdc3e',
                              'class_sequencer.cog': '7a057711f1e6fb33e1a7b410d657738531c5b6664af3259dad3ab16c4b30cae5',
                              'courtyard_start.cog': 'd0e7dbe98e237b86a3cc79ae2e71f26d9293aeb578abe8cc0c5aecf5afd545da',
                              'eye_actor1.cog': '8a86b857b808103769ed56fa82f7119c79fea0a5dea16234e2e4463db5fff3c5',
                              'kyle.cog': 'cf68cc4754acd78d2d84297eb6d05df80d0e8e265fa5d5a902b7101f8e523955',
                              'pow_backpack.cog': '7bacc8efb06a8d6b71ab3780f2ab6302ad1c63d245bd9524c0b89258053b08ed',
                              'pow_bacta.cog': '8b420d7556d92a9f2bcfbb99aeac690e85d7beb54baa7f7e7321f4121b090d56',
                              'pow_bryar.cog': 'd533156b8283c2c21f44355f7146192df873f5806499cc57fb9fbfa838a2a169',
                              'pow_concrifle.cog': 'a762451646e8598bc64afc70c6ef5054e434dda6da5a4d5f735c13fef00de011',
                              'pow_crossbow.cog': 'e5dfce5f5f394b670ac2a7a9d2c569085127b1857bc52b3859475ae10b285f85',
                              'pow_health.cog': '764f213b0dfb0623fecef59f46850fc37c5a0e4e0599f15411d35ee4b6ffb011',
                              'pow_lightside.cog': 'a5f632793d2366554dd40d6cefeadba3e111a7f52b3b626c3a53c698cb84abf3',
                              'pow_mana.cog': 'f7253958c01e90bfc99d162ec0af0c2cc819e561c817165bcf434dadb776a30a',
                              'pow_power.cog': '073756cb1b74cc2f84393215297cbd6f5e739d15972c283afcccd2130ebb5061',
                              'pow_powerboost.cog': '1dd3214a7c95a9c88f32c0710747648aefcc54495d666496cbfeae697aa085d8',
                              'pow_railcharges.cog': '18e5b0cf2ee4cc133582ba8879577f060b06c8eeda22d63bbc401deb998f57e3',
                              'pow_railgun.cog': '4dd2252dde766ad47c9e89a1bb59e009431c7c3838e98cd703bbc4332a5d26bc',
                              'pow_repeater.cog': '83505b4b4620ce33e494caab76769e59a9ececceaeef161122ab64dc3861feb6',
                              'pow_sequencer.cog': '0f5b9acde5776625fd32f7d7582c4676dfc3b64cf784614fcd69733bcd324392',
                              'pow_shields.cog': '8d515630da6ac31126decd4ca8c94ef840c42edc1110ef102e5f48530d88e8ad',
                              'pow_single_sequencer.cog': '2777cacb7aceff81128cbf8b432cda15a32557f716cabe2ff6111183c79b965e',
                              'pow_single_thermal.cog': 'fbf8c39c853bf5e9a60cf3016bba7a39936c136552ce094b80c872d205c811cf',
                              'pow_strifle.cog': 'edddcde2521e57fcf7d3c8c6e83ec25b7085d6230c4e09cf1387091f08697a73',
                              'pow_supershield.cog': '73d88c22033240be74810cb8457fd94834a7d3aa35065a102312f4289730d004',
                              'pow_thermal.cog': '962d2fb78f1e818439056039b76573f69ec50b0ffcea442cecedb05783290f3b'},
               'source_omissions': [],
               'resource_aliases': {},
               'cog_edits': {},
               'missing_template_arguments': [{'row': '2:',
                                               'cog': 'eye_actor1.cog',
                                               'symbol': 'enemy_tpl',
                                               'name': 'max',
                                               'reason': 'Original Courtyard generator instance names MAX, '
                                                         'absent from its complete template table and the '
                                                         'owned JK static world. Preserve failed template '
                                                         'lookup and failed CreateThing; do not supply an '
                                                         'actor.'}]},
 'shadow-caverns': {'tag': 'shadowcaverns',
                    'title': 'Shadow Caverns',
                    'author': 'NOFpuXnk',
                    'source_url': 'https://www.massassi.net/levels/files/1169.shtml',
                    'download_url': 'https://www.massassi.net/media/levels/files/jkmp/shadowcaverns.zip',
                    'zip_sha256': '18fad02f58d755f8e19d4da184354c3d85269c52ec161ee17468a13194fe1765',
                    'gob_sha256': '31a9af2172aaef14f699d211e7bdf39ac84714fdb384b1481ed98ab662e3aed0',
                    'gob_member': 'shadowcaverns.gob',
                    'world': 'jkl/greenroom.jkl',
                    'sha256': 'c8f27866248a9a02207c193658189850f57021e7c00354383428e6193a101b7e',
                    'scripts_sha256': '8fa96f5990c7b8b3cc3a9ccdf97a7dbd4cde0bef72894703eebbe52e2aa935b8',
                    'episode_type': 2,
                    'runtime_cogs': '00_desttrail.cog 00_smoketrail.cog class_sequencer.cog kyle.cog '
                                    'pow_backpack.cog pow_bacta.cog pow_bryar.cog pow_concrifle.cog '
                                    'pow_crossbow.cog pow_health.cog pow_lightside.cog pow_mana.cog '
                                    'pow_powerboost.cog pow_railgun.cog pow_repeater.cog pow_revive.cog '
                                    'pow_sequencer.cog pow_single_sequencer.cog pow_single_thermal.cog '
                                    'pow_strifle.cog pow_thermal.cog',
                    'environment': '00_camera.cog 00_door.cog 00_elev_switch.cog 00_generator.cog '
                                   '00_slashgrate.cog actor_kd.cog detroll-destruction.cog '
                                   'greenroom_start.cog nm_tlockdoor.cog speeder.cog',
                    'requires_jksp': False,
                    'cog_sha256': {'00_camera.cog': '70adcb46d2d7c59155e3c4328bbcb5d176eb7cb039d4c988d6c74a40ceb87b94',
                                   '00_desttrail.cog': '6c56bf2f756cd63625443d5fa76f8d72521c1f19ed9b61a7ce6252b1ecc00c48',
                                   '00_door.cog': 'a07fb10fadbc81bf4a970cd4ced495240ccfa86f35e3f9de954729d65cbfba5a',
                                   '00_elev_switch.cog': 'c1e492ba2c3b8cc0399f777e8a61338e4a1f9aed816ab3e62974e8b92d2adcc3',
                                   '00_generator.cog': 'a764810a081562dcbd245688842a384414f1d147bc4af267cffa56adba954c5c',
                                   '00_slashgrate.cog': '9b737dee56d44dff90626a865fcee9db0da241cb1c617b48735dffd6dc8e71d9',
                                   '00_smoketrail.cog': '2a990da3d41131bca2d1481562592742e5f8c543ac846dd95311a361189c7bbf',
                                   'actor_kd.cog': '26460ded9177e10ef6a145e6f87b0683307b9bf50d9d8264b5c140feabb771bf',
                                   'class_sequencer.cog': '7a057711f1e6fb33e1a7b410d657738531c5b6664af3259dad3ab16c4b30cae5',
                                   'detroll-destruction.cog': 'b4008d7eafac36f7e78fb21e6b83e3b5d0db8eb33b49418e2987e5738e07a54f',
                                   'greenroom_start.cog': '42699e8d749ab8ef4f67d0db625070e2a0530f0febe5d25afd216c2259e4100b',
                                   'kyle.cog': 'cf68cc4754acd78d2d84297eb6d05df80d0e8e265fa5d5a902b7101f8e523955',
                                   'nm_tlockdoor.cog': '7926beed28bfa7b40321b0b453a69908d427ea030b2d1327e39e002535850d7f',
                                   'pow_backpack.cog': '7bacc8efb06a8d6b71ab3780f2ab6302ad1c63d245bd9524c0b89258053b08ed',
                                   'pow_bacta.cog': '8b420d7556d92a9f2bcfbb99aeac690e85d7beb54baa7f7e7321f4121b090d56',
                                   'pow_bryar.cog': 'd533156b8283c2c21f44355f7146192df873f5806499cc57fb9fbfa838a2a169',
                                   'pow_concrifle.cog': 'a762451646e8598bc64afc70c6ef5054e434dda6da5a4d5f735c13fef00de011',
                                   'pow_crossbow.cog': 'e5dfce5f5f394b670ac2a7a9d2c569085127b1857bc52b3859475ae10b285f85',
                                   'pow_health.cog': '764f213b0dfb0623fecef59f46850fc37c5a0e4e0599f15411d35ee4b6ffb011',
                                   'pow_lightside.cog': 'a5f632793d2366554dd40d6cefeadba3e111a7f52b3b626c3a53c698cb84abf3',
                                   'pow_mana.cog': 'f7253958c01e90bfc99d162ec0af0c2cc819e561c817165bcf434dadb776a30a',
                                   'pow_powerboost.cog': '1dd3214a7c95a9c88f32c0710747648aefcc54495d666496cbfeae697aa085d8',
                                   'pow_railgun.cog': '4dd2252dde766ad47c9e89a1bb59e009431c7c3838e98cd703bbc4332a5d26bc',
                                   'pow_repeater.cog': '83505b4b4620ce33e494caab76769e59a9ececceaeef161122ab64dc3861feb6',
                                   'pow_revive.cog': '6904811bf2f22d8fbfde1c206ec8f1c0da2ed66f4217312fa31c934f52f3214e',
                                   'pow_sequencer.cog': '0f5b9acde5776625fd32f7d7582c4676dfc3b64cf784614fcd69733bcd324392',
                                   'pow_single_sequencer.cog': '2777cacb7aceff81128cbf8b432cda15a32557f716cabe2ff6111183c79b965e',
                                   'pow_single_thermal.cog': 'fbf8c39c853bf5e9a60cf3016bba7a39936c136552ce094b80c872d205c811cf',
                                   'pow_strifle.cog': 'edddcde2521e57fcf7d3c8c6e83ec25b7085d6230c4e09cf1387091f08697a73',
                                   'pow_thermal.cog': '962d2fb78f1e818439056039b76573f69ec50b0ffcea442cecedb05783290f3b',
                                   'speeder.cog': '07de41d24400e1cb8f153201aaa83758a501e771d76f63cd11736863321f81c0'},
                    'source_omissions': [],
                    'resource_aliases': {},
                    'cog_edits': {}},
 'deicide': {'tag': 'deicide',
             'title': 'Deicide',
             'author': 'NOFpuXnk',
             'source_url': 'https://www.massassi.net/levels/files/3082.shtml',
             'download_url': 'https://www.massassi.net/media/levels/files/jkmp/deicide.zip',
             'zip_sha256': 'a6c5c1234d1f679a074e6234e52cc17725d103d1cd895074e412504c81f45a3c',
             'gob_sha256': 'eea53f43b3871043ece301a7fe94258724234cba2f31832234352cb913eb1d8d',
             'gob_member': 'deicide.gob',
             'world': 'jkl/deicide.jkl',
             'sha256': 'cb99f46572e87b7164da22d63d0130a108ebef60466fe405d68aae5ee5079913',
             'scripts_sha256': '59400b8bf84547d50c1ba6b3907a4c6f13b16a646537034e4d775af2de464224',
             'episode_type': 2,
             'runtime_cogs': '00_desttrail.cog 00_smoketrail.cog class_sequencer.cog kyle.cog '
                             'pow_backpack.cog pow_bacta.cog pow_bryar.cog pow_concrifle.cog '
                             'pow_crossbow.cog pow_railgun.cog pow_repeater.cog pow_sequencer.cog '
                             'pow_shields.cog pow_single_sequencer.cog pow_single_thermal.cog '
                             'pow_strifle.cog pow_vest.cog',
             'environment': 'ammo.cog',
             'requires_jksp': False,
             'cog_sha256': {'00_desttrail.cog': '6c56bf2f756cd63625443d5fa76f8d72521c1f19ed9b61a7ce6252b1ecc00c48',
                            '00_smoketrail.cog': '2a990da3d41131bca2d1481562592742e5f8c543ac846dd95311a361189c7bbf',
                            'ammo.cog': 'e1c2e22f745bd8ec9e1d54f2da17a0c6ec82361496a1d0295ebcc15928ec068d',
                            'class_sequencer.cog': '7a057711f1e6fb33e1a7b410d657738531c5b6664af3259dad3ab16c4b30cae5',
                            'kyle.cog': 'cf68cc4754acd78d2d84297eb6d05df80d0e8e265fa5d5a902b7101f8e523955',
                            'pow_backpack.cog': '7bacc8efb06a8d6b71ab3780f2ab6302ad1c63d245bd9524c0b89258053b08ed',
                            'pow_bacta.cog': '8b420d7556d92a9f2bcfbb99aeac690e85d7beb54baa7f7e7321f4121b090d56',
                            'pow_bryar.cog': 'd533156b8283c2c21f44355f7146192df873f5806499cc57fb9fbfa838a2a169',
                            'pow_concrifle.cog': 'a762451646e8598bc64afc70c6ef5054e434dda6da5a4d5f735c13fef00de011',
                            'pow_crossbow.cog': 'e5dfce5f5f394b670ac2a7a9d2c569085127b1857bc52b3859475ae10b285f85',
                            'pow_railgun.cog': '4dd2252dde766ad47c9e89a1bb59e009431c7c3838e98cd703bbc4332a5d26bc',
                            'pow_repeater.cog': '83505b4b4620ce33e494caab76769e59a9ececceaeef161122ab64dc3861feb6',
                            'pow_sequencer.cog': '0f5b9acde5776625fd32f7d7582c4676dfc3b64cf784614fcd69733bcd324392',
                            'pow_shields.cog': '8d515630da6ac31126decd4ca8c94ef840c42edc1110ef102e5f48530d88e8ad',
                            'pow_single_sequencer.cog': '2777cacb7aceff81128cbf8b432cda15a32557f716cabe2ff6111183c79b965e',
                            'pow_single_thermal.cog': 'fbf8c39c853bf5e9a60cf3016bba7a39936c136552ce094b80c872d205c811cf',
                            'pow_strifle.cog': 'edddcde2521e57fcf7d3c8c6e83ec25b7085d6230c4e09cf1387091f08697a73',
                            'pow_vest.cog': 'd3550f626554565280f3fa30bbc4c0c5b9032caad6f6d5fed47e16732efe2d5f'},
             'source_omissions': [],
             'resource_aliases': {},
             'cog_edits': {}}}

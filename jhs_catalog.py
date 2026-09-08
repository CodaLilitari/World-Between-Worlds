"""Original conversion metadata for the recovered PeD_HeAd JHS 1.0 package.

No level assets or original COG bodies are distributed here. The original readme
asks permission before modifying the level; its restrictions and credits remain
attached to the locally recovered input. This recipe does not relicense it.
"""

CATALOG = {
    'jhs': {
        'tag': 'jhs',
        'title': "Jedi's High School",
        'author': 'PeD_HeAd',
        'source_url': 'https://www.jkdf2.net/JKBot/JKArchive/JKDF2/JKDF2/Game%20Files/jkmp/jhs.zip',
        'catalog_url': 'https://www.jkdf2.net/JKBot/JKArchive/?dir=JKDF2/JKDF2/Game+Files/jkmp',
        'announcement_url': 'https://www.massassi.net/oldnews/old19.htm',
        'version': '1.0',
        'release_date': '1999-05-02',
        'zip_sha256': 'a30e2b74db290b580effe442ac1345b9158a36b9803234a4a347a997039c0411',
        'gob_sha256': 'a62c94789c521af2746cc8378301a4940a59a24f6fb44dd4c443caacc0211b04',
        'gob_member': 'jhs.gob',
        'world': 'jkl/jhs.jkl',
        'sha256': '90e2641a58e0ec0102355dca9d3ec5eb55c4cbc9945a427227dcc8244885619d',
        'scripts_sha256': 'f53e909af03a8abd9ebe2b656037908f13d327ab154f9fc1e33d5142f96bf14b',
        'episode_type': 2,
        'requires_jksp': False,
        # Every resolvable original world-script byte stream, before substitution.
        'cog_sha256': {
            '00_breakingglass.cog': '6ffab345663d464a3c8fa846f406eaeeb5228f8d07df60c2e4bbdf3b2b0b8fd9',
            '00_camera.cog': '70adcb46d2d7c59155e3c4328bbcb5d176eb7cb039d4c988d6c74a40ceb87b94',
            '00_desttrail.cog': '6c56bf2f756cd63625443d5fa76f8d72521c1f19ed9b61a7ce6252b1ecc00c48',
            '00_door.cog': 'a07fb10fadbc81bf4a970cd4ced495240ccfa86f35e3f9de954729d65cbfba5a',
            '00_doubledoor.cog': 'e70e3067aa5a56a9220d22c603dac97a3c777105f26893925bbf33ae26038800',
            '00_elev_switch.cog': 'c1e492ba2c3b8cc0399f777e8a61338e4a1f9aed816ab3e62974e8b92d2adcc3',
            '00_slashgrate.cog': '9b737dee56d44dff90626a865fcee9db0da241cb1c617b48735dffd6dc8e71d9',
            '00_smoketrail.cog': '2a990da3d41131bca2d1481562592742e5f8c543ac846dd95311a361189c7bbf',
            'class_sequencer.cog': '7a057711f1e6fb33e1a7b410d657738531c5b6664af3259dad3ab16c4b30cae5',
            'detroll-destruction.cog': 'b4008d7eafac36f7e78fb21e6b83e3b5d0db8eb33b49418e2987e5738e07a54f',
            'detroll-grenade.cog': '394a16b0f76fa3fd7a841533d33f2cf04638bfffa7553cd91f6c44119eb97291',
            'detroll-railgun.cog': 'b1c184d728443f3ef0b4f8b9c1fefe2eb2263a98fb8b3fa2188829256b75a4c9',
            'detroll-seqchrg2.cog': '071de6cee541f8af4ac67298204422b2efb3d923304f33349595e955604ff2ad',
            'kyle.cog': 'cf68cc4754acd78d2d84297eb6d05df80d0e8e265fa5d5a902b7101f8e523955',
            'm5_convbelt.cog': '233921704da91cc627eebb9254bd4090d92dfd448c8460fbabee817d6daabe72',
            'pow_backpack.cog': '7bacc8efb06a8d6b71ab3780f2ab6302ad1c63d245bd9524c0b89258053b08ed',
            'pow_bacta.cog': '8b420d7556d92a9f2bcfbb99aeac690e85d7beb54baa7f7e7321f4121b090d56',
            'pow_bryar.cog': 'd533156b8283c2c21f44355f7146192df873f5806499cc57fb9fbfa838a2a169',
            'pow_concrifle.cog': 'a762451646e8598bc64afc70c6ef5054e434dda6da5a4d5f735c13fef00de011',
            'pow_crossbow.cog': 'e5dfce5f5f394b670ac2a7a9d2c569085127b1857bc52b3859475ae10b285f85',
            'pow_darkside.cog': '739d2bd52cd1ad550178805a780db8095a1a34bb5d366c41d5871995b069c504',
            'pow_energy.cog': '1bcd549121e3e9afd5ebe2bbe4b509d6d022265eee3239a164f3a7816bf10d8f',
            'pow_health.cog': '764f213b0dfb0623fecef59f46850fc37c5a0e4e0599f15411d35ee4b6ffb011',
            'pow_mana.cog': 'f7253958c01e90bfc99d162ec0af0c2cc819e561c817165bcf434dadb776a30a',
            'pow_power.cog': '073756cb1b74cc2f84393215297cbd6f5e739d15972c283afcccd2130ebb5061',
            'pow_powerboost.cog': '1dd3214a7c95a9c88f32c0710747648aefcc54495d666496cbfeae697aa085d8',
            'pow_railcharges.cog': '18e5b0cf2ee4cc133582ba8879577f060b06c8eeda22d63bbc401deb998f57e3',
            'pow_railgun.cog': '4dd2252dde766ad47c9e89a1bb59e009431c7c3838e98cd703bbc4332a5d26bc',
            'pow_repeater.cog': '83505b4b4620ce33e494caab76769e59a9ececceaeef161122ab64dc3861feb6',
            'pow_revive.cog': '6904811bf2f22d8fbfde1c206ec8f1c0da2ed66f4217312fa31c934f52f3214e',
            'pow_sequencer.cog': '0f5b9acde5776625fd32f7d7582c4676dfc3b64cf784614fcd69733bcd324392',
            'pow_shields.cog': '8d515630da6ac31126decd4ca8c94ef840c42edc1110ef102e5f48530d88e8ad',
            'pow_single_sequencer.cog': '2777cacb7aceff81128cbf8b432cda15a32557f716cabe2ff6111183c79b965e',
            'pow_single_thermal.cog': 'fbf8c39c853bf5e9a60cf3016bba7a39936c136552ce094b80c872d205c811cf',
            'pow_strifle.cog': 'edddcde2521e57fcf7d3c8c6e83ec25b7085d6230c4e09cf1387091f08697a73',
            'pow_thermal.cog': '962d2fb78f1e818439056039b76573f69ec50b0ffcea442cecedb05783290f3b',
            'speeder.cog': '07de41d24400e1cb8f153201aaa83758a501e771d76f63cd11736863321f81c0',
            'turret.cog': 'b257dc6c215f924e85fc4435570d207bd1a3b4fee197e7300d7581e6188e2b93',
        },
        # Individually resolved in the pinned native MotS resource catalog.
        # Custom environment scripts are never classified by a pow_ heuristic.
        'runtime_cogs': (
            '00_desttrail.cog 00_smoketrail.cog class_sequencer.cog kyle.cog '
            'pow_backpack.cog pow_bacta.cog pow_bryar.cog pow_concrifle.cog '
            'pow_crossbow.cog pow_darkside.cog pow_energy.cog pow_health.cog '
            'pow_mana.cog pow_power.cog pow_powerboost.cog pow_railcharges.cog '
            'pow_railgun.cog pow_repeater.cog pow_revive.cog pow_sequencer.cog '
            'pow_shields.cog pow_single_sequencer.cog pow_single_thermal.cog '
            'pow_strifle.cog pow_thermal.cog'
        ),
        # Thirteen present scripts plus the exact reviewed missing declaration.
        'environment': (
            '00_breakingglass.cog 00_camera.cog 00_door.cog 00_doubledoor.cog '
            '00_elev_switch.cog 00_slashgrate.cog detroll-destruction.cog '
            'detroll-grenade.cog detroll-railgun.cog detroll-seqchrg2.cog '
            'm5_convbelt.cog minetrap.cog speeder.cog turret.cog'
        ),
        'source_omissions': [
            {
                'name': '00_glass.mat',
                'referrer': '3do/shard0.3do',
                'referrer_sha256': 'f0b4102b3ba378913b6d16ee585baab2d14f46f9ae4ae293a1c24b9f2369f44d',
                'untextured_3do': True,
                'reason': 'Original sole material declaration in the pinned shard model; its one face is untextured geo3 with zero texture vertices. Preserve the absent namespaced reference without a substitute.',
            },
            {
                'name': '00_glass.mat',
                'referrer': 'jkl/jhs.jkl',
                'referrer_sha256': '90e2641a58e0ec0102355dca9d3ec5eb55c4cbc9945a427227dcc8244885619d',
                'reason': 'Original world material index2 has no world-surface references. It is absent from the complete inspected JK archive set; preserve the exact namespaced omission.',
            },
            {
                'name': 'minetrap.cog',
                'referrer': 'jkl/jhs.jkl',
                'referrer_sha256': '90e2641a58e0ec0102355dca9d3ec5eb55c4cbc9945a427227dcc8244885619d',
                'reason': 'Original missing world-script declaration15 and COG placement17 with zero arguments. Preserve both references as br_minetrap.cog; do not invent or import a mine-trap implementation.',
            },
        ],
        'resource_aliases': {},
        'template_aliases': {},
        'cog_edits': {},
        'notes': [
            'Readme identifies JHS1.0 by PeD_HeAd, released 1999-05-02, matching the primary contemporary announcement. Credits to Slade, Pack_Emp_Steve, and _JWS_Cingan remain with the original package.',
            'Bundled jhs_start.cog, jp_up.cog, gravswch.cog, and mpsimplesparks.cog are not referenced by the world or recursive source graph. Do not activate them or silently add their inventory/jetpack behavior.',
            'The thirteen active environment COGs have no inventory or weapon-selection calls requiring conversion; preserve their code and execution flags with typed resource/template namespacing.',
            'Original speeder.cog uses undeclared fly_snd and calls multiple MoveToFrame targets consecutively. These inherited behaviors require gameplay checks; no source repair is invented.',
            'Measured source scene:2236 surfaces,216 sectors,263 placed things,153 templates,39 script declarations,41 COG placements,6 walkplayer spawns. Declared capacities80 COGs/463 things exceed the actual row counts.',
            'Recovery, dependency review, and a generated archive do not establish gameplay, visual, or multiplayer synchronization compatibility.',
        ],
    },
}

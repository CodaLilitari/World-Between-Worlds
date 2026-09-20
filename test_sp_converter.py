"""Asset-free SP episode and original-source contract checks."""
from pathlib import Path
import copy
import os
import re
import tempfile
import unittest
from unittest.mock import patch

import bridge
import blackwing_revisions
from gob import Gob, build_gob
import sp_converter


class SingleplayerContracts(unittest.TestCase):
    def test_existing_recipe_readmes_keep_exact_prior_text(self):
        prior = ('Experimental whole-episode SP conversion. Full gameplay remains unverified.\n'
            'Use OpenJKDF2 in MotS single-player mode (-motsCompat -sp), with only the declared startup profile.\n'
            'Copy the generated GOO to a private test installation episode folder; retain all original notices.\n'
            'No retail/custom assets or this converted output may be committed to the WBW repository.\n')
        for recipe in ('sp-phantom-menace-final-battle', 'sp-maul-vs-qui-gon',
                       'sp-imperial-pumping-station', 'sp-steal-the-bottle'):
            with self.subTest(recipe=recipe):
                self.assertEqual(sp_converter.readme_text(sp_converter.recipe_details(recipe)), prior)
        self.assertEqual(sp_converter.readme_text({'readme_source_defects': ['not approved prose'],
                                                   'semantic_notes': ['not approved prose']}), prior)

    def test_explicit_behavior_caveats_append_only_reviewed_lines(self):
        caveats = ['Original missing resource remains absent.', 'Initial render checked; mission untested.']
        base = sp_converter.readme_text({})
        self.assertEqual(sp_converter.readme_text({'source_behavior_caveats': caveats}),
                         base + '\nSource behavior caveats:\n- ' + '\n- '.join(caveats) + '\n')
        self.assertEqual(caveats, ['Original missing resource remains absent.',
                                  'Initial render checked; mission untested.'])

    def test_invalid_behavior_caveat_fields_fail_before_source_open(self):
        for invalid in (None, '', 'one line', {}, (), [], [None], [1], [''], ['  '],
                        [' trailing '], ['two\nlines'], ['two\rlines']):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(sp_converter.SingleplayerError, 'behavior caveats'):
                sp_converter.readme_text({'source_behavior_caveats': invalid})
        spec = {**sp_converter.recipe_details('sp-steal-the-bottle'), 'source_behavior_caveats': []}
        with tempfile.TemporaryDirectory() as directory, patch.object(sp_converter, 'recipe_details', return_value=spec), \
                patch.object(sp_converter, 'open_original', side_effect=AssertionError('source opened')):
            with self.assertRaisesRegex(sp_converter.SingleplayerError, 'behavior caveats'):
                sp_converter.build_to_directory({}, 'unused.zip', directory, 'sp-steal-the-bottle')
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_steal_bottle_versioned_name_fits_engine_episode_stem(self):
        spec = sp_converter.recipe_details('sp-steal-the-bottle')
        legacy, = spec['entry']['legacy_filenames']
        self.assertEqual(legacy, spec['output_filename'])
        name = blackwing_revisions.versioned_name(legacy, spec['entry']['revision'])
        self.assertEqual(name, 'wbw-sp-steal-bottle_wbw_v1.goo')
        self.assertLessEqual(len(Path(name).stem.encode('cp1252')), 31)

    def test_pumping_station_versioned_name_fits_engine_episode_stem(self):
        spec = sp_converter.recipe_details('sp-imperial-pumping-station')
        legacy, = spec['entry']['legacy_filenames']
        self.assertEqual(legacy, spec['output_filename'])
        name = blackwing_revisions.versioned_name(legacy, spec['entry']['revision'])
        self.assertEqual(name, 'wbw-sp-pumping-station_wbw_v1.goo')
        self.assertLessEqual(len(Path(name).stem.encode('cp1252')), 31)
        with self.assertRaisesRegex(ValueError, '31-byte episode-name limit'):
            blackwing_revisions.versioned_name('wbw-sp-imperial-pumping-station.goo', 1)

    def typed_closure(self, output_files, native_files=None):
        archives = {'motsres': Gob(build_gob(native_files or {'native.txt': b'synthetic'})),
                    'motssnd': Gob(build_gob({'native.txt': b'synthetic'}))}
        return sp_converter.verify_typed_literal_closure(Gob(build_gob(output_files)), archives)

    def test_matching_basename_in_wrong_directory_does_not_satisfy_loader(self):
        for name, wrong_path in (('gate.cog', 'misc/gate.cog'),
                                 ('panel.mat', 'misc/panel.mat'),
                                 ('idle.key', 'misc/key/idle.key')):
            with self.subTest(name=name), self.assertRaisesRegex(
                    sp_converter.SingleplayerError, 'Unresolved typed resource path'):
                self.typed_closure({'jkl/test.jkl': name.encode(), wrong_path: b'synthetic'})

    def test_material_and_sound_fallback_use_exact_directories(self):
        report = self.typed_closure({'jkl/test.jkl': b'panel.mat chirp.wav',
                                    '3do/mat/panel.mat': b'synthetic',
                                    'voice/chirp.wav': b'synthetic'})
        self.assertEqual(report['checked_literals'], 2)
        self.assertEqual(report['distinct_literals'], 2)
        self.assertEqual(report['loader_directory_counts'], {'3do/mat': 1, 'voice': 1})

    def test_loader_directory_precedence_precedes_archive_precedence(self):
        # The engine finds native mat/sound before trying episode 3do/mat/voice.
        report = self.typed_closure({'jkl/test.jkl': b'panel.mat chirp.wav',
                                    '3do/mat/panel.mat': b'second material candidate',
                                    'voice/chirp.wav': b'second sound candidate'},
                                   {'mat/panel.mat': b'first material candidate',
                                    'sound/chirp.wav': b'first sound candidate'})
        self.assertEqual(report['provider_counts'], {'motsres': 2})
        self.assertEqual(report['loader_directory_counts'], {'mat': 1, 'sound': 1})

    def test_qualified_token_is_not_silently_stripped_to_basename(self):
        for token in (b'custom/panel.mat', b'custom\\panel.mat', b'../panel.mat'):
            with self.subTest(token=token), self.assertRaisesRegex(
                    sp_converter.SingleplayerError, 'Qualified resource token'):
                self.typed_closure({'jkl/test.jkl': token, 'mat/panel.mat': b'synthetic'})

    def test_branching_episode_retains_exact_rows_and_progression(self):
        data = (b'"Synthetic"\nTYPE 1\nSEQ 3\n'
                b'10: 1 1 LEVEL first.jkl 24 0 20 30\n'
                b'20: 1 2 LEVEL light.jkl 25 0 -1 -1\n'
                b'30: 2 2 LEVEL dark.jkl 0 29 20 -1\nend\n')
        rows = sp_converter.episode_rows(data)
        self.assertEqual(rows[0], ['10:', '1', '1', 'LEVEL', 'first.jkl', '24', '0', '20', '30'])
        self.assertEqual(rows[2][1:], ['2', '2', 'LEVEL', 'dark.jkl', '0', '29', '20', '-1'])

    def test_missing_branch_target_is_rejected(self):
        with self.assertRaisesRegex(sp_converter.SingleplayerError, 'branch'):
            sp_converter.episode_rows(b'TYPE 1\n10: 1 1 LEVEL a.jkl 0 0 30 -1\n')

    def test_duplicate_entry_and_non_sp_type_are_rejected(self):
        for data in (b'TYPE 1\n10: 1 1 LEVEL a.jkl 0 0 -1 -1\n10: 1 1 LEVEL b.jkl 0 0 -1 -1\n',
                     b'TYPE 2\n10: 1 1 LEVEL a.jkl 0 0 -1 -1\n'):
            with self.assertRaises(sp_converter.SingleplayerError):
                sp_converter.episode_rows(data)

    def test_original_contract_offers_zip_only_and_rejects_unpinned_bytes(self):
        entry = sp_converter.catalog_entries()[0]
        spec = sp_converter.recipe_details(entry['id'])
        self.assertEqual(sp_converter.original_hashes(entry['id']), [spec['zip_sha256']])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'unreviewed.zip'
            path.write_bytes(b'synthetic unrelated input')
            before = path.read_bytes()
            with self.assertRaisesRegex(sp_converter.SingleplayerError, 'reviewed original ZIP'):
                sp_converter.open_original(path, entry['id'])
            self.assertEqual(path.read_bytes(), before)


class SourceOmissionControls(unittest.TestCase):
    """Synthetic complete graph; no authored or retail assets in fixtures."""
    def setUp(self):
        tables = {'sounds': ['alarm.wav', 'command_alarm.wav'],
                  'materials': ['0: panel.mat 1 1'],
                  'scripts': ['0: first.cog', '1: second.cog']}
        self.world = ('# synthetic omission contract\n' + ''.join(
            f'World {label} {len(tables.get(label, []))}\n' +
            '\n'.join(tables.get(label, [])) + '\n' for label in bridge.TABLES) +
            'World templates 1\nwalkplayer none type=player\n'
            'World cogs 2\n0: first.cog\n1: second.cog\n'
            'World things 1\n0: walkplayer player 0 0 0 0 0 0 0\n'
            'World vertices 0\nWorld adjoins 0\n'
            'World surfaces 1\n0: 0 0x0 0x0 0 3 1 -1 0 1 0,0 0.5\n'
            'World sectors 1\n0:\nSOUND alarm.wav 1\nend\n').encode()
        self.source_files = {
            'episode.jk': b'TYPE 1\n10: 1 1 LEVEL test.jkl 0 0 -1 -1\n',
            'jkl/test.jkl': self.world,
            'cog/first.cog': b'symbols\nsound beep=alarm.wav local\nmaterial screen=panel.mat local\nend\ncode\nend\n',
            'cog/second.cog': b'symbols\nmaterial screen=panel.mat local\nend\ncode\nend\n',
        }
        self.originals = {'episode': Gob(build_gob(self.source_files))}
        self.archives = {key: Gob(build_gob({'placeholder.txt': key.encode()}))
                         for key in ('jkres', 'jksnd', 'jksp', 'motssnd')}
        self.archives.update(motsres=Gob(build_gob({'jkl/static.jkl': b'World templates 0\n',
                                                   'misc/items.dat': b'# no synthetic native inventory\n'})),
                             motssp=Gob(build_gob({'jkl/native.jkl': b'World templates 0\n'})))
        self.spec = {'owned_hashes': {key: value.sha256 for key, value in self.archives.items()},
                     'archives': [{'sha256': self.originals['episode'].sha256}],
                     'episode_rows': sp_converter.episode_rows(self.source_files['episode.jk']),
                     'worlds': {'jkl/test.jkl': sp_converter.sha(self.world)},
                     'native_world': 'jkl/native.jkl', 'native_cog_bindings': {},
                     'native_binding_source_sha256': {},
                     'source_cog_sha256': {Path(path).name: sp_converter.sha(raw)
                         for path, raw in self.source_files.items() if path.endswith('.cog')},
                     'source_omissions': []}
        for path in ('jkl/test.jkl', 'cog/first.cog', 'cog/second.cog'):
            for name in sorted(sp_converter.literal_counts(self.source_files[path])):
                if name.endswith(('.wav', '.mat')):
                    self.spec['source_omissions'].append(self.rule(path, name))
        self.recipe = 'synthetic-source-omissions'
        self.catalog_patch = patch.dict(sp_converter.sp_catalog.RECIPES, {self.recipe: self.spec})
        self.catalog_patch.start()
        self.addCleanup(self.catalog_patch.stop)

    def rule(self, path, name, owner='authored', raw=None):
        raw = self.source_files[path] if raw is None else raw
        return {'name': name, 'owner': owner, 'referrer': path,
                'referrer_sha256': sp_converter.sha(raw),
                'occurrences': sp_converter.literal_counts(raw)[name],
                'output_name': 'bs_' + name,
                'output_referrer': path if path.endswith('.jkl') else
                                   path.rsplit('/', 1)[0] + '/bs_' + Path(path).name,
                'active_lines': sp_converter.omission_lines(raw, name),
                'usage': 'literal', 'reason': 'Exact synthetic original omission; behavior unverified.'}

    def build(self):
        return sp_converter.build(self.archives, self.originals, self.recipe)

    def verify(self, payload):
        return sp_converter.verify(self.archives, self.originals, self.recipe, payload)

    def test_complete_graph_retains_each_edge_and_reports_partial_closure(self):
        payload, manifest = self.build()
        report = self.verify(payload)
        self.assertEqual(report['status'], 'structural-preservation-with-reviewed-source-omissions')
        self.assertFalse(report['literal_resource_closure'])
        self.assertFalse(report['runtime_verified'])
        self.assertEqual(report['typed_resource_closure']['retained_omission_edges'], 6)
        self.assertEqual(report['typed_resource_closure']['retained_omission_occurrences'], 7)
        self.assertEqual(manifest['source_omissions'], report['typed_resource_closure']['retained_omissions'])
        output = Gob(payload)
        self.assertFalse(any(path.endswith(('.wav', '.mat')) for path in output.entries))
        # The independent verifier cannot use a manifest or call the builder.
        with patch.object(sp_converter, 'build', side_effect=AssertionError('builder called')):
            self.assertEqual(self.verify(payload), report)

    def test_rule_authority_mutations_fail_in_builder_and_verifier(self):
        payload, _ = self.build()
        mutations = {'owner': 'jkres', 'referrer': 'cog/unreached.cog',
                     'referrer_sha256': '0' * 64, 'occurrences': 99,
                     'output_name': 'bs_other.wav', 'output_referrer': 'jkl/other.jkl',
                     'active_lines': [{'sha256': '0' * 64, 'occurrences': 1, 'repetitions': 1}]}
        for key, value in mutations.items():
            with self.subTest(field=key):
                old = self.spec['source_omissions'][0][key]
                self.spec['source_omissions'][0][key] = value
                try:
                    for operation in (self.build, lambda: self.verify(payload)):
                        with self.assertRaises((sp_converter.SingleplayerError, bridge.RecipeError)):
                            operation()
                finally:
                    self.spec['source_omissions'][0][key] = old

    def test_removed_late_duplicate_and_unused_edges_are_not_name_waivers(self):
        payload, _ = self.build()
        rules = copy.deepcopy(self.spec['source_omissions'])
        variants = [rules[:-1], rules + [rules[0]], rules + [self.rule('cog/first.cog', 'alarm.wav')]]
        variants[-1][-1]['referrer'] = 'cog/unreached.cog'
        for variant in variants:
            self.spec['source_omissions'] = variant
            for operation in (self.build, lambda: self.verify(payload)):
                with self.subTest(variant=len(variant)), self.assertRaises(sp_converter.SingleplayerError):
                    operation()
        self.spec['source_omissions'] = rules

    def test_whole_token_count_case_comments_and_qualified_paths(self):
        raw = b'ALARM.WAV command_alarm.wav alarm.wav # alarm.wav\n// alarm.wav\n'
        self.assertEqual(sp_converter.literal_counts(raw), {'alarm.wav': 2, 'command_alarm.wav': 1})
        for token in (b'sound/alarm.wav', b'sound\\alarm.wav', b'../alarm.wav'):
            audit = sp_converter.SourceOmissions(self.spec)
            with self.subTest(token=token), self.assertRaisesRegex(sp_converter.SingleplayerError, 'Qualified'):
                audit.inspect('authored', 'jkl/test.jkl', token, 'jkl/test.jkl',
                              bridge.Catalog([('authored', self.originals['episode'])]), {})

    def test_added_occurrence_or_referrer_requires_its_own_source_authority(self):
        catalog = bridge.Catalog([('authored', self.originals['episode'])])
        for path, raw in [('jkl/test.jkl', self.world + b'\nalarm.wav\n'),
                          ('cog/third.cog', b'alarm.wav')]:
            audit = sp_converter.SourceOmissions(self.spec)
            with self.subTest(path=path), self.assertRaises(sp_converter.SingleplayerError):
                audit.inspect('authored', path, raw, path, catalog, {})

    def test_present_wrong_directory_and_ambiguous_sources_cannot_be_omissions(self):
        for files, error in [({'misc/alarm.wav': b'not a sound provider'}, 'unexpectedly resolves'),
                             ({'sound/alarm.wav': b'one', 'voice/alarm.wav': b'two'}, 'Ambiguous')]:
            self.archives['jkres'] = Gob(build_gob(files))
            self.spec['owned_hashes']['jkres'] = self.archives['jkres'].sha256
            with self.subTest(files=list(files)), self.assertRaisesRegex(ValueError, error):
                self.build()

    def test_missing_cog_model_and_unreviewed_name_are_never_accepted(self):
        catalog = bridge.Catalog([('authored', self.originals['episode'])])
        for name in ('lost.cog', 'lost.3do', 'lost.wav'):
            with self.subTest(name=name), self.assertRaisesRegex(sp_converter.SingleplayerError, 'Unreviewed source'):
                sp_converter.SourceOmissions(self.spec).inspect('authored', 'jkl/test.jkl',
                    name.encode(), 'jkl/test.jkl', catalog, {})
        self.spec['source_omissions'][0]['name'] = 'lost.cog'
        with self.assertRaisesRegex(sp_converter.SingleplayerError, 'MAT/WAV'):
            sp_converter.SourceOmissions(self.spec)

    def test_typed_candidates_reject_output_native_and_fallback_providers(self):
        payload, manifest = self.build()
        output = Gob(payload)
        files = {path: output.read(path) for path in output.entries}
        for path in ('sound/bs_alarm.wav', 'voice/bs_alarm.wav', 'mat/bs_panel.mat', '3do/mat/bs_panel.mat'):
            for provider in ('output', 'motsres', 'motssnd'):
                with self.subTest(path=path, provider=provider):
                    archives, candidate = self.archives.copy(), files.copy()
                    if provider == 'output':
                        candidate[path] = b'unexpected provider'
                    else:
                        old = archives[provider]
                        archives[provider] = Gob(build_gob({**{p: old.read(p) for p in old.entries}, path: b'unexpected'}))
                    with self.assertRaisesRegex(sp_converter.SingleplayerError, 'unexpectedly resolves'):
                        sp_converter.verify_typed_literal_closure(Gob(build_gob(candidate)), archives,
                                                                 manifest['source_omissions'])
        # A wrong-directory basename is not a loader provider. The full verifier
        # still rejects this unrelated extra file through exact ownership.
        files['misc/bs_alarm.wav'] = b'not a provider'
        sp_converter.verify_typed_literal_closure(Gob(build_gob(files)), self.archives, manifest['source_omissions'])
        with self.assertRaisesRegex(sp_converter.SingleplayerError, 'Native copied resource set'):
            self.verify(build_gob(files))

    def test_output_mutations_cannot_authorize_their_own_hash_or_count(self):
        payload, manifest = self.build()
        output = Gob(payload)
        changes = [('jkl/test.jkl', b'bs_alarm.wav', b'bs_other.wav'),
                   ('jkl/test.jkl', b'SOUND bs_alarm.wav 1', b'SOUND bs_alarm.wav 2'),
                   ('jkl/test.jkl', b'0:\t0\t0x0\t0x0\t0', b'0:\t0\t0x0\t0x0\t4'),
                   ('cog/bs_first.cog', b'bs_alarm.wav', b'bs_alarm.wav bs_alarm.wav')]
        for path, old, new in changes:
            files = {p: output.read(p) for p in output.entries}
            self.assertIn(old, files[path]); files[path] = files[path].replace(old, new)
            with self.subTest(path=path, old=old), self.assertRaises(sp_converter.SingleplayerError):
                self.verify(build_gob(files))
        rules = copy.deepcopy(manifest['source_omissions'])
        rules[0]['occurrences'] += 1
        with self.assertRaisesRegex(sp_converter.SingleplayerError, 'hash or count'):
            sp_converter.verify_typed_literal_closure(output, self.archives, rules)

    def test_untextured_guard_checks_semantics_even_with_rehashed_source(self):
        raw = (b'MATERIALS 1\n0: panel.mat\nGEOSETS 1\nGEOSET 0\nMESHES 1\nMESH 0\n'
               b'TEXTURE VERTICES 0\nFACES 1\n0: 0 0 3 0 0 0 0\nFACE NORMALS\n')
        for changed, should_pass in [(raw, True), (raw.replace(b'VERTICES 0', b'VERTICES 1'), False),
                                     (raw.replace(b'0: 0 0 3', b'0: 0 0 4'), False),
                                     (raw + b'MESH 1\nTEXTURE VERTICES 3\nFACES 1\n0: 0 0 4 0 0 0 0\nFACE NORMALS\n', False)]:
            rule = self.rule('3do/shard.3do', 'panel.mat', raw=changed)
            rule['usage'] = 'untextured-one-face-material'
            spec = {**self.spec, 'source_omissions': [rule]}
            audit = sp_converter.SourceOmissions(spec)
            catalog = bridge.Catalog([('authored', Gob(build_gob({'3do/shard.3do': changed})))])
            if should_pass:
                audit.inspect('authored', '3do/shard.3do', changed, '3do/bs_shard.3do', catalog, {})
                self.assertEqual(len(audit.used), 1)
            else:
                with self.assertRaisesRegex(sp_converter.SingleplayerError, 'untextured'):
                    audit.inspect('authored', '3do/shard.3do', changed, '3do/bs_shard.3do', catalog, {})


class SourceTemplateOmissionControls(unittest.TestCase):
    rule = SourceOmissionControls.rule
    build = SourceOmissionControls.build
    verify = SourceOmissionControls.verify

    def setUp(self):
        SourceOmissionControls.setUp(self)
        raw = self.source_files['cog/first.cog'].replace(
            b'end\ncode\nend\n', b'template pilot2=LostPilotT local\nend\ncode\nkilled:\n'
            b'if (Rand() < 0.60) { newThing = CreateThing(pilot2, GetSenderRef()); }\nreturn;\nend\n')
        self.source_files['cog/first.cog'] = raw
        declaration = next(line for line in bridge.active_lines(bridge.text(raw)).splitlines()
                           if line.startswith('template pilot2='))
        self.spec['source_template_omissions'] = [{
            'world': 'jkl/test.jkl', 'world_sha256': sp_converter.sha(self.world),
            'owner': 'authored', 'referrer': 'cog/first.cog', 'referrer_sha256': sp_converter.sha(raw),
            'symbol': 'pilot2', 'default': 'LostPilotT', 'output_name': 'bs_lostpilott',
            'output_referrer': 'cog/bs_first.cog', 'declaration_sha256': sp_converter.sha(declaration.encode()),
            'declaration_count': 1, 'symbol_use_count': 1,
            'reason': 'Synthetic active missing local template; source control flow retained.'}]
        self.repin()

    def repin(self):
        self.world = self.source_files['jkl/test.jkl']
        self.originals['episode'] = Gob(build_gob(self.source_files))
        self.spec['archives'][0]['sha256'] = self.originals['episode'].sha256
        self.spec['worlds']['jkl/test.jkl'] = sp_converter.sha(self.world)
        for path, raw in self.source_files.items():
            if path.endswith('.cog'):
                self.spec['source_cog_sha256'][Path(path).name] = sp_converter.sha(raw)
        for index, rule in enumerate(self.spec['source_omissions']):
            self.spec['source_omissions'][index] = self.rule(rule['referrer'], rule['name'])
        for rule in self.spec['source_template_omissions']:
            rule['world_sha256'] = sp_converter.sha(self.world)
            rule['referrer_sha256'] = sp_converter.sha(self.source_files['cog/first.cog'])

    def test_exact_local_default_is_isolated_without_changing_branch(self):
        payload, manifest = self.build()
        report = self.verify(payload)
        self.assertFalse(report['literal_resource_closure'])
        self.assertFalse(report['template_resource_closure'])
        self.assertEqual(report['source_template_omissions'], manifest['source_template_omissions'])
        omission, = report['source_template_omissions']
        self.assertEqual(omission['status'], 'active-original-missing-template-preserved')
        self.assertFalse(omission['runtime_verified'])
        raw = Gob(payload).read('cog/bs_first.cog')
        self.assertIn(b'template pilot2=bs_lostpilott local', raw)
        source_code = self.source_files['cog/first.cog'].split(b'code\n', 1)[1]
        self.assertEqual(raw.split(b'code\n', 1)[1], source_code)
        self.assertEqual(omission['output_referrer_sha256'], sp_converter.sha(raw))
        with patch.object(sp_converter, 'build', side_effect=AssertionError('builder called')):
            self.assertEqual(self.verify(payload), report)

    def test_template_rule_authority_cannot_be_replaced_by_output(self):
        payload, _ = self.build()
        changes = {'world': 'jkl/other.jkl', 'world_sha256': '0' * 64, 'owner': 'jkres',
                   'referrer': 'cog/second.cog', 'referrer_sha256': '0' * 64,
                   'symbol': 'another', 'default': 'OtherPilot', 'output_name': 'bs_otherpilot',
                   'output_referrer': 'cog/bs_second.cog', 'declaration_sha256': '0' * 64,
                   'declaration_count': 2, 'symbol_use_count': 2}
        rule = self.spec['source_template_omissions'][0]
        for field, value in changes.items():
            old = rule[field]; rule[field] = value
            try:
                for operation in (self.build, lambda: self.verify(payload)):
                    with self.subTest(field=field), self.assertRaises(sp_converter.SingleplayerError):
                        operation()
            finally:
                rule[field] = old

    def test_absent_duplicate_and_unused_template_rules_fail(self):
        payload, _ = self.build()
        original = copy.deepcopy(self.spec['source_template_omissions'])
        stale = copy.deepcopy(original[0]); stale.update(default='NeverDeclared', output_name='bs_neverdeclared', symbol='unused')
        for rules in ([], original + original, original + [stale]):
            self.spec['source_template_omissions'] = rules
            for operation in (self.build, lambda: self.verify(payload)):
                with self.subTest(rules=len(rules)), self.assertRaises(sp_converter.SingleplayerError):
                    operation()
        self.spec['source_template_omissions'] = original

    def test_exposed_duplicate_new_symbol_and_extra_referrer_are_rejected_even_after_repinning(self):
        files = copy.deepcopy(self.source_files)
        variants = [
            ('cog/first.cog', files['cog/first.cog'].replace(b'LostPilotT local', b'LostPilotT')),
            ('cog/first.cog', files['cog/first.cog'].replace(b'end\ncode', b'int pilot2=0 local\nend\ncode')),
            ('cog/first.cog', files['cog/first.cog'].replace(b'end\ncode', b'template pilot3=LostPilotT local\nend\ncode')),
            ('cog/second.cog', files['cog/second.cog'].replace(b'end\ncode', b'template pilot2=LostPilotT local\nend\ncode')),
            ('jkl/test.jkl', files['jkl/test.jkl'].replace(b'0: first.cog', b'0: first.cog LostPilotT')),
        ]
        for path, raw in variants:
            self.source_files = {**files, path: raw}; self.repin()
            with self.subTest(path=path, raw=raw[:30]), self.assertRaises(sp_converter.SingleplayerError):
                self.build()

    def test_new_source_or_native_template_provider_fails_for_both_names(self):
        payload, _ = self.build()
        files = copy.deepcopy(self.source_files)
        base_archives = self.archives.copy()
        for name in ('lostpilott', 'bs_lostpilott'):
            for provider in ('world', 'jkres', 'motsres', 'motssp'):
                self.source_files = files.copy(); self.archives = base_archives.copy()
                if provider == 'world':
                    value = bridge.text(files['jkl/test.jkl'])
                    self.source_files['jkl/test.jkl'] = bridge.replace_block(value, 'templates',
                        bridge.records(value, 'templates') + [name + ' none type=actor']).encode()
                else:
                    archive = self.archives[provider]
                    path = 'jkl/native.jkl' if provider == 'motssp' else 'jkl/static.jkl'
                    entries = {p: archive.read(p) for p in archive.entries}
                    entries[path] = ('World templates 1\n' + name + ' none type=actor\n').encode()
                    self.archives[provider] = Gob(build_gob(entries))
                self.repin()
                self.spec['owned_hashes'] = {k:v.sha256 for k,v in self.archives.items()}
                for operation in (self.build, lambda: self.verify(payload)):
                    with self.subTest(name=name, provider=provider), self.assertRaisesRegex(
                            sp_converter.SingleplayerError, 'unexpectedly resolves'):
                        operation()

    def test_changed_output_default_predicate_spawn_or_damage_fails(self):
        payload, _ = self.build(); output = Gob(payload)
        for old, new in [(b'bs_lostpilott', b'bs_walkplayer'), (b'0.60', b'0.90'),
                         (b'CreateThing(pilot2', b'CreateThing(-1'),
                         (b'return;', b'DamageThing(newThing, 100, 0x2, -1); return;')]:
            files = {p:output.read(p) for p in output.entries}
            self.assertIn(old, files['cog/bs_first.cog'])
            files['cog/bs_first.cog'] = files['cog/bs_first.cog'].replace(old,new)
            with self.subTest(old=old), self.assertRaisesRegex(sp_converter.SingleplayerError, 'Source resource transformation'):
                self.verify(build_gob(files))
        files = {p:output.read(p) for p in output.entries}
        world = bridge.text(files['jkl/test.jkl'])
        files['jkl/test.jkl'] = bridge.replace_block(world, 'templates',
            bridge.records(world,'templates') + ['bs_lostpilott none type=actor']).encode()
        with self.assertRaises(sp_converter.SingleplayerError):
            self.verify(build_gob(files))

    def test_rule_forbids_behavior_edits_and_oversized_isolated_default(self):
        self.spec['cog_edits'] = {'first.cog': [{'old':'0.60','new':'0.90','count':1}]}
        with self.assertRaisesRegex(sp_converter.SingleplayerError, 'behavior edits'):
            self.build()
        del self.spec['cog_edits']
        rule = self.spec['source_template_omissions'][0]
        rule['default'] = 'a' * 29; rule['output_name'] = 'bs_' + rule['default']
        with self.assertRaisesRegex(sp_converter.SingleplayerError, 'authority'):
            self.build()


@unittest.skipUnless(os.environ.get('WBW_SP_TEST_BASELINES') and os.environ.get('WBW_SP_TEST_ORIGINAL'),
                     'Set explicit owned baselines and original ZIP paths to run private payload controls')
class SingleplayerPayloadControls(unittest.TestCase):
    """Code-only tests: retail and authored fixture bytes are supplied locally."""
    @classmethod
    def setUpClass(cls):
        cls.recipe_id = 'sp-phantom-menace-final-battle'
        cls.archives = bridge.pinned_archives(Path(os.environ['WBW_SP_TEST_BASELINES']),
                                              include_jksp=True, include_motssp=True)
        cls.originals, _ = sp_converter.open_original(Path(os.environ['WBW_SP_TEST_ORIGINAL']), cls.recipe_id)
        cls.payload, cls.manifest = sp_converter.build(cls.archives, cls.originals, cls.recipe_id)
        cls.output = Gob(cls.payload)
        cls.world_path = next(iter(sp_converter.recipe_details(cls.recipe_id)['worlds']))

    def mutated_files(self):
        return {path: self.output.read(path) for path in self.output.entries}

    def rejects(self, files, expected):
        with self.assertRaisesRegex(sp_converter.SingleplayerError, expected):
            sp_converter.verify(self.archives, self.originals, self.recipe_id, build_gob(files))

    def test_valid_payload_and_manifest_repeat_exactly(self):
        repeat, manifest = sp_converter.build(self.archives, self.originals, self.recipe_id)
        self.assertEqual(self.payload, repeat)
        self.assertEqual(self.manifest, manifest)
        self.assertEqual(sp_converter.verify(self.archives, self.originals, self.recipe_id,
                                             self.payload)['status'], 'structural-preservation-pass')

    def test_missing_source_cog_and_model_are_rejected(self):
        for path in ('cog/bs_untitled_start.cog', '3do/bs_obiduel.3do'):
            with self.subTest(path=path):
                files = self.mutated_files(); del files[path]
                self.rejects(files, 'Source resource transformation')

    def test_changed_authored_cog_is_rejected(self):
        files = self.mutated_files()
        files['cog/bs_untitled_start.cog'] += b'\n'
        self.rejects(files, 'Source resource transformation')

    def test_progression_change_is_rejected(self):
        files = self.mutated_files(); files['episode.jk'] += b'\n'
        self.rejects(files, 'Episode progression')

    def test_header_and_physics_change_is_rejected(self):
        files = self.mutated_files()
        world = bridge.text(files[self.world_path])
        changed, count = re.subn(r'(?im)^(World gravity\s+)\S+', r'\g<1>123', world, count=1)
        self.assertEqual(count, 1)
        files[self.world_path] = changed.encode('cp1252')
        self.rejects(files, 'header, normals, physics')

    def test_authored_template_parameter_change_is_rejected(self):
        files = self.mutated_files(); world = bridge.text(files[self.world_path])
        rows = bridge.records(world, 'templates')
        index = next(i for i,row in enumerate(rows) if row.startswith('bs_') and 'health=' in row)
        rows[index] = re.sub(r'health=\S+', 'health=123456', rows[index], count=1)
        files[self.world_path] = bridge.replace_block(world, 'templates', rows).encode('cp1252')
        self.rejects(files, 'Authored template physics')

    def test_placed_thing_template_change_is_rejected(self):
        files = self.mutated_files(); world = bridge.text(files[self.world_path])
        rows = bridge.records(world, 'things'); parts = rows[0].split(); parts[1] = 'bs_unreviewed'
        rows[0] = ' '.join(parts)
        files[self.world_path] = bridge.replace_block(world, 'things', rows,
            int(bridge.block(world, 'things')[2])).encode('cp1252')
        self.rejects(files, 'Placed thing parameters')

    def test_missing_native_preload_is_rejected(self):
        files = self.mutated_files(); world = bridge.text(files[self.world_path])
        rows = bridge.records(world, 'scripts'); del rows[-1]
        files[self.world_path] = bridge.replace_block(world, 'scripts', rows,
            int(bridge.block(world, 'scripts')[2])).encode('cp1252')
        self.rejects(files, 'Resource table differs')

    def test_arbitrary_identical_native_asset_and_native_override_are_rejected(self):
        path = next(path for path in self.archives['motsres'].entries
                    if path.endswith('.wav') and path not in self.output.entries)
        for raw in (self.archives['motsres'].read(path), b'unreviewed override'):
            with self.subTest(identical=raw == self.archives['motsres'].read(path)):
                files = self.mutated_files(); files[path] = raw
                self.rejects(files, 'Native copied resource set')

    def test_native_player_controller_override_is_rejected(self):
        path = 'cog/kyle_m.cog'
        files = self.mutated_files(); files[path] = self.archives['motsres'].read(path) + b'\n'
        self.rejects(files, 'Native copied resource set')

    def test_gameplay_capacity_change_is_rejected(self):
        files = self.mutated_files(); world = bridge.text(files[self.world_path])
        files[self.world_path] = bridge.replace_block(world, 'cogs', bridge.records(world, 'cogs'), 0).encode('cp1252')
        self.rejects(files, 'Gameplay table capacity')

    def test_adapter_writes_exact_notices_and_refuses_repository_or_nonempty_stage(self):
        original = Path(os.environ['WBW_SP_TEST_ORIGINAL'])
        with tempfile.TemporaryDirectory() as directory:
            result = sp_converter.build_to_directory(self.archives, original, directory, self.recipe_id)
            self.assertEqual(set(result), {'filename', 'manifest_filename', 'verification', 'startup_overlay'})
            self.assertIsNone(result['startup_overlay'])
            self.assertEqual((Path(directory) / result['filename']).read_bytes(), self.payload)
            _, notices = sp_converter.open_original(original, self.recipe_id)
            for name, data in notices.items():
                self.assertEqual((Path(directory) / name).read_bytes(), data)
            with self.assertRaisesRegex(sp_converter.SingleplayerError, 'empty staging'):
                sp_converter.build_to_directory(self.archives, original, directory, self.recipe_id)
        with self.assertRaisesRegex(sp_converter.SingleplayerError, 'outside the source'):
            sp_converter.build_to_directory(self.archives, original, Path(sp_converter.__file__).parent, self.recipe_id)


@unittest.skipUnless(os.environ.get('WBW_SP_TEST_BASELINES') and os.environ.get('WBW_SP_TEST_MAUL_ORIGINAL'),
                     'Set explicit owned baselines and Maul/Jinn source ZIP to run private payload controls')
class MaulJinnPayloadControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe_id = 'sp-maul-vs-qui-gon'
        cls.archives = bridge.pinned_archives(Path(os.environ['WBW_SP_TEST_BASELINES']),
                                              include_jksp=True, include_motssp=True)
        cls.originals, _ = sp_converter.open_original(Path(os.environ['WBW_SP_TEST_MAUL_ORIGINAL']), cls.recipe_id)
        cls.payload, cls.manifest = sp_converter.build(cls.archives, cls.originals, cls.recipe_id)
        cls.output = Gob(cls.payload)

    def test_full_episode_rebuild_and_original_force_setup_preserved(self):
        repeat, manifest = sp_converter.build(self.archives, self.originals, self.recipe_id)
        self.assertEqual(repeat, self.payload); self.assertEqual(manifest, self.manifest)
        self.assertEqual(self.output.read('episode.jk'), self.originals['episode'].read('episode.jk'))
        self.assertEqual(sp_converter.verify(self.archives, self.originals, self.recipe_id,
            self.payload)['status'], 'structural-preservation-pass')
        self.assertEqual(sp_converter.recipe_details(self.recipe_id)['entry']['massassi_id'], 26)

    def test_changed_authored_force_rank_is_rejected(self):
        files = {path: self.output.read(path) for path in self.output.entries}
        path = 'cog/bs_duel_start.cog'
        changed = files[path].replace(b'SetInv(player, 20, 7)', b'SetInv(player, 20, 8)')
        self.assertNotEqual(changed, files[path]); files[path] = changed
        with self.assertRaisesRegex(sp_converter.SingleplayerError, 'Source resource transformation'):
            sp_converter.verify(self.archives, self.originals, self.recipe_id, build_gob(files))

    def test_sector_sound_rewrite_is_verified_without_allowing_arbitrary_change(self):
        files = {path: self.output.read(path) for path in self.output.entries}
        path = 'jkl/zela_duel.jkl'
        world = bridge.text(files[path])
        changed, count = re.subn(r'(?m)^(SOUND\s+)\S+', r'\g<1>unreviewed.wav', world, count=1)
        self.assertEqual(count, 1)
        files[path] = changed.encode('cp1252')
        with self.assertRaisesRegex(sp_converter.SingleplayerError, 'geometry/topology change: sectors'):
            sp_converter.verify(self.archives, self.originals, self.recipe_id, build_gob(files))

    def test_native_pickup_controller_cannot_be_overridden(self):
        files = {path: self.output.read(path) for path in self.output.entries}
        files['cog/pow_mana.cog'] = self.archives['jkres'].read('cog/pow_mana.cog')
        with self.assertRaisesRegex(sp_converter.SingleplayerError, 'Native copied resource set'):
            sp_converter.verify(self.archives, self.originals, self.recipe_id, build_gob(files))


@unittest.skipUnless(os.environ.get('WBW_SP_TEST_BASELINES') and os.environ.get('WBW_SP_TEST_PUMPING_ORIGINAL'),
                     'Set explicit owned baselines and Pumping Station source ZIP to run private payload controls')
class PumpingStationPayloadControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe_id = 'sp-imperial-pumping-station'
        cls.archives = bridge.pinned_archives(Path(os.environ['WBW_SP_TEST_BASELINES']),
                                              include_jksp=True, include_motssp=True)
        cls.originals, cls.notices = sp_converter.open_original(
            Path(os.environ['WBW_SP_TEST_PUMPING_ORIGINAL']), cls.recipe_id)
        cls.payload, cls.manifest = sp_converter.build(cls.archives, cls.originals, cls.recipe_id)
        cls.output = Gob(cls.payload)

    def files(self):
        return {path: self.output.read(path) for path in self.output.entries}

    def rejects(self, files, expected):
        with self.assertRaisesRegex(sp_converter.SingleplayerError, expected):
            sp_converter.verify(self.archives, self.originals, self.recipe_id, build_gob(files))

    def test_repeat_build_preserves_episode_and_non_jedi_inventory(self):
        repeat, manifest = sp_converter.build(self.archives, self.originals, self.recipe_id)
        self.assertEqual((repeat, manifest), (self.payload, self.manifest))
        self.assertEqual(self.output.read('episode.jk'), self.originals['episode'].read('episode.jk'))
        report = sp_converter.verify(self.archives, self.originals, self.recipe_id, self.payload)
        self.assertEqual(report['status'], 'structural-preservation-pass')
        self.assertFalse(report['runtime_verified'])
        source = bridge.text(self.originals['episode'].read('cog/installation_start.cog'))
        converted = bridge.text(self.output.read('cog/bs_installation_start.cog'))
        self.assertEqual(source, converted)  # No filename/default-template substitutions in this COG.
        self.assertIn('SetInv(player, 20, 0);', converted)
        for ordinal, amount in ((1, 1), (2, 1), (3, 1), (4, 12), (8, 3), (11, 300)):
            self.assertIn(f'SetInv(player, {ordinal}, {amount});', converted)
        self.assertNotIn('SetInv(player, 131,', converted)

    def test_adding_force_rank_or_rewriting_original_weapon_ordinal_is_rejected(self):
        path = 'cog/bs_installation_start.cog'
        for old, new in ((b'SetInv(player, 20, 0);', b'SetInv(player, 20, 8);'),
                         (b'SetInv(player, 8, 3);', b'SetInv(player, 128, 3);')):
            with self.subTest(change=new):
                files = self.files()
                self.assertIn(old, files[path])
                files[path] = files[path].replace(old, new)
                self.rejects(files, 'Source resource transformation')

    def test_corbit_player_model_and_reactor_model_are_retained(self):
        world = bridge.text(self.output.read('jkl/mk_ips.jkl'))
        rows = bridge.records(world, 'templates')
        player = next(row for row in rows if row.startswith('bs_walkplayer2 '))
        self.assertIn('type=player', player)
        self.assertIn('model3d=bs_rebcom.3do', player)
        self.assertIn('cog=kyle_m.cog', player)
        self.assertNotIn('model3d=ky.3do', player)
        reactor = next(row for row in rows if row.startswith('bs_reactorbomb '))
        self.assertIn('model3d=bs_bomb.3do', reactor)
        self.assertNotIn('cog=pow_', reactor)
        files = self.files()
        del files['3do/bs_rebcom.3do']
        self.rejects(files, 'Source resource transformation')

    def test_native_ordinary_pickups_do_not_ship_jk_controller_replacements(self):
        world = bridge.text(self.output.read('jkl/mk_ips.jkl'))
        for name in ('pow_drailgun', 'pow_drepeater', 'pow_dstrifle', 'pow_energy',
                     'pow_railcharges', 'pow_sequencer', 'pow_smbkpk', 'pow_thermal'):
            with self.subTest(controller=name):
                self.assertIn(name + '_m.cog', world)
                self.assertNotIn('cog/bs_' + name + '.cog', self.output.entries)
                self.assertNotIn('cog/' + name + '_m.cog', self.output.entries)
        files = self.files()
        files['cog/pow_energy_m.cog'] = self.archives['jkres'].read('cog/pow_energy.cog')
        self.rejects(files, 'Native copied resource set')

    def test_original_wrench_logic_stays_isolated_from_mots_story_dialogue(self):
        for color, bin_number in (('blue', 49), ('yellow', 50)):
            path = 'cog/bs_pow_wrench' + color + '.cog'
            value = bridge.text(self.output.read(path))
            self.assertRegex(value, rf'\bbin\s*=\s*{bin_number}\b')
            self.assertNotIn('PlayVoiceLocal', value)
            self.assertNotIn('Duncansnd', value)
            self.assertNotIn('cog/pow_wrench' + color + '.cog', self.output.entries)
            files = self.files()
            native = 'cog/pow_wrench' + color + '.cog'
            files[path] = self.archives['motsres'].read(native)
            self.rejects(files, 'Source resource transformation')

    def test_no_speculative_camera_repair_and_no_removed_goal_sequence(self):
        start = bridge.text(self.output.read('cog/bs_installation_start.cog'))
        self.assertEqual(start.count('stopbrief'), 1)
        self.assertEqual(start.count('briefstop'), 3)
        files = self.files()
        path = 'cog/bs_installation_goals.cog'
        self.assertIn(b'jkEndLevel(1);', files[path])
        files[path] = files[path].replace(b'jkEndLevel(1);', b'return;')
        self.rejects(files, 'Source resource transformation')

    def test_key_gate_and_pump_control_changes_are_rejected(self):
        for path, old, new in (
                ('cog/bs_watergate.cog', b'GetInv(GetSourceRef(), 49)', b'GetInv(GetSourceRef(), 50)'),
                ('cog/bs_movepipes.cog', b'GetInv(GetSourceRef(), 50)', b'GetInv(GetSourceRef(), 49)'),
                ('cog/bs_pumpcontrol.cog', b'pathmovepause', b'pathmoveresume')):
            with self.subTest(path=path):
                files = self.files()
                self.assertIn(old, files[path])
                files[path] = files[path].replace(old, new)
                self.rejects(files, 'Source resource transformation')


@unittest.skipUnless(os.environ.get('WBW_SP_TEST_BASELINES') and os.environ.get('WBW_SP_TEST_STB_ORIGINAL'),
                     'Set explicit owned baselines and Steal the Bottle source ZIP to run private payload controls')
class StealBottlePayloadControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe_id = 'sp-steal-the-bottle'
        cls.archives = bridge.pinned_archives(Path(os.environ['WBW_SP_TEST_BASELINES']),
                                              include_jksp=True, include_motssp=True)
        cls.originals, cls.notices = sp_converter.open_original(
            Path(os.environ['WBW_SP_TEST_STB_ORIGINAL']), cls.recipe_id)
        cls.payload, cls.manifest = sp_converter.build(cls.archives, cls.originals, cls.recipe_id)
        cls.output = Gob(cls.payload)
        cls.world_path = 'jkl/jksp1.jkl'

    def files(self):
        return {path: self.output.read(path) for path in self.output.entries}

    def rejects(self, files, expected):
        with self.assertRaisesRegex(sp_converter.SingleplayerError, expected):
            sp_converter.verify(self.archives, self.originals, self.recipe_id, build_gob(files))

    def test_exact_saber_port_preserves_rank_and_startup_timer_fallthrough(self):
        source = bridge.text(self.originals['episode'].read('cog/jksp1_start.cog'))
        converted = bridge.text(self.output.read('cog/bs_jksp1_start.cog'))
        self.assertEqual(source.count('SetInv(player, 10, 1);'), 1)
        self.assertEqual(converted, source.replace('SetInv(player, 10, 1);', 'SetInv(player, 131, 1);'))
        for statement in ('SetInv(player, 1, 1);', 'SetInv(player, 2, 1);',
                          'SetInv(player, 11, 100);', 'SetInv(player, 20, 0);',
                          'SetInv(player, 14, 4*50);', 'SetInv(player, 99, 1000);'):
            self.assertIn(statement, converted)
        self.assertRegex(converted, r'SetTimer\(15\);\s*timer:')
        for old, new in ((b'SetInv(player, 131, 1);', b'SetInv(player, 10, 1);'),
                         (b'SetTimer(15);', b'SetTimer(15); Return;'),
                         (b'SetInv(player, 20, 0);', b'SetInv(player, 20, 8);')):
            with self.subTest(change=new):
                files = self.files()
                files['cog/bs_jksp1_start.cog'] = files['cog/bs_jksp1_start.cog'].replace(old, new)
                self.rejects(files, 'Source resource transformation')

    def test_authored_officer_ai_is_preserved_instead_of_native_namesake(self):
        original = self.originals['episode'].read('misc/ai/iodefault.ai')
        # Text normalization and the existing filename-comment rewrite are exact;
        # all authored AI parameters and instincts must remain unchanged.
        expected = bridge.text(original).replace('IODEFAULT.AI', 'bs_iodefault.ai')
        self.assertEqual(bridge.text(self.output.read('misc/ai/bs_iodefault.ai')), expected)
        native = self.archives['motsres'].read('misc/ai/iodefault.ai')
        self.assertNotEqual(original, native)
        world = bridge.text(self.output.read(self.world_path))
        officer = next(row for row in bridge.records(world, 'templates') if row.startswith('bs_iofficeri '))
        self.assertIn('aiclass=bs_iodefault.ai', officer)
        self.assertIn('soundclass=bs_drunkguard.snd', officer)
        files = self.files(); files['misc/ai/bs_iodefault.ai'] = native
        self.rejects(files, 'Source resource transformation')

    def test_drunk_guard_behavior_and_custom_speech_remain_authored(self):
        original = self.originals['episode']
        ai = original.read('misc/ai/drunkguard.ai')
        self.assertEqual(bridge.text(self.output.read('misc/ai/bs_drunkguard.ai')), bridge.text(ai))
        self.assertNotRegex(bridge.text(ai), r'(?im)^\s*(PrimaryFire|BlindFire)\b')
        self.assertRegex(bridge.text(ai), r'(?im)^\s*Talk\s+3\.0,\s*0\.90')
        sound = bridge.text(self.output.read('misc/snd/bs_drunkguard.snd'))
        for name in ('pampadim', 'hik', 'royh', 'mmmm'):
            self.assertIn('bs_' + name + '.wav', sound)
            self.assertEqual(self.output.read('sound/bs_' + name + '.wav'),
                             original.read('sound/' + name + '.wav'))
        files = self.files(); files['misc/ai/bs_drunkguard.ai'] += b'\nPrimaryFire 800.0\n'
        self.rejects(files, 'Source resource transformation')

    def test_door_patrol_thrust_and_surface_motion_arguments_are_unchanged(self):
        source = bridge.text(self.originals['episode'].read(self.world_path))
        world = bridge.text(self.output.read(self.world_path))
        old_rows, new_rows = bridge.records(source, 'cogs'), bridge.records(world, 'cogs')
        self.assertEqual(len(new_rows), 7)
        for left, right in zip(old_rows, new_rows):
            self.assertEqual(left.split()[2:], right.split()[2:])
        self.assertEqual(new_rows[1].split()[2:], ['7', '6', '0.75', '1', '0.25'])
        self.assertEqual(new_rows[4].split()[2:], ['32', '-1', '-1', '-1', '8', '2', '0.5'])
        for index in (0, 1, 2, 3, 4):
            with self.subTest(cog_index=index):
                rows = new_rows.copy(); parts = rows[index].split(); parts[-1] = '12345'
                rows[index] = ' '.join(parts)
                files = self.files()
                files[self.world_path] = bridge.replace_block(world, 'cogs', rows,
                    int(bridge.block(world, 'cogs')[2])).encode('cp1252')
                self.rejects(files, 'Authored COG argument changed')

    def test_original_bottle_room_crossing_remains_victory_condition(self):
        world = bridge.text(self.output.read(self.world_path))
        rows = bridge.records(world, 'cogs')
        self.assertEqual(rows[5], '5: bs_00_endlevel.cog 682')
        ending = bridge.text(self.output.read('cog/bs_00_endlevel.cog'))
        self.assertRegex(ending, r'(?im)^crossed:')
        self.assertIn('jkEndLevel();', ending)
        bottle = next(row for row in bridge.records(world, 'templates') if row.startswith('bs_bottle05 '))
        self.assertEqual(bottle.split()[1], 'bs__structure')
        self.assertNotIn('cog=', bottle)
        rows[5] = '5: bs_00_endlevel.cog 684'
        files = self.files()
        files[self.world_path] = bridge.replace_block(world, 'cogs', rows,
            int(bridge.block(world, 'cogs')[2])).encode('cp1252')
        self.rejects(files, 'Authored COG argument changed')

    def test_unused_bundled_scripts_stay_unused_and_disabled_tanks_are_preserved(self):
        world = bridge.text(self.output.read(self.world_path))
        for name in ('00_aiframepatrol.cog', '00_simple_elev.cog'):
            self.assertIn('cog/' + name, self.originals['episode'].entries)
            self.assertNotIn('cog/bs_' + name, self.output.entries)
            self.assertNotIn(name, world)
        things = bridge.records(world, 'things')
        self.assertEqual(len(things), 42)
        self.assertEqual(int(bridge.block(world, 'things')[2]), 242)
        for index in (3, 4, 5):
            self.assertEqual(things[index].split()[9], '-1')
        self.assertIn('numframes=2', things[32])
        self.assertIn('frame=(20.3/-9.45/-2.2:0/90/0)', things[32])
        files = self.files(); rows = things.copy(); parts = rows[3].split(); parts[9] = '0'
        rows[3] = ' '.join(parts)
        files[self.world_path] = bridge.replace_block(world, 'things', rows, 242).encode('cp1252')
        self.rejects(files, 'Placed thing parameters changed')

    def test_native_inventory_bindings_do_not_ship_controller_replacements(self):
        spec = sp_converter.recipe_details(self.recipe_id)
        world = bridge.text(self.output.read(self.world_path))
        for source, native in spec['native_cog_bindings'].items():
            self.assertIn(native, world)
            self.assertNotIn('cog/bs_' + source, self.output.entries)
            self.assertNotIn('cog/' + native, self.output.entries)
        files = self.files()
        files['cog/pow_concrifle_m.cog'] = self.archives['jkres'].read('cog/pow_concrifle.cog')
        self.rejects(files, 'Native copied resource set')

    def test_exact_episode_notice_and_goal_strings_are_retained(self):
        source = self.originals['episode']
        self.assertEqual(self.output.read('episode.jk'), source.read('episode.jk'))
        self.assertEqual(self.output.read('misc/cogstrings.uni'), source.read('misc/cogstrings.uni'))
        with tempfile.TemporaryDirectory() as directory:
            result = sp_converter.build_to_directory(self.archives,
                Path(os.environ['WBW_SP_TEST_STB_ORIGINAL']), directory, self.recipe_id)
            self.assertEqual((Path(directory) / result['filename']).read_bytes(), self.payload)
            self.assertIsNone(result['startup_overlay'])
            for path, data in self.notices.items():
                self.assertEqual((Path(directory) / path).read_bytes(), data)
            self.assertFalse(result['verification']['runtime_verified'])
            self.assertEqual(result['verification']['status'], 'structural-preservation-pass')


if __name__ == '__main__':
    unittest.main()

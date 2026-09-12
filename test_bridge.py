"""Synthetic fixtures only. Retail invariant checks live outside this project."""
import struct
import hashlib
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from gob import ArchiveError, Gob, build_gob, resource_name, write_gob
from bridge import (RecipeError, Catalog, convert_things, expand_surface_lighting,
                    recipe, references, records, replace_block, template_defaults,
                    rewrite_cog_template_arguments, pinned_archives, open_dojo, HASHES,
                    STOCK_MAPS, stock_selector, stock_output_name, check_output_path,
                    adapt_ctf_saber_grants, ctf_items_dat, reviewed_source_omission,
                    ctf_startup_candidate, ctf_startup_files, write_ctf_startup,
                    check_ctf_startup_directory, CTF_STARTUP_ARCHIVE)


class ArchiveSafety(unittest.TestCase):
    def test_reads_legacy_directory_at_end(self):
        # Independent hand-built archive, unlike the writer's directory-first form.
        data = struct.pack('<4sII', b'GOB ', 20, 17) + b'hello'
        data += struct.pack('<I', 1) + struct.pack('<II128s', 12, 5, b'COG\\demo.cog')
        self.assertEqual(Gob(data).read('cog/DEMO.cog'), b'hello')

    def test_roundtrip_binary_and_deterministic_order(self):
        payload = {'mat/x.mat': bytes(range(256)), 'cog/x.cog': b'\x00\r\n'}
        a = build_gob(payload); b = build_gob(dict(reversed(list(payload.items()))))
        self.assertEqual(a, b)
        self.assertEqual(Gob(a).read('mat/x.mat'), bytes(range(256)))

    def test_path_attacks(self):
        for value in ('../x', '/x', 'C:\\x', 'a//b', 'a/./b', 'a/../b',
                      'NUL.txt', 'x:stream', 'x.', 'x ', 'a\x00b', '\\\\server\\x'):
            with self.subTest(value=value), self.assertRaises(ArchiveError):
                resource_name(value)

    def test_case_collision(self):
        with self.assertRaises(ArchiveError):
            build_gob({'MAT/X.MAT': b'x', 'mat/x.mat': b'y'})

    def test_truncation_and_bounds(self):
        good = build_gob({'a': b'abc'})
        for data in (good[:8], good[:-1], good[:8] + b'\xff' * 4 + good[12:]):
            with self.assertRaises(ArchiveError):
                Gob(data)

    def test_overlapping_payloads(self):
        data = bytearray(build_gob({'a': b'abc', 'b': b'def'}))
        first = struct.unpack_from('<I', data, 16)[0]
        struct.pack_into('<I', data, 16 + 136, first + 1)
        with self.assertRaises(ArchiveError):
            Gob(data)

    def test_writer_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.goo'
            write_gob(path, {'a': b'first'})
            with self.assertRaises(FileExistsError):
                write_gob(path, {'a': b'second'})
            self.assertEqual(Gob.open(path).read('a'), b'first')


class SemanticTransforms(unittest.TestCase):
    def test_stock_selectors_identify_exact_pinned_worlds(self):
        expected = {'m2': 'nar-shaddaa', 'm4': 'bespin', 'm5': 'blades-of-death',
                    'm10': 'canyon-oasis', 'm_boss15': 'valley', 'm_boss17': 'battleground',
                    'c1': 'ctf-duel', 'c2': 'ctf-arena', 'c3': 'ctf-challenge'}
        for world, key in expected.items():
            with self.subTest(world=world):
                self.assertEqual(stock_selector(world), key)
                self.assertEqual(stock_selector(world.upper() + '.JKL'), key)
                self.assertEqual(stock_selector(STOCK_MAPS[key]['title']), key)
        self.assertEqual(stock_selector('Canyon Oasis'), 'canyon-oasis')
        with self.assertRaises(RecipeError):
            stock_selector('../../unsupported.jkl')

    def test_ctf_recipes_keep_separate_source_archive_and_episode_type(self):
        self.assertEqual(len(STOCK_MAPS), 9)
        for key in ('ctf-duel', 'ctf-arena', 'ctf-challenge'):
            with self.subTest(key=key):
                self.assertEqual(STOCK_MAPS[key]['archive'], 'jkctf')
                self.assertEqual(STOCK_MAPS[key]['episode_type'], 8)
        from types import SimpleNamespace
        headers_only = {key: SimpleNamespace(sha256=value) for key, value in HASHES.items()}
        with self.assertRaisesRegex(RecipeError, 'JK1CTF.GOB'):
            recipe(headers_only, stock_map='ctf-duel')

    def test_ctf_saber_grants_do_not_remap_flag_or_key_bins(self):
        value = 'SetInv(player, 10, 1);\nSetInv(player, 81, 1);\nSetInv(player, 84, 1);\nSetInv(player, 10, 1);'
        result = adapt_ctf_saber_grants(value)
        self.assertEqual(result.count('SetInv(player, 131, 1);'), 2)
        self.assertIn('SetInv(player, 81, 1);', result)
        self.assertIn('SetInv(player, 84, 1);', result)
        with self.assertRaises(RecipeError):
            adapt_ctf_saber_grants('SetInv(player, 10, 1);')

    def test_ctf_hud_descriptor_preserves_native_gameplay_items(self):
        value = 'ysalamiri 68 0 1 0x042\nysalamiri 81 0 1 0x048\ngoldflag 82 0 1 0x048\nlightsaber 131 0 1 0x0a4 cog=weap_saber_m.cog\n'
        result = ctf_items_dat(value)
        self.assertEqual(result, value.replace('ysalamiri 81', 'redflag 81'))
        with self.assertRaises(RecipeError):
            ctf_items_dat(value.replace('81 0 1', '81 0 2'))

    def test_ctf_startup_overlay_contains_only_native_items_edit(self):
        from types import SimpleNamespace
        items = b'ysalamiri 68 0 1 0x042\nysalamiri 81 0 1 0x048\ngoldflag 82 0 1 0x048\n'
        seen_icons = []
        def icon_read(path):
            seen_icons.append(path)
            return b'synthetic icon'
        archives = {'motsres': SimpleNamespace(sha256=HASHES['motsres'], read=lambda path: items),
                    'motssnd': SimpleNamespace(sha256=HASHES['motssnd'], read=icon_read)}
        data, manifest = ctf_startup_candidate(archives)
        archive = Gob(data)
        self.assertEqual(set(archive.entries), {'misc/items.dat'})
        self.assertEqual(archive.read('misc/items.dat'), items.replace(b'ysalamiri 81', b'redflag 81'))
        self.assertEqual(set(seen_icons), {'ui/bm/' + name for name in
                         ('icredfl8.bm', 'icredfl16.bm', 'icgoldf8.bm', 'icgoldf16.bm')})
        self.assertEqual(manifest['required_for'], ['ctf-duel', 'ctf-arena', 'ctf-challenge'])
        self.assertEqual(manifest['required_launch_arguments'], ['-motsCompat', '-path', 'bridge-ctf-ui'])
        archives['motsres'].sha256 = '0' * 64
        with self.assertRaisesRegex(RecipeError, 'input hash'):
            ctf_startup_candidate(archives)

    def test_ctf_startup_exact_reuse_and_contamination_rejection(self):
        data = build_gob({'misc/items.dat': b'synthetic fixture'})
        manifest = {'required_launch_arguments': ['-motsCompat', '-path', 'bridge-ctf-ui']}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'bridge-ctf-ui'
            first = write_ctf_startup(output, data, manifest)
            self.assertFalse(first['reused_identical'])
            self.assertTrue(write_ctf_startup(output, data, manifest)['reused_identical'])
            self.assertEqual((output / CTF_STARTUP_ARCHIVE).read_bytes(), data)
            (output / 'unexpected.goo').write_bytes(b'foreign mod')
            with self.assertRaisesRegex(RecipeError, 'different or extra'):
                write_ctf_startup(output, data, manifest)
            self.assertEqual((output / 'unexpected.goo').read_bytes(), b'foreign mod')

    def test_ctf_startup_refuses_different_items_and_missing_sidecars(self):
        original = build_gob({'misc/items.dat': b'original synthetic'})
        replacement = build_gob({'misc/items.dat': b'changed synthetic'})
        manifest = {'required_launch_arguments': ['-motsCompat', '-path', 'bridge-ctf-ui']}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'bridge-ctf-ui'
            write_ctf_startup(output, original, manifest)
            with self.assertRaises(RecipeError):
                check_ctf_startup_directory(output, ctf_startup_files(replacement, manifest))
            (output / 'README.txt').unlink()
            with self.assertRaises(RecipeError):
                write_ctf_startup(output, original, manifest)
            self.assertEqual((output / CTF_STARTUP_ARCHIVE).read_bytes(), original)

    def test_original_missing_material_waiver_requires_exact_edge_and_usage(self):
        model = b'MATERIALS 1\n0: absent.mat\nTEXTURE VERTICES 0\nFACES 1\n0: 0 0x3 3 3 0 0.0 3 0,0 1,0 2,0\nFACE NORMALS\n0: 0 1 0\n'
        catalog = Catalog([('synthetic', Gob(build_gob({'3do/shard.3do': model})))])
        rule = {'name': 'absent.mat', 'referrer': '3do/shard.3do',
                'referrer_sha256': hashlib.sha256(model).hexdigest(),
                'untextured_3do': True, 'reason': 'Synthetic untextured missing slot'}
        accepted = reviewed_source_omission('absent.mat', '3do/shard.3do', catalog, [rule])
        self.assertEqual(accepted['output_name'], 'br_absent.mat')
        self.assertEqual(accepted['output_referrer'], '3do/br_shard.3do')
        for name, caller in [('other.mat', '3do/shard.3do'), ('absent.mat', '3do/other.3do')]:
            with self.subTest(name=name, caller=caller), self.assertRaises(RecipeError):
                reviewed_source_omission(name, caller, catalog, [rule])
        with self.assertRaises(RecipeError):
            reviewed_source_omission('absent.mat', '3do/shard.3do', catalog,
                                     [{**rule, 'referrer_sha256': '0' * 64}])
        textured = model.replace(b'0: 0 0x3 3 3', b'0: 0 0x3 4 3')
        textured_catalog = Catalog([('synthetic', Gob(build_gob({'3do/shard.3do': textured})))])
        with self.assertRaises(RecipeError):
            reviewed_source_omission('absent.mat', '3do/shard.3do', textured_catalog,
                                     [{**rule, 'referrer_sha256': hashlib.sha256(textured).hexdigest()}])

    def test_stock_output_names_are_unique_and_keep_existing_revisions(self):
        outputs = [stock_output_name(key) for key in STOCK_MAPS]
        self.assertEqual(len(outputs), len(set(outputs)))
        self.assertEqual(stock_output_name('valley'), 'bridge-valley-v2.goo')
        self.assertEqual(stock_output_name('battleground'), 'bridge-battleground-v1.goo')

    def test_output_preflight_rejects_manifest_collision_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fixture.goo'
            path.with_suffix('.manifest.json').write_text('existing evidence')
            with self.assertRaises(RecipeError):
                check_output_path(path)
            self.assertFalse(path.exists())

    def test_legacy_tilde_filenames_are_whole_resource_references(self):
        self.assertEqual(references('material a=j_shou~1.mat\nmaterial b=shut~fbt.mat'),
                         {'j_shou~1.mat', 'shut~fbt.mat'})

    def test_template_namespace_preserves_unrelated_symbol_values(self):
        source = 'symbols\ntemplate spawn=Enemy local\nint health=20 local\nsound noise=door.wav local\nend\n'
        result = template_defaults(source, {'enemy': 'br_enemy'})
        self.assertIn('template spawn=br_enemy local', result)
        self.assertIn('int health=20 local', result)
        self.assertIn('sound noise=door.wav local', result)

    def test_exposed_template_argument_is_rewritten_by_type(self):
        cog = b'symbols\nmessage startup\nsector trigger\nthing position nolink\ntemplate enemy\nint count=1 local\nend\ncode\nstartup:\nReturn;\nend\n'
        catalog = Catalog([('synthetic', Gob(build_gob({'cog/generator.cog': cog})))])
        source = 'World cogs 257\n0: generator.cog 5 6 Enemy\nend\n'
        result = rewrite_cog_template_arguments(source, catalog, {'enemy': 'br_enemy'})
        self.assertIn('0: generator.cog 5 6 br_enemy', result)
        self.assertIn('World cogs 257', result)

    def test_incomplete_public_root_options_are_rejected(self):
        with self.assertRaises(RecipeError):
            pinned_archives(jk_root='synthetic')
        with self.assertRaises(RecipeError):
            pinned_archives('synthetic', jk_root='mixed', mots_root='mixed')

    def test_native_singleplayer_archive_is_optional_and_hash_gated(self):
        import bridge
        from types import SimpleNamespace
        paths = dict(bridge.PATHS, motssp=bridge.MOTSSP_PATH)
        keys = {str(Path('synthetic') / value): key for key, value in paths.items()}
        observed = []
        def open_archive(path):
            key = keys[str(path)]
            observed.append(key)
            return SimpleNamespace(sha256=bridge.MOTSSP_SHA256 if key == 'motssp' else HASHES[key])
        with patch.object(bridge.Gob, 'open', side_effect=open_archive):
            self.assertNotIn('motssp', pinned_archives('synthetic'))
            self.assertNotIn('motssp', observed)
            self.assertEqual(pinned_archives('synthetic', include_motssp=True)['motssp'].sha256,
                             bridge.MOTSSP_SHA256)
        def wrong_native(path):
            key = keys[str(path)]
            return SimpleNamespace(sha256='0' * 64 if key == 'motssp' else HASHES[key])
        with patch.object(bridge.Gob, 'open', side_effect=wrong_native):
            with self.assertRaisesRegex(RecipeError, 'motssp'):
                pinned_archives('synthetic', include_motssp=True)

    def test_battleground_requires_original_stream_archive(self):
        from types import SimpleNamespace
        headers_only = {key: SimpleNamespace(sha256=value) for key, value in HASHES.items()}
        with self.assertRaisesRegex(RecipeError, 'JK1.GOB'):
            recipe(headers_only, stock_map='battleground')

    def test_unknown_custom_package_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'dojo.gob'
            path.write_bytes(build_gob({'jkl/synthetic.jkl': b'synthetic'}))
            with self.assertRaises(RecipeError):
                open_dojo(path)

    def test_colormap_boundary_does_not_consume_geometry(self):
        source = 'World Colormaps 1\n0: palette.cmp\nWorld vertices 1\n# positions\n0: 1 2 3\nWorld texture vertices 0\nend\n'
        self.assertEqual(records(source, 'colormaps'), ['0: palette.cmp'])
        result = replace_block(source, 'colormaps', ['0: br_palette.cmp'])
        self.assertEqual(result[result.index('World vertices'):], source[source.index('World vertices'):])
    def test_light_channel_conversion_preserves_topology(self):
        source = 'World surfaces 1\n# comment\n0: 4 0x24 0x0 4 3 1 -1 0.25 3 2,7 3,8 4,9 0.1 2.50 0\nWorld sectors 1\n'
        actual, count = expand_surface_lighting(source)
        values = actual.splitlines()[2].split()
        self.assertEqual(count, 1)
        self.assertEqual(values[:13], source.splitlines()[2].split()[:13])
        self.assertEqual(values[13:], ['0.1'] * 4 + ['2.50'] * 4 + ['0'] * 4)
        self.assertTrue(actual.endswith('World sectors 1\n'))

    def test_already_colored_input_rejected(self):
        source = 'World surfaces 1\n0: 4 0x0 0x0 4 3 1 -1 0 1 0,0 1 1 1 1\n'
        with self.assertRaises(RecipeError):
            expand_surface_lighting(source)

    def test_thing_transform_preserves_placement_and_arguments(self):
        source = 'World things 257\n0: door object 1 2 3 10 20 30 4 numframes=1 frame=(1/2/3:0/0/0)\nend\n'
        result, count = convert_things(source, {'door': 'br_door'})
        self.assertEqual(count, 1)
        self.assertIn('World things 257', result)
        self.assertIn('0: br_door object 1 2 3 10 20 30 4 -1 numframes=1 frame=(1/2/3:0/0/0)', result)

    def test_player_uses_native_template(self):
        source = 'World things 1\n0: walkplayer player 1 2 3 0 0 0 4\nend\n'
        result, _ = convert_things(source, {'walkplayer': 'br_walkplayer'})
        self.assertIn('0: walkplayer player', result)

    def test_literals_exclude_comments(self):
        self.assertEqual(references('# ignored.cog\nsound s=door.wav // old.wav\nLoadModel("demo.3do");'), {'door.wav', 'demo.3do'})

    def test_unsupported_archive_recipe_rejected(self):
        with self.assertRaises(RecipeError):
            recipe({'jkmp': Gob(build_gob({'x': b'synthetic'}))})

    def test_ambiguous_resource_checked_when_used(self):
        a = Gob(build_gob({'mat/x.mat': b'a', '3do/mat/x.mat': b'b', 'y.wav': b'y'}))
        catalog = Catalog([('synthetic', a)])
        self.assertEqual(catalog.get('y.wav')[1], 'y.wav')
        with self.assertRaises(RecipeError):
            catalog.get('x.mat')


if __name__ == '__main__':
    unittest.main()

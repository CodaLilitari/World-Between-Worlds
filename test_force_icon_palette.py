"""Asset-free tests for the proposed derived-icon helper and both wrappers."""
import importlib.util
import pathlib
import struct
import sys
import unittest
from force_icon_palette import derive_allocation_icon,derivation_report,allocation_menu_palette

HERE=pathlib.Path(__file__).resolve().parent
GRAY=bytes(channel for i in range(256) for channel in (i,i,i))

def fixture(flags=0,key=0,palette=GRAY):
    header=bytearray(128);header[:4]=b'BM  '
    struct.pack_into('<I',header,4,70);struct.pack_into('<I',header,12,flags)
    struct.pack_into('<III',header,16,3,19,23);struct.pack_into('<I',header,28,key)
    struct.pack_into('<I',header,36,8)
    frames=[struct.pack('<II',28,28)+bytes((i+n*13)%256 for i in range(784)) for n in range(3)]
    return bytes(header)+b''.join(frames)+(palette if flags&2 else b'')

class IconTests(unittest.TestCase):
    def test_background_palette_extraction_and_negative_payloads(self):
        self.assertEqual(allocation_menu_palette(fixture(2)),GRAY)
        for data in (fixture(),fixture(2)[:-1],fixture(2)+b'x'):
            with self.assertRaises(ValueError):allocation_menu_palette(data)

    def test_identity_remap_preserves_original_three_frames(self):
        original=fixture();output=derive_allocation_icon(original,GRAY,GRAY)
        self.assertEqual(output[128:128+3*792],original[128:])
        self.assertEqual(struct.unpack_from('<III',output,16),(4,0,0))
        self.assertEqual(output[:16],original[:16]);self.assertEqual(output[28:128],original[28:128])

    def test_disabled_is_exact_third_luma_and_never_new_alpha(self):
        data=fixture();out=derive_allocation_icon(data,GRAY,GRAY)
        source=data[136:920];disabled=out[128+3*792+8:]
        self.assertEqual(disabled,bytes(0 if i==0 else max(1,i//3) for i in source))
        self.assertNotEqual(disabled,source)

    def test_explicit_colorkey_mask_preserved_all_states(self):
        data=fixture(1,42);out=derive_allocation_icon(data,GRAY,GRAY)
        for n in range(4):
            old=data[136+792*min(n,2):920+792*min(n,2)] if n<3 else data[136:920]
            new=out[136+792*n:920+792*n]
            self.assertEqual([i in (0,42) for i in old],[i in (0,42) for i in new])
        self.assertEqual(struct.unpack_from('<I',out,28)[0],42)

    def test_embedded_palette_replaced_only_on_derived_output(self):
        target=GRAY[:3]+b''.join(GRAY[i*3:i*3+3] for i in range(255,0,-1))
        data=fixture(2);before=bytes(data);out=derive_allocation_icon(data,GRAY,target)
        self.assertEqual(data,before);self.assertTrue(out.endswith(target));self.assertTrue(data.endswith(GRAY))
        self.assertEqual(struct.unpack_from('<I',out,12)[0],2)

    def test_embedded_source_disagreement_rejected(self):
        with self.assertRaisesRegex(ValueError,'disagree'):derive_allocation_icon(fixture(2),bytes(reversed(GRAY)),GRAY)

    def test_deterministic_output_and_report(self):
        data=fixture();a=derive_allocation_icon(data,GRAY,GRAY);b=derive_allocation_icon(data,GRAY,GRAY)
        self.assertEqual(a,b);report=derivation_report(data,a,GRAY,GRAY)
        self.assertEqual(report['weighted_rgb_rmse'],0);self.assertTrue(all(report['transparent_masks_preserved']))

    def test_mutated_output_report_rejected(self):
        data=fixture();out=bytearray(derive_allocation_icon(data,GRAY,GRAY));out[200]^=1
        with self.assertRaisesRegex(ValueError,'differs'):derivation_report(data,bytes(out),GRAY,GRAY)

    def test_bad_headers_counts_depths_sizes_and_flags(self):
        for offset,value in ((4,69),(16,4),(36,16),(128,27),(12,4),(28,256)):
            data=bytearray(fixture());struct.pack_into('<I',data,offset,value)
            with self.subTest(offset=offset),self.assertRaises(ValueError):derive_allocation_icon(bytes(data),GRAY,GRAY)
        for data in (b'',fixture()[:-1],fixture()+b'x'):
            with self.subTest(length=len(data)),self.assertRaises(ValueError):derive_allocation_icon(data,GRAY,GRAY)

    def test_bad_palettes_and_no_dark_ramp_rejected(self):
        for source,target in ((GRAY[:-1],GRAY),(GRAY,GRAY[:-1]),(GRAY,bytes([255,0,0])*256)):
            with self.assertRaises(ValueError):derive_allocation_icon(fixture(),source,target)

    def test_stable_smallest_index_tie_break(self):
        target=bytearray(GRAY);target[50*3:50*3+3]=bytes((49,49,49));target[51*3:51*3+3]=bytes((51,51,51))
        data=fixture();out=derive_allocation_icon(data,GRAY,bytes(target))
        self.assertEqual(out[136+50],49)

    def test_no_input_mutation(self):
        data=fixture();before=(data,GRAY);derive_allocation_icon(data,GRAY,GRAY);self.assertEqual(before,(data,GRAY))

    def test_actual_project_wrapper(self):
        import importlib
        name = 'ninja_converter' if (HERE/'ninja_converter.py').exists() else 'mfr'
        module = importlib.import_module(name)
        self.assertEqual(module.allocation_icon(fixture(),GRAY,GRAY),derive_allocation_icon(fixture(),GRAY,GRAY))
        with self.assertRaises(ValueError):module.allocation_icon(b'bad',GRAY,GRAY)

if __name__=='__main__':unittest.main()

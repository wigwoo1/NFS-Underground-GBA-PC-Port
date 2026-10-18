from pathlib import Path
p=Path(r'G:\EXTRA DATA DRIVE\Desktop\Games\Codex\NFSUG-Native-PC-Port\work\v2\test_make_seamless_texture.py')
s=p.read_text()
marker='''    def test_validation_and_no_overwrite(self):
'''
insert='''    def test_uv_atlas_mode_keeps_opposite_borders_independent(self):
        source = Image.open(self.source).convert("RGBA")
        pixels = np.asarray(source).copy()
        pixels[:, 0, :] = (245, 24, 32, 255)
        pixels[:, -1, :] = (18, 36, 240, 255)
        Image.fromarray(pixels, "RGBA").save(self.source)
        output = self.root / "uv-atlas.png"
        report = create(self.source, output, seamless=False)
        actual = np.asarray(Image.open(output).convert("RGBA"))
        self.assertFalse(report["seamless"])
        self.assertEqual(report["edge_blend_output_pixels"], 0)
        self.assertFalse(np.array_equal(actual[:, 0, :3], actual[:, -1, :3]))
        expected_alpha = np.asarray(Image.open(self.source).convert("RGBA").resize(
            (256, 256), Image.Resampling.NEAREST))[..., 3]
        np.testing.assert_array_equal(actual[..., 3], expected_alpha)
        self.assertFalse(report["complete_pack"])

'''
if s.count(marker)!=1: raise SystemExit('test insertion point not unique')
p.write_text(s.replace(marker,insert+marker))
print('patched',p)

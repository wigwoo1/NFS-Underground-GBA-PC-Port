from pathlib import Path
p=Path(r'G:\EXTRA DATA DRIVE\Desktop\Games\Codex\NFSUG-Native-PC-Port\work\v2\make_seamless_texture.py')
s=p.read_text()
repls=[
('''           preserve_bright_feather: int = 24) -> dict:''','''           preserve_bright_feather: int = 24, seamless: bool = True) -> dict:'''),
('''    if isinstance(edge_width_source, bool) or not isinstance(edge_width_source, int) or edge_width_source < 1:
        raise ValueError("edge_width_source must be a positive integer")''','''    if isinstance(seamless, bool) is False:
        raise ValueError("seamless must be a boolean")
    if isinstance(edge_width_source, bool) or not isinstance(edge_width_source, int) or edge_width_source < 1:
        raise ValueError("edge_width_source must be a positive integer")'''),
('''    strip = edge_width_source * scale
    if strip * 2 > min(width, height):
        raise ValueError("edge blend band must fit within half the smaller output dimension")''','''    strip = edge_width_source * scale if seamless else 0
    if seamless and strip * 2 > min(width, height):
        raise ValueError("edge blend band must fit within half the smaller output dimension")'''),
('''    before = _seam_mean(pixels)
    _blend_axis(pixels, strip, 1)
    _blend_axis(pixels, strip, 0)
    rgb = np.clip(np.rint(pixels), 0, 255).astype(np.uint8)''','''    before = _seam_mean(pixels)
    if seamless:
        _blend_axis(pixels, strip, 1)
        _blend_axis(pixels, strip, 0)
    rgb = np.clip(np.rint(pixels), 0, 255).astype(np.uint8)'''),
('''        "scale": scale, "edge_width_source_pixels": edge_width_source,
        "edge_blend_output_pixels": strip, "sharpen_percent": sharpen_percent,''','''        "scale": scale, "seamless": seamless,
        "edge_width_source_pixels": edge_width_source if seamless else 0,
        "edge_blend_output_pixels": strip, "sharpen_percent": sharpen_percent,'''),
('''    parser.add_argument("--preserve-bright-feather", type=int, default=24)
    args = parser.parse_args()
    print(json.dumps(create(args.source, args.output, args.scale,
                            args.edge_width_source, args.sharpen_percent,
                            args.detail_image, args.preserve_bright_threshold,
                            args.preserve_bright_feather), indent=2))''','''    parser.add_argument("--preserve-bright-feather", type=int, default=24)
    parser.add_argument("--uv-atlas", action="store_true",
                        help="keep opposite borders independent for non-repeating UV atlases")
    args = parser.parse_args()
    print(json.dumps(create(args.source, args.output, args.scale,
                            args.edge_width_source, args.sharpen_percent,
                            args.detail_image, args.preserve_bright_threshold,
                            args.preserve_bright_feather, not args.uv_atlas), indent=2))''')]
for old,new in repls:
 if s.count(old)!=1: raise SystemExit(f'expected one match, found {s.count(old)}: {old[:60]!r}')
 s=s.replace(old,new)
p.write_text(s)
print('patched',p)

"""Exact captured pose only: export original wall bounds for diagnostic replay."""
from pathlib import Path
import json
import struct
from PIL import Image, ImageChops
from scene_batches import batches

root = Path('work/camera')
p = (root / 'reference-scene-0.packet').read_bytes()
sections = {t: p[o:o+n] for t, o, n in
            (struct.unpack_from('<3I', p, 32+i*12) for i in range(5))}
events = {e['blocks'][5][0]: e for e in
          next(batches(root / 'shading-spans.bin'))['events']
          if e['pc'] == 0x03000304}
count = struct.unpack_from('<I', sections[2], 4)[0]
bounds = []
walls = 0
for i in range(count):
    identity = struct.unpack_from('<5I', sections[5], 8+i*20)
    pair = (0, 240)
    if identity[0] == 2:
        left, right = struct.unpack_from('<2H', events[identity[2]]['blocks'][1][1], 0xe2)
        pair = ((left >> 1)*2, ((right >> 1)+1)*2)
        walls += 1
    bounds.append(pair)
assert count <= 128 and walls == 22
(root / 'scene0-wall-bounds.bin').write_bytes(
    struct.pack('<I', count) + b''.join(struct.pack('<2d', *v) for v in bounds))
report = dict(scene=0, surfaces=count, walls=walls,
              scope='Frozen original horizontal bounds; exact-pose diagnostic only, not a motion implementation.')
preview = root / 'wall-bounds-preview-0.ppm'
if preview.exists():
    original = Image.open(root / 'reference-scene-0-native.png').convert('RGB')
    bounded = Image.open(preview).convert('RGB')
    assert original.size == bounded.size == (3840, 2160)
    bounded.save(root / 'wall-bounds-preview.png')
    difference = ImageChops.difference(original, bounded)
    report['changed_pixels'] = sum(pixel != (0, 0, 0) for pixel in difference.get_flattened_data())
    report['changed_bbox'] = difference.getbbox()
    comparison = Image.new('RGB', (1440, 720))
    for i, picture in enumerate((original, bounded)):
        comparison.paste(picture.crop((975, 540, 2190, 1755)).resize((720, 720)), (i*720, 0))
    comparison.save(root / 'wall-bounds-comparison.png')
(root / 'wall-bounds-preview-report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))

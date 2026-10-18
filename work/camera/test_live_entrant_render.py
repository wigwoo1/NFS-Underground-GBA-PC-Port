"""Render exported older-owned entrants against candidate-hidden controls."""
from pathlib import Path
import json, math, os, struct, subprocess, hashlib
from PIL import Image, ImageChops

p = Path(__file__).resolve().parent
results = []
stems = [p / f'entrant-phase-e{epoch}-s{scene}-a{alpha:.9f}' for epoch in (2,3) for scene,alpha in ((27,1/3),(27,2/3),(28,.75))]
for stem in stems:
    clips = bytearray(Path(str(stem)+'.clips').read_bytes())
    magic, serial, begin, end, count = struct.unpack_from('<5I', clips)
    alpha = struct.unpack_from('<d', clips, 20)[0]
    scene = serial
    assert magic == 0x3150434e and scene in (27,28)
    assert len(clips) == 28 + count * 28
    offset = 28 + (count - 1) * 28
    identity = struct.unpack_from('<5I', clips, offset)
    bounds = struct.unpack_from('<4H', clips, offset + 20)
    assert identity[0] == 2 and identity[2] == {27:139937788,28:139937312}[scene]
    hidden = bytearray(clips)
    struct.pack_into('<4H', hidden, offset + 20, 0, 0, 0, 0)
    control = Path(str(stem)+'-hidden.clips')
    control.write_bytes(hidden)
    images = []
    for label, clip in [('shown', Path(str(stem)+'.clips')), ('hidden', control)]:
        prefix = Path(str(stem)+f'-{label}')
        env = os.environ.copy()
        env.update(NF_CAPTURE_CLIPS=str(clip), NF_PREVIEW_FRACTION=str(alpha), NF_PREVIEW_PHASE='2')
        subprocess.run([str(p/'sampled-clip-preview.exe'), str(Path(str(stem)+'.bin')),
                        str(stem)+'-new.bin', str(prefix)], env=env,
                       check=True, capture_output=True)
        with Image.open(str(prefix)+'-2.ppm') as image:
            assert image.size == (3840,2160)
            images.append(image.convert('RGB'))
    diff = ImageChops.difference(*images)
    bbox = diff.getbbox()
    changed = sum(1 for rgb in diff.get_flattened_data() if rgb != (0,0,0))
    l,r,t,b = bounds
    scissor = (math.ceil(300+l*13.5-.5), 2160-math.ceil((160-t)*13.5-.5),
               math.ceil(300+r*13.5-.5), 2160-math.ceil((160-b)*13.5-.5))
    if bbox:
        assert bbox[0] >= scissor[0] and bbox[1] >= scissor[1]
        assert bbox[2] <= scissor[2] and bbox[3] <= scissor[3]
    images[0].save(str(stem)+'-shown.png')
    results.append(dict(fixture=stem.name,image_sha256=hashlib.sha256(images[0].tobytes()).hexdigest(),scene=scene,alpha=alpha,identity=identity,bounds=bounds,
                        changed_pixels=changed,changed_bbox=bbox,scissor=scissor))
for first, reloaded in zip(results[:3],results[3:]):
    assert first['image_sha256'] == reloaded['image_sha256']
assert all(case['changed_pixels'] > 0 for case in results)
report = dict(result='PASS', cases=results, scope='Diagnostic packet render and candidate-hidden control; not live insertion or gameplay timing validation.')
(p/'live-entrant-render-tests.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))




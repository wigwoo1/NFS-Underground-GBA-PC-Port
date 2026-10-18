import json
from pathlib import Path
p=Path('work/camera/prototype-runs')
base=json.loads((p/'d3d-baseline-backdrop-parity-source.json').read_text())
cand=json.loads((p/'d3d-texture-backdrop-parity-source.json').read_text())
assert len(base['frames'])==len(cand['frames'])==5
for a,b in zip(base['frames'],cand['frames']):
 assert a['publication']==b['publication']
 assert a['native_rgb_sha256']==b['native_rgb_sha256'],(a['publication'],a['index'],a['native_rgb_sha256'],b['native_rgb_sha256'])
out={'result':'PASS_SAME_CAPTURE_FIVE_FRAME_TEXTURE_BACKDROP_PARITY','matches':[{'publication':a['publication'],'sha256':a['native_rgb_sha256']} for a in base['frames']],'scope':'Same immutable native-source fixture rendered in separate baseline and texture-candidate sessions; exact 3840x2160 RGB hashes. Component replay only, no gameplay timing or promotion.'}
(p/'d3d-texture-backdrop-same-capture-comparison.json').write_text(json.dumps(out,indent=2));print(out['result'])

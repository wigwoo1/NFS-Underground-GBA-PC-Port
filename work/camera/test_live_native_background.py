from pathlib import Path
import json
from scene_batches import batches
p=Path('work/camera');sources=json.loads((p/'motion-model-snapshots.json').read_text())['scenes'];draws=json.loads((p/'motion-draw-page-tests.json').read_text())['draws'];checks=[]
for scene in batches(p/'motion-original-source-8750-8781.bin'):
 if (scene['begin_refresh'],scene['end_refresh']) not in {(s['begin'],s['end']) for s in sources}:continue
 event=next(e for e in scene['events'] if e['pc'] in (0x030032f0,0x03000304,0x03004770));refresh=scene['end_refresh']+1
 actual=(p/f'motion-actual-scanline-assets/{refresh}-native-background.bin').read_bytes();expected=Path(draws[str(event['id'])]['before_path']).read_bytes()[:0x18000]
 assert actual==expected,(refresh,event['id'],sum(a!=b for a,b in zip(actual,expected)))
 checks.append(dict(refresh=refresh,first_draw=event['id'],exact_bytes=len(actual)))
assert len(checks)==7
r=dict(result='PASS_LIVE_NATIVE_BEFORE_WORLD_BACKGROUNDS',checks=checks,scope='Native persistent scene snapshot before first world draw vs original complete VRAM before that draw. Background composed from ordered fill/copy events; contents not yet classified for GPU use.')
(p/'live-native-background-tests.json').write_text(json.dumps(r,indent=2));print(r)

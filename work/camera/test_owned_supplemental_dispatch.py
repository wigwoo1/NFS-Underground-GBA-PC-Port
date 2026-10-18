from pathlib import Path
import struct,json
from owned_scene_bundle import SceneBundle,chunks
from owned_supplemental_dispatch import calls
p=Path('work/camera');checks=[];count=0
for file in sorted((p/'scene-bundles').glob('*.nsb')):
 bundle=SceneBundle.decode(file.read_bytes());derived=calls(bundle);original=list(chunks(bundle.supplements,'supplements'))
 assert [c.descriptor for c in derived]==[h[3] for h,raw in original]
 assert [c.region for c in derived]==[raw[192:208] for h,raw in original]
 count+=len(derived);checks.append(dict(scene=file.name,calls=len(derived),object_indices=[c.object_index for c in derived],region_ordinals=[c.region_ordinal for c in derived],exact_original_order=True))
assert count==9
r=dict(result='PASS_OWNED_SUPPLEMENTAL_INVOCATIONS',calls=count,checks=checks,scope='Supplement descriptor and clip inherited from callback-complete owned object dispatch/association; all9 call regions/order match original. Assets still captured at original call; global road/model/wall ordering and live publication pending.')
(p/'owned-supplemental-dispatch.json').write_text(json.dumps(r,indent=2));print(r)

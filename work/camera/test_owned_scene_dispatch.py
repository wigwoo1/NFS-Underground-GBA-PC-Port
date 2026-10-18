from pathlib import Path
import json
from collections import Counter
from owned_scene_bundle import SceneBundle
from owned_scene_dispatch import draws
p=Path('work/camera');checks=[];counts=Counter()
for file in sorted((p/'scene-bundles').glob('*.nsb')):
 plan=draws(SceneBundle.decode(file.read_bytes()))
 counts.update(row['dispatch']['kind'] for row in plan)
 checks.append(dict(scene=file.name,draws=len(plan)))
assert len(checks)==7 and counts['model']==7 and counts['supplement']==9,(checks,counts)
r=dict(result='PASS_IMMUTABLE_SCENE_DISPATCH',scenes=checks,kinds=dict(counts),scope='Derived owned draw plan; GPU geometry/pose binding and live publication pending.')
(p/'owned-scene-dispatch.json').write_text(json.dumps(r,indent=2));print(r)

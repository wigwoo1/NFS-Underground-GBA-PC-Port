import json
from pathlib import Path
from owned_complete_road_candidates import road_candidates as baseline
from owned_road_material_resolution_candidate import road_candidates as candidate
from owned_closed_scene_memory import ClosedSceneMemory
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-stall-exact-capture-20261008')
s=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(cp/'scene-inputs'))+')')
exec(compile(s,'fixture_setup','exec'));prepared.close();history.close()
rows=[]
class Missing:
 def __init__(self):self.calls=[]
 def read(self,address,size):self.calls.append((address,size));raise ValueError('Unowned scene read')
for scene in scenes:
 a=ClosedSceneMemory(scene.graph,rom);b=ClosedSceneMemory(scene.graph,rom)
 x=baseline(scene.graph,a);y=candidate(scene.graph,b);assert x==y and a.missing==b.missing
 ma=Missing();mb=Missing();assert baseline(scene.graph,ma)==candidate(scene.graph,mb) and ma.calls==mb.calls
 rows.append(dict(refresh=scene.graph.refresh,candidates=len(x),missing_read_calls=len(ma.calls),exact_records=True,exact_missing_call_sequence=True))
r=dict(result='PASS',rows=rows,scope='Two current captured endpoints; exact dataclass fields and missing-read sequence; no GPU or live pacing proof.')
(cp/'road-material-records.json').write_text(json.dumps(r,indent=2));print(r)

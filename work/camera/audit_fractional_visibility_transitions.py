"""Actual production full-scene callback pixels at varying sky weights."""
import ctypes as C,json,struct,hashlib
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_motion_scene import MotionScene
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_prepared_world_motion import PreparedWorldMotion
from owned_motion_pairs import records
from live_native_batch_candidate import DrawContext
p=Path('work/camera');r=json.loads((p/'prototype-runs/owned-native-1791267744113946700.json').read_text());fa,fb=r['wall_diagnostic_frames'][:2]
a=ClosedGraph.decode(Path(fa['graph']).read_bytes());b=ClosedGraph.decode(Path(fb['graph']).read_bytes());sa=ClosedSupplements.decode(Path(fa['supplements']).read_bytes(),a);sb=ClosedSupplements.decode(Path(fb['supplements']).read_bytes(),b)
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',(p/'road-correction-reciprocal.bin').read_bytes()[:131072]);history=EndpointRoadPlanner(rom,table);roads,_=history.plan(a);pair=PreparedWorldMotion(Path(fa['regenerated']).read_bytes(),Path(fb['regenerated']).read_bytes(),MotionScene(a,sa),MotionScene(b,sb),history,roads,rom)
import owned_wall_visibility_candidate as visibility
original_batch=visibility.batch;visibility_counts=[0]
def checked_batch(calls):
 outputs=original_batch(calls)
 for call,output in zip(calls,outputs):
  reference=visibility.select_wall(*call)
  assert output.visible==reference.visible and output.reason==reference.reason and output.flags==reference.flags
  assert len(output.x)==len(reference.x) and len(output.y)==len(reference.y)
  assert all(abs(a-b)<1e-7 for a,b in zip(output.x+output.y,reference.x+reference.y))
  visibility_counts[0]+=1
 return outputs
visibility.batch=checked_batch
checks=[];transitions=[];previous=None
try:
 for step in range(1,100):
  alpha=step/100;frame,camera,models,bounds,detail=pair.sample(alpha);rows=records(frame)['records'];keys={r['key'] for r in rows};assert len(keys)==len(rows),'Duplicate source identity'
  counts={kind:sum(r['kind']==kind for r in rows) for kind in (1,2,3)}
  checks.append(dict(alpha=alpha,count=len(rows),kinds=counts,detail=detail))
  if previous is not None and keys!=previous[1]:
   transitions.append(dict(older_alpha=previous[0],newer_alpha=alpha,added=[list(k) for k in sorted(keys-previous[1])],removed=[list(k) for k in sorted(previous[1]-keys)],kinds=counts))
  previous=alpha,keys
finally:pair.close();history.close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/fractional-visibility-transitions-20261007');cp.mkdir(exist_ok=True)
(cp/'transitions.json').write_text(json.dumps(dict(source_older=fa['refresh'],source_newer=fb['refresh'],samples=checks,transitions=transitions,visibility_reference_cases=visibility_counts[0],scope='Captured complete scene reconstructed at99fractional camera/pose samples. Static source identity transitions, not independent visibility oracle or visual correctness.'),indent=2));(cp/Path(__file__).name).write_text(Path(__file__).read_text());print(json.dumps(transitions));print('PASS99 bounded source-identity samples; recovered scalar wall visibility cases',visibility_counts[0])

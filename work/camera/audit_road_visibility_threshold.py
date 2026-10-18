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
samples=[]
def inspect(alpha):
 selected,details=pair.roads.sample(alpha)
 return dict(alpha=alpha,portal_regions=[list(x) for x in pair.roads.portal.sample(alpha)],selected=[dict(descriptor=x['descriptor'],depth=x.get('static_depth',0),bounds=x['bounds']) for x in selected],details=list(details))
try:
 lo=.59;hi=.60
 for _ in range(32):
  mid=(lo+hi)/2;row=inspect(mid)
  if len(row['selected'])>=9:hi=mid
  else:lo=mid
 for alpha in [.59,lo,hi,.60]:samples.append(inspect(alpha))
finally:pair.close();history.close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/road-visibility-threshold-20261007');cp.mkdir(exist_ok=True)
(cp/'threshold.json').write_text(json.dumps(dict(samples=samples,bracket=[lo,hi],scope='Actual captured pair road/portal metadata and32bisectionsteps; not independent arithmetic proof or visual correctness.'),indent=2));(cp/Path(__file__).name).write_text(Path(__file__).read_text());print(json.dumps(samples))

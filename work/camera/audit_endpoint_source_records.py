"""Measure exact endpoint approach for default and fractional clipping candidate."""
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

checks=[]
try:
 for endpoint in (0,1):
  exact=pair.sample(endpoint)[0];sample=pair.sample(1e-9 if endpoint==0 else 1-1e-9)[0]
  er=records(exact)['records'];sr=records(sample)['records'];em={x['key']:x for x in er};sm={x['key']:x for x in sr};rows=[]
  for key in em.keys()&sm.keys():
   rows.append(dict(key=key,different_blocks=[i for i,(a,b) in enumerate(zip(em[key]['blocks'],sm[key]['blocks'])) if bytes(a)!=bytes(b)]))
  checks.append(dict(endpoint=endpoint,exact_count=len(er),sample_count=len(sr),missing_keys=list(em.keys()-sm.keys()),added_keys=list(sm.keys()-em.keys()),common=rows))
finally:pair.close();history.close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/endpoint-source-records-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps({'checks':checks,'scope':'Exact static raw topology identities; compares payload blocks without screen matching.'},indent=2));(cp/Path(__file__).name).write_text(Path(__file__).read_text());print(json.dumps(checks))

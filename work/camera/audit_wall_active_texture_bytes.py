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
  er=records(pair.sample(endpoint)[0])['records'];sr=records(pair.sample(1e-9 if endpoint==0 else 1-1e-9)[0])['records'];em={r['key']:r for r in er if r['kind']==2}
  for row in sr:
   if row['kind']!=2 or row['key'] not in em:continue
   e=em[row['key']];shift,height=struct.unpack_from('<2H',e['blocks'][4],36);n=(1<<shift)*height
   tex=bytes(e['blocks'][8]);sample=bytes(row['blocks'][8]);changed=sum(x!=y for x,y in zip(tex[:n],sample[:n]));checks.append(dict(endpoint=endpoint,key=row['key'],active_bytes=n,exact_bytes=len(tex),sample_bytes=len(sample),changed_active_bytes=changed,exact_hash=hashlib.sha256(tex[:n]).hexdigest(),sample_hash=hashlib.sha256(sample[:n]).hexdigest()))
finally:pair.close();history.close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/wall-active-texture-bytes-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps({'checks':checks,'scope':'Compared only actual indexed texture extent declared by endpoint material dimensions; excludes unused packet padding.'},indent=2));(cp/Path(__file__).name).write_text(Path(__file__).read_text());print([(r['endpoint'],r['key'][2][:8],r['active_bytes'],r['changed_active_bytes']) for r in checks])

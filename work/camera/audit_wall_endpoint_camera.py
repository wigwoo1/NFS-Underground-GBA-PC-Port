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

d=C.CDLL(str((p/'owned-sky-queued-targets.dll').resolve()));d.nf_wall_owned_quad.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p];checks=[]
try:
 for endpoint in (0,1):
  exact=pair.sample(endpoint)[0];sample,camera,*_=pair.sample(1e-9 if endpoint==0 else 1-1e-9);em={r['key']:r for r in records(exact)['records'] if r['kind']==2}
  for row in records(sample)['records']:
   if row['kind']!=2 or row['key'] not in em:continue
   e=em[row['key']];src=bytes(e['blocks'][0]);off=bytes(e['blocks'][1]);mat=bytes(e['blocks'][3]);raw=(C.c_double*12)()
   assert d.nf_wall_owned_quad(C.create_string_buffer(src),C.create_string_buffer(off),C.create_string_buffer(mat),raw)==1
   word=lambda o:struct.unpack_from('<i',src,o)[0];half=lambda data,o:struct.unpack_from('<h',data,o)[0]
   x=word(0)+half(off,0);z=word(4)+half(off,2);nx=word(68)+half(off,32);nz=word(72)+half(off,34)
   world=((x,half(src,8)+half(off,8),z),(nx,half(src,12)+half(off,8),nz),(nx,half(src,14)+half(off,10),nz),(x,half(src,10)+half(off,10),z))
   continuous=[sum((point[j]+camera[9+j])*camera[j*3+k] for j in range(3)) for point in world for k in range(3)]
   error=max(abs(v-w) for v,w in zip(raw,continuous))
   checks.append(dict(endpoint=endpoint,key=row['key'],max_camera_space_difference=error,endpoint_quad=list(raw),sampled_quad=continuous))
finally:pair.close();history.close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/wall-endpoint-camera-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps({'checks':checks,'scope':'Recovered original integer-cell camera-space wall quad compared with sampled rigid camera applied to identical world source coordinates; numerical evidence, not cause attribution.'},indent=2));(cp/Path(__file__).name).write_text(Path(__file__).read_text());print([(r['endpoint'],r['key'][2][:8],r['max_camera_space_difference']) for r in checks])

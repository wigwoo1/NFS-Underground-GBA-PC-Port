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

from PIL import Image,ImageChops
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/endpoint-repeatability-20261007');cp.mkdir(exist_ok=True)
d=C.CDLL(str((p/'owned-sky-queued-targets.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t]
rgb=C.create_string_buffer(3840*2160*3);checks=[]
try:
 for endpoint in (0,1):
  frame,*_=pair.sample(endpoint);f=C.create_string_buffer(frame);previous=None
  for repeat in range(3):
   assert d.nf_owned_gpu_draw(f,len(frame))==0;assert d.nf_owned_gpu_read(rgb,len(rgb))==0;pixels=rgb.raw
   bbox=None if previous is None else ImageChops.difference(Image.frombytes('RGB',(3840,2160),pixels),Image.frombytes('RGB',(3840,2160),previous)).getbbox()
   checks.append(dict(endpoint=endpoint,repeat=repeat,hash=hashlib.sha256(pixels).hexdigest(),changed_bbox=bbox));previous=pixels
   Image.frombytes('RGB',(3840,2160),pixels).save(cp/('endpoint-'+str(endpoint)+'-repeat-'+str(repeat)+'.png'))
finally:pair.close();history.close();assert d.nf_owned_gpu_close()
(cp/'tests.json').write_text(json.dumps({'checks':checks,'scope':'Repeated identical endpoint source through default queued GPU; detect persistent renderer state dependence.'},indent=2));(cp/Path(__file__).name).write_text(Path(__file__).read_text());print(json.dumps(checks))

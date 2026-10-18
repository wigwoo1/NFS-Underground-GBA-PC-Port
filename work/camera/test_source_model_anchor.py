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
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/model-anchor-candidate-20261007');cp.mkdir(exist_ok=True)
checks=[]
from owned_source_model_anchor_candidate import SourceModelAnchors
model_anchors=SourceModelAnchors(pair.pair.portal.motion)
plan,_,pa,pb,*_=pair.pair.portal.motion.arguments
rawa=(C.c_int32*12)(*struct.unpack('<12i',plan['camera_older']));rawb=(C.c_int32*12)(*struct.unpack('<12i',plan['camera_newer']))
def rigid_camera(pose):
 x,y,z,w=(getattr(pose.rotation,k) for k in ('x','y','z','w'))
 rows=((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),(2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),(2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)))
 return (C.c_double*12)(*[rows[r][c] for c in range(3) for r in range(3)],-pose.position.x,-pose.position.y,-pose.position.z)
rigida=rigid_camera(pa);rigidb=rigid_camera(pb)

def compare(actual,endpoint):
 diff=ImageChops.difference(Image.frombytes('RGB',(3840,2160),actual),Image.frombytes('RGB',(3840,2160),endpoint))
 channels=diff.split();maximum=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2])
 hist=maximum.histogram();mae=sum(sum(i*n for i,n in enumerate(c.histogram())) for c in channels)/(3840*2160*3)
 return dict(changed_pixels=3840*2160-hist[0],bbox=diff.getbbox(),mean_absolute_channel_error=mae,max_channel_error=max(i for i,n in enumerate(hist) if n))
import math
from sample_owned_motion import Point
motion=pair.pair.portal.motion;plan,d,ca,cb,objects,basis=motion.arguments
maximum=0;vertices=0;checks=0
try:
 for endpoint in (0,1):
  frame=motion.older if endpoint==0 else motion.newer;rows=records(frame)['records'];models=(C.c_double*(12*len(rows)))()
  for original_index,oa,ob in objects:
   key=plan['older']['records'][original_index]['key'];index=next(i for i,row in enumerate(rows) if row['key']==key);points=(Point*4)()
   assert d.nf_rigid_scene_sample(C.byref(ca),C.byref(cb),C.byref(oa),C.byref(ob),endpoint,basis,4,points)==1
   for k,name in enumerate(('x','y','z')):
    models[index*12+9+k]=getattr(points[0],name)
    for col in range(3):models[index*12+col*3+k]=getattr(points[col+1],name)-getattr(points[0],name)
  before=bytes(models);anchored=model_anchors.sample(frame,models,endpoint);assert bytes(models)==before
  for index,row in enumerate(rows):
   if row['kind']!=3:continue
   raw=struct.unpack('<12i',row['blocks'][2]);local=bytes(row['blocks'][4])
   assert len(local)%6==0
   for j in range(0,len(local),6):
    point=struct.unpack_from('<3h',local,j)
    for k in range(3):
     expected=raw[9+k]+sum(point[col]*raw[col*3+k]/16384 for col in range(3))
     actual=anchored[index*12+9+k]+sum(point[col]*anchored[index*12+col*3+k] for col in range(3))
     error=abs(actual-expected);maximum=max(maximum,error);assert error<1e-8;checks+=1
    vertices+=1
 for alpha in (.25,.5,.75):
  frame,_,models=motion.sample(alpha);assert all(math.isfinite(v) for v in model_anchors.sample(frame,models,alpha))
 rejected=0
 for alpha in (-.1,1.1,float('nan')):
  try:model_anchors.sample(frame,models,alpha)
  except ValueError:rejected+=1
  else:raise AssertionError('Invalid fraction accepted')
 try:model_anchors.sample(frame,(C.c_double*1)(),.5)
 except ValueError:rejected+=1
 else:raise AssertionError('Invalid array accepted')
finally:pair.close();history.close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/model-source-anchor-component-20261007');cp.mkdir(exist_ok=True)
result=dict(result='PASS_SOURCE_MODEL_ANCHOR',source_vertices=vertices,coordinate_checks=checks,max_endpoint_camera_vertex_error=maximum,finite_interior_samples=3,negative_cases=rejected,private_input_unchanged=True,scope='Actual paired car source vertices reproduce original raw matrix camera-space outputs at endpoints. GPU visibility/raster and broader source model types still require verification.')
(cp/'tests.json').write_text(json.dumps(result,indent=2));(cp/Path(__file__).name).write_text(Path(__file__).read_text());print(json.dumps(result,indent=2))

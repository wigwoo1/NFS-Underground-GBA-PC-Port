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
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/camera-anchor-candidate-20261007');cp.mkdir(exist_ok=True)
checks=[]
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
d=C.CDLL(str((p/'owned-sky-camera-anchor-candidate.dll').resolve()))
d.nf_source_camera_anchor.argtypes=[C.c_void_p]*6+[C.c_double,C.c_void_p]
d.nf_road_camera_continuous.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p]
checks=0;maximum_endpoint_error=0;maximum_residual=0
try:
 for endpoint in (0,1):
  frame=pair.sample(endpoint)[0]
  for row in records(frame)['records']:
   if row['kind']!=2:continue
   src=bytes(row['blocks'][0]);off=bytes(row['blocks'][1]);word=lambda o:struct.unpack_from('<i',src,o)[0];half=lambda data,o:struct.unpack_from('<h',data,o)[0]
   x=word(0)+half(off,0);z=word(4)+half(off,2);nx=word(68)+half(off,32);nz=word(72)+half(off,34)
   points=((x,half(src,8)+half(off,8),z),(nx,half(src,12)+half(off,8),nz),(nx,half(src,14)+half(off,10),nz),(x,half(src,10)+half(off,10),z))
   for point in points:
    pv=(C.c_double*3)(*point)
    for alpha in (0,.25,.5,.75,1):
     rs=rigida if alpha==0 else rigidb if alpha==1 else pair.pair.portal.motion.sample(alpha)[1]
     out=(C.c_double*3)();assert d.nf_source_camera_anchor(pv,rawa,rawb,rigida,rigidb,rs,alpha,out)==0
     assert all(__import__('math').isfinite(v) for v in out)
     uncorrected=[sum((point[j]+rs[9+j])*rs[j*3+k] for j in range(3)) for k in range(3)]
     maximum_residual=max(maximum_residual,max(abs(v-w) for v,w in zip(out,uncorrected)))
     if alpha in (0,1):
      expected=(C.c_double*3)();assert d.nf_road_camera_continuous(pv,rawa if alpha==0 else rawb,expected)==1
      error=max(abs(v-w) for v,w in zip(out,expected));maximum_endpoint_error=max(maximum_endpoint_error,error);assert error<=1e-9
     checks+=1
 sentinel=(C.c_double*3)(123,123,123)
 for bad in (-.1,1.1,float('nan')):
  assert d.nf_source_camera_anchor(pv,rawa,rawb,rigida,rigidb,rigida,bad,sentinel)==37 and list(sentinel)==[123]*3
finally:pair.close();history.close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/camera-anchor-component-20261007');cp.mkdir(exist_ok=True)
result=dict(result='PASS_SOURCE_SPACE_CAMERA_ANCHOR',checks=checks,max_endpoint_camera_error=maximum_endpoint_error,max_tested_correction=maximum_residual,invalid_alpha_cases=3,scope='Actual captured world wall vertices, original bilinear integer-cell camera endpoints reproduced numerically, finite quarter-step rigid samples. Candidate full-scene motion/policy still needs broader and live verification; no screen polygon interpolation.')
(cp/'tests.json').write_text(json.dumps(result,indent=2));(cp/Path(__file__).name).write_text(Path(__file__).read_text());print(json.dumps(result,indent=2))

"""Measure exact endpoint approach for default and fractional clipping candidate."""
import ctypes as C,json,struct,hashlib
from pathlib import Path
from PIL import Image,ImageChops
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_motion_scene import MotionScene
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_prepared_world_motion import PreparedWorldMotion
from owned_motion_pairs import records
from live_native_batch_candidate import DrawContext
def rigid_camera(pose):
 x,y,z,w=(getattr(pose.rotation,k) for k in ('x','y','z','w'))
 rows=((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),(2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),(2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)))
 return (C.c_double*12)(*[rows[r][c] for c in range(3) for r in range(3)],-pose.position.x,-pose.position.y,-pose.position.z)
def compare(actual,endpoint):
 diff=ImageChops.difference(Image.frombytes('RGB',(3840,2160),actual),Image.frombytes('RGB',(3840,2160),endpoint))
 channels=diff.split();maximum=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2])
 hist=maximum.histogram();mae=sum(sum(i*n for i,n in enumerate(c.histogram())) for c in channels)/(3840*2160*3)
 return dict(changed_pixels=3840*2160-hist[0],bbox=diff.getbbox(),mean_absolute_channel_error=mae,max_channel_error=max(i for i,n in enumerate(hist) if n))
p=Path('work/camera');report=json.loads((p/'prototype-runs/owned-native-1791267744113946700.json').read_text());frames=report['wall_diagnostic_frames']
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',(p/'road-correction-reciprocal.bin').read_bytes()[:131072])
from owned_sampled_graph_wall_visibility import wall_metadata
from owned_motion_wall_regions import wall_region_candidates
from owned_continuous_wall_visibility import sampled_edge
root=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/wall-anchor-visibility-agreement-20261007');root.mkdir(exist_ok=True)
d=C.CDLL(str((p/'owned-sky-camera-anchor-candidate.dll').resolve()));d.nf_source_camera_anchor.argtypes=[C.c_void_p]*6+[C.c_double,C.c_void_p]
history=EndpointRoadPlanner(rom,table);initial=ClosedGraph.decode(Path(frames[0]['graph']).read_bytes());roads,_=history.plan(initial);results=[]
try:
 for index,(fa,fb) in enumerate(zip(frames,frames[1:])):
  a=ClosedGraph.decode(Path(fa['graph']).read_bytes());b=ClosedGraph.decode(Path(fb['graph']).read_bytes());sa=ClosedSupplements.decode(Path(fa['supplements']).read_bytes(),a);sb=ClosedSupplements.decode(Path(fb['supplements']).read_bytes(),b)
  pair=PreparedWorldMotion(Path(fa['regenerated']).read_bytes(),Path(fb['regenerated']).read_bytes(),MotionScene(a,sa),MotionScene(b,sb),history,roads,rom)
  next_history=pair.take_next_history();next_roads=pair.endpoint_roads[1];portal=pair.pair.portal
  plan,_,pa,pb,*_=portal.motion.arguments;rawa=(C.c_int32*12)(*struct.unpack('<12i',plan['camera_older']));rawb=(C.c_int32*12)(*struct.unpack('<12i',plan['camera_newer']));rigida=rigid_camera(pa);rigidb=rigid_camera(pb)
  maximum=0;checks=0
  try:
   rings,_,_=wall_metadata(portal,portal.older)
   for alpha in (.000000001,.25,.5,.75,.999999999):
    camera=portal.motion.sample(alpha)[1]
    for candidate in wall_region_candidates(portal,alpha):
     _,ring,offsets=rings[candidate.descriptor];edge=sampled_edge(candidate.wall,ring,portal.older.context[256:304],portal.newer.context[256:304],tuple(camera),portal.endpoints,alpha,offsets)
     if edge is None:continue
     n=len(ring)//68
     for slot,vertex in enumerate((candidate.edge,(candidate.edge+1)%n)):
      x,z=struct.unpack_from('<2i',ring,vertex*68)
      if struct.unpack_from('<H',ring,vertex*68+42)[0]!=65535:
       dx,dz=struct.unpack_from('<2h',offsets,vertex*32);x+=dx;z+=dz
      point=(C.c_double*3)(x,0,z);out=(C.c_double*3)()
      assert d.nf_source_camera_anchor(point,rawa,rawb,rigida,rigidb,camera,alpha,out)==0
      maximum=max(maximum,abs(out[0]-edge[slot]),abs(out[2]-edge[2+slot]));checks+=2
  finally:pair.close()
  history.close();history=next_history;roads=next_roads
  results.append(dict(pair=index,checks=checks,max_horizontal_depth_error=maximum))
finally:
 history.close()
 if 'next_history' in locals() and next_history is not history:next_history.close()
result=dict(result='MEASURED_SOURCE_COORDINATE_AGREEMENT',pairs=results,total_coordinate_checks=sum(x['checks'] for x in results),max_error=max(x['max_horizontal_depth_error'] for x in results),scope='Wall candidate horizontal/depth source transforms across 15 retained pairs and five fractions. Excludes heights, portal clipping, model visibility, live rendering and physical display.')
(root/'tests.json').write_text(json.dumps(result,indent=2));(root/Path(__file__).name).write_text(Path(__file__).read_text());print(json.dumps(result,indent=2))


import json,struct,ctypes as C
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates
from owned_sampled_road_camera import sampled_road_camera,sampled_road_far_depths
from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import pose_camera
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();d=C.CDLL(str(Path('work/camera/visibility-probe-wide.dll').resolve()));d.nf_road_camera_continuous.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p];checks=[]
for fa,fb in zip(r['wall_diagnostic_frames'],r['wall_diagnostic_frames'][1:]):
 a=ClosedGraph.decode(Path(fa['graph']).read_bytes());b=ClosedGraph.decode(Path(fb['graph']).read_bytes());motion=PreparedMotionPair(Path(fa['regenerated']).read_bytes(),Path(fb['regenerated']).read_bytes());poses=tuple(pose_camera(p) for p in motion.arguments[2:4]);ma=struct.unpack_from('<12i',a.graph.context,256);mb=struct.unpack_from('<12i',b.graph.context,256);world=[]
 for x in road_candidates(a,ClosedSceneMemory(a,rom)):
  for i in range(len(x.vertices)//68):
   v=x.vertices[i*68:];o=x.offsets[i*32:];world.extend((struct.unpack_from('<i',v)[0]+struct.unpack_from('<h',o)[0],struct.unpack_from('<h',v,56)[0]+struct.unpack_from('<h',o,6)[0]+struct.unpack_from('<h',x.face,6)[0],struct.unpack_from('<i',v,4)[0]+struct.unpack_from('<h',o,2)[0]))
 for alpha,matrix in ((0,ma),(1,mb)):
  values=sampled_road_camera(world,ma,mb,poses,poses[int(alpha)],alpha);far=sampled_road_far_depths(world,ma,mb,poses,poses[int(alpha)],alpha);assert len(far)==len(world)//3;cm=(C.c_int32*12)(*matrix)
  for i in range(0,len(world),3):
   point=(C.c_double*3)(*world[i:i+3]);out=(C.c_double*3)();assert d.nf_road_camera_continuous(point,cm,out) and values[i:i+3]==tuple(out)
 for alpha in (.25,.5,.75):
  _,camera,_=motion.sample(alpha);sampled_road_camera(world,ma,mb,poses,camera,alpha);sampled_road_far_depths(world,ma,mb,poses,camera,alpha)
 checks.append(dict(older=a.refresh,newer=b.refresh,points=len(world)//3))
out=dict(result='PASS_SAMPLED_RAW_ROAD_CAMERA',checks=checks,scope='Endpoint camera-space parity and finite interior corrected rigid samples; full sampled ring/submission integration pending')
Path('work/camera/sampled-road-camera-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],len(checks))

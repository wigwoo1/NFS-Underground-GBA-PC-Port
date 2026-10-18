import ctypes as C,json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_sampled_road_sequence import SampledRoadSequence
from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import PortalMotionPair
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);history=EndpointRoadPlanner(rom,table);checks=[];gpu=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));gpu.nf_owned_gpu_draw_surface_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint];gpu.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3);gpu_frames=0
try:
 first=ClosedGraph.decode(Path(r['wall_diagnostic_frames'][0]['graph']).read_bytes());history.plan(first)
 for fa,fb in zip(r['wall_diagnostic_frames'],r['wall_diagnostic_frames'][1:]):
  a=ClosedGraph.decode(Path(fa['graph']).read_bytes());b=ClosedGraph.decode(Path(fb['graph']).read_bytes());motion=PreparedMotionPair(Path(fa['regenerated']).read_bytes(),Path(fb['regenerated']).read_bytes());portal=PortalMotionPair(a.graph,b.graph,table,motion);seq=SampledRoadSequence(a,b,portal,history);samples=[]
  for alpha in (.25,.5,.75):
   selected,details=seq.sample(alpha);again,_=seq.sample(alpha);assert [x['record'] for x in selected]==[x['record'] for x in again] and history.refresh==a.refresh
   if selected:
    baseframe=Path(fa['regenerated']).read_bytes();h=list(struct.unpack_from('<6I2Q',baseframe));tail=baseframe[40+h[2]:];geometry=b''.join(x['record'] for x in selected);h[2]=len(geometry);frame=struct.pack('<6I2Q',*h)+geometry+tail
    _,camera,_=motion.sample(alpha);bounds=(C.c_double*(len(selected)*4))(*(v for x in selected for v in x['bounds']));models=(C.c_double*(len(selected)*12))()
    assert gpu.nf_owned_gpu_draw_surface_clips(frame,len(frame),camera,models,bounds,len(selected))==0 and gpu.nf_owned_gpu_read(rgb,len(rgb))==0;gpu_frames+=1
   samples.append(dict(alpha=alpha,roads=len(selected),details=details))
  expected=history.fork()
  try:er,ed=expected.plan(b)
  finally:expected.close()
  actual,ad=history.plan(b);assert [x['record'] for x in actual]==[x['record'] for x in er] and ad==ed
  checks.append(dict(older=a.refresh,newer=b.refresh,samples=samples))
finally:history.close();assert gpu.nf_owned_gpu_close()
out=dict(result='PASS_SAMPLED_ROAD_SEQUENCE',checks=checks,intermediate_4k_gpu_frames=gpu_frames,scope='Complete primary sampled source sequence/portal clips/emission counts/isolated history; 45 road-only GPU draw/read samples; fractional submission oracle and fullscene verification pending')
Path('work/camera/sampled-road-sequence-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],len(checks))

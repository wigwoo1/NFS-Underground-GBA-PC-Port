import json,struct,ctypes as C
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_graph_packet import GraphPacket
from owned_closed_supplements import ClosedSupplements
from owned_model_builder_inputs import OwnedModelBuilders
from owned_model_sources import OwnedModelSources
from owned_motion_scene import MotionScene
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_motion_pairs import records
folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);frames=[];scenes=[]
for name in ('older','newer'):
 raw_supp=(folder/(name+'.supplements.bin')).read_bytes();refresh=struct.unpack_from('<I',raw_supp,8)[0];epoch=struct.unpack_from('<Q',raw_supp,24)[0]
 graph=ClosedGraph(epoch,refresh,GraphPacket.decode((folder/(name+'.graph.bin')).read_bytes()),*((folder/(name+'.'+section+'.bin')).read_bytes() for section in ('objects','callbacks','associations')))
 scenes.append(MotionScene(graph,ClosedSupplements.decode((folder/(name+'.supplements.bin')).read_bytes(),graph,rom),OwnedModelBuilders((folder/(name+'.builders.bin')).read_bytes()),OwnedModelSources.decode((folder/(name+'.current-sources.bin')).read_bytes(),graph)))
 frames.append((folder/(name+'.frame.bin')).read_bytes())
history=EndpointRoadPlanner(rom,table);roads,_=history.plan(scenes[0].graph);prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)

import hashlib
from owned_motion_pairs import records
compact_gpu=C.CDLL(str(Path('work/camera/owned-world-gpu-compact-candidate.dll').resolve()));legacy_gpu=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()))
for gpu in (compact_gpu,legacy_gpu):
 gpu.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];gpu.nf_owned_gpu_draw_scene_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint];gpu.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t]
def compact(frame):
 h=list(struct.unpack_from('<6I2Q',frame));rows=records(frame)['records'];out=[];walls=0;saved=0
 for row in rows:
  blocks=list(row['blocks'])
  if row['kind']==2:
   shift,height=struct.unpack_from('<HH',blocks[4],36);assert shift<=10 and 0<height<=1024
   needed=(1<<shift)*height;assert needed<=len(blocks[8]);saved+=len(blocks[8])-needed;blocks[8]=blocks[8][:needed];walls+=1
  out.append(struct.pack('<4I',0x3147534e,row['kind'],row['context'],12)+b''.join(struct.pack('<I',len(x))+bytes(x) for x in blocks))
 geometry=b''.join(out);tail=frame[40+h[2]:];h[2]=len(geometry)
 return struct.pack('<6I2Q',*h)+geometry+tail,walls,saved
checks=[]
try:
 for alpha in (0.,.25,.5,.75,1.):
  frame,camera,models,bounds,detail=prepared.sample(alpha);small,walls,saved=compact(frame);digests=[]
  for gpu,packet in ((legacy_gpu,frame),(compact_gpu,small)):
   rgb=C.create_string_buffer(3840*2160*3)
   try:
    status=gpu.nf_owned_gpu_draw(packet,len(packet)) if alpha in (0,1) else gpu.nf_owned_gpu_draw_scene_clips(packet,len(packet),camera,models,bounds,detail['geometry_records'])
    assert status==0,(alpha,status);assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0;digests.append(hashlib.sha256(rgb.raw).hexdigest())
   finally:assert gpu.nf_owned_gpu_close()==1
  assert digests[0]==digests[1],(alpha,digests)
  checks.append(dict(alpha=alpha,walls=walls,saved_bytes=saved,legacy_bytes=len(frame),compact_bytes=len(small),pixel_sha256=digests[0]))
 result=dict(result='PASS_EXACT_4K_PIXELS',checks=checks,scope='Five captured full scenes legacy GPU vs isolated compact GPU; source endpoints retained; excludes live gameplay timing')
 Path('work/camera/compact-wall-gpu-pixel-tests.json').write_text(json.dumps(result,indent=2));print(result)
finally:prepared.close();history.close()

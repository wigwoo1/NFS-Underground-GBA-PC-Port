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
samples=[prepared.sample(i/20) for i in range(21)]
all_hashes=[]
try:
 for name in ('owned-world-gpu.dll','owned-world-gpu-reciprocal-candidate.dll'):
  gpu=C.CDLL(str(Path('work/camera',name).resolve()));gpu.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];gpu.nf_owned_gpu_draw_scene_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint];gpu.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t]
  rgb=C.create_string_buffer(3840*2160*3);hashes=[]
  try:
   for i,(frame,camera,models,bounds,detail) in enumerate(samples):
    result=gpu.nf_owned_gpu_draw(frame,len(frame)) if i in (0,20) else gpu.nf_owned_gpu_draw_scene_clips(frame,len(frame),camera,models,bounds,detail['geometry_records'])
    assert result==0;assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0;hashes.append(hashlib.sha256(rgb.raw).hexdigest())
  finally:assert gpu.nf_owned_gpu_close()==1
  all_hashes.append(hashes)
 assert all_hashes[0]==all_hashes[1]
 out=dict(result='PASS_PIXEL_PARITY',poses=21,native4k_readbacks=42,hashes=all_hashes[0],scope='complete captured scene candidate versus current renderer; excludes live timing')
 Path('work/camera/gpu-reciprocal-pixel-parity.json').write_text(json.dumps(out,indent=2));print(out['result'])
finally:prepared.close();history.close()

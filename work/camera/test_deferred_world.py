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
folder=Path('G:\\EXTRA DATA DRIVE\\Desktop\\Games\\Codex\\NFSUG-Native-PC-Port\\work\\camera\\prototype-runs\\fullscene-failure-1791307302908465800')
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);frames=[];scenes=[]
for name in ('older','newer'):
 raw_supp=(folder/(name+'.supplements.bin')).read_bytes();refresh=struct.unpack_from('<I',raw_supp,8)[0];epoch=struct.unpack_from('<Q',raw_supp,24)[0]
 graph=ClosedGraph(epoch,refresh,GraphPacket.decode((folder/(name+'.graph.bin')).read_bytes()),*((folder/(name+'.'+section+'.bin')).read_bytes() for section in ('objects','callbacks','associations')))
 scenes.append(MotionScene(graph,ClosedSupplements.decode((folder/(name+'.supplements.bin')).read_bytes(),graph,rom),OwnedModelBuilders((folder/(name+'.builders.bin')).read_bytes()),OwnedModelSources.decode((folder/(name+'.current-sources.bin')).read_bytes(),graph)))
 frames.append((folder/(name+'.frame.bin')).read_bytes())
history=EndpointRoadPlanner(rom,table);roads,_=history.plan(scenes[0].graph);prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)

gpu=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));gpu.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];gpu.nf_owned_gpu_draw_scene_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint];gpu.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3)
try:
 samples=[prepared.sample(i/100) for i in range(101)];assert samples[0][0]==frames[0] and samples[-1][0]==frames[-1]
 for i,(frame,camera,models,bounds,detail) in enumerate(samples):
  result=gpu.nf_owned_gpu_draw(frame,len(frame)) if i in (0,100) else gpu.nf_owned_gpu_draw_scene_clips(frame,len(frame),camera,models,bounds,detail['geometry_records'])
  assert result==0,(i,result);assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0
 result=dict(result='PASS',samples=101,native4k_readbacks=101,exact_endpoints=2,projection_policy='constant integer-cell values preserved exactly',scope='captured publication boundary replay; excludes live timing')
 Path('work/camera/deferred-world-tests.json').write_text(json.dumps(result,indent=2));print(result)
finally:
 assert gpu.nf_owned_gpu_close()==1;prepared.close();history.close()

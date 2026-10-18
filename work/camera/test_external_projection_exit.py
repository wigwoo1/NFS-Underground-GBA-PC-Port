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
folder=Path('G:\\EXTRA DATA DRIVE\\Desktop\\Games\\Codex\\NFSUG-Native-PC-Port\\work\\camera\\prototype-runs\\fullscene-failure-1791305478926527600')
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
 pair=prepared.pair._scenery_record_pairs[0]
 for i,(frame,camera,models,bounds,detail) in enumerate(samples):
  texture=pair.newer_blocks[10] if i==100 else pair.older_blocks[10]
  assert any(bytes(row['blocks'][1])==pair.older_blocks[1] and bytes(row['blocks'][10])==texture for row in records(frame)['records'] if row['kind']==3),(i,'material state')
  result=gpu.nf_owned_gpu_draw(frame,len(frame)) if i in (0,100) else gpu.nf_owned_gpu_draw_scene_clips(frame,len(frame),camera,models,bounds,detail['geometry_records'])
  assert result==0,(i,result);assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0
 assert len({prepared.pair._scenery_motion.matrix(0,i/100) for i in range(101)})==101
 visit=prepared.pair._external_visits[1];assert hasattr(visit,'projection_vertices')
 gpu.nfs_model_project.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_int,C.c_int,C.c_void_p,C.c_void_p]
 table_buffer=(C.c_uint32*len(table))(*table);source_pair=prepared.pair._scenery_record_pairs[1]
 for endpoint,blocks in enumerate((source_pair.older_blocks,source_pair.newer_blocks)):
  count=len(blocks[4])//6;projected=C.create_string_buffer(count*4);scale=struct.unpack_from('<I',blocks[0],64)[0];cx,cy=struct.unpack_from('<2h',blocks[3],8)
  assert gpu.nfs_model_project(blocks[2],blocks[4],count,scale,cx,cy,table_buffer,projected)==(1 if endpoint==0 else 0)
 assert len({prepared.pair._scenery_motion.matrix(1,i/100) for i in range(101)})==101
 for i in range(101):
  sampled=visit.sample(i/100,prepared.pair.portal.sample(i/100));assert (sampled is not None)==all(0<=visit.motion.matrix(i/100)[11]+x*visit.motion.matrix(i/100)[2]+y*visit.motion.matrix(i/100)[5]+z*visit.motion.matrix(i/100)[8]<=0x6000 for x,y,z in visit.projection_vertices)
 result=dict(result='PASS',samples=101,native4k_readbacks=101,exact_endpoints=2,distinct_player_poses=101,material_policy='older for alpha<1; exact newer at alpha=1',scope='captured publication boundary replay; excludes live timing')
 Path('work/camera/external-projection-exit-tests.json').write_text(json.dumps(result,indent=2));print(result)
finally:
 assert gpu.nf_owned_gpu_close()==1;prepared.close();history.close()

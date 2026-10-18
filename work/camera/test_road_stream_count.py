import ctypes as C,json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates
from owned_endpoint_road_selection import Reader
from owned_sampled_road_camera import sampled_road_camera,_signed,sampled_road_far_depths
from owned_road_stream_count import surface_stream_count
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=(C.c_uint32*32768).from_buffer_copy(Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);d=C.CDLL(str(Path('work/camera/visibility-probe-wide.dll').resolve()));d.nfs_visibility_region_reconstruct.argtypes=[C.c_void_p,C.c_void_p,Reader,C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t];checks=[]
for f in r['wall_diagnostic_frames']:
 c=ClosedGraph.decode(Path(f['graph']).read_bytes());m=ClosedSceneMemory(c,rom);matrix=struct.unpack_from('<12i',c.graph.context,256);near=struct.unpack_from('<i',c.graph.context,320)[0];seen=set();tested=0
 @Reader
 def read(ctx,address,out,size):
  try:C.memmove(out,m.read(address,size),size);return 1
  except ValueError:return 0
 for x in road_candidates(c,m):
  if x.descriptor in seen:continue
  seen.add(x.descriptor);world=[]
  for i in range(len(x.vertices)//68):
   v=x.vertices[i*68:];o=x.offsets[i*32:];world.extend((struct.unpack_from('<i',v)[0]+struct.unpack_from('<h',o)[0],struct.unpack_from('<h',v,56)[0]+struct.unpack_from('<h',o,6)[0]+struct.unpack_from('<h',x.face,6)[0],struct.unpack_from('<i',v,4)[0]+struct.unpack_from('<h',o,2)[0]))
  camera=sampled_road_camera(world,matrix,matrix,((0,)*12,(0,)*12),(0,)*12,0);hidden=bool(struct.unpack_from('<H',x.face,8)[0]&0x40);far=[_signed((world[i]+matrix[9])*matrix[2]+(world[i+2]+matrix[11])*matrix[8],32)>>14 for i in range(0,len(world),3)];owned_far=sampled_road_far_depths(world,matrix,matrix,((0,)*12,(0,)*12),(0,)*12,0);assert tuple(far)==owned_far
  assert sampled_road_far_depths(world,matrix,matrix,((0,)*12,(0,)*12),(0,)*12,.5)==owned_far
  predicted=surface_stream_count(camera,near,face_hidden=hidden,far_depths=owned_far)
  state=C.create_string_buffer(c.graph.context[:256],256);edges=C.create_string_buffer(32*52);stream=C.create_string_buffer(64*24);record=struct.pack('<8H',x.descriptor,0,239,0,159,0,0,65535);status=d.nfs_visibility_region_reconstruct(state,record,read,None,table,edges,len(edges),stream,len(stream));assert status>=0
  actual=None if status==0 else struct.unpack_from('<H',state.raw,242)[0];assert predicted==actual,(c.refresh,x.descriptor,predicted,actual);tested+=1
 checks.append(dict(refresh=c.refresh,descriptors=tested))
out=dict(result='PASS_RECOVERED_ROAD_STREAM_COUNT',checks=checks,scope='Complete owned graph endpoint emission count vs original native region reconstruction, no retained invocation count inputs')
Path('work/camera/road-stream-count-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],sum(x['descriptors'] for x in checks))

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


class Context(C.Structure):_fields_=[('epoch',C.c_uint64),('timed',C.c_uint32),('result',C.c_int32),('elapsed_ns',C.c_uint64)]
gpu=C.CDLL(str(Path('work/camera/owned-world-gpu-native-callback.dll').resolve()));handoff=C.CDLL(str(Path('work/camera/owned-frame-handoff.dll').resolve()));P=C.c_void_p;U=C.c_uint64;Callback=C.CFUNCTYPE(C.c_int,P)
gpu.nf_owned_gpu_draw.argtypes=[P,C.c_size_t];native_callback=C.cast(gpu.nf_owned_gpu_present_callback,Callback)
handoff.nf_owned_handoff_create.argtypes=[U];handoff.nf_owned_handoff_create.restype=P;handoff.nf_owned_handoff_pause.argtypes=[P,C.c_uint];handoff.nf_owned_handoff_destroy.argtypes=[P];handoff.nf_owned_handoff_commit_token.argtypes=[P,U,U,Callback,P];handoff.nf_owned_handoff_commit_token_timed.argtypes=[P,U,U,Callback,P,P]
frame=prepared.sample(0)[0];epoch=struct.unpack_from('<Q',frame,24)[0];q=handoff.nf_owned_handoff_create(epoch);assert q;checks=[]
try:
 assert gpu.nf_owned_gpu_window(0)==0;assert gpu.nf_owned_gpu_draw(frame,len(frame))==0
 for timed in (0,1):
  context=Context(epoch,timed,-999,0);ticks=(U*6)()
  assert handoff.nf_owned_handoff_commit_token_timed(q,epoch,1,native_callback,C.byref(context),ticks)==1
  assert context.result==0 and (context.elapsed_ns>0 if timed else context.elapsed_ns==0);checks.append('native timed='+str(timed))
 context=Context(epoch,1,-999,123)
 assert handoff.nf_owned_handoff_pause(q,1);assert handoff.nf_owned_handoff_pause(q,0)
 assert handoff.nf_owned_handoff_commit_token(q,epoch,1,native_callback,C.byref(context))==0;assert context.result==-999 and context.elapsed_ns==123;checks.append('retired token never invokes callback')
 context.epoch=epoch+1
 assert handoff.nf_owned_handoff_commit_token(q,epoch,3,native_callback,C.byref(context))==-1;assert context.result==32;checks.append('native epoch mismatch propagates')
 out=dict(result='PASS_NATIVE_PRESENT_CALLBACK',checks=checks,context_size=C.sizeof(Context),scope='actual GPU context and native handoff callback ABI/lifecycle; not live60fpsproof')
 Path('work/camera/native-present-callback-tests.json').write_text(json.dumps(out,indent=2));print(out)
finally:handoff.nf_owned_handoff_destroy(q);assert gpu.nf_owned_gpu_close()==1;prepared.close();history.close()

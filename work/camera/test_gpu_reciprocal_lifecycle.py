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


import os,tempfile
root=Path.cwd();gpu=C.CDLL(str(root/'work/camera/owned-world-gpu-reciprocal-candidate.dll'));gpu.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t]
frame=prepared.sample(0)[0];checks=[]
try:
 with tempfile.TemporaryDirectory(prefix='nfs-reciprocal-') as directory:
  empty=Path(directory);table=empty/'work/camera/road-correction-reciprocal.bin';table.parent.mkdir(parents=True)
  os.chdir(empty);assert gpu.nf_owned_gpu_draw(frame,len(frame))==19;checks.append('missing fails')
  table.write_bytes(b'partial');assert gpu.nf_owned_gpu_draw(frame,len(frame))==19;checks.append('truncated fails and retry remains open')
  os.chdir(root);assert gpu.nf_owned_gpu_draw(frame,len(frame))==0;checks.append('valid retry succeeds')
  os.chdir(empty);assert gpu.nf_owned_gpu_draw(frame,len(frame))==0;checks.append('warm session owns table')
  assert gpu.nf_owned_gpu_close()==1
  assert gpu.nf_owned_gpu_draw(frame,len(frame))==19;checks.append('close resets loaded state')
  os.chdir(root);assert gpu.nf_owned_gpu_draw(frame,len(frame))==0;checks.append('reopen reload succeeds')
  assert gpu.nf_owned_gpu_close()==1
 out=dict(result='PASS_SESSION_LOAD_RECOVERY',checks=checks,scope='actual candidate DLL and temporary missing/truncated files; protected project table untouched')
 Path('work/camera/gpu-reciprocal-lifecycle-tests.json').write_text(json.dumps(out,indent=2));print(out)
finally:
 os.chdir(root);assert gpu.nf_owned_gpu_close()==1;prepared.close();history.close()

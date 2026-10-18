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



import time,statistics
samples=[prepared.sample(i/20) for i in range(21)];rows=[]
try:
 for trial in range(6):
  names=('owned-world-gpu.dll','owned-world-gpu-reciprocal-candidate.dll')
  for name in (names if trial%2==0 else names[::-1]):
   gpu=C.CDLL(str(Path('work/camera',name).resolve()));gpu.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];gpu.nf_owned_gpu_draw_scene_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint]
   times=[]
   try:
    for repeat in range(3):
     begin=time.perf_counter_ns()
     for i,(frame,camera,models,bounds,detail) in enumerate(samples):
      result=gpu.nf_owned_gpu_draw(frame,len(frame)) if i in (0,20) else gpu.nf_owned_gpu_draw_scene_clips(frame,len(frame),camera,models,bounds,detail['geometry_records'])
      assert result==0
     times.append((time.perf_counter_ns()-begin)/1e6)
   finally:assert gpu.nf_owned_gpu_close()==1
   rows.append(dict(trial=trial,renderer=name,cold_ms=times[0],warm_ms=times[1:]))
 out=dict(result='PASS_NATIVE_DRAWS_REOPEN',rows=rows,warm_median_ms={n:statistics.median(t for r in rows if r['renderer']==n for t in r['warm_ms']) for n in names},scope='Interleaved complete21pose native draw submission; no GPU completion or live cadence proof')
 Path('work/camera/gpu-reciprocal-benchmark.json').write_text(json.dumps(out,indent=2));print(out['warm_median_ms'])
finally:prepared.close();history.close()

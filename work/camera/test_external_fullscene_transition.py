import json,struct,sys
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_model_builder_inputs import OwnedModelBuilders
from owned_model_sources import OwnedModelSources
from owned_motion_scene import MotionScene
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_motion_pairs import records
r=json.loads(Path(sys.argv[1]).read_text());start=int(sys.argv[2]) if len(sys.argv)>2 else 1;captures=r['model_scene_captures'][start:start+2]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);scenes=[];frames=[]
for c in captures:
 closed=ClosedGraph.decode(Path(c['graph']).read_bytes());scenes.append(MotionScene(closed,ClosedSupplements.decode(Path(c['supplements']).read_bytes(),closed,rom),OwnedModelBuilders(Path(c['builders']).read_bytes()),OwnedModelSources.decode(Path(c['current-sources']).read_bytes(),closed)));frames.append(Path(c['frame']).read_bytes())
history=EndpointRoadPlanner(rom,table);roads,_=history.plan(scenes[0].graph);prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
try:
 samples=[prepared.sample(i/100) for i in range(101)]
 if '--gpu' in sys.argv or '--timing-gpu' in sys.argv:
  import ctypes as C,time,statistics
  gpu=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));gpu.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];gpu.nf_owned_gpu_draw_scene_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint];gpu.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3)
  timings=[];gpu.nf_owned_gpu_timer_read.argtypes=[C.POINTER(C.c_uint64)]
  try:
   # Initialize the context before timestamp queries; finish excludes warm-up work.
   assert gpu.nf_owned_gpu_draw(samples[0][0],len(samples[0][0]))==0
   assert gpu.nf_owned_gpu_finish()==0
   for i,(frame,camera,models,bounds,detail) in enumerate(samples):
    if '--timing-gpu' in sys.argv:assert gpu.nf_owned_gpu_timer_begin()==0
    begin=time.perf_counter_ns()
    result=gpu.nf_owned_gpu_draw(frame,len(frame)) if i in (0,100) else gpu.nf_owned_gpu_draw_scene_clips(frame,len(frame),camera,models,bounds,detail['geometry_records'])
    draw_ns=time.perf_counter_ns()-begin
    assert result==0,(i,result)
    if '--timing-gpu' in sys.argv:
     assert gpu.nf_owned_gpu_timer_end()==0
     wait_begin=time.perf_counter_ns();assert gpu.nf_owned_gpu_finish()==0
     wait_ns=time.perf_counter_ns()-wait_begin;elapsed=C.c_uint64()
     assert gpu.nf_owned_gpu_timer_read(C.byref(elapsed))==0 and elapsed.value>0
     timings.append(dict(alpha=i/100,draw_cpu_ns=draw_ns,completion_wait_ns=wait_ns,gpu_elapsed_ns=elapsed.value))
    assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0
   print('PASS101 fullscene native4K GPU submissions/readbacks')
   if timings:
    output=Path(sys.argv[1]).with_suffix('.isolated-gpu-timing.json')
    output.write_text(json.dumps(dict(scope='precomputed isolated fullscene draw; excludes preparation, presentation and live timing',pair_index=start,samples=timings),indent=2))
    print(str(output))
    for key in ('draw_cpu_ns','completion_wait_ns','gpu_elapsed_ns'):
     values=sorted(x[key]/1e6 for x in timings);print(key,dict(median_ms=statistics.median(values),p95_ms=values[int(.95*(len(values)-1))],max_ms=max(values)))
  finally:gpu.nf_owned_gpu_close()
 assert samples[0][0]==frames[0] and samples[-1][0]==frames[-1]
 assert 1 in prepared.pair._external_visits
 assert len({prepared.pair._scenery_motion.matrix(1,i/100) for i in range(101)})==101
 if start==1:assert prepared.pair._scenery_activation[1]==1
 print('PASS101 fullscene external samples, exact original endpoints and101distinctopponentposes')
finally:prepared.close();history.close()

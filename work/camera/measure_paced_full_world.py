"""Paced full-world diagnostic: no readback inside measured frame sequence."""
from pathlib import Path
setup=Path('work/camera/measure_completed_world_frame.py').read_text().split('history=EndpointRoadPlanner(rom,table);')[0]
exec(compile(setup,'paced_setup','exec'))
history=EndpointRoadPlanner(rom,table);old_roads,_=history.plan(ClosedGraph.decode(Path(r['wall_diagnostic_frames'][0]['graph']).read_bytes()));samples=[];preparations=[]
d.nf_owned_gpu_timer_read.argtypes=[C.POINTER(C.c_uint64)]
def draw(prepared,alpha,timed=True):
 began=time.perf_counter_ns();frame,camera,models,bounds,detail=prepared.sample(alpha);sampled=time.perf_counter_ns()
 if timed:assert d.nf_owned_gpu_timer_begin()==0
 assert d.nf_owned_gpu_draw_surface_clips(frame,len(frame),camera,models,bounds,detail['geometry_records'])==0
 if timed:assert d.nf_owned_gpu_timer_end()==0
 submitted=time.perf_counter_ns();assert d.nf_owned_gpu_finish()==0;finished=time.perf_counter_ns()
 gpu_ns=C.c_uint64()
 if timed:assert d.nf_owned_gpu_timer_read(C.byref(gpu_ns))==0
 return [(sampled-began)/1e6,(submitted-sampled)/1e6,(finished-submitted)/1e6,gpu_ns.value/1e6]
try:
 for fa,fb in zip(r['wall_diagnostic_frames'],r['wall_diagnostic_frames'][1:]):
  a=ClosedGraph.decode(Path(fa['graph']).read_bytes());b=ClosedGraph.decode(Path(fb['graph']).read_bytes());sa=ClosedSupplements.decode(Path(fa['supplements']).read_bytes(),a);sb=ClosedSupplements.decode(Path(fb['supplements']).read_bytes(),b);old=Path(fa['regenerated']).read_bytes();new=Path(fb['regenerated']).read_bytes()
  began=time.perf_counter_ns();prepared=PreparedWorldMotion(old,new,MotionScene(a,sa),MotionScene(b,sb),history,old_roads,rom);preparations.append((time.perf_counter_ns()-began)/1e6)
  try:
   for alpha in (.25,.5,.75):draw(prepared,alpha,timed=False)
   origin=time.perf_counter_ns()+20000000
   for index in range(8):
    start=origin+index*1000000000//60;deadline=origin+(index+1)*1000000000//60
    remaining=start-time.perf_counter_ns()
    if remaining>0:time.sleep(remaining/1e9)
    began=time.perf_counter_ns();alpha=(index+1)/9;before=texture_stats();stages=draw(prepared,alpha);finished=time.perf_counter_ns();after=texture_stats()
    samples.append(dict(older=a.refresh,newer=b.refresh,alpha=alpha,work_ms=(finished-began)/1e6,start_late_ms=(began-start)/1e6,deadline_late_ms=max(0,finished-deadline)/1e6,uploads=after[0]-before[0],sample_cpu_ms=stages[0],draw_cpu_ms=stages[1],finish_wait_ms=stages[2],gpu_timestamp_ms=stages[3]))
  finally:prepared.close()
  old_roads,_=history.plan(b)
finally:history.close();assert d.nf_owned_gpu_close()
work=sorted(x['work_ms'] for x in samples)
out=dict(result='PACED_FULL_WORLD_DIAGNOSTIC',samples=samples,prepare_ms=preparations,frames=len(samples),work_p95_ms=work[int(.95*(len(work)-1))],work_max_ms=max(work),deadline_misses=sum(x['deadline_late_ms']>0 for x in samples),scope='120 paced 4K CPU sample+draw+glFinish frames across15 retained intervals, warmup before each interval, no measured readback. Each interval stretched over8 presentation slots for diagnostics; preparation outside paced sequence. No original game timeline, SwapBuffers/scanout, fractional selection oracle or live60fps certification.')
Path('work/camera/paced-full-world-timing.json').write_text(json.dumps(out,indent=2))
print(out['result'],out['frames'],'p95',out['work_p95_ms'],'max',out['work_max_ms'],'deadline misses',out['deadline_misses'])


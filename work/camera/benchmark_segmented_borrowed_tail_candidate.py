"""Alternating encoder comparison on actual segmented captured samples."""
import json,time,tracemalloc,statistics,gc
from pathlib import Path
exec(Path('work/camera/test_spawned_segmented_shared_failure_candidate.py').read_text().split("if __name__=='__main__':")[0])
from owned_segmented_process_encode_candidate import encode_samples as copied
from owned_segmented_borrowed_tail_encode_candidate import encode_samples as borrowed
report=json.loads(Path('work/camera/prototype-runs/owned-native-1791539869506441500.json').read_text());folder=Path(report['live_preparation_profiles'][0]['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
ns={};exec(compile(source,'borrowed-tail-captured-setup','exec'),ns);ns['prepared'].close();ns['history'].close()
frames,scenes,rom,table=[ns[k] for k in ('frames','scenes','rom','table')]
from owned_endpoint_road_planner import EndpointRoadPlanner
history=EndpointRoadPlanner(rom,table);roads,_=history.plan(scenes[0].graph);prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);samples=PrecomputedSourceWorldSamples(prepared,(.1,.35,.9))
funcs={'copied':lambda:copied(samples.samples),'borrowed':lambda:borrowed(samples.samples,borrow_tails=True)}
try:
 a=funcs['copied']();b=funcs['borrowed']();assert a==b
 tail_bytes=sum(len(x) for x in b['tails']);del a,b
 rows=[]
 for i in range(24):
  for name in (('copied','borrowed') if i%2==0 else ('borrowed','copied')):
   start=time.perf_counter_ns();value=funcs[name]();end=time.perf_counter_ns();del value;rows.append(dict(iteration=i,variant=name,wall_ns=end-start))
 allocation={}
 for name in funcs:
  gc.collect();tracemalloc.start();before=tracemalloc.get_traced_memory()[0];value=funcs[name]();current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();allocation[name]=dict(current_delta=current-before,peak_delta=peak-before);del value
finally:samples.close();history.close()
out=dict(result='PASS_CAPTURED_BORROWED_TAIL_ENCODE_PARITY',tail_bytes=tail_bytes,median_ms={name:statistics.median(r['wall_ns']/1e6 for r in rows if r['variant']==name) for name in funcs},allocation=allocation,rows=rows,scope='24 alternating actual captured three-sample encodes; excludes reconstruction/shared mapping/live scheduling. Allocation tracing separate. No live cadence gain claim.')
Path('work/camera/prototype-runs/borrowed-tail-benchmark-20261009.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'})

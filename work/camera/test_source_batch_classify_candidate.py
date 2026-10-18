import runpy,json,time,concurrent.futures
from pathlib import Path
import owned_source_batch_classify_candidate as native
v=runpy.run_path('work/camera/test_projection_scratch_candidate.py');a=v['a'];c=native.SourceFaceDeterminants(v['ends'][0][v['key']],v['ends'][1][v['key']],v['gpu'],v['table']);jobs=[]
for i in range(101):
 alpha=i/100;m=tuple((1-alpha)*x+alpha*y for x,y in zip(*a.matrices))
 for rect in ((0,0,240,160),(-.5,-.5,.5,.5),(80,20,130,100),(240,160,0,0)):
  expected=a.combined_decisions(m,alpha,rect);assert c.combined_decisions(m,alpha,rect)==expected;jobs.append((m,alpha,rect,expected))
def run(job):
 m,alpha,rect,expected=job;assert c.combined_decisions(m,alpha,rect)==expected
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(run,jobs))
old=c._offsets[0];c._offsets[0]=1;before=(bytes(c._faces_out),bytes(c._codes_out))
try:
 try:c.combined_decisions(*jobs[0][:3])
 except ValueError:pass
 else:raise AssertionError('Malformed offsets accepted')
 assert before==(bytes(c._faces_out),bytes(c._codes_out))
finally:c._offsets[0]=old
run(jobs[0]);times={}
for name,owner in [('original',a),('native',c)]:
 t=time.perf_counter_ns()
 for _ in range(8):
  for m,alpha,rect,expected in jobs:assert owner.combined_decisions(m,alpha,rect)==expected
 times[name]=(time.perf_counter_ns()-t)/1e6
out=dict(result='PASS',decision_cases=len(jobs),concurrent_cases=len(jobs),malformed_offsets_output_unchanged=True,error_lock_released=True,benchmark_3232_calls_ms=times,scope='Actual paired53vertex source exact face/rectangle decisions across101alphas/fourrectangles; native component timing, no gameplay cadence claim');Path('work/camera/source-batch-classify-tests.json').write_text(json.dumps(out,indent=2));print(out)

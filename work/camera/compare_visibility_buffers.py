import runpy,json,time,statistics
from pathlib import Path
import owned_visibility_buffers_candidate as candidate
import owned_wall_visibility_candidate as original
saved=[]
def capture(calls):
 if len(saved)<10:saved.append(tuple(calls))
 return candidate.reference(calls)
original.batch=capture
runpy.run_path('work/camera/test_combined_segmented_gpu.py',run_name='__main__')
assert len(saved)==10
rows=[]
for round in range(20):
 row={}
 for name,fn in ([('original',candidate.reference),('candidate',candidate.batch)] if round%2==0 else [('candidate',candidate.batch),('original',candidate.reference)]):
  start=time.perf_counter_ns()
  for repeat in range(100):
   for calls in saved:fn(calls)
  row[name]=(time.perf_counter_ns()-start)/1e6/1000
 rows.append(row)
result=dict(result='PASS_ALTERNATING_COMPONENT',fixture_calls=len(saved),calls_per_round=1000,rounds=rows,median_original_ms=statistics.median(x['original'] for x in rows[4:]),median_candidate_ms=statistics.median(x['candidate'] for x in rows[4:]),scope='Alternating captured-call microbenchmark, first4warmup excluded; environment uncontrolled, no fullscene or physical cadence proof.')
Path('work/camera/visibility-buffers-performance.json').write_text(json.dumps(result,indent=2));print(result)

import sys,time,statistics,json,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import owned_model_visit_index_install_candidate
from owned_sampled_model_visit import sampled_model_visit as baseline
from owned_sampled_model_visit_index_candidate import sampled_model_visit as candidate
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0]
exec(compile(source,'captured_model_setup','exec'))
checks=[];times=[[],[]]
try:
 pair=prepared.pair
 # Initialize the original validated endpoint population before indexing.
 baseline(pair,0,0)
 ids=sorted({v['object'] for visits in pair._ordinary_visit_cache for v in visits}|set(getattr(pair,'_external_visits',{})))
 def outcome(fn,alpha,index):
  try:return ('value',fn(pair,alpha,index))
  except ValueError as e:return ('error',str(e))
 for alpha in [i/100 for i in range(101)]:
  for index in ids+[None,65535]:
   a=outcome(baseline,alpha,index);b=outcome(candidate,alpha,index);assert a==b,(alpha,index,a,b)
   checks.append(dict(alpha=alpha,object=index,result=a[0]))
 before=copy.deepcopy(pair._ordinary_visit_cache)
 for repetition in range(20):
  for which in (repetition%2,1-repetition%2):
   begin=time.perf_counter_ns()
   for alpha in (.1,.3,.5,.7,.9):
    for index in ids:outcome((baseline,candidate)[which],alpha,index)
   times[which].append(time.perf_counter_ns()-begin)
 assert before==pair._ordinary_visit_cache
 index=pair._ordinary_visit_object_index
 for groups,visits in zip(index,pair._ordinary_visit_cache):
  assert sum(len(x) for x in groups.values())==len(visits)
  assert all(value==tuple(v for v in visits if v['object']==key) for key,value in groups.items())
 out=dict(result='PASS_MODEL_VISIT_INDEX_CAPTURED_SAMPLES',samples=len(checks),objects=ids,checks=checks,baseline_median_ns=statistics.median(times[0]),candidate_median_ns=statistics.median(times[1]),scope='One captured changed-parent scene pair, 101 alphas, all present object IDs plus invalid/unspecified IDs; exact values and errors, endpoint records unchanged. Warm isolated visit timing, not live cadence or broad route qualification.')
 Path('work/camera/prototype-runs/model-visit-index-samples.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='checks'})
finally:
 prepared.close();history.close()
 assert not hasattr(prepared.pair,'_ordinary_visit_object_index')
 prepared.close()
 print('PASS_INDEX_REMOVED_ON_IDEMPOTENT_CLOSE')

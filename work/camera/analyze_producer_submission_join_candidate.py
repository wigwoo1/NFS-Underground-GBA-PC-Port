"""Complete expensive scene/submission identity join and nested budget audit."""
import json,sys,statistics
from pathlib import Path
from analyze_long_scene_preparation_candidate import analyze
from analyze_slow_producer_gc_candidate import overlap

def joined(r):
 base=analyze(r);out=[]
 keys=('space_wait_ns','frame_ownership_ns','snapshot_lock_ns','preparation_submit_ns','native_push_ns','notification_ns')
 native=('native_eligibility_wait_ns','native_eligibility_hold_ns','native_copy_unlocked_ns','native_publish_wait_ns','native_publish_hold_ns')
 for x in r['producer_retention']['long_scene_preparations']['records']:
  w=x['worker_submission'];a=w['submit_begin_ns'];b=w['submit_end_ns']
  assert w['scene_identity'][1]==x['refresh'] and not w['replay']
  assert x['started_ns']<=a<=b<=x['completed_ns']
  assert all(type(w[k]) is int and w[k]>=0 for k in (*keys,*native,'native_push_internal_ns'))
  assert sum(w[k] for k in keys)<=b-a
  assert sum(w[k] for k in native)<=w['native_push_internal_ns']+10
  assert w['native_push_internal_ns']<=w['native_push_ns']+10
  out.append(dict(refresh=x['refresh'],gc_overlap_ms=overlap(x['started_ns'],x['completed_ns'],r['gc_collection_samples'])/1e6,submission_ms=(b-a)/1e6,stages_ms={k:w[k]/1e6 for k in (*keys,*native,'native_push_internal_ns')},native_return_residual_ms=(w['native_push_ns']-w['native_push_internal_ns'])/1e6))
 low=[x for x in out if x['gc_overlap_ms']<=2]
 return dict(result='COMPLETE_EXPENSIVE_SCENE_SUBMISSION_JOIN',count=len(out),low_gc_count=len(low),low_gc_medians_ms={k:statistics.median(x['stages_ms'][k] for x in low) for k in low[0]['stages_ms']} if low else {},records=out,scope='Whole long-scene record identity join; nested native/caller wall budgets. Scheduling/FFI/GC may affect timings; no exclusive cause or pixel cadence proof.')
if __name__=='__main__':
 out=joined(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='records'})

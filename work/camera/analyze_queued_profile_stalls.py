"""Join disjoint stall boundaries with same-sample native deadline profiles."""
import json,sys
from pathlib import Path
from analyze_consumer_gap_partition import analyze
r=json.loads(Path(sys.argv[1]).read_text());part=analyze(r);rows={x['display_index']:x for x in r['presentation_samples'] if x.get('queued_wait_profile')}
for gap in part['largest']:
 x=rows[gap['display_index']];p=x['queued_wait_profile'];w=x['native_wait_timing'];assert p[:3]==[w[0],w[2],w[1]]
 gap.update(wait_profile=p,wait_ms=(p[1]-p[0])/1e6,entered_late_ms=max(0,p[0]-p[2])/1e6,returned_late_ms=max(0,p[1]-p[2])/1e6,max_lock_interval_ms=p[4]/1e6,max_blocking_wait_interval_ms=p[5]/1e6,blocking_wait_sum_ms=p[6]/1e6,executed_thread_cycles=p[3],queued_ready_timing=x['queued_stage_timing'],ready_fence_observations=x['queued_fence_observations'])
for gap in part['largest']:
 x=rows[gap['display_index']]
 candidates=[p for p in r['world_preparation_stage_samples'] if p['older']==x['source_older'] and p['newer']==x['refresh'] and p['completed_ns']<=x['pair_ready_ns']]
 assert candidates,'Missing authoritative preparation completion'
 p=max(candidates,key=lambda p:p['completed_ns'])
 gap['preparation_readiness']=dict(older=p['older'],newer=p['newer'],unfinished_at_acquire_ms=max(0,p['completed_ns']-x['pair_begin_ns'])/1e6,ready_before_acquire_ms=max(0,x['pair_begin_ns']-p['completed_ns'])/1e6,completion_to_acquired_ms=(x['pair_ready_ns']-p['completed_ns'])/1e6,stages=p)
part['scope']+=' Native timer/lock intervals include scheduler delays; executed cycles are not wall time.'
Path(sys.argv[2]).write_text(json.dumps(part,indent=2));print(json.dumps(part,indent=2))

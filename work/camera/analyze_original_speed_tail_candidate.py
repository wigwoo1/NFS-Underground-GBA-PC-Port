"""Account for final original-clock lag; never replaces strict speed gate."""
from pathlib import Path
import json,sys
r=json.loads(Path(sys.argv[1]).read_text());assert r['result']=='SMOKE_COMPLETE' and r['error'] is None
pauses=r['pause_events'];assert r['pause_retention']['dropped_records']==0
paused=sum(p['duration_ns'] for p in pauses);u=r['original_update_samples'][-1]
assert all(p['end_ns']<=u['started_ns'] for p in pauses)
base=u['clock_base'];assert u['refresh']-base+1==r['original_updates']
initial_origin=u['clock_origin']-paused;end=initial_origin+r['timing']['live_elapsed_ns']
deadline=u['clock_origin']+(r['original_updates']*280896*1000000000+16777215)//16777216
assert deadline==u['original_deadline_ns'] and deadline<=u['started_ns']<=u['completed_ns']<=end
lag=end-deadline;native_late=u['completed_ns']-deadline;tail=end-u['completed_ns'];assert lag==native_late+tail
producer=r['producer_cycle_samples'][-1];matching=producer['refresh']==u['refresh']
if matching:assert u['completed_ns']<=producer['started_ns']<=producer['completed_ns']<=end
out=dict(result='PASS_ORIGINAL_CLOCK_TAIL_ACCOUNTING',last_refresh=u['refresh'],updates=r['original_updates'],pause_total_ns=paused,initial_clock_origin_ns=initial_origin,derived_live_end_ns=end,deadline_lag_ms=lag/1e6,last_update_completion_late_ms=native_late/1e6,post_update_tail_ms=tail/1e6,final_scene_matches_last_update=matching,final_scene_producer=producer,scope='Complete retained pause history and last native deadline partition. Derives initial clock from final pause-adjusted origin and validates exact update/refresh count. Does not turn failed strict speed into a pass or prove all-run cadence.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],out['deadline_lag_ms'],out['post_update_tail_ms'],matching)

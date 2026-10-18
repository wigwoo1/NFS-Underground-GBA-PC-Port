"""Attribute measured endpoint shortfall without changing clock or tolerance."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text()); assert r['result']=='SMOKE_COMPLETE'
hz=16777216; cycles=280896
pauses=r['pause_events']; assert r['pause_retention']['dropped_records']==0
paused=sum(x['duration_ns'] for x in pauses)
rows=r['original_update_samples']; final=rows[-1]
assert final['refresh']-final['clock_base']+1==r['original_updates']
assert final['original_deadline_ns']==final['clock_origin']+(r['original_updates']*cycles*1000000000+hz-1)//hz
initial_origin=final['clock_origin']-paused
end=initial_origin+r['timing']['live_elapsed_ns']
endpoint_lag=end-final['original_deadline_ns']
shortfall=r['timing']['live_elapsed_ns']-paused-r['original_updates']*cycles*1000000000/hz
assert abs(endpoint_lag-shortfall)<=1
assert final['completed_ns']<=end
ledger=r['producer_retention']['long_scene_preparations']; assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
long=sorted(ledger['records'],key=lambda x:x['ns'],reverse=True)
out=dict(result='PASS_CLOCK_SHORTFALL_ATTRIBUTION',original_updates=r['original_updates'],endpoint_shortfall_ms=shortfall/1e6,final_update_started_late_ms=(final['started_ns']-final['original_deadline_ns'])/1e6,final_update_completed_late_ms=(final['completed_ns']-final['original_deadline_ns'])/1e6,post_final_update_ms=(end-final['completed_ns'])/1e6,complete_long_producer_count=len(long),largest_producer_records=long[:10],scope='Exact endpoint deadline identity and complete long-producer ledger. PASS means attribution checks pass, not original timing or smooth60. Scheduling and CPU causes remain unresolved.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2)); print(json.dumps({k:v for k,v in out.items() if k!='largest_producer_records'},indent=2))

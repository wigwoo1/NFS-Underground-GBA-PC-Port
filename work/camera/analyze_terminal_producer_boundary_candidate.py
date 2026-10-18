"""Partition terminal producer timing; never relax the original-speed gate."""
import json,sys
from pathlib import Path

def analyze(r):
 assert r['result']=='SMOKE_COMPLETE' and r['error'] is None
 assert r['pause_retention']['dropped_records']==0
 t=r['timing'];assert t['original_clock_hz']==16777216 and t['cycles_per_update']==280896
 rows=r['original_update_samples'];assert rows
 x=rows[-1];n=x['native_boundary'];assert len(n)==5
 start,end=x['started_ns'],x['completed_ns'];deadline=x['original_deadline_ns']
 assert deadline<=start<=n[0]<=n[1]<=end
 assert r['inputs'][-1]['refresh']==x['refresh']
 assert x['refresh']-x['clock_base']+1==r['original_updates']
 pauses=sum(p['duration_ns'] for p in r['pause_events'])
 active=t['live_elapsed_ns']-pauses
 sim=r['original_updates']*280896/16777216*1e9
 parts=dict(deadline_to_start_ns=start-deadline,pre_native_ns=n[0]-start,native_ns=n[1]-n[0],post_native_ns=end-n[1])
 assert sum(parts.values())==end-deadline
 return dict(result='TERMINAL_PRODUCER_BOUNDARY_PARTITION',refresh=x['refresh'],parts=parts,completion_lateness_ms=(end-deadline)/1e6,active_wall_deficit_ms=(active-sim)/1e6,tolerance_ms=2*280896/16777216*1000,original_speed_gate_pass=abs(active-sim)<=2*280896/16777216*1e9,scope='Final retained update only; post-native includes Python scheduling/cleanup/profiling. No exclusive cause or whole-run pacing proof; failed original-speed gate unchanged.')

if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

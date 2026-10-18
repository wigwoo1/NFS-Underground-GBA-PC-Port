"""Compare observed enabled/disabled child release runs; no exclusive benchmark claim."""
import json,sys,statistics
from pathlib import Path
rows=[]
for expected,name in zip((False,True),sys.argv[1:3]):
 r=json.loads(Path(name).read_text());assert r['result']=='SMOKE_COMPLETE' and r['error'] is None
 requests=r['world_preparation_stage_samples'];events=[];seen=set()
 for x in requests:
  c=x['terminal'][5];assert c['child_idle_release_enabled'] is expected
  g=c['child_gc_trace'];assert g['dropped']==0
  for e in g['rows']:
   key=(e['thread'],e['generation'],e['start_ns'],e['end_ns']);assert key not in seen;seen.add(key);events.append(e)
 full=[(e['end_ns']-e['start_ns'])/1e6 for e in events if e['generation']==2]
 n=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_intervals']
 ledger=r['original_update_retention']['complete_original_updates'];assert ledger['dropped']==0 and ledger['total']==r['original_updates']
 s=r['frame_preparation_shutdown'];assert s['joined'] and s['pending']==0 and s['owner_released_after_renderer_close']
 rows.append(dict(source=name,enabled=expected,updates=r['original_updates'],requests=len(requests),native_intervals=n,gc_events=len(events),gen2_count=len(full),gen2_mean_ms=statistics.mean(full) if full else None,gen2_max_ms=max(full) if full else None,gen2_total_ms=sum(full)))
assert len(rows)==2
out=dict(result='PASS_COMPLETE_IDLE_RELEASE_RUN_COMPARISON',runs=rows,scope='Sequential runs with identical requested steering/pause duration and explicit child selection; complete retained update and GC coverage. OS scheduling and differing scene trajectories are not controlled; one pair cannot establish exclusive performance causation or visible 60 fps.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

from pathlib import Path
import json,sys
raw=Path(sys.argv[1]);r=json.loads(raw.read_text());ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert ledger['dropped']==0;rows=[]
for e in ledger['records']:
 c=e['caller_stages'];a=c['hud_prefetch_wait_begin_ns'];b=c['hud_prefetch_wait_end_ns'];d=c['hud_prefetch_dispatch']
 if d is None:assert a==b;continue
 assert d['kind']=='hud_prefetch' and d['submitted_ns']<=d['started_ns']<=d['completed_ns']<=b
 ticks=[a,d['started_ns'],d['completed_ns'],b];ticks=[max(a,min(b,t)) for t in ticks];assert ticks==sorted(ticks)
 rows.append(dict(index=e['display_index'],interval_ms=e['interval_ns']/1e6,hud_wait_ms=(b-a)/1e6,queue_wait_clipped_ms=(ticks[1]-ticks[0])/1e6,command_clipped_ms=(ticks[2]-ticks[1])/1e6,future_return_ms=(ticks[3]-ticks[2])/1e6,full_command_ms=(d['completed_ns']-d['started_ns'])/1e6,poll_ms=(d['poll_end_ns']-d['poll_begin_ns'])/1e6))
assert rows
out=dict(result='PASS_COMPLETE_HUD_DISPATCH_WAIT_PARTITIONS',raw=str(raw),rows=rows,scope='Exact clipped HUD prefetch Future wait partitions within complete retained native >25ms intervals. Command may close retired snapshots and queue builds; elapsed timing includes scheduling, not exclusive HUD CPU.')
p=Path(sys.argv[2]);p.write_text(json.dumps(out,indent=2));print(out['result'],len(rows));print(sorted(rows,key=lambda x:x['hud_wait_ms'],reverse=True)[:3])

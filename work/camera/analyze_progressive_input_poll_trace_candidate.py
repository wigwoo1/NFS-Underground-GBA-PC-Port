from pathlib import Path
import json,sys
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert ledger['dropped']==0;rows=[]
for e in ledger['records']:
 for kind,d in [('prepare',e['prepared']['renderer_dispatch']),('hud_prefetch',e['caller_stages'].get('hud_prefetch_dispatch'))]:
  if d is None:continue
  p=d['input_poll_profile'];assert p is not None and p['begin_ns']<=p['end_ns']<=d['started_ns']
  names=('message_ns','keyboard_ns','controller_ns','publication_ns');assert all(p[k]>=0 for k in names) and sum(p[k] for k in names)<=p['native_ns']
  rows.append(dict(index=e['display_index'],kind=kind,interval_ms=e['interval_ns']/1e6,poll_ms=(p['end_ns']-p['begin_ns'])/1e6,native_ms=p['native_ns']/1e6,**{k.replace('_ns','_ms'):p[k]/1e6 for k in names},connected=p['connected'],queue_ms=(d['started_ns']-d['submitted_ns'])/1e6))
assert rows
out=dict(result='PASS_RETAINED_INPUT_POLL_STAGE_ACCOUNTING',rows=rows,scope='All retained long native interval preparation/HUD commands with owner-thread fresh input stage timing; connected field is detection only, not physical controller functional verification. Timed calls perturb overhead; no exclusive CPU or cadence claim.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],len(rows));print(sorted(rows,key=lambda x:x['poll_ms'],reverse=True)[:3])

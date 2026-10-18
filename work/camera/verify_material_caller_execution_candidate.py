import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());seen={};ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert ledger['dropped']==0
items=[(p['commit'],p['prepared']) for p in r['presentation_samples']]+[(e['transaction']['commit'],e['prepared']) for e in ledger['records']]
for commit,p in items:
 for c in p['d3d_call_profiles']:
  x=c['caller_execution'];a=x['before'];b=x['after']
  assert a[0]<=c['caller_begin_ns']<=c['native_begin_ns']<=c['native_end_ns']<=c['caller_end_ns']<=b[0]
  assert b[1]-a[1]==x['raw_cycles']>=c['native_cycles'] and b[2]-a[2]==x['cpu_ns']>=0
  k=(commit[0],commit[1],commit[4],c['call']);row=dict(identity=list(k[:3]),call=k[3],return_ms=(c['caller_end_ns']-c['native_end_ns'])/1e6,native_ms=(c['native_end_ns']-c['native_begin_ns'])/1e6,caller_raw_cycles=x['raw_cycles'],native_raw_cycles=c['native_cycles'],caller_cpu_ns=x['cpu_ns'])
  assert k not in seen or seen[k]==row;seen[k]=row
assert seen
out=dict(result='PASS_ACTUAL_MATERIAL_CALL_EXECUTION_ACCOUNTING',verified_rows=len(seen),long_frame_records=len(ledger['records']),max_return_ms=max(x['return_ms'] for x in seen.values()),rows=list(seen.values()),scope='Retained120frame tail plus complete >25ms event ledger. Thread CPU timestamps coarse; raw cycles include getter overhead and cannot establish GIL causality. Not whole-run per-call coverage or sustained60.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'})

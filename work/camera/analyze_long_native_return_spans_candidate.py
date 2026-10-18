import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());l=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert l['dropped']==0 and l['total']==len(l['records']);assert r['gc_trace_dropped']==0
rows=[]
def profile(x):
 a=x['caller_begin_ns'];b=x['native_begin_ns'];d=x['native_end_ns'];e=x['caller_end_ns'];assert a<=b<=d<=e;assert x['native_cycles']>=0
 return dict(entry_ms=(b-a)/1e6,native_ms=(d-b)/1e6,return_ms=(e-d)/1e6,cycles=x['native_cycles'])
for e in l['records']:
 p=e['prepared'];lease=p['hud_lease_stages'];n=lease['native_callback_profile'];assert lease['callback_begin_ns']<=n[0]<=n[1]<=lease['callback_end_ns'];assert n[2]>=0
 gc=[]
 for g in r['gc_collection_samples']:
  assert g['start_ns']<=g['end_ns']
  a=max(n[1],g['start_ns']);b=min(lease['callback_end_ns'],g['end_ns'])
  if b>a:gc.append(dict(generation=g['generation'],overlap_ms=(b-a)/1e6))
 rows.append(dict(identity=[e['epoch'],e['generation'],e['display_index']],interval_ms=e['interval_ns']/1e6,source_callback_native_ms=(n[1]-n[0])/1e6,source_callback_cycles=n[2],source_callback_return_ms=(lease['callback_end_ns']-n[1])/1e6,source_callback_return_parent_gc=gc,bundle=profile(p['bundle_transfer_profile']),materials=[dict(call=x['call'],**profile(x)) for x in p['d3d_call_profiles']]))
out=dict(result='PASS_COMPLETE_LONG_NATIVE_RETURN_SPANS',rows=rows,scope='Native entry/end and caller return spans; raw cycles are not converted to elapsed CPU time. Parent GC overlap only. Does not identify GIL, driver, OS scheduling, or exclusive cause.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],len(rows))

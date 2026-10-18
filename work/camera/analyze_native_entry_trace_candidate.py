import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());s=r['bounded_diagnostic_stats']['whole_run_api_intervals'];assert r['result']=='SMOKE_COMPLETE' and r['error'] is None and s['slow_gap_dropped']==0 and r['gc_trace_dropped']==0
rows=[]
for x in s['slow_gap_samples']:
 t=x['native_entry_trace'];w=x['wait_trace'];assert len(t)==9 and all(t[i]<=t[i+1] for i in range(8));assert w[1]==x['deadline_ns'];assert t[3]<=x['draw_begin_ns']<=t[4]
 gc=[g for g in r['gc_collection_samples'] if g['start_ns']<x['end_ns'] and g['end_ns']>x['start_ns']]
 rows.append(dict(display_index=x['display_index'],gap_ms=(x['end_ns']-x['start_ns'])/1e6,eligibility_ms=(t[2]-t[1])/1e6,python_draw_entry_delay_ms=(x['draw_begin_ns']-t[3])/1e6,native_deadline_wait_ms=(t[6]-t[5])/1e6,wait_overshoot_ms=max(0,w[2]-max(w[0],w[1]))/1e6,draw_ms=x['draw_ns']/1e6,present_ms=x['present_ns']/1e6,gc_max_ms=max(((g['end_ns']-g['start_ns'])/1e6 for g in gc),default=0)))
assert len(rows)==s['over_25ms']
out=dict(result='MEASURED_NATIVE_WAIT_CALLBACK_ATTRIBUTION',gaps=len(rows),worst=sorted(rows,key=lambda x:x['gap_ms'],reverse=True)[:12],without_long_collection=sorted([x for x in rows if x['gc_max_ms']<=8],key=lambda x:x['gap_ms'],reverse=True)[:12],scope='Bounded whole-run slow API gaps, native and Python timestamps. Callback-entry delay includes scheduling/GIL; cause not independently distinguished. No physical scanout proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

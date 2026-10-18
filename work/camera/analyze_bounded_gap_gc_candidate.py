"""Correlate bounded slow API intervals with the complete collection ledger."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());s=r['bounded_diagnostic_stats']['whole_run_api_intervals'];assert r['result']=='SMOKE_COMPLETE' and not r['error'];assert s['slow_gap_dropped']==0 and r['gc_trace_dropped']==0;assert len(s['slow_gap_samples'])==s['over_25ms']
gc=r['gc_collection_samples'];rows=[]
for gap in s['slow_gap_samples']:
 overlaps=[x for x in gc if x['start_ns']<gap['end_ns'] and x['end_ns']>gap['start_ns']]
 clipped=sum(max(0,min(x['end_ns'],gap['end_ns'])-max(x['start_ns'],gap['start_ns'])) for x in overlaps)
 rows.append(dict(**gap,gap_ms=(gap['end_ns']-gap['start_ns'])/1e6,gc_overlap_ms=clipped/1e6,gc_max_ms=max(((x['end_ns']-x['start_ns'])/1e6 for x in overlaps),default=0),generations=sorted({x['generation'] for x in overlaps})))
out=dict(result='MEASURED_WHOLE_RUN_SLOW_GAP_GC_OVERLAP',slow_gaps=len(rows),overlap_any=sum(x['gc_overlap_ms']>0 for x in rows),overlap_collection_over8ms=sum(x['gc_max_ms']>8 for x in rows),no_collection_overlap=sum(x['gc_overlap_ms']==0 for x in rows),worst=sorted(rows,key=lambda x:x['gap_ms'],reverse=True)[:15],without_long_collection=sorted([x for x in rows if x['gc_max_ms']<=8],key=lambda x:x['gap_ms'],reverse=True)[:15],scope='All observed API intervals >25ms, zero timestamp/GC drops. Correlation only; not exclusive cause or visible scanout timing.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

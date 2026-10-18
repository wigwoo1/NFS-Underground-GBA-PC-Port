"""Correlate actual observed collections with adjacent native API gaps."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());gc=r['gc_collection_samples'];assert r['gc_trace_dropped']==0,'Incomplete collection coverage';rows=[x for x in r['presentation_samples'] if x['native_result']==1];gaps=[]
for a,b in zip(rows,rows[1:]):
 if (b['epoch'],b['generation'],b['display_index'])!=(a['epoch'],a['generation'],a['display_index']+1):continue
 begin=a['callback_timing']['present_end_ns'];end=b['callback_timing']['present_end_ns'];duration=(end-begin)/1e6
 if duration<=25:continue
 overlaps=[dict(generation=x['generation'],collection_ms=(x['end_ns']-x['start_ns'])/1e6,overlap_ms=max(0,min(end,x['end_ns'])-max(begin,x['start_ns']))/1e6,thread_id=x['thread_id']) for x in gc if x['start_ns']<end and x['end_ns']>begin]
 gaps.append(dict(index=b['display_index'],gap_ms=duration,collections=overlaps))
out=dict(result='MEASURED_GC_GAP_CORRELATION',report=sys.argv[1],collections=len(gc),maximum_collection_ms=max(((x['end_ns']-x['start_ns'])/1e6 for x in gc),default=0),gaps_over_25ms=len(gaps),gaps_over_50ms=sum(x['gap_ms']>50 for x in gaps),long_gaps_with_collection=sum(x['gap_ms']>50 and bool(x['collections']) for x in gaps),gap_records=gaps,scope='Observed same-process GC and native API intervals, unchanged GC policy. Overlap supports correlation, not exclusive causality or scanout evidence.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='gap_records'})

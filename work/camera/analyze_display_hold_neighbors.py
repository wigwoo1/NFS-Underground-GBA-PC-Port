"""Inspect temporally associated display holds; association is not frame identity."""
import csv,json,sys
from pathlib import Path
report,trace,association,out=map(Path,sys.argv[1:5]);r=json.loads(report.read_text());rows=list(csv.DictReader(trace.open()));a=json.loads(association.read_text());samples={x['display_index']:x for x in r['presentation_samples'] if x.get('native_committed_sample')};ordered=sorted(samples);positions={v:i for i,v in enumerate(ordered)};checks=[]
for link in a['associations']:
 row=rows[link['csv_index']]
 try:duration=float(row['DisplayedTime'])
 except ValueError:continue
 if duration<=25:continue
 s=samples[link['display_index']];i=positions[s['display_index']]
 n=samples[ordered[i+1]] if i+1<len(ordered) else None
 checks.append(dict(csv_index=link['csv_index'],display_index=s['display_index'],display_duration_ms=duration,draw_ms=(s['draw_complete_ns']-s['sample_begin_ns'])/1e6,next_commit_gap_ms=None if n is None else (n['native_committed_sample'][6]-s['native_committed_sample'][6])/1e6,next_draw_ms=None if n is None else (n['draw_complete_ns']-n['sample_begin_ns'])/1e6,source_pair=[s['source_older'],s['refresh']],next_source_pair=None if n is None else [n['source_older'],n['refresh']]))
result=dict(result='TEMPORAL_HOLD_DIAGNOSTIC',checks=checks,scope='Unfiltered display holds including pauses. Unique ETW/native temporal candidates only; not semantic frame identity or causal attribution. Duration versus next native commit/draw timing is diagnostic.')
out.write_text(json.dumps(result,indent=2));print(dict(holds=len(checks),largest=sorted(checks,key=lambda x:x['display_duration_ms'],reverse=True)[:3]))

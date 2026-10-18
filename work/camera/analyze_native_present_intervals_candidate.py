"""Successful Present-return cadence, explicitly excluding physical scanout claims."""
import sys,json,statistics
from pathlib import Path
report=json.loads(Path(sys.argv[1]).read_text());rows=report['presentation_samples']
previous=None;intervals=[];skipped=0;worst=[]
for row in rows:
 if row['native_result']!=1:continue
 timing=row['callback_timing'];at=timing['present_end_ns']
 assert timing['present_begin_ns']<=at<=row['transaction_end_ns']
 if previous is not None:
  if (row['epoch'],row['generation'])==(previous['epoch'],previous['generation']) and row['display_index']==previous['display_index']+1:
   delta=(at-previous['callback_timing']['present_end_ns'])/1e6
   assert delta>=0
   intervals.append(delta);worst.append(dict(index=row['display_index'],interval_ms=delta,deadline_spacing_ms=(row['presentation_deadline_ns']-previous['presentation_deadline_ns'])/1e6))
  else:skipped+=1
 previous=row
assert intervals
ordered=sorted(intervals)
result=dict(result='PASS_PRESENT_RETURN_INTERVAL_TELEMETRY',adjacent_successful_intervals=len(intervals),excluded_discontinuities=skipped,median_ms=statistics.median(intervals),p95_ms=ordered[int(.95*(len(ordered)-1))],max_ms=max(intervals),over_25ms=sum(x>25 for x in intervals),over_33_333ms=sum(x>100/3 for x in intervals),over_50ms=sum(x>50 for x in intervals),under_8ms=sum(x<8 for x in intervals),worst=sorted(worst,key=lambda x:x['interval_ms'],reverse=True)[:10],scope='Native successful Present return times for adjacent slots in same generation; excludes pause/reset boundaries. This measures API cadence, not display scanout or pixel motion.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='worst'},indent=2))

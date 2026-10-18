"""Summarize native presentation stalls without attributing them to GPU execution."""
import json,sys,statistics
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads(p.read_text());rows=[]
for x in r['presentation_samples']:
 if x.get('present_begin_ns') is None or x.get('present_end_ns') is None:continue
 assert x['present_end_ns']>=x['present_begin_ns']
 rows.append(dict(refresh=x['refresh'],wall_ms=(x['present_end_ns']-x['present_begin_ns'])/1e6,draw_call_ms=x['cpu_call_ns']/1e6,native_stage_ms=None if x.get('native_present_stage_ns') is None else [v/1e6 for v in x['native_present_stage_ns']],native_present_ms=None if x.get('native_present_ns') is None else x['native_present_ns']/1e6))
assert rows,'Missing presentation telemetry'
values=sorted(x['wall_ms'] for x in rows)
out=dict(scope='Native present call wall duration includes driver/scheduling waits; not GPU execution or scanout proof',count=len(rows),median_ms=statistics.median(values),p95_ms=values[int((len(values)-1)*.95)],over_two_refreshes=sum(v>33.333 for v in values),largest=sorted(rows,key=lambda x:x['wall_ms'],reverse=True)[:10],producer_wall_summary=r['timing']['producer_read_validate_reconstruct_submit'])
p.with_suffix('.presentation-stalls.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

"""Separate paced sleep lateness from preparation and presentation CPU times."""
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads(p.read_text());rows=[x for x in r['presentation_samples'] if x.get('hidden_window_presented') and x.get('display_index') is not None];out=[]
for a,b in zip(rows,rows[1:]):
 if any(min(b['present_end_ns'],e['end_ns'])>max(a['present_end_ns'],e['begin_ns']) for e in r['pause_events']):continue
 gap=(b['present_end_ns']-a['present_end_ns'])/1e6
 if gap<=1000/30:continue
 deadline=b['presentation_deadline_ns'];draw_end=b['draw_complete_ns'];begin=b['present_begin_ns']
 out.append(dict(gap_ms=gap,index=b['display_index'],older=b['source_older'],newer=b['refresh'],pair_wait_ms=b['pair_prepare_ns']/1e6,draw_ms=b['draw_cpu_ns']/1e6,requested_wait_ms=max(0,deadline-draw_end)/1e6,actual_wait_ms=(begin-draw_end)/1e6,wait_overshoot_ms=(begin-max(deadline,draw_end))/1e6,present_call_ms=(b['present_end_ns']-begin)/1e6,deadline_lateness_ms=(begin-deadline)/1e6))
result=dict(scope='CPU deadline/wait/presentation timestamps; no OS scheduler or scanout attribution',gaps=out)
p.with_suffix('.deadline-overruns.json').write_text(json.dumps(result,indent=2));print(result)

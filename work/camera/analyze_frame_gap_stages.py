"""Partition observed presentation gaps by actual recorded CPU timestamps."""
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);d=json.loads(p.read_text());rows=[r for r in d['presentation_samples'] if r.get('interpolated') and r.get('hidden_window_presented')];out=[]
for a,b in zip(rows,rows[1:]):
 begin=a['present_end_ns'];end=b['present_end_ns'];assert end>=begin
 if end-begin<=1000000000/30:continue
 if any(min(end,v['end_ns'])>max(begin,v['begin_ns']) for v in d.get('pause_events',[])):continue
 stamps=[b[k] for k in ('slot_begin_ns','sample_begin_ns','draw_complete_ns','present_begin_ns','commit_return_ns','present_end_ns')];assert all(y>=x for x,y in zip(stamps,stamps[1:]))
 stamps=[begin]+[max(begin,min(end,t)) for t in stamps];durations=[(y-x)/1e6 for x,y in zip(stamps,stamps[1:])];assert abs(sum(durations)-(end-begin)/1e6)<1e-6
 out.append(dict(display_index=b['display_index'],source_older=b['source_older'],refresh=b['refresh'],gap_ms=(end-begin)/1e6,new_pair=a['refresh']!=b['refresh'],stages_ms=dict(zip(('before_slot','input','sample_draw','pacing','commit','after_commit'),durations)),pose_sample_ms=b['pose_sample_cpu_ns']/1e6,draw_ms=b['draw_cpu_ns']/1e6,pair_wait_ms=b['pair_prepare_ns']/1e6))
result=dict(scope='Disjoint CPU timestamp gap partition outside recorded pauses; preparation wait is interval-inclusive diagnostic, not additive; no scanout or exclusive CPU proof',count=len(out),gaps=sorted(out,key=lambda x:x['gap_ms'],reverse=True))
p.with_suffix('.gap-stages.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

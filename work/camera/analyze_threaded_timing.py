"""Separate queue wait, extraction/render work and presentation scheduling evidence."""
import csv,json,statistics,sys
from pathlib import Path
m=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'));prefix=m['prefix']
def rows(suffix):return list(csv.DictReader(Path(prefix+suffix).open()))
def summary(values):
 v=sorted(values)
 return dict(count=len(v),minimum=v[0],p01=v[int((len(v)-1)*.01)],median=statistics.median(v),p95=v[int((len(v)-1)*.95)],p99=v[int((len(v)-1)*.99)],maximum=v[-1]) if v else None
stages=rows('-stages.csv')
stage_timings={name:summary([(int(r[end])-int(r[start]))/1e6 for r in stages]) for name,start,end in [('setup','renderer_begin_ns','setup_end_ns'),('scene','setup_end_ns','scene_end_ns'),('hud','scene_end_ns','hud_end_ns'),('finish','hud_end_ns','finish_end_ns')]}
w=rows('-worker.csv');p=rows('-producer.csv');inputs=rows('-input.csv');accepted=[r for r in w if int(r['committed'])==1]
intervals=[(int(b['end_ns'])-int(a['end_ns']))/1e6 for a,b in zip(accepted,accepted[1:])]
produced={(r['epoch'],r['target']):r for r in p if int(r['pushed'])}
ready_margins=[];finish_lateness=[]
for r in accepted:
 source=produced.get((r['epoch'],r['target']))
 if source:ready_margins.append((int(r['deadline_ns'])-int(source['push_end_ns']))/1e6)
 finish_lateness.append((int(r['draw_end_ns'])-int(r['deadline_ns']))/1e6)
stage_rows={(r['epoch'],r['target']):r for r in stages}
late_frames=[]
for r in accepted:
 if int(r['draw_end_ns'])<=int(r['deadline_ns']):continue
 key=(r['epoch'],r['target']);source=produced.get(key);stage=stage_rows.get(key)
 assert source is not None and stage is not None,'Missing stage/source row for late frame'
 late_frames.append(dict(target=float(r['target']),producer_ready_margin_ms=(int(r['deadline_ns'])-int(source['push_end_ns']))/1e6,queue_ms=(int(r['start_ns'])-int(source['push_end_ns']))/1e6,render_ms=(int(r['draw_end_ns'])-int(r['start_ns']))/1e6,render_lateness_ms=(int(r['draw_end_ns'])-int(r['deadline_ns']))/1e6,extraction_ms=(int(source['extract_end_ns'])-int(source['begin_ns']))/1e6,copy_ms=(int(source['copy_end_ns'])-int(source['extract_end_ns']))/1e6,setup_ms=(int(stage['setup_end_ns'])-int(stage['renderer_begin_ns']))/1e6,scene_ms=(int(stage['scene_end_ns'])-int(stage['setup_end_ns']))/1e6,hud_ms=(int(stage['hud_end_ns'])-int(stage['scene_end_ns']))/1e6,finish_ms=(int(stage['finish_end_ns'])-int(stage['hud_end_ns']))/1e6))
stalls=[]
for a,b,gap in zip(accepted,accepted[1:],intervals):
 if gap>20:
  source=produced.get((b['epoch'],b['target']));stalls.append(dict(target=float(b['target']),interval_ms=gap,render_ms=(int(b['draw_end_ns'])-int(b['start_ns']))/1e6,lateness_ms=(int(b['commit_begin_ns'])-int(b['deadline_ns']))/1e6,queue_ms=None if source is None else (int(b['start_ns'])-int(source['push_end_ns']))/1e6,extraction_ms=None if source is None else (int(source['extract_end_ns'])-int(source['begin_ns']))/1e6))
report=dict(result='MEASURED',timing_only=m.get('timing_only',False),renderer_stages_ms=stage_timings,producer_ready_margin_ms=summary(ready_margins),render_finish_lateness_ms=summary(finish_lateness),render_finishes_after_deadline=sum(v>0 for v in finish_lateness),presentation_intervals_ms=summary(intervals),render_ms=summary([(int(r['draw_end_ns'])-int(r['start_ns']))/1e6 for r in accepted]),extraction_ms=summary([(int(r['extract_end_ns'])-int(r['begin_ns']))/1e6 for r in p]),copy_ms=summary([(int(r['copy_end_ns'])-int(r['extract_end_ns']))/1e6 for r in p]),original_tick_execution_ms=summary([(int(r['end_ns'])-int(r['start_ns']))/1e6 for r in inputs]),intervals_above_20ms=len(stalls),intervals_above_33_333ms=sum(v>100/3 for v in intervals),stalls=stalls,late_frames=late_frames,smooth_60fps_verified=False,scope='CPU ledger timings only; original RAM verification is separate. Does not measure scanout, physical response or temporal image fidelity.')
Path(prefix+'-timing-analysis.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='stalls'},indent=2))

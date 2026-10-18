"""Compare stalled wall durations with measured execution cycles; no causal claim."""
import json,statistics,sys
from pathlib import Path

def analyze(r):
 groups={}
 for job in r['world_preparation_stage_samples']:
  for sample in job.get('sample_timings',[]):
   for stage in sample.get('assembly_stages',[]):
    if stage['wall_ns']>0 and stage['thread_cycles']>0:groups.setdefault(stage['name'],[]).append(stage)
 stages=[]
 for name,rows in sorted(groups.items()):
  median_wall=statistics.median(x['wall_ns'] for x in rows)
  median_cycles=statistics.median(x['thread_cycles'] for x in rows)
  slow=max(rows,key=lambda x:x['wall_ns'])
  stages.append(dict(name=name,count=len(rows),median_wall_ms=median_wall/1e6,median_cycles=median_cycles,slowest=slow,wall_ratio=slow['wall_ns']/median_wall,cycle_ratio=slow['thread_cycles']/median_cycles))
 draws=[x for x in r['presentation_samples'] if x.get('native_draw_boundary') and x['native_draw_boundary'][2]>0]
 assert draws
 mw=statistics.median(x['native_draw_boundary'][1]-x['native_draw_boundary'][0] for x in draws)
 mc=statistics.median(x['native_draw_boundary'][2] for x in draws)
 longest=sorted(draws,key=lambda x:x['native_draw_boundary'][1]-x['native_draw_boundary'][0],reverse=True)[:10]
 return dict(result='RECORDED_WALL_CYCLE_COMPARISON',stages=stages,draw_median_wall_ms=mw/1e6,draw_median_cycles=mc,longest_draws=[dict(display_index=x['display_index'],wall_ms=(x['native_draw_boundary'][1]-x['native_draw_boundary'][0])/1e6,cycles=x['native_draw_boundary'][2],wall_ratio=(x['native_draw_boundary'][1]-x['native_draw_boundary'][0])/mw,cycle_ratio=x['native_draw_boundary'][2]/mc) for x in longest],scope='Within-run wall and thread-cycle ratios. Large wall with normal cycles suggests elapsed waiting/descheduling, but does not distinguish GIL, OS scheduling, driver wait, or synchronization. Cycles are not CPU time and ratios do not prove causality.')
if __name__=='__main__':
 result=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(dict(result=result['result'],draw_median_wall_ms=result['draw_median_wall_ms'],longest_draws=result['longest_draws'][:2],slow_frame_join=next(x for x in result['stages'] if x['name']=='immutable_frame_join')),indent=2))

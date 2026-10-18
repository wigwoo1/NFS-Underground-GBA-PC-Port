"""Join default renderer commit gaps to concurrent producer/preparation evidence."""
import json,sys
from pathlib import Path
def analyze(r):
 rows=[x for x in r['presentation_samples'] if x.get('native_committed_sample') and x.get('hidden_window_presented')]; gaps=[]
 for old,new in zip(rows,rows[1:]):
  a=old['native_committed_sample'][6];b=new['native_committed_sample'][6]
  if old['epoch']!=new['epoch'] or b-a<=1000000000/30:continue
  if any(p['begin_ns']<b and p['end_ns']>a for p in r['pause_events']):continue
  points=[a,max(a,new['sample_begin_ns']),max(a,new['draw_complete_ns']),max(a,new['present_begin_ns']),b]
  assert points==sorted(points), 'Nonmonotonic consumer stages'
  phases=dict(zip(['before_sample','sample_and_draw','pacing','present_commit'],[(y-x)/1e6 for x,y in zip(points,points[1:])]))
  assert abs(sum(phases.values())-(b-a)/1e6)<.000001
  updates=[u for u in r['original_update_samples'] if u['started_ns']<b and u['completed_ns']>a]
  preparations=[s for s in r['world_preparation_stage_samples'] if s['started_ns']<b and s['completed_ns']>a]
  gaps.append(dict(display_index=new['display_index'],source=[new['epoch'],new['source_older'],new['refresh']],gap_ms=(b-a)/1e6,phases_ms=phases,overlapping_updates=updates,overlapping_preparations=preparations))
 return dict(active_long_gaps=len(gaps),gaps=sorted(gaps,key=lambda x:x['gap_ms'],reverse=True),scope='Disjoint consumer elapsed phases; concurrent producer/preparation overlap is not causal or additive CPU evidence. No physical scanout certification.')
if __name__=='__main__':
 result=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps([dict(index=g['display_index'],gap_ms=g['gap_ms'],phases=g['phases_ms'],updates=[u['refresh'] for u in g['overlapping_updates']],preparations=[[s['older'],s['newer']] for s in g['overlapping_preparations']]) for g in result['gaps']],indent=2))

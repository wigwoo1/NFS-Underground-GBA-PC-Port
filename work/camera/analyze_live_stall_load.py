"""Correlate unpaused presentation gaps with recorded work and load, not causality."""
import json,sys
from pathlib import Path
from analyze_gc_stall_overlap import overlap
from analyze_active_play_cadence import analyze

def correlate(report,load):
 assert load['thread_stopped'] and not load['errors']
 previous_end=None
 for item in load['samples']:
  assert item['end_ns']>item['begin_ns'] and 0<=item['busy_fraction']<=1
  if previous_end is not None:assert item['begin_ns']>=previous_end,'Overlapping load samples'
  previous_end=item['end_ns']
 rows=[x for x in report['presentation_samples'] if x.get('interpolated') and x.get('hidden_window_presented')]
 results=[]
 for a,b in zip(rows,rows[1:]):
  begin,end=a['present_end_ns'],b['present_end_ns']
  pause=sum(max(0,min(end,p['end_ns'])-max(begin,p['begin_ns'])) for p in report['pause_events'])
  active=(end-begin-pause)/1e6
  if active<=1000/30:continue
  load_ns=busy_ns=0
  for item in load['samples']:
   span=max(0,min(end,item['end_ns'])-max(begin,item['begin_ns']))
   load_ns+=span;busy_ns+=span*item['busy_fraction']
  stages=b.get('native_commit_stage_ns');callback=None if not stages else (stages[4]-stages[3])/1e6
  prep=[]
  for x in report['world_preparation_stage_samples']:
   span=max(0,min(end,x['completed_ns'])-max(begin,x['started_ns']))
   if span:prep.append(dict(older=x['older'],newer=x['newer'],overlap_ms=span/1e6,wall_ms=(x['completed_ns']-x['started_ns'])/1e6,thread_cpu_ms=(x['construct_thread_cpu_ns']+x['precompute_thread_cpu_ns'])/1e6))
  results.append(dict(display_index=b['display_index'],older=b['source_older'],newer=b['refresh'],active_gap_ms=active,pause_overlap_ms=pause/1e6,gc_overlap_ms=overlap(begin,end,report['gc_collection_samples']),callback_ms=callback,draw_cpu_ms=b.get('draw_cpu_ns',0)/1e6 if b.get('draw_cpu_ns') is not None else None,load_busy_fraction=busy_ns/load_ns if load_ns else None,load_coverage=load_ns/(end-begin),preparation=prep))
 cadence=analyze(report);assert len(results)==cadence['active_gaps_over_two_refreshes']
 return dict(result='CORRELATED',gaps=len(results),cadence=cadence,records=sorted(results,key=lambda x:x['active_gap_ms'],reverse=True),scope='Timestamp overlap of unpaused gaps, GC, preparation and aggregate system CPU load. Native callback/draw is current-row wall time. Overlap is not exclusive causality, process attribution or physical scanout proof.')
if __name__=='__main__':
 rp,lp,out=map(Path,sys.argv[1:4]);r=correlate(json.loads(rp.read_text()),json.loads(lp.read_text()));out.write_text(json.dumps(r,indent=2));print(json.dumps(dict(gaps=r['gaps'],largest=r['records'][:3]),indent=2))


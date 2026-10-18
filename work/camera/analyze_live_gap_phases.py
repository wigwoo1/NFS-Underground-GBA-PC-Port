"""Partition host presentation gaps; durations are not exclusive CPU cost."""
import json,sys
from pathlib import Path

def overlap(start,end,left,right):
 return max(0,min(end,right)-max(start,left))/1e6

def analyze(r):
 rows=[]
 for previous,current in zip(r['presentation_samples'],r['presentation_samples'][1:]):
  left=previous['present_end_ns'];right=current['present_end_ns']
  assert right>=left
  if right-left<=1e9/30:continue
  phases={}
  for name,a,b in [('pair','pair_begin_ns','pair_ready_ns'),('draw','sample_begin_ns','draw_complete_ns'),('present','present_begin_ns','present_end_ns')]:
   start=current.get(a);end=current.get(b)
   if start is not None and end is not None:
    assert end>=start;phases[name]=overlap(start,end,left,right)
  jobs=[]
  for job in r.get('preparation_queue_samples',[]):
   start=job.get('started_ns');end=job.get('finished_ns')
   if start is not None and end is not None and overlap(start,end,left,right)>0:
    jobs.append(dict(identity=job['identity'],factory_overlap_ms=overlap(start,end,left,right)))
  rows.append(dict(index=current['display_index'],gap_ms=(right-left)/1e6,phase_overlap_ms=phases,swap_ms=current['native_present_stage_ns'][1]/1e6,preparation_jobs=jobs))
 return dict(scope='Host clock phase intersections with complete presentation gaps, including intentional pause crossings. Concurrent preparation overlaps are not additive or causal/exclusive CPU attribution. Native swap duration is a nested presentation measurement. No scanout proof.',long_gaps=len(rows),largest=sorted(rows,key=lambda x:x['gap_ms'],reverse=True)[:20])
if __name__=='__main__':
 p=Path(sys.argv[1]);out=analyze(json.loads(p.read_text()));p.with_suffix('.gap-phases.json').write_text(json.dumps(out,indent=2));print(json.dumps(out['largest'][:4],indent=2))

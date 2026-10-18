"""Join presentation gaps to ordered original producer/capture boundaries.

Overlapping threads are not additive CPU time or proof of scheduling cause.
"""
import json,sys
from pathlib import Path
from analyze_live_gap_phases import overlap

def analyze(r):
 rows=r['presentation_samples'];chains=[]
 for previous,current in zip(rows,rows[1:]):
  left=previous['present_end_ns'];right=current['present_end_ns']
  if right-left<=1e9/30:continue
  updates=[];captures=[]
  for source,name,output in ((r.get('original_update_samples',[]),'update',updates),(r.get('producer_cycle_samples',[]),'capture',captures)):
   for item in source:
    start=item.get('started_ns');end=item.get('completed_ns')
    if start is None or end is None:continue
    assert end>=start
    ms=overlap(start,end,left,right)
    if ms:output.append(dict(refresh=item['refresh'],overlap_ms=ms,wall_ms=(end-start)/1e6,thread_cycles=item.get('thread_cycles'),stages=item.get('stages')))
  submitted=current.get('source_submitted_ns');dequeued=current.get('source_dequeued_ns');draw_start=current.get('sample_begin_ns');draw_end=current.get('draw_complete_ns')
  chains.append(dict(index=current['display_index'],older=current.get('source_older'),newer=current['refresh'],gap_ms=(right-left)/1e6,before_source_submission_ms=overlap(left,submitted,left,right) if submitted is not None else None,source_queue_overlap_ms=overlap(submitted,dequeued,left,right) if submitted is not None and dequeued is not None else None,draw_overlap_ms=overlap(draw_start,draw_end,left,right) if draw_start is not None and draw_end is not None else None,gpu_query_ms=current.get('gpu_elapsed_ns',0)/1e6 if current.get('gpu_elapsed_ns') is not None else None,original_updates=updates,captures=captures))
 return dict(scope='Host-clock interval intersections; source submission can precede gap, yielding zero overlap. CPU draw includes native/driver/wait. GPU timestamps are diagnostic and not scanout proof. Raw gaps include pauses. Concurrent intervals are not additive or causal.',chains=sorted(chains,key=lambda x:x['gap_ms'],reverse=True))
if __name__=='__main__':
 source=Path(sys.argv[1]);result=analyze(json.loads(source.read_text()));out=Path(sys.argv[2]);out.write_text(json.dumps(result,indent=2));print(json.dumps(result['chains'][:5],indent=2))

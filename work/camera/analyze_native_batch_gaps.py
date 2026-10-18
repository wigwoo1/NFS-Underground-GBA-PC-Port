"""Native batch commit gaps and bounded overlap evidence; no causal CPU claim."""
import json,sys
from pathlib import Path

def analyze(report):
 rows=[r for r in report['presentation_samples'] if r.get('native_batch_candidate') and r.get('hidden_window_presented')]
 assert rows
 pauses=report.get('pause_events',[]);gaps=[]
 for previous,row in zip(rows,rows[1:]):
  begin=previous['native_committed_sample'][6];end=row['native_committed_sample'][6]
  assert end>=begin and row['display_index']==previous['display_index']+1
  if any(max(begin,p['begin_ns'])<min(end,p['end_ns']) for p in pauses):continue
  if end-begin<=1000000000/30:continue
  draw_begin,draw_end=row['native_draw_boundary'][:2]
  called=row.get('batch_native_call_ns',row['transaction_begin_ns'])
  prepare_begin=row.get('batch_preparation_begin_ns',row['sample_begin_ns'])
  def overlap(a,b):return max(0,min(end,b)-max(begin,a))/1e6
  assert prepare_begin<=called<=draw_begin<=draw_end<=end
  gaps.append(dict(display_index=row['display_index'],source=[row['source_older'],row['refresh']],gap_ms=(end-begin)/1e6,before_draw_ms=max(0,draw_begin-begin)/1e6,native_draw_overlap_ms=overlap(draw_begin,draw_end),after_draw_ms=(end-max(begin,draw_end))/1e6,batch_packaging_overlap_ms=overlap(prepare_begin,called),pair_acquisition_overlap_ms=overlap(row['pair_begin_ns'],row['pair_ready_ns']),native_call_to_draw_overlap_ms=overlap(called,draw_begin),deadline_lateness_ms=(end-row['presentation_deadline_ns'])/1e6))
 return dict(result='BATCH_GAP_BOUNDARIES_VERIFIED',native_batch_samples=len(rows),long_active_gaps=len(gaps),largest=sorted(gaps,key=lambda x:x['gap_ms'],reverse=True)[:20],scope='Authoritative native commit/draw times; packaging/pair overlaps are concurrent evidence, not additive CPU cost or causal attribution. Original report remains unchanged.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

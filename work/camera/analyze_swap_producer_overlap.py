"""Native swap interval joins with captured producer windows, not causal CPU attribution."""
import json,sys
from pathlib import Path
def union_overlap(begin,end,intervals):
 spans=sorted((max(begin,a),min(end,b)) for a,b in intervals if max(begin,a)<min(end,b))
 merged=[]
 for a,b in spans:
  if merged and a<=merged[-1][1]:merged[-1][1]=max(b,merged[-1][1])
  else:merged.append([a,b])
 return sum(b-a for a,b in merged)/1e6
def analyze(r):
 updates=[(x['native_boundary'][0],x['native_boundary'][1]) for x in r['original_update_samples']]
 captures=[(x['started_ns'],x['completed_ns']) for x in r['producer_cycle_samples']]
 rows=[]
 for x in r['presentation_samples']:
  if not x.get('native_batch_candidate'):continue
  stages=x['native_present_stage_ns']
  if stages[1]<=33333333:continue
  # Profile starts inside the native callback; stage0 precedes SwapBuffers.
  # Commit stage4 follows the callback. Anchor its tail and retain bounded restore error.
  end=x['native_commit_stage_ns'][4]-stages[2];begin=end-stages[1]
  residual=x['native_commit_stage_ns'][4]-x['native_commit_stage_ns'][3]-sum(stages)
  assert begin<=end and residual>=0
  rows.append(dict(display_index=x['display_index'],swap_ms=stages[1]/1e6,swap_cycles=x['native_present_thread_cycles'][1],estimated_swap_window=[begin,end],window_uncertainty_ms=residual/1e6,update_union_overlap_ms=union_overlap(begin,end,updates),capture_union_overlap_ms=union_overlap(begin,end,captures)))
 return dict(result='PASS_PRODUCER_OVERLAP_JOINS',long_swaps=len(rows),worst=sorted(rows,key=lambda x:x['swap_ms'],reverse=True)[:10],rows=rows,scope='Swap window anchored at post-callback native stage with measured instrumentation tail uncertainty. Wall interval overlap is not CPU occupancy, exclusive time, causality or scheduler trace.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))

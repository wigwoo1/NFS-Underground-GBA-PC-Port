"""Attribute observed frame gaps to measured presentation duration, not cause."""
import json,sys
from pathlib import Path
def analyze(r):
 rows=[x for x in r['presentation_samples'] if x.get('native_committed_sample')];assert rows
 gaps=[]
 for a,b in zip(rows,rows[1:]):
  start=a['native_committed_sample'][6];end=b['native_committed_sample'][6]
  if any(start<p['native_resume_ack_ns'] and end>=p['native_pause_ack_ns'] for p in r['pause_events']):continue
  gap=end-start
  if gap<=33333334:continue
  stages=b.get('native_present_stage_ns');assert stages is not None and len(stages)==3 and all(x>=0 for x in stages)
  commit=b['native_commit_stage_ns'];assert len(commit)==7 and commit[3]<=commit[4]
  # Profiled swap duration is inside the native present callback interval.
  assert sum(stages)<=commit[4]-commit[3]+1000000,'Profile duration outside callback tolerance'
  gaps.append(dict(display_index=b['display_index'],gap_ms=gap/1e6,blit_ms=stages[0]/1e6,swap_ms=stages[1]/1e6,after_swap_ms=stages[2]/1e6,swap_fraction_of_gap=stages[1]/gap,swap_cycles=b.get('native_present_thread_cycles',[None]*4)[1],callback_begin_ns=commit[3],callback_end_ns=commit[4]))
 return dict(long_gaps=len(gaps),swap_dominant_long_gaps=sum(x['swap_fraction_of_gap']>=.5 for x in gaps),largest_gaps=sorted(gaps,key=lambda x:x['gap_ms'],reverse=True)[:20],scope='Measured SwapBuffers elapsed duration versus active intercommit gap. Callback profiling tolerance1ms. Does not distinguish compositor/driver/GPU backlog/OS descheduling or prove physical scanout.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(dict(long_gaps=out['long_gaps'],swap_dominant_long_gaps=out['swap_dominant_long_gaps'],largest_gap=out['largest_gaps'][:1])))

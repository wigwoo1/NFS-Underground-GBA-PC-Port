"""Compare sequential measured runs; recorded load is not experimental control."""
import json,statistics,sys
from pathlib import Path
def analyze(report,load):
 assert report['result']=='SMOKE_COMPLETE' and load['thread_stopped'] and not load['errors']
 rows=[x for x in report['presentation_samples'] if x.get('native_committed_sample')];assert rows
 gaps=[];skipped=0
 for a,b in zip(rows,rows[1:]):
  delta=b['display_index']-a['display_index'];assert delta>0
  if b.get('display_advancement_candidate'):assert b['display_advance_audit'][:2]==[a['display_index'],delta-1]
  else:assert delta==1
  skipped+=delta-1
  start=a['native_committed_sample'][6];end=b['native_committed_sample'][6]
  if any(start<p['native_resume_ack_ns'] and end>=p['native_pause_ack_ns'] for p in report['pause_events']):continue
  duration=end-start;assert duration>=0
  overlap=[(max(0,min(end,s['end_ns'])-max(start,s['begin_ns'])),s['busy_fraction']) for s in load['samples'] if s['busy_fraction'] is not None]
  covered=sum(n for n,v in overlap)
  gaps.append(dict(begin_ns=start,end_ns=end,gap_ms=duration/1e6,load_coverage_ns=covered,busy_fraction=sum(n*v for n,v in overlap)/covered if covered else None))
 active=[x['gap_ms'] for x in gaps];busy=[s['busy_fraction'] for s in load['samples'] if s['busy_fraction'] is not None]
 return dict(window_shown=bool(report.get('window_shown')),commits=len(rows),original_updates=report['original_updates'],skipped_display_slots=skipped,median_gap_ms=statistics.median(active),p95_gap_ms=sorted(active)[int(.95*(len(active)-1))],long_gaps=sum(x>1000/30 for x in active),max_gap_ms=max(active),median_system_busy=statistics.median(busy),largest_gaps=sorted(gaps,key=lambda x:x['gap_ms'],reverse=True)[:10],scope='Sequential instrumented queued runs. Load intervals are coarse aggregate CPU observations, not attribution or causal control; no physical scanout proof.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()),json.loads(Path(sys.argv[2]).read_text()));Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='largest_gaps'}))

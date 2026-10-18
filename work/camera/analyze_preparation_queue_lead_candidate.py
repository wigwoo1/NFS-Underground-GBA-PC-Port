"""Validate bounded queue lead evidence and correlate retained native waits."""
import json,sys,statistics
from pathlib import Path
def analyze(r):
 requests=r['world_preparation_stage_samples'];rows=[]
 shutdown=r['shutdown_evidence']['preparation_service_shutdown']
 assert requests and shutdown['diagnostic_dropped']==0 and shutdown['completed']==len(requests)
 for q in requests:
  submitted,dispatch=q['queue_submitted_ns'],q['queue_dispatch_ns']
  assert type(submitted)is int and submitted<=dispatch==q['started_ns']<=q['completed_ns']
  first=q['parent_sample_rows'][0]['published_ns'] if q['parent_sample_rows'] else None
  if first is not None:assert dispatch<=first<=q['completed_ns']
  rows.append(dict(generation=q['generation'],older=q['older'],newer=q['newer'],submitted_ns=submitted,dispatch_ns=dispatch,queue_ms=(dispatch-submitted)/1e6,submit_to_first_ms=None if first is None else (first-submitted)/1e6))
 waits=[]
 ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert ledger['dropped']==0
 for event in ledger['records']:
  c=event['caller_stages'];a,b=c['preparation_take_begin_ns'],c['preparation_take_end_ns']
  publications=[]
  for q,row in zip(requests,rows):
   for sample in q['parent_sample_rows']:
    if a<=sample['published_ns']<=b:
     publications.append(dict(row,sample_index=sample['index'],submitted_before_take_ms=(a-row['submitted_ns'])/1e6,dispatched_before_take_ms=(a-row['dispatch_ns'])/1e6))
  latest_pause=next((p for p in reversed(r['pause_events']) if p['end_ns']<=a),None)
  waits.append(dict(after_latest_pause_ms=None if latest_pause is None else (a-latest_pause['end_ns'])/1e6,identity=[event['epoch'],event['generation'],event['display_index']],wait_ms=(b-a)/1e6,publications=publications))
 return dict(result='PASS_COMPLETE_PREPARATION_QUEUE_LEAD',requests=len(rows),mean_queue_ms=statistics.mean(x['queue_ms'] for x in rows),max_queue_ms=max(x['queue_ms'] for x in rows),largest_queue=sorted(rows,key=lambda x:x['queue_ms'],reverse=True)[:10],waits=waits,scope='Submission recorded immediately before unchanged queue insertion; dispatch at existing worker pickup. Full completed request ledger only; retired requests outside retained completed rows. Association does not establish exclusive scheduler or CPU cause.')
if __name__=='__main__':
 raw=json.loads(Path(sys.argv[1]).read_text());out=analyze(raw)
 # Invalid causal chronology must fail, rather than silently clipping.
 from copy import deepcopy
 bad=deepcopy(raw);bad['world_preparation_stage_samples'][0]['queue_submitted_ns']=bad['world_preparation_stage_samples'][0]['started_ns']+1
 try:analyze(bad)
 except AssertionError:pass
 else:raise AssertionError('Invalid queue chronology accepted')
 out['negative_control_rejected']=True
 Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ('largest_queue','waits')})

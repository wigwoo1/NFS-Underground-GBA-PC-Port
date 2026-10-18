"""Conservative pause-aware success coverage; no scanout qualification."""
import json,sys
from pathlib import Path
def verify(r):
 w=r['live_observation_stats']['whole_run_api_intervals'];s=w['native_success_segments'];records=s['records'];pauses=r['pause_events'];begin=r['live_observation_begin_ns'];end=r['live_observation_end_ns']
 if s['dropped'] or s['total']!=len(records):raise ValueError('Incomplete native segment ledger')
 if len(records)!=len(pauses)+1:raise ValueError('Zero-success or unclassified active segment')
 if not records or sum(x['successful_samples'] for x in records)!=w['native_success_boundaries']['successful_samples']:raise ValueError('Incomplete success counts')
 starts=[begin];ends=[]
 for pause in pauses:
  a,b,c,d=[pause[k] for k in ['begin_ns','native_pause_ack_ns','end_ns','native_resume_ack_ns']]
  if not starts[-1]<=a<=b<=c<=d<=end:raise ValueError('Unordered pause acknowledgments')
  ends.append(a);starts.append(d)
 ends.append(end);rows=[]
 for i,(record,start,stop) in enumerate(zip(records,starts,ends)):
  first,last,deadline=[record[k] for k in ['first_success_ns','last_success_ns','first_success_deadline_ns']]
  if record['successful_samples']<=0 or not start<=first<=last<=stop:raise ValueError('Success outside active segment')
  if record['last_index']-record['first_index']+1!=record['successful_samples']:raise ValueError('Skipped segment display index')
  if i and (record['epoch']!=records[i-1]['epoch'] or record['generation']<=records[i-1]['generation'] or record['first_index']!=records[i-1]['last_index']+1):raise ValueError('Unclassified epoch/reset or index transition')
  eligible=max(start,deadline) if i==0 else start
  if eligible>first:raise ValueError('Success precedes eligible deadline')
  rows.append(dict(generation=record['generation'],successful_samples=record['successful_samples'],initial_active_hold_ms=(first-eligible)/1e6,first_deadline_late_ms=max(0,first-deadline)/1e6,trailing_active_hold_ms=(stop-last)/1e6,scope='Startup eligible first deadline; resume measured directly from native resume acknowledgment. Pause-command begin ends active segment.'))
 a=w['all_successful_native_intervals'];assert a['successful_samples']==sum(x['successful_samples'] for x in rows)
 passed=a['over25']==0 and a['skipped_indices_between_successes']==0 and all(max(x['initial_active_hold_ms'],x['trailing_active_hold_ms'])<=25 for x in rows)
 return dict(result='PASS_PAUSE_AWARE_COVERAGE_ACCOUNTING',segments=rows,active_intervals=a,cadence_screen_passed=passed,scope='Complete retained generation summaries with explicit pauses, initial/resume/prepause/trailing holds. 25ms screen is weaker than sustained60; no physicalscanout qualification. Zero-success/dropped/reset ambiguity fails.')
if __name__=='__main__':
 r=json.loads(Path(sys.argv[1]).read_text());out=verify(r);Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)

"""Exact clipped caller GPU preparation wait partition; no nested duration addition."""
import json,sys
from pathlib import Path
def analyze(report):
 ledger=report['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals']
 assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
 rows=[]
 for event in ledger['records']:
  caller=event['caller_timing'];prepared=event['prepared'];dispatch=prepared['renderer_dispatch']
  assert dispatch['kind']=='prepare'
  begin=caller['draw_begin_ns'];end=caller['draw_end_ns']
  assert begin<=dispatch['submitted_ns']<=dispatch['started_ns']<=dispatch['completed_ns']<=end
  times=[begin,dispatch['submitted_ns'],dispatch['started_ns'],dispatch['completed_ns'],end]
  clip=[max(event['begin_ns'],min(event['end_ns'],x)) for x in times]
  spans=[b-a for a,b in zip(clip,clip[1:])]
  assert sum(spans)==clip[-1]-clip[0]
  stages=prepared.get('consumer_stages',[])
  assert all(s['elapsed_ns']>=0 for s in stages)
  rows.append(dict(index=event['display_index'],interval_ms=event['interval_ns']/1e6,prepare_wait_ms=sum(spans)/1e6,partition_ms=dict(zip(['before_submit','queue_wait','renderer_job','future_return'],[x/1e6 for x in spans])),consumer_stages=stages,d3d_call_profiles=prepared.get('d3d_call_profiles',[]),scope='Consumer stages/native calls nested inside renderer job; elapsed includes scheduling and GC, do not sum into wait partition.'))
 return dict(result='PASS_EXACT_NATIVE_PREPARE_WAIT_PARTITION',records=len(rows),rows=sorted(rows,key=lambda x:x['prepare_wait_ms'],reverse=True),scope='All retained >25ms native gaps, exact caller/dispatch boundaries; renderer job wall time is not exclusive GPU execution or CPU time.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()))
 Path(sys.argv[2]).write_text(json.dumps(out,indent=2))
 print(out['result']);print([(x['index'],x['prepare_wait_ms'],x['partition_ms']) for x in out['rows'][:3]])

"""Reconcile complete prepare callback with dispatch, worker and wakeup costs."""
import json,sys,statistics
from pathlib import Path
from analyze_long_interval_partition_candidate import union_ns

def analyze(report):
 assert report['gc_trace_dropped']==0
 api=report['bounded_diagnostic_stats']['whole_run_api_intervals'];ledger=api['long_intervals'];assert ledger['dropped']==0
 assert ledger['total']==api['over_33_333ms']==len(ledger['records']), 'Incomplete long interval ledger'
 rows=[]
 for e in ledger['records']:
  d=e['renderer_dispatch'];assert d['kind']=='prepare'
  stamps=[e['draw_begin_ns'],d['submitted_ns'],d['started_ns'],d['completed_ns'],e['draw_end_ns']]
  assert all(a<=b for a,b in zip(stamps,stamps[1:])),stamps
  chunks=[b-a for a,b in zip(stamps,stamps[1:])];assert sum(chunks)==e['draw_end_ns']-e['draw_begin_ns']
  source=e['source_prepare_ns'];consumer=sum(x['elapsed_ns'] for x in e['consumer_stages']);assert source>=0 and consumer>=0 and source+consumer<=chunks[2]
  gc=union_ns([(g['start_ns'],g['end_ns']) for g in report['gc_collection_samples']],e['begin_ns'],e['end_ns'])
  hud=e.get('hud_lease_stages') or {};snapshot=hud['snapshot_end_ns']-hud['snapshot_begin_ns'] if hud else None
  assert snapshot is None or 0<=snapshot<=source, 'HUD snapshot exceeds source budget'
  stage_ms={}
  for stage in e['consumer_stages']:
   name=stage['stage'];assert name not in stage_ms and stage['elapsed_ns']>=0
   stage_ms[name]=stage['elapsed_ns']/1e6
  rows.append(dict(consumer_stage_ms=stage_ms,index=e['display_index'],interval_ms=e['interval_ns']/1e6,gc_ms=gc/1e6,pre_submit_ms=chunks[0]/1e6,dispatch_wait_ms=chunks[1]/1e6,worker_ms=chunks[2]/1e6,caller_resume_ms=chunks[3]/1e6,source_ms=source/1e6,consumer_ms=consumer/1e6,worker_other_ms=(chunks[2]-source-consumer)/1e6,hud_snapshot_ms=snapshot/1e6 if snapshot is not None else None,hud_snapshot_new=hud.get('snapshot_new')))
 groups={}
 keys=('dispatch_wait_ms','worker_ms','caller_resume_ms','source_ms','consumer_ms','worker_other_ms','hud_snapshot_ms')
 for name,group in [('all',rows),('gc_at_most_2ms',[x for x in rows if x['gc_ms']<=2]),('gc_over_10ms',[x for x in rows if x['gc_ms']>10])]:
  groups[name]=dict(count=len(group),median_ms={k:statistics.median(x[k] for x in group if x[k] is not None) for k in keys} if group else {})
  names=sorted({k for row in group for k in row['consumer_stage_ms']})
  groups[name]['consumer_stage_median_ms']={k:statistics.median(row['consumer_stage_ms'][k] for row in group if k in row['consumer_stage_ms']) for k in names}
 return dict(result='LONG_PREPARE_DISPATCH_WORKER_RECONCILED',groups=groups,rows=sorted(rows,key=lambda x:x['interval_ms'],reverse=True),scope='All retained long intervals, ordered timestamp partition with nested source/consumer budgets reconciled. Wall-clock includes scheduling/GIL/GC/native work; no exclusive CPU causality, no smooth gameplay or scanout proof.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],out['groups']);print(out['rows'][:2])

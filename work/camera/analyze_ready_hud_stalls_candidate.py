"""Complete long-frame stages grouped by actual HUD readiness, not causal labels."""
import json,sys,statistics
from pathlib import Path
from analyze_prepare_budget_candidate import analyze

def analyze_ready(r):
 partition=analyze(r);by_index={x['index']:x for x in partition['rows']};groups={name:[] for name in ('ready_transfer','waited_transfer','cached_hud','unprefetched_new_hud')}
 for e in r['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']['records']:
  transfer=e.get('hud_transfer');hud=e.get('hud_lease_stages');assert hud is not None
  if transfer is not None:
   assert hud['snapshot_new']
   assert transfer['submitted_ns']<=transfer['started_ns']<=transfer['completed_ns']<=transfer['take_end_ns']
   assert hud['snapshot_begin_ns']<=transfer['take_begin_ns']<=transfer['take_end_ns']<=hud['snapshot_end_ns']
   if transfer['ready_before_take']:assert transfer['completed_ns']<=transfer['take_begin_ns']
   name='ready_transfer' if transfer['ready_before_take'] else 'waited_transfer'
  else:name='unprefetched_new_hud' if hud['snapshot_new'] else 'cached_hud'
  row=dict(by_index[e['display_index']]);row['ready_group']=name;groups[name].append(row)
 out={}
 for name,rows in groups.items():
  names=sorted({stage for row in rows for stage in row['consumer_stage_ms']})
  out[name]=dict(count=len(rows),gc_over10ms=sum(row['gc_ms']>10 for row in rows),median_ms={key:statistics.median(row[key] for row in rows) for key in ('interval_ms','gc_ms','source_ms','consumer_ms','worker_ms','caller_resume_ms')} if rows else {},consumer_stage_median_ms={stage:statistics.median(row['consumer_stage_ms'][stage] for row in rows) for stage in names},rows=rows)
 assert sum(x['count'] for x in out.values())==len(partition['rows'])
 return dict(result='COMPLETE_LONG_STALLS_BY_HUD_READINESS',groups=out,total=len(partition['rows']),scope='Complete long API interval ledger partitioned by actual HUD Future readiness and cached source. Stage wall times include scheduling/GC/native waits, medians not additive, no exclusive cause or visible motion claim.')
if __name__=='__main__':
 out=analyze_ready(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print({k:{a:b for a,b in v.items() if a!='rows'} for k,v in out['groups'].items()})

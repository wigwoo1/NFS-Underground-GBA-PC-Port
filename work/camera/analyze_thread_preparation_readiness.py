"""Join threaded preparation completion to renderer acquisition; intervals overlap."""
import json,sys
from pathlib import Path
from analyze_live_stall_load import correlate

def analyze(report,load):
 gaps=correlate(report,load)['records']
 rows={x['display_index']:x for x in report['presentation_samples'] if 'display_index' in x}
 preparations=report['world_preparation_stage_samples']
 result=[]
 for gap in gaps:
  row=rows[gap['display_index']]
  candidates=[p for p in preparations if p['older']==gap['older'] and p['newer']==gap['newer'] and p['completed_ns']<=row['pair_ready_ns']]
  if not candidates:raise ValueError('Missing completed preparation for acquired pair')
  p=max(candidates,key=lambda x:x['completed_ns'])
  begin,ready=row['pair_begin_ns'],row['pair_ready_ns']
  assert begin<=ready and p['started_ns']<=p['completed_ns']<=ready
  result.append(dict(display_index=gap['display_index'],older=gap['older'],newer=gap['newer'],active_gap_ms=gap['active_gap_ms'],acquisition_ms=(ready-begin)/1e6,unfinished_preparation_at_acquire_ms=max(0,p['completed_ns']-begin)/1e6,completed_before_acquire_ms=max(0,begin-p['completed_ns'])/1e6,completion_to_acquired_ms=(ready-p['completed_ns'])/1e6,construct_ms=p['construct_advance_ns']/1e6,precompute_ms=p['precompute_ns']/1e6,preparation_completed_after_display_deadline_ms=(p['completed_ns']-row['presentation_deadline_ns'])/1e6))
 return dict(result='JOINED',gaps=len(result),records=result,scope='Timestamp readiness evidence; overlapping intervals are not exclusive costs. Active gap removes intentional pause only. No physical scanout or causal load proof.')
if __name__=='__main__':
 report,load,out=map(Path,sys.argv[1:4]);data=analyze(json.loads(report.read_text()),json.loads(load.read_text()));out.write_text(json.dumps(data,indent=2));print(json.dumps(dict(gaps=data['gaps'],largest=data['records'][:3]),indent=2))

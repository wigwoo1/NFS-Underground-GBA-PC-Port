"""Concurrent producer intervals inside native presentation gaps; no CPU causality."""
import json,sys
from pathlib import Path
from analyze_gap_preparation_pairs import analyze as base

def union_ms(begin,end,intervals):
 pieces=sorted((max(begin,a),min(end,b)) for a,b in intervals if max(begin,a)<min(end,b))
 total=0;last=None
 for a,b in pieces:
  if last is None:last=[a,b]
  elif a<=last[1]:last[1]=max(last[1],b)
  else:total+=last[1]-last[0];last=[a,b]
 if last:total+=last[1]-last[0]
 assert 0<=total<=end-begin
 return total/1e6

def analyze(report):
 out=(__import__('analyze_process_preparation_gaps').analyze(report) if report.get('process_preparation_enabled') else base(report));rows={x['display_index']:x for x in report['presentation_samples'] if x.get('native_committed_sample')}
 for gap in out['largest']:
  begin=rows[gap['display_index']-1]['native_committed_sample'][6];end=rows[gap['display_index']]['native_committed_sample'][6]
  updates=[x for x in report['original_update_samples'] if x['started_ns']<end and x['completed_ns']>begin]
  submits=[x for x in report['worker_submit_stage_samples'] if x['submit_begin_ns']<end and x['submit_end_ns']>begin]
  gap['producer_overlap']=dict(update_count=len(updates),update_wall_union_ms=union_ms(begin,end,[(x['started_ns'],x['completed_ns']) for x in updates]),native_update_wall_union_ms=union_ms(begin,end,[(x['native_boundary'][0],x['native_boundary'][1]) for x in updates]),submission_count=len(submits),submission_wall_union_ms=union_ms(begin,end,[(x['submit_begin_ns'],x['submit_end_ns']) for x in submits]),longest_updates=[dict(refresh=x['refresh'],wall_ms=(x['completed_ns']-x['started_ns'])/1e6,native_wall_ms=(x['native_boundary'][1]-x['native_boundary'][0])/1e6,thread_cycles=x['thread_cycles'],admission_lateness_ms=(x['started_ns']-x['original_deadline_ns'])/1e6) for x in sorted(updates,key=lambda x:x['completed_ns']-x['started_ns'],reverse=True)[:3]])
 out['scope']+=' Producer/consumer/preparation execute concurrently; union overlap is bounded wall coincidence, not additive cost, CPU utilization or scheduling causality.'
 return out
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

"""Exact owner completion partition; elapsed waits do not imply exclusive cause."""
import json,sys,copy
from pathlib import Path
def analyze(t):
 rows=[];owners=set()
 for r in t['rows']:
  k=tuple(r['identity']);assert k not in owners;owners.add(k)
  if not r['commit_ns']:continue
  st=r['native_stage_ns'];dispatch=r['renderer_dispatch']
  points=[r['commit_ns'],st[5],st[6],r['native_transaction_end_ns'],dispatch['completed_ns'],r['transaction_end_ns'],r['append_begin_ns'],r['append_end_ns']]
  assert points==sorted(points)
  names=['commit_to_callback_return','callback_to_native_return','native_to_python_end','python_end_to_dispatch_complete','dispatch_complete_to_parent_return','parent_return_to_append','append']
  parts=dict(zip(names,[(b-a)/1e6 for a,b in zip(points,points[1:])]))
  assert abs(sum(parts.values())-(points[-1]-points[0])/1e6)<1e-6
  rows.append(dict(identity=r['identity'],commit_to_parent_ms=(r['transaction_end_ns']-r['commit_ns'])/1e6,partition_ms=parts))
 assert rows
 return dict(result='PASS_EXACT_PARENT_COMPLETION_PARTITION',attempts=len(t['rows']),committed=len(rows),max_commit_to_parent_ms=max(r['commit_to_parent_ms'] for r in rows),largest=sorted(rows,key=lambda r:r['commit_to_parent_ms'],reverse=True)[:12],scope='Exact native identities and ordered timestamps. Dispatch completion precedes Future.set_result; final phase includes Future notification, parent GIL/scheduling and caller work, not exclusively a wakeup wait.')
if __name__=='__main__':
 t=json.loads(Path(sys.argv[1]).read_text());out=analyze(t)
 bad=copy.deepcopy(t);r=next(r for r in bad['rows'] if r['commit_ns']);r['renderer_dispatch']['completed_ns']=r['native_transaction_end_ns']-1
 try:analyze(bad)
 except AssertionError:out['reversed_completion_negative_control']='PASS'
 else:raise AssertionError('Reversed completion accepted')
 Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='largest'});print(out['largest'][:2])

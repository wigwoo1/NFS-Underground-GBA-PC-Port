"""Split retained completed-request reporting tails from next-dispatch delay."""
import json,sys
from pathlib import Path
def analyze(r):
 q=r['world_preparation_stage_samples'];rows=[]
 assert r['shutdown_evidence']['preparation_service_shutdown']['diagnostic_dropped']==0
 for prev,current in zip(q,q[1:]):
  t=current['previous_request_tail'];assert t is not None
  points=[t['completed_ns'],t['report_append_begin_ns'],t['report_append_end_ns'],t['release_end_ns'],current['queue_dispatch_ns']]
  assert points==sorted(points) and points[0]==prev['completed_ns']
  spans=[(b-a)/1e6 for a,b in zip(points,points[1:])]
  rows.append(dict(pair=[current['older'],current['newer']],previous_pair=[prev['older'],prev['newer']],idle_before_submission_ms=max(0,current['queue_submitted_ns']-points[3])/1e6,released_with_request_queued_ms=(points[4]-max(points[3],current['queue_submitted_ns']))/1e6,completed_to_dispatch_ms=(points[-1]-points[0])/1e6,partition_ms=dict(zip(['row_to_append','report_append','release','released_to_next_dispatch'],spans))))
 assert rows
 return dict(result='PASS_COMPLETED_REQUEST_REPORT_TAIL_PARTITION',rows=len(rows),max_report_append_ms=max(x['partition_ms']['report_append'] for x in rows),largest=sorted(rows,key=lambda x:x['released_with_request_queued_ms'],reverse=True)[:20],scope='Elapsed completed row construction/report append/release/next pickup. Released-to-next may include idle, cancellation or scheduling; not exclusively CPU or serialization. Last request tail is not retained.')
if __name__=='__main__':
 r=json.loads(Path(sys.argv[1]).read_text());out=analyze(r)
 from copy import deepcopy
 bad=deepcopy(r);bad['world_preparation_stage_samples'][1]['previous_request_tail']['report_append_end_ns']=0
 try:analyze(bad)
 except AssertionError:pass
 else:raise AssertionError('Invalid report tail accepted')
 out['negative_control_rejected']=True;Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],out['rows']);print(out['largest'][:3])

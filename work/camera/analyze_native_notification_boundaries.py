"""Native semaphore wait versus Python return, exact notification identities."""
import json,sys
from pathlib import Path

def analyze(report):
 rows=[]
 for x in report['consumer_boundary_stage_samples']:
  n=x.get('native_notification_get')
  assert n and len(n)==4 and n[3]==x['source_submitted_ns']
  assert x['notification_wait_begin_ns']<=n[0]<=n[1]<=n[2]<=x['dequeued_ns']
  rows.append(dict(refresh=x['refresh'],source_submitted_ns=n[3],kernel_wait_ms=(n[1]-n[0])/1e6,native_post_wait_ms=(n[2]-n[1])/1e6,python_return_ms=(x['dequeued_ns']-n[2])/1e6,total_wait_ms=(x['dequeued_ns']-x['notification_wait_begin_ns'])/1e6))
 assert rows
 shutdown=report['shutdown_evidence']
 assert shutdown['notification_queue_released'] and shutdown['active_contexts_after_close']==0 and shutdown['native_owner_released'] and not shutdown['gpu_thread_alive'] and not shutdown['preparation_thread_alive']
 return dict(result='PASS_NATIVE_NOTIFICATION_BOUNDARIES',samples=len(rows),largest_kernel_waits=sorted(rows,key=lambda x:x['kernel_wait_ms'],reverse=True)[:12],largest_python_returns=sorted(rows,key=lambda x:x['python_return_ms'],reverse=True)[:12],shutdown=shutdown,scope='Native kernel wait and return brackets; Python return includes GIL reacquisition and scheduling. Does not distinguish either cause or prove consistent 60fps.')

if __name__=='__main__':
 result=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

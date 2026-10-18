"""Join native-worker notification publication to dequeue and thread activity."""
import json,sys
from pathlib import Path

def analyze(report):
 publications={x['notification_begin_ns']:x for x in report['worker_submit_stage_samples'] if 'notification_begin_ns' in x}
 row_sources={x['source_dequeued_ns']:x['source_submitted_ns'] for x in report['presentation_samples'] if x.get('native_batch_candidate')}
 evidence=[]
 for boundary in report['consumer_boundary_stage_samples']:
  source=boundary.get('source_submitted_ns',row_sources.get(boundary['dequeued_ns']))
  if source not in publications:continue
  publication=publications[source]
  assert publication['notification_begin_ns']<=publication['notification_end_ns']<=publication['submit_end_ns']
  assert boundary['notification_wait_begin_ns']<=boundary['dequeued_ns']
  assert boundary['notification_wait_cpu_ns'] is not None and boundary['notification_wait_thread_cycles']>=0
  evidence.append(dict(refresh=boundary['refresh'],source_submitted_ns=source,wait_ms=(boundary['dequeued_ns']-boundary['notification_wait_begin_ns'])/1e6,wait_thread_cpu_ms=boundary['notification_wait_cpu_ns']/1e6,wait_thread_cycles=boundary['notification_wait_thread_cycles'],publication_to_dequeue_ms=(boundary['dequeued_ns']-publication['notification_end_ns'])/1e6,notification_ms=(publication['notification_end_ns']-source)/1e6))
 assert evidence
 return dict(result='NOTIFICATION_WAIT_BOUNDARIES_JOINED',samples=len(evidence),largest_waits=sorted(evidence,key=lambda x:x['wait_ms'],reverse=True)[:12],scope='Exact signal timestamp identity; wait includes condition wait and Python reacquisition/scheduling. Low thread activity does not distinguish OS scheduling from GIL wait. CPU clocks may be coarse; no causal attribution.')

if __name__=='__main__':
 result=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

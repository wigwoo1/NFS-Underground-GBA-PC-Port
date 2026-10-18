"""Audit bounded nonblocking GPU command-stream marker telemetry; no scanout claim."""
import json,sys
from pathlib import Path

def verify(report):
 rows=[x for x in report['presentation_samples'] if x.get('native_batch_candidate')]
 assert rows
 for x in rows:
  q=x['gpu_fence_probe']
  assert x['gpu_fence_probe_enabled'], 'Fence probe did not activate'
  assert len(q)==8 and q[6]==0 and 0<=q[0]<=16 and 0<=q[1]<=16
  assert not x['present_completion_barrier'], 'Blocking completion enabled'
 worst=sorted([dict(index=x['native_committed_sample'][4],swap_ms=x['native_present_stage_ns'][1]/1e6,pending_before=x['gpu_fence_probe'][0],pending_after=x['gpu_fence_probe'][1],retired=x['gpu_fence_probe'][2],oldest_pending_ms=x['gpu_fence_probe'][3]/1e6,max_retired_age_ms=x['gpu_fence_probe'][4]/1e6,probe_ms=x['gpu_fence_probe'][7]/1e6) for x in rows],key=lambda x:x['swap_ms'],reverse=True)[:12]
 return dict(result='PASS_NONBLOCKING_FENCE_RECORDS',samples=len(rows),maximum_pending=max(x['gpu_fence_probe'][1] for x in rows),diagnostic_markers_skipped=sum(x['gpu_fence_probe'][5] for x in rows),maximum_probe_ms=max(x['gpu_fence_probe'][7] for x in rows)/1e6,worst_swap=worst,scope='Command-stream marker readiness; ages are observation upper bounds, not GPU execution duration or physical scanout. Zero timeout is established by C source review, not telemetry alone.')

if __name__=='__main__':
 result=verify(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

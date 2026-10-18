"""Native presentation wall time versus actual owner-thread execution cycles."""
import json,sys
from pathlib import Path

def analyze(report):
 rows=[x for x in report['presentation_samples'] if x.get('native_batch_candidate')]
 assert rows
 for x in rows:
  assert x['native_present_cpu_result']==0 and x['native_present_profile_result']==0
  c=x['native_present_thread_cycles'];t=x['native_present_stage_ns']
  assert len(c)==4 and c[3]==7 and all(0<=v<2**64-1 for v in c[:3])
  assert len(t)==3 and all(v>=0 for v in t)
 worst=[dict(index=x['display_index'],stages_ms=[v/1e6 for v in x['native_present_stage_ns']],thread_cycles=x['native_present_thread_cycles'][:3],fence=x.get('gpu_fence_probe')) for x in sorted(rows,key=lambda x:x['native_present_stage_ns'][1],reverse=True)[:20]]
 return dict(result='PASS_NATIVE_PRESENT_EXECUTION_COUNTERS',samples=len(rows),worst_swap=worst,scope='Actual native phase wall times and same-thread execution cycles. Cycles are not converted to time; GPU duration, off-thread driver execution, scheduling and scanout are not measured.')

if __name__=='__main__':
 result=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

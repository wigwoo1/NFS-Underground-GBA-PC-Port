"""Audit retained GPU token attribution and conservative CPU fence observation bounds."""
import json,sys
from pathlib import Path
def analyze(report):
 rows=[];tokens=set()
 for x in report['presentation_samples']:
  if not x.get('native_queued_targets'):continue
  q=x['queued_slot_gpu_query'];t=x['queued_stage_timing'];o=x['queued_fence_observations'];c=x['queued_readiness_thread_cpu']
  assert q[0] and q[0] not in tokens and q[1]==x['epoch'] and 0<=q[2]<3
  tokens.add(q[0]);assert q[3]<=q[4] and t[0]<=q[6]<=q[7]<=t[1] and q[7]<=q[5]<=x['present_end_ns']
  assert t[0]<=t[1]<=t[2]<=t[3]<=o[0]<=o[3]<=o[4]<=t[4] and o[5]>=1 and c[1]>=c[0] and c[1]!=2**64-1
  if o[5]==1:assert o[1]==o[2]==o[6]==o[7]==0
  else:assert o[0]<=o[1]<=o[2]<=o[7]<=o[3] and o[6]<=t[7]
  # Fence state is evaluated somewhere within each driver call. Use call
  # begin/end as conservative bounds, not its return timestamp as exact state.
  rows.append(dict(index=x['display_index'],token=q[0],slot=q[2],polls=o[5],gpu_timestamp_span_ms=(q[4]-q[3])/1e6,draw_wall_ms=(t[1]-t[0])/1e6,readiness_wall_ms=(t[4]-t[3])/1e6,readiness_cpu_ms=(c[1]-c[0])/1e6,last_not_ready_from_wait_begin_ms=(o[1]-t[3])/1e6 if o[1] else None,completion_observation_width_ms=(o[4]-o[1])/1e6 if o[1] else None,max_yield_ms=o[6]/1e6,swap_ms=x['native_present_stage_ns'][1]/1e6))
 assert rows
 return dict(result='PASS_TOKEN_AND_OBSERVATION_ACCOUNTING',records=rows,worst={k:sorted(rows,key=lambda x:x[k],reverse=True)[:5] for k in ('readiness_wall_ms','max_yield_ms','swap_ms','gpu_timestamp_span_ms')},scope='CPU fence status observation bounds, retained frame GPU timestamp differences and coarse thread CPU time. GPU/QPC origins are independent; timestamp span includes submission gaps, not GPU busy time. No scanout or sustained gameplay certification.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out['worst'],indent=2))

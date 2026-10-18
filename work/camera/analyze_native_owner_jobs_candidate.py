"""Attribute owner-job latency without treating wall time as CPU execution."""
import json,sys,statistics,collections
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());costs=collections.defaultdict(list);tails=[]
for row in r['presentation_samples']:
 for kind,key in [('prepare','prepared'),('present','presentation')]:
  result=row.get(key)
  if not result:continue
  t=result['owner_job_timing'];assert t['submitted_ns']<=t['dequeued_ns']<=t['completed_ns']
  poll=t['prior_input_poll'];queue=(t['dequeued_ns']-t['submitted_ns'])/1e6;wall=(t['completed_ns']-t['dequeued_ns'])/1e6
  costs[kind+'_queue'].append(queue);costs[kind+'_execution_wall'].append(wall);costs[kind+'_execution_cpu'].append(t['thread_cpu_ns']/1e6);costs[kind+'_prior_poll_wall'].append((poll['end_ns']-poll['begin_ns'])/1e6)
  if kind=='present':
   n=result['native_present_timing'];assert t['dequeued_ns']<=n['begin_ns']<=n['pumped_ns']<=n['ended_ns']<=t['completed_ns']
   pump=(n['pumped_ns']-n['begin_ns'])/1e6;present=(n['ended_ns']-n['pumped_ns'])/1e6
   costs['window_pump'].append(pump);costs['actual_present_call'].append(present)
   tails.append(dict(index=row['display_index'],queue_ms=queue,execution_ms=wall,cpu_ms=t['thread_cpu_ns']/1e6,pump_ms=pump,actual_present_ms=present,prior_poll_ms=(poll['end_ns']-poll['begin_ns'])/1e6))
out={}
for key,a in costs.items():
 a.sort();out[key]=dict(count=len(a),median_ms=statistics.median(a),p95_ms=a[int((len(a)-1)*.95)],max_ms=max(a))
result=dict(result='MEASURED_NATIVE_OWNER_JOBS',stages=out,largest_present_jobs=sorted(tails,key=lambda x:x['queue_ms']+x['execution_ms'],reverse=True)[:10],scope='Owner queue/execution CPU versus wall/inputpoll/pump/D3Dcall observations; nativecall wall includes driver or descheduling; priorpoll not automatically causal. No scanout/60fps/controller verification')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

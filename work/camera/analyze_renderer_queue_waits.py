"""Join producer queue waits to disjoint measured consumer phases."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());spans=set()
for x in r['presentation_samples']:
 if not x.get('native_transaction_candidate'):continue
 def add(name,a,b):
  assert a<=b
  if a<b:spans.add((a,b,name))
 add('pair_claim_and_ready_wait',x['pair_begin_ns'],x['pair_ready_ns'])
 add('sample_and_native_arguments',x['sample_begin_ns'],x['transaction_begin_ns'])
 # Native draw timestamps derive from draw_complete minus native draw duration.
 draw_end=x['draw_complete_ns'];draw_start=draw_end-x['draw_cpu_ns']
 add('transaction_entry',x['transaction_begin_ns'],draw_start)
 add('native_draw',draw_start,draw_end)
 commit=x['native_commit_stage_ns'];wait=x['native_wait_timing']
 add('deadline_wait_and_commit_entry',draw_end,commit[0])
 add('presentation_commit',commit[0],commit[6])
 add('transaction_return',commit[6],x['transaction_return_ns'])
spans=sorted(spans)
for previous,current in zip(spans,spans[1:]):assert previous[1]<=current[0],(previous,current)
rows=[]
for s in r['worker_submit_stage_samples']:
 if s['space_wait_ns']<=33333333:continue
 a=s['submit_begin_ns'];b=a+s['space_wait_ns'];phases={};related=[]
 for start,end,name in spans:
  duration=max(0,min(b,end)-max(a,start))
  if duration:phases[name]=phases.get(name,0)+duration;related.append(dict(name=name,started_ns=start,completed_ns=end,overlap_ms=duration/1e6))
 covered=sum(phases.values());assert 0<=covered<=b-a
 rows.append(dict(scene_identity=s['scene_identity'],replay=s['replay'],started_ns=a,completed_ns=b,wait_ms=(b-a)/1e6,phases_ms={k:v/1e6 for k,v in phases.items()},unobserved_ms=(b-a-covered)/1e6,consumer_spans=related))
out=dict(long_queue_waits=len(rows),total_wait_ms=sum(x['wait_ms'] for x in rows),phase_totals_ms={name:sum(x['phases_ms'].get(name,0) for x in rows) for name in sorted({name for x in rows for name in x['phases_ms']})},longest=sorted(rows,key=lambda x:x['wait_ms'],reverse=True)[:12],scope='Disjoint consumer host-clock spans overlapping producer queue wait; pair claim/take includes scheduling and result availability, not exclusive preparation computation. Unobserved includes gaps/endpoint paths; no causal scheduler proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='longest'},indent=2));print(json.dumps([{k:v for k,v in x.items() if k!='consumer_spans'} for x in out['longest'][:3]],indent=2))

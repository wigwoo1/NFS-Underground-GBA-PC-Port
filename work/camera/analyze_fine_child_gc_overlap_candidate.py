"""Correlate retained child stage timing and completed GC intervals; no cause claim."""
import json,sys
from pathlib import Path
raw=Path(sys.argv[1]);r=json.loads(raw.read_text());requests=r['world_preparation_stage_samples'];seen=set();events=[];stages=[];fine=0
for request in requests:
 c=request['terminal'][5];g=c.get('child_gc_trace');assert g is not None and g['dropped']==0
 for event in g['rows']:
  key=(event['thread'],event['generation'],event['start_ns'],event['end_ns']);assert key not in seen;seen.add(key);assert key[2]<=key[3];events.append(event)
 if not c.get('fine_trace'):continue
 fine+=1
 def walk(v,path):
  if isinstance(v,dict):
   if all(k in v for k in ('wall_ns','started_ns','completed_ns')):
    a,b=v['started_ns'],v['completed_ns'];assert b-a==v['wall_ns'] and a<=b
    stages.append(dict(older=request['older'],newer=request['newer'],name=v.get('name',path),begin_ns=a,end_ns=b,wall_ms=(b-a)/1e6))
   for k,x in v.items():walk(x,path+'/'+k)
  elif isinstance(v,list):
   for x in v:walk(x,path)
 walk([c['construct_stages'],c['source_setup_stages'],c['sample_timings'][:1]],'first_sample')
for stage in stages:
 a,b=stage['begin_ns'],stage['end_ns'];stage['gc_overlaps']=[dict(generation=e['generation'],duration_ms=(e['end_ns']-e['start_ns'])/1e6,overlap_ms=(min(b,e['end_ns'])-max(a,e['start_ns']))/1e6) for e in events if max(a,e['start_ns'])<min(b,e['end_ns'])]
assert fine and stages
out=dict(result='PASS_RETAINED_FINE_STAGE_GC_INTERVAL_CORRELATION',requests=len(requests),fine_requests=fine,unique_gc_events=len(events),stages=len(stages),largest_stages=sorted(stages,key=lambda x:x['wall_ms'],reverse=True),scope='Complete retained request GC snapshots have no drops or duplicate events. Nested stage overlaps are not additive or exclusive CPU causation. Fine-stage coverage is the selected range and first sample only; no historic-stall recurrence or scanout proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],fine,'fine requests',len(events),'GC events');print(json.dumps(out['largest_stages'][:3],indent=2))

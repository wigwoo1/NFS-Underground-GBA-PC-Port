import json,sys
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads(p.read_text());submissions=r['worker_submit_stage_samples'];preparation=r['world_preparation_stage_samples'];joined=[];unmatched=[]
for x in submissions:
 assert x['submit_begin_ns']<=x['submit_end_ns']
 if x['preparation_pair'] is not None:assert x['preparation_pair'][1]==x['scene_identity']
for job in preparation:
 candidates=[x for x in submissions if x['preparation_pair'] is not None and tuple(y[1] for y in x['preparation_pair'])==(job['older'],job['newer']) and x['submit_begin_ns']<=job['started_ns']]
 if not candidates:unmatched.append((job['older'],job['newer']));continue
 source=max(candidates,key=lambda x:x['submit_begin_ns'])
 joined.append(dict(older=job['older'],newer=job['newer'],source_replay=source['replay'],intentional_pause_overlap_ms=sum(max(0,min(job['started_ns'],q['end_ns'])-max(source['submit_begin_ns'],q['begin_ns'])) for q in r.get('pause_events',[]))/1e6,submit_begin_to_prepare_start_ms=(job['started_ns']-source['submit_begin_ns'])/1e6,submit_wall_ms=(source['submit_end_ns']-source['submit_begin_ns'])/1e6,prepare_wall_ms=(job['completed_ns']-job['started_ns'])/1e6,prepare_cpu_ms=(job['construct_thread_cpu_ns']+job['precompute_thread_cpu_ns'])/1e6))
result=dict(scope='Exact scene-pair join; submit-begin-to-start includes submit and queue delays,not exclusive queue wait; pause-prepared jobs may lack a corresponding submission',submissions=len(submissions),joined_preparation=len(joined),unmatched_preparation=unmatched,largest_start_delays=sorted(joined,key=lambda x:x['submit_begin_to_prepare_start_ms'],reverse=True)[:10],largest_nonpause_start_delays=sorted([x for x in joined if not x['intentional_pause_overlap_ms']],key=lambda x:x['submit_begin_to_prepare_start_ms'],reverse=True)[:10])
p.with_suffix('.submission-timeline.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

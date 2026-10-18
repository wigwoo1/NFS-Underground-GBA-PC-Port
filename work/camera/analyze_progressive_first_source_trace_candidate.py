from pathlib import Path
import json,sys
r=json.loads(Path(sys.argv[1]).read_text());rows=r['world_preparation_stage_samples'];out=[]
for x in rows:
 d=x['terminal'][5];assert len(d['sample_timings'])==x['prepared_sample_count'],'Detailed trace missing'
 if not d['sample_timings']:continue
 first=d['sample_timings'][0];out.append(dict(older=x['older'],newer=x['newer'],construct_ms=(d['constructed_ns']-d['initialized_ns'])/1e6,setup=first['source_setup_stages'],sample=first))
slow=sorted(out,key=lambda x:x['sample']['wall_ns'],reverse=True)[:8]
result=dict(result='PASS_COMPLETE_FIRST_SOURCE_TRACE',requests=len(rows),first_sample_rows=len(out),slowest=slow,scope='Instrumented live traces; publication includes IPC/ack, elapsed ranges include scheduling, not exclusive CPU or sustained cadence proof.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(result['result'])
for x in slow[:3]:
 print('pair',x['older'],x['newer'],'construct',x['construct_ms'])
 print([(y['name'],y['wall_ns']/1e6,y.get('thread_cycles')) for y in x['sample']['source_sample_stages']]);print('assembly',x['sample']['assembly_stages'])

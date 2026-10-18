"""Validate traced first-source hierarchy; cycle counts are never elapsed seconds."""
from pathlib import Path
import json,sys,statistics,collections
r=json.loads(Path(sys.argv[1]).read_text());groups=collections.defaultdict(list);requests=0
for req in r['world_preparation_stage_samples']:
 d=req['terminal'][5];samples=d.get('sample_timings',[])
 if not samples:continue
 requests+=1;first=samples[0]
 def record(prefix,stages,parent=None):
  previous=None
  for stage in stages:
   a,b=stage['started_ns'],stage['completed_ns'];assert b>=a and stage['thread_cycles']>=0
   assert stage['wall_ns']==b-a
   if previous is not None:assert a==previous
   if parent is not None:assert parent['started_ns']<=a<=b<=parent['completed_ns']
   previous=b;groups[prefix+stage['name']].append(dict(wall_ns=b-a,cycles=stage['thread_cycles']))
 record('setup/',d['source_setup_stages'])
 record('first/',first['source_sample_stages'],first)
 world=next(s for s in first['source_sample_stages'] if s['name']=='world_sample')
 assembly=first['assembly_stages'];record('world/',assembly,world)
 main=next(s for s in assembly if s['name']=='main_graph_surfaces')
 record('wall/',main['visibility_stages'],main)
assert requests and all(len(v)==requests for v in groups.values())
summary={k:dict(count=len(v),mean_wall_ms=statistics.mean(x['wall_ns'] for x in v)/1e6,median_wall_ms=statistics.median(x['wall_ns'] for x in v)/1e6,mean_cycles=statistics.mean(x['cycles'] for x in v),total_cycles=sum(x['cycles'] for x in v)) for k,v in groups.items()}
out=dict(result='PASS_FIRST_SOURCE_CYCLE_TRACE_HIERARCHY',requests=requests,summary=summary,scope='Saved trace hierarchy and complete first-source group coverage. Group levels overlap and must not be summed together. Cycles identify execution cost, not fixed-frequency elapsed time; saved diagnostic run is not current matched performance or fullscene fidelity proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],requests)
for prefix in ['setup/','first/','world/','wall/']:
 print(prefix,sorted([(k,v['mean_cycles'],v['mean_wall_ms']) for k,v in summary.items() if k.startswith(prefix)],key=lambda x:x[1],reverse=True)[:4])

from pathlib import Path
import json,sys,statistics
r=json.loads(Path(sys.argv[1]).read_text());values={};rows=[]
for request in r['world_preparation_stage_samples']:
 d=request['terminal'][5];stages=d['construct_stages'];assert stages
 assert all(s['wall_ns']==s['completed_ns']-s['started_ns'] and s['wall_ns']>=0 for s in stages)
 assert all(a['completed_ns']==b['started_ns'] for a,b in zip(stages,stages[1:]))
 assert sum(s['wall_ns'] for s in stages)==stages[-1]['completed_ns']-stages[0]['started_ns']
 for s in stages:
  values.setdefault(s['name'],[]).append(s['wall_ns'])
  assert s.get('road_advance_stage_dropped',0)==0
 rows.append(dict(older=request['older'],newer=request['newer'],wall_ms=sum(s['wall_ns'] for s in stages)/1e6,stages=stages))
out=dict(result='PASS_COMPLETE_CONSTRUCTION_PARTITIONS',requests=len(rows),summary={k:dict(mean_ms=statistics.mean(v)/1e6,max_ms=max(v)/1e6,total_ms=sum(v)/1e6) for k,v in values.items()},slowest=sorted(rows,key=lambda x:x['wall_ms'],reverse=True)[:8],scope='Exact contiguous construction elapsed partitions with cycle counters; includes scheduling, no exclusive CPU or live cadence claim.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result']);print(json.dumps(out['summary'],indent=2))

import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=[]
for request in r['world_preparation_stage_samples']:
 for stage in request['child_stages']['construct_stages']:
  if stage['name']=='newer_road_assets':
   phases=stage.get('asset_stages',[])
   assert all(p['started_ns']<=p['completed_ns'] and p['wall_ns']==p['completed_ns']-p['started_ns'] for p in phases)
   rows.append(dict(older=request['older'],newer=request['newer'],asset_ms=stage['wall_ns']/1e6,**{p['name']+'_ms':p['wall_ns']/1e6 for p in phases}))
assert rows
keys=set.intersection(*(set(x) for x in rows))-{'older','newer'}
out=dict(result='PASS_RETAINED_ASSET_COSTS',requests=len(rows),stats={k:dict(median=statistics.median(x[k] for x in rows),maximum=max(x[k] for x in rows)) for k in sorted(keys)},rows=rows,scope='Last retained preparation window only; different runs are not matched causal cadence proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))

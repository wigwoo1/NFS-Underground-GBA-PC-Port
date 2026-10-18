import json,statistics
from pathlib import Path
sources=['work/camera/prototype-runs/owned-native-1791639240764589700.json','work/camera/prototype-runs/owned-native-1791640884023146000.json']
rows=[];groups={}
for source in sources:
 report=json.loads(Path(source).read_text())
 for job in report['world_preparation_stage_samples']:
  d=job['terminal'][5]
  if not d['fine_trace']:continue
  assert d['clean_request_close'] and d['constructed_ns']>=d['initialized_ns']
  values=[]
  for stage in d['construct_stages']:
   assert stage['started_ns']<=stage['completed_ns'] and stage['wall_ns']==stage['completed_ns']-stage['started_ns']
   ms=stage['wall_ns']/1e6;groups.setdefault(stage['name'],[]).append(ms)
   for nested in stage.get('asset_stages',[]):
    assert nested['started_ns']<=nested['completed_ns'] and nested['wall_ns']==nested['completed_ns']-nested['started_ns']
    groups.setdefault(stage['name']+':'+nested['name'],[]).append(nested['wall_ns']/1e6)
   values.append(dict(name=stage['name'],ms=ms,cycles=stage.get('thread_cycles')))
  first=d['sample_transfer_rows'][0]
  rows.append(dict(raw=source,older=job['older'],newer=job['newer'],geometry_selected=d.get('geometry_input_selected',False),construct_ms=(d['constructed_ns']-d['initialized_ns'])/1e6,first_ready_ms=(first['ready_ns']-d['constructed_ns'])/1e6,stages=values))
assert len(rows)>=16
summary=sorted([dict(name=k,median_ms=statistics.median(v),max_ms=max(v),samples=len(v)) for k,v in groups.items()],key=lambda x:x['median_ms'],reverse=True)
out=dict(result='PASS_CURRENT_CONSTRUCTION_STAGE_ACCOUNTING',pairs=len(rows),summary=summary,rows=rows,scope='Completed fine-profile jobs across two live source ranges; different input selection/profiling runs, not a matched optimization comparison. Wall scopes include scheduling, nested costs not exclusive.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/current-construction-stages.json').write_text(json.dumps(out,indent=2));print(out['result'],out['pairs']);print(summary)

"""Locate active GC intervals within recorded preparation stages."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());commits=[x['native_committed_sample'][6] for x in r['presentation_samples'] if x.get('native_committed_sample')];assert commits
stages=[]
def walk(v,path,owner):
 if isinstance(v,dict):
  owner=v.get('thread_id',owner)
  if isinstance(v.get('started_ns'),int) and isinstance(v.get('completed_ns'),int):stages.append((path,v,owner))
  for k,x in v.items():
   if isinstance(x,(list,dict)):walk(x,path+'/'+k,owner)
 elif isinstance(v,list):
  for i,x in enumerate(v):walk(x,path+'/'+str(i),owner)
walk(r['world_preparation_stage_samples'],'preparation',None)
collections=[]
for g in r['gc_collection_samples']:
 if g['generation']!=2 or not(g['start_ns']<commits[-1] and g['end_ns']>commits[0]):continue
 matches=[]
 for path,s,owner in stages:
  if owner!=g['thread_id']:continue
  overlap=max(0,min(s['completed_ns'],g['end_ns'])-max(s['started_ns'],g['start_ns']))
  if overlap:matches.append(dict(path=path,name=s.get('name'),overlap_ms=overlap/1e6,stage_ms=(s['completed_ns']-s['started_ns'])/1e6))
 matches.sort(key=lambda x:(-len(x['path'].split('/')),x['stage_ms']))
 collections.append(dict(collection=g,duration_ms=(g['end_ns']-g['start_ns'])/1e6,deepest_stages=matches[:5],located_in_preparation=bool(matches)))
out=dict(result='OBSERVED',gc_dropped=r['gc_trace_dropped'],collections=sorted(collections,key=lambda x:x['duration_ms'],reverse=True),scope='Generation2 intervals overlapping first/last presentation, including pauses; same-thread preparation interval overlap, nested stages overlap and must not be summed; unlocated does not prove absence of renderer/producer work')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps([{k:v for k,v in x.items() if k!='collection'} for x in out['collections'][:5]],indent=2))

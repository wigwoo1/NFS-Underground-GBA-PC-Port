"""Extract bounded nested preparation costs from the captured worst pair."""
import json,sys
from pathlib import Path
cp=Path(sys.argv[1]);r=json.loads((cp/'current-stalls.json').read_text());s=r['largest'][0]['preparation']['stages']
rows=[]
def walk(v,path=''):
 if isinstance(v,dict):
  if 'name' in v and 'wall_ns' in v:rows.append(dict(path=path,name=v['name'],wall_ms=v['wall_ns']/1e6,thread_cpu_ms=None if 'thread_cpu_ns' not in v else v['thread_cpu_ns']/1e6,count=v.get('count')))
  for k,x in v.items():walk(x,path+'/'+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):walk(x,path+'/'+str(i))
walk(s)
r=dict(pair=[s['older'],s['newer']],rows=sorted(rows,key=lambda x:x['wall_ms'],reverse=True),scope='Nested intervals overlap; wall time includes scheduling. Not an additive exclusive CPU profile.')
(cp/'nested-preparation-costs.json').write_text(json.dumps(r,indent=2));print(json.dumps(r['rows'][:24],indent=2))

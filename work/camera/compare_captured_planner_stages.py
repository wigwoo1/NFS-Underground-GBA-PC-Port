"""Compare fixture planner values and expose source preparation stage costs."""
import json,sys
from pathlib import Path
cp=Path(sys.argv[1]); old=Path(sys.argv[2]); differences=[]
def walk(a,b,path=''):
 if type(a)!=type(b):differences.append(dict(path=path,older=a,newer=b));return
 if isinstance(a,dict):
  for k in sorted(a.keys()|b.keys()):
   if k not in a or k not in b:differences.append(dict(path=path+'/'+k,older=a.get(k),newer=b.get(k)))
   else:walk(a[k],b[k],path+'/'+k)
 elif isinstance(a,list):
  if len(a)!=len(b):differences.append(dict(path=path+'/length',older=len(a),newer=len(b)))
  for i,(x,y) in enumerate(zip(a,b)):walk(x,y,path+'/'+str(i))
 elif a!=b:differences.append(dict(path=path,older=a,newer=b))
walk(json.loads((old/'road-history.json').read_text()),json.loads((cp/'scene-inputs/road-history.json').read_text()))
old_history=json.loads((old/'road-history.json').read_text());new_history=json.loads((cp/'scene-inputs/road-history.json').read_text())
old_map=dict(old_history['scratch']['rows']);new_map=dict(new_history['scratch']['rows']); map_equal=old_map==new_map
stalls=json.loads((cp/'current-stalls.json').read_text()); rows=[]
for gap in stalls['largest']:
 s=gap['preparation']['stages']; stages=[]
 for sample in s['sample_timings']:
  for stage in sample['assembly_stages']:
   stages.append(dict(alpha=sample['alpha'],name=stage['name'],wall_ms=stage['wall_ns']/1e6,thread_cpu_ms=stage['thread_cpu_ns']/1e6,cycles=stage['thread_cycles']))
 rows.append(dict(display_index=gap['display_index'],pair=[s['older'],s['newer']],construct_ms=s['construct_advance_ns']/1e6,precompute_ms=s['precompute_ns']/1e6,largest_assembly_stages=sorted(stages,key=lambda x:x['wall_ms'],reverse=True)[:12]))
r=dict(planner_address_depth_maps_equal=map_equal,planner_differences=differences,live_stages=rows,scope='Exact parsed planner comparison; nested stage wall times include scheduling and are not additive or exclusive CPU causes.')
(cp/'planner-and-stages.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))


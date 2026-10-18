import json,sys,statistics,collections
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());groups=collections.defaultdict(list)
for row in r['presentation_samples']:
 for x in (row.get('prepared') or {}).get('consumer_stages',[]):
  name=x['stage']
  if name.startswith('texture_'):
   identity=x['identity'];category='material' if identity<1000 else ('sky' if identity in (1001,1002) else 'hud')
   assert x['thread_cycles']>=0
   name=category+'/'+name
  elif name not in ('world_packet_copy_convert','material_packet_copy'):continue
  assert x['elapsed_ns']>=0;groups[name].append(dict(ms=x['elapsed_ns']/1e6,index=row['display_index'],cycles=x.get('thread_cycles')))
assert groups
def stats(v):
 a=sorted(x['ms'] for x in v);return dict(count=len(a),median_ms=statistics.median(a),p95_ms=a[min(len(a)-1,int(len(a)*.95))],max_ms=a[-1],largest=sorted(v,key=lambda x:x['ms'],reverse=True)[:5])
out=dict(result='PASS_MATERIAL_SUBSTAGE_TELEMETRY',groups={k:stats(v) for k,v in groups.items()},scope='Nested pertexture wall intervals, do not sum with enclosing stage. Profiling overhead included, cycles not elapsed CPU time, no driver or GIL causal attribution/visible cadence proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2))
for k,v in out['groups'].items():print(k,{a:b for a,b in v.items() if a!='largest'})

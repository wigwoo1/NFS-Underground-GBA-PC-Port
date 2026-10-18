"""Summarize actual native road edge UV trace at classified near events."""
import csv,hashlib,json,math,sys
from pathlib import Path
manifest=Path(sys.argv[1]);s=json.loads(manifest.read_text(encoding='utf-8-sig'));prefix=s['prefix'];gpu_path=Path(prefix+'-dense-near-events-gpu-audit.json');gpu=json.loads(gpu_path.read_text());checks=[]
for item in gpu['checks']:
 event=item['event']; endpoints=[];edge_sets=[]
 for endpoint in item['endpoints']:
  path=Path(prefix+f"-dense-{endpoint['index']:02d}-near-{endpoint['ordinal']}-isolated.ppm.edges.csv");raw=path.read_bytes();rows=list(csv.DictReader(raw.decode().splitlines()));edges={}
  for row in rows:
   assert int(row['ring'])==endpoint['ordinal'];edge=int(row['edge']);assert edge not in edges;values={k:float(row[k]) for k in ['z0','z1','u','v','x0','y0','x1','y1']};assert all(math.isfinite(v) for v in values.values());crossing=(values['z0']<64)!=(values['z1']<64);assert crossing==bool(int(row['crossing']));edges[edge]=values|dict(crossing=crossing)
  assert bool(rows)==(event['identity'][0]==1), 'Road source attributes must be traced; wall generic path intentionally has no corrected-road trace'
  endpoints.append(dict(index=endpoint['index'],trace_sha256=hashlib.sha256(raw).hexdigest(),edges=len(rows),crossing_edges=sum(e['crossing'] for e in edges.values())));edge_sets.append(edges)
 changes=[]
 for edge in edge_sets[0].keys()&edge_sets[1].keys():
  a,b=edge_sets[0][edge],edge_sets[1][edge]
  if a['crossing'] and b['crossing']:changes.append(dict(edge=edge,uv_step=math.hypot(b['u']-a['u'],b['v']-a['v']),from_uv=[a['u'],a['v']],to_uv=[b['u'],b['v']]))
 checks.append(dict(event=event,endpoints=endpoints,persistent_clipped_edges=changes))
out=Path(prefix+'-dense-near-edge-trace-audit.json');out.write_text(json.dumps(dict(result='AUDITED',gpu_report_sha256=hashlib.sha256(gpu_path.read_bytes()).hexdigest(),checks=checks,scope='Finite actual native corrected-road generated UVs and exact depth-mask classification at event endpoints. Persistent edge UV steps measured, with no arbitrary smoothness tolerance. Walls use generic texture clip and produce no corrected-road trace. Neither topology-transition UV limits nor wall continuity verified.'),indent=2));print(json.dumps(dict(report=str(out),road_endpoint_traces=sum(e['edges']>0 for c in checks for e in c['endpoints']),persistent_clipped_edges=sum(len(c['persistent_clipped_edges']) for c in checks))))

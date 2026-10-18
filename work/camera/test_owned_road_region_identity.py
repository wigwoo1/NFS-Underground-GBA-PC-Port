import json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_motion_pairs import records
from owned_wall_region_candidates import regions
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);checks=[]
for f in r['wall_diagnostic_frames']:
 c=ClosedGraph.decode(Path(f['graph']).read_bytes());graph=c.graph;rings={};at=0
 while at<len(graph.geometry):
  identifier,n,_,_=struct.unpack_from('<4I',graph.geometry,at);desc=graph.geometry[at+16:at+64];at+=64;ring=graph.geometry[at:at+n*68];at+=n*68;rings[identifier]=(desc,ring)
 queue=regions(graph,table);roads=[]
 for i,row in enumerate(records(Path(f['regenerated']).read_bytes())['records']):
  if row['kind']!=1:continue
  matches=[d for d,(desc,ring) in rings.items() if desc==bytes(row['blocks'][9]) and ring==bytes(row['blocks'][0])]
  assert len(matches)==1
  owner=matches[0];bounds=struct.unpack('<4H',row['blocks'][5]);visits=[ordinal for ordinal,q in enumerate(queue) if q[0]==owner and tuple(q[1:5])==bounds and not q[5]&8];assert len(visits)==1
  roads.append(dict(record_index=i,descriptor=owner,ordinal=visits[0],bounds=bounds))
 checks.append(dict(refresh=c.refresh,roads=roads))
out=dict(result='PASS_OWNED_ROAD_REGION_IDENTITIES',checks=checks,scope='Captured raw descriptor/ring/portal-bound ownership for road placement, without screen matching. Newly visible road geometry remains a separate dependency.')
Path('work/camera/owned-road-region-identity-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],sum(len(x['roads']) for x in checks))

from pathlib import Path
from owned_scene_bundle import chunks
from owned_object_filter import depth_distance
exec(compile(Path('work/camera/test_supplemental_visit_order.py').read_text(),'fixture','exec'))
from owned_motion_pairs import records
result=[]
for endpoint in (0,1):
 scene=scenes[endpoint];ordinary=[]
 for h,raw in chunks(scene.objects,'graph_objects'):
  for i in range(h[5]):
   index=struct.unpack_from('<I',raw,128+i*168)[0];source=raw[132+i*168:296+i*168]
   if index==0:ordinary.append(dict(parent=h[3],object=index,depth_distance=depth_distance(source,scene.graph.context[256:304])))
 candidates=pair.sample(endpoint);queue=portal.sample(endpoint);rows=records(frames[endpoint])['records'];model_index=next(i for i,x in enumerate(rows) if x['kind']==3);after=[]
 for row in rows[model_index+1:]:
  if row['kind']==2:
   after.append([dict(descriptor=w.descriptor,edge=w.edge) for w in pair.assets[endpoint] if w.vertices==bytes(row['blocks'][0])])
 result.append(dict(refresh=scene.refresh,ordinary=ordinary,visits=[dict(ordinal=i,region=q) for i,q in enumerate(queue) if q[0] in {x['parent'] for x in ordinary}],supplemental=[dict(parent=c.parent,object=c.object,descriptor=c.descriptor,ordinal=c.ordinal,distance=c.distance) for c in candidates],records_after_model=after))
(folder/'ordinary-depth-order-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

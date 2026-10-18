import runpy,struct
from pathlib import Path
from owned_model_builder_inputs import OwnedModelBuilders
from owned_scenery_projection import SceneryProjection
v=runpy.run_path('work/camera/audit_model_owner_boundary.py');projection=SceneryProjection(v['rom']);owners=[]
for endpoint,scene in enumerate(v['v']['scenes']):
 builders=OwnedModelBuilders((v['v']['folder']/(('older','newer')[endpoint]+'.builders.bin')).read_bytes());base=struct.unpack_from('<I',scene.graph.context,60)[0];matrix_base=struct.unpack_from('<I',scene.graph.context,252)[0];resolved=[]
 for index,row in [(i,r) for i,r in enumerate(v['records'](v['v']['frames'][endpoint])['records']) if r['kind']==3]:
  matches=[]
  for owner,visit in v['v']['visits'][endpoint].items():
   if not visit['allocated']:continue
   address=visit['dispatch']['descriptor']-0x08000000
   if bytes(row['blocks'][1])!=v['rom'][address:address+40]:continue
   if visit['dispatch']['model']==7:matches.append(owner);continue
   builder=builders.at(base+owner*164,matrix_base+visit['source'][136]*48,scene.refresh)
   if projection.matrix(builder.camera,builder.source,builder.initial_matrix)==bytes(row['blocks'][2]):matches.append(owner)
  assert len(matches)==1,(endpoint,index,matches);resolved.append(matches[0])
 assert len(set(resolved))==len(resolved);owners.append(resolved)
print('PASS exact source-builder model ownership, shared descriptor resolved',owners)


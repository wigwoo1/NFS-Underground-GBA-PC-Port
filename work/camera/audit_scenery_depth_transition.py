"""Distinguish source loss, slot loss and camera-depth visibility transitions."""
import sys,runpy,struct
sys.argv=['audit','work/camera/prototype-runs/fullscene-failure-1791283235984215700']
v=runpy.run_path('work/camera/audit_failed_model_association.py')
from owned_scene_bundle import chunks
from owned_object_filter import depth_distance,eligibility
from owned_object_dispatch import select
findings=[]
for endpoint,scene in enumerate(v['scenes']):
 found=[]
 for h,raw in chunks(scene.objects,'graph_objects'):
  for i in range(h[5]):
   index=struct.unpack_from('<I',raw,128+i*168)[0]
   if index!=31:continue
   found.append((h[3],index));source=raw[132+i*168:296+i*168];depth,distance,horizontal=depth_distance(source,scene.graph.context[256:304])
   print('SOURCE_VISIBILITY',dict(endpoint=endpoint,source_refresh=scene.graph.refresh,object=index,parent=h[3],slot=source[136],eligibility=eligibility(source),depth=depth,horizontal=horizontal,dispatch=select(source,scene.graph.context[:256],depth),queue=[q for q in v['portal'].sample(endpoint) if q[0]==h[3]]))
 findings.append(found)
assert findings[0]==[(29,31)] and findings[1]==[], findings
import json
out={'source':31,'older_chain_memberships':findings[0],'newer_chain_memberships':findings[1],'conclusion':'Newer source not captured; depth/slot disappearance cannot be reconstructed from this fixture','held_pose_allowed':False,'full_scene_verified':False}
print(json.dumps(out,indent=2))

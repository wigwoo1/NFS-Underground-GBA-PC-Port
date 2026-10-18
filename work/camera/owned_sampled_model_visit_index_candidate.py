"""Sampled single ordinary-model visit from owned endpoint chains and rigid pose."""
import struct
from owned_ordinary_model_visits import ordinary_model_visits
from owned_spatial_descriptors import SpatialDescriptors
from owned_object_filter import depth_distance

def sampled_model_visit(pair,alpha,object_index=None):
 if object_index in getattr(pair,'_external_visits',{}):return pair._external_visits[object_index].sample(alpha,pair.portal.sample(alpha))
 if not hasattr(pair,'_ordinary_visit_cache'):
  pair._ordinary_visit_cache=tuple(ordinary_model_visits(scene,pair.portal.sample(i),hasattr(pair,'_scenery_record_pairs')) for i,scene in enumerate(pair.scenes))
  if getattr(pair,'_scenery_deactivation',{}) or getattr(pair,'_scenery_depth_exit',set()) or getattr(pair,'_scenery_portal_exit',set()):
   from owned_removed_scenery_visit import removed_scenery_visit,depth_hidden_scenery_visit,portal_hidden_scenery_visit
   old,new=pair.portal.motion.scene_pair
   queues=[pair.portal.sample(i) for i in (0,1)]
   extra=tuple(removed_scenery_visit(old,new,*queues,index) for index in pair._scenery_deactivation)+tuple(depth_hidden_scenery_visit(old,new,*queues,index) for index in pair._scenery_depth_exit)+tuple(portal_hidden_scenery_visit(old,new,*queues,index) for index in pair._scenery_portal_exit)
   pair._ordinary_visit_cache=(pair._ordinary_visit_cache[0],pair._ordinary_visit_cache[1]+extra)
  pair._ordinary_spatial=SpatialDescriptors(pair.scenes[0].graph)
 endpoint_visits=pair._ordinary_visit_cache
 if object_index is not None:
  if not hasattr(pair,'_ordinary_visit_object_index'):
   groups=[]
   for visits in pair._ordinary_visit_cache:
    grouped={}
    for visit in visits:grouped.setdefault(visit['object'],[]).append(visit)
    groups.append({key:tuple(value) for key,value in grouped.items()})
   pair._ordinary_visit_object_index=tuple(groups)
  endpoint_visits=tuple(group.get(object_index,()) for group in pair._ordinary_visit_object_index)
 if alpha in (0,1):
  endpoint=endpoint_visits[int(alpha)]
  if len(endpoint)!=1:raise ValueError('Unverified endpoint ordinary model population')
  return dict(endpoint[0],dispatch=dict(endpoint[0]['dispatch']))
 if any(len(x)!=1 for x in endpoint_visits):raise ValueError('Unverified ordinary model population')
 a,b=(x[0] for x in endpoint_visits)
 if a['object']!=b['object'] or any(a['dispatch'].get(k)!=b['dispatch'].get(k) for k in ('kind','model','variant','descriptor')):raise ValueError('Ordinary model identity transition')
 if alpha in (0,1):return dict(endpoint_visits[int(alpha)][0],dispatch=dict(endpoint_visits[int(alpha)][0]['dispatch']))
 _,camera,_=pair.portal.motion.sample(alpha)
 raw_points=[tuple(struct.unpack_from('<i',visit['source'],12+i*4)[0]>>8 for i in range(3)) for visit in (a,b)]
 # Pose translation is linear in original rigid sampler; preserve raw endpoint
 # position floor corrections used by original association/depth queries.
 world=tuple((1-alpha)*raw_points[0][i]+alpha*raw_points[1][i] for i in range(3))
 spatial=pair._ordinary_spatial
 # Scenery draw ownership comes from original region object chains. Its mesh
 # origin need not lie inside that region (verified at both source endpoints).
 # Keep an unchanged owned chain association while sampling its moving pose.
 model=a['dispatch']['model']
 if 30<=model<=36 and a['parent']==b['parent']:
  parent=a['parent']
 else:
  if 30<=model<=36:
   for endpoint,expected in zip(raw_points,(a['parent'],b['parent'])):
    selected=spatial.select(a['parent'],(endpoint[0],endpoint[2]))
    if selected==65535:selected=spatial.fallback(a['parent'],(endpoint[0],endpoint[2]))
    if selected!=expected:raise ValueError('Unverified scenery association transition')
  parent=spatial.select(a['parent'],(world[0],world[2]))
  if parent==65535:parent=spatial.fallback(a['parent'],(world[0],world[2]))
 if parent==65535:raise ValueError('Sampled ordinary association unresolved')
 visits=[(i,q) for i,q in enumerate(pair.portal.sample(alpha)) if q[0]==parent and not q[5]&0x88]
 if not visits:
  if object_index in getattr(pair,'_scenery_portal_exit',set()):return None
  raise ValueError('Sampled ordinary model outside owned visits')
 ordinal,q=visits[-1]
 def projected(point,m):
  x,z=point[0]+m[9],point[2]+m[11]
  return x*m[2]+z*m[8],x*m[0]+z*m[6]
 now=projected(world,camera);raw_depths=[depth_distance(v['source'],s.graph.context[256:304]) for v,s in zip((a,b),pair.scenes)];ideals=[projected(point,m) for point,m in zip(raw_points,pair.portal.endpoints)]
 depth,horizontal=(now[k]+(1-alpha)*(raw_depths[0][0 if k==0 else 2]-ideals[0][k])+alpha*(raw_depths[1][0 if k==0 else 2]-ideals[1][k]) for k in range(2))
 if depth<=0:
  if object_index in getattr(pair,'_scenery_depth_exit',set()):return None
  raise ValueError('Sampled ordinary model depth transition')
 if depth>=8192:
  if object_index in getattr(pair,'_scenery_far_exit',set()):return None
  raise ValueError('Unverified ordinary far-depth transition')
 distance=(depth*depth+horizontal*horizontal)/256
 distance+=(1-alpha)*(a['distance']-(raw_depths[0][0]**2+raw_depths[0][2]**2)/256)+alpha*(b['distance']-(raw_depths[1][0]**2+raw_depths[1][2]**2)/256)
 if not 0<=distance<2147483648:raise ValueError('Unverified ordinary distance wrap')
 result=dict(a,dispatch=dict(a['dispatch']),ordinal=ordinal,parent=parent,bounds=tuple(q[1:5]),depth=depth,distance=distance)
 return result







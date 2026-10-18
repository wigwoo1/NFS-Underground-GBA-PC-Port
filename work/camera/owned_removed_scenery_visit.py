"""Preparation-only visit for an original removed source, never a live draw allocation."""
import struct
from owned_ordinary_model_visits import ordinary_model_visits
from owned_object_filter import depth_distance,eligibility
from owned_object_dispatch import select

def removed_scenery_visit(older,newer,old_queue,new_queue,index):
 return absent_scenery_visit(older,newer,old_queue,new_queue,index,False)

def depth_hidden_scenery_visit(older,newer,old_queue,new_queue,index):
 return absent_scenery_visit(older,newer,old_queue,new_queue,index,True)

def absent_scenery_visit(older,newer,old_queue,new_queue,index,depth_hidden):
 matches=[v for v in ordinary_model_visits(older.graph,old_queue) if v['object']==index]
 if len(matches)!=1 or newer.sources is None:raise ValueError('Missing removed source ownership')
 ref=matches[0];base=struct.unpack_from('<I',newer.graph.graph.context,60)[0];address=base+index*164
 source=newer.sources.sources.get(address);event=newer.sources.removals.get(address)
 if source is None:raise ValueError('Missing hidden scenery source')
 depth,distance,_=depth_distance(source,newer.graph.graph.context[256:304])
 if depth_hidden:
  if source[136]==255 or eligibility(source)!='project' or depth>0:raise ValueError('Unverified depth-hidden scenery source')
 elif event is None or not older.graph.graph.refresh<event[0]<=newer.graph.graph.refresh or event[1]!=0x0801e4c2:raise ValueError('Missing current original removal event')
 if not depth_hidden and source[136]!=255:raise ValueError('Removed source slot remains allocated')
 model=struct.unpack_from('<h',source,54)[0]
 if not 30<=model<=36 or model!=ref['dispatch']['model']:raise ValueError('Removed scenery identity changed')
 scratch=bytearray(source);scratch[136]=0
 depth,distance,_=depth_distance(source,newer.graph.graph.context[256:304]);dispatch=select(scratch,newer.graph.graph.context[:256],depth)
 if (not depth_hidden and depth<=0) or any(dispatch.get(k)!=ref['dispatch'].get(k) for k in ('kind','model','variant','descriptor')):raise ValueError('Unverified removed scenery projection')
 regions=[(i,q) for i,q in enumerate(new_queue) if q[0]==ref['parent'] and not q[5]&0x88]
 if not regions:raise ValueError('Removed scenery parent outside owned portal coverage')
 ordinal,q=regions[-1]
 return dict(ref,source=source,allocated=depth_hidden,dispatch=dispatch,depth=depth,distance=distance,ordinal=ordinal,bounds=tuple(q[1:5]))






def portal_hidden_scenery_visit(older,newer,old_queue,new_queue,index):
 """Preparation candidate from an unchanged chain outside newer portal coverage."""
 from owned_scene_bundle import chunks
 matches=[v for v in ordinary_model_visits(older.graph,old_queue) if v['object']==index]
 if len(matches)!=1 or newer.sources is None:raise ValueError('Missing portal-exit source ownership')
 ref=matches[0];base=struct.unpack_from('<I',newer.graph.graph.context,60)[0]
 source=newer.sources.sources.get(base+index*164)
 if source is None or source[136]==255 or eligibility(source)!='project':raise ValueError('Unverified portal-exit allocation')
 depth,distance,_=depth_distance(source,newer.graph.graph.context[256:304])
 if depth<=0 or struct.unpack_from('<H',source,10)[0]&16:raise ValueError('Unverified portal-exit source visibility')
 chain=[]
 for h,raw in chunks(newer.graph.objects,'graph_objects'):
  for i in range(h[5]):
   if struct.unpack_from('<I',raw,128+i*168)[0]==index:chain.append((h[3],i,raw[132+i*168:296+i*168]))
 if chain!=[(ref['parent'],ref['position'],source)]:raise ValueError('Portal-exit chain identity changed')
 if any(q[0]==ref['parent'] and not q[5]&0x88 and q[1]<=q[2] and q[3]<=q[4] for q in new_queue):raise ValueError('Portal-exit parent remains visible')
 dispatch=select(source,newer.graph.graph.context[:256],depth)
 if not 30<=dispatch.get('model',-1)<=36 or any(dispatch.get(k)!=ref['dispatch'].get(k) for k in ('kind','model','variant','descriptor')):raise ValueError('Portal-exit model identity changed')
 # Bounds belong to the older owned portal; used only to prepare asset records.
 # Fractional draw eligibility and bounds come from sampled portal traversal.
 return dict(ref,source=source,allocated=True,dispatch=dispatch,depth=depth,distance=distance)

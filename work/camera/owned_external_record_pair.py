"""Complete source-owned external record pair with original builder activation."""
from owned_external_model_visit import PreparedExternalModelVisit
from owned_external_record_candidate import external_record_candidate
from owned_external_model_owners import external_model_owners
from owned_scenery_record_pairs import SceneryRecordPair
from owned_model_assets import model_palette_equivalent
from owned_motion_pairs import records
import struct

def prepare_external_record_pair(scenes,queues,frames,rom,index,endpoint_owners=None):
 closed=tuple(s.graph for s in scenes)
 visit=PreparedExternalModelVisit(closed,tuple(s.sources for s in scenes),index,rom)
 blocks=[];visible=[];portal_exit=False
 for endpoint,scene in enumerate(scenes):
  hidden_depth=False;sampled=visit.sample(endpoint,queues[endpoint])
  if sampled is None:
   # A proven old region supplies assets only, never visibility in the new queue.
   if endpoint!=1 or not blocks:raise ValueError('Missing external candidate portal')
   parent=visit.visits[1][0][0]
   active=[q for q in queues[1] if q[0]==parent and not q[5]&0x88 and q[1]<=q[2] and q[3]<=q[4]]
   if active:
    if visit.motion.matrix(1)[11]>=0:raise ValueError('Unverified external hidden depth')
    region=active[-1];hidden_depth=True
   else:
    retained=visit.sample(0,queues[0])
    if retained is None:raise ValueError('Missing retained external asset region')
    retained_region=queues[0][retained['ordinal']]
    # A missing parent can coincide with source-projection exit. When the
    # original source flag selects depth-independent materials, rebuild only
    # the hidden endpoint assets from retained bounds; visit.sample still
    # applies the newer pose, current queue, and per-vertex depth gate.
    raw=visit.visits[1][1]
    if visit.motion.matrix(1)[11]<0:
     if not struct.unpack_from('<H',raw,10)[0]&2:raise ValueError('Unsupported external projection-exit material')
     region=(parent,*retained_region[1:]);hidden_depth=True
    else:
     # The unique newer object chain owns parent identity. Retained bounds
     # supply asset context only; sampled visibility always uses current queue.
     region=(parent,*retained_region[1:]);portal_exit=True
  else:region=queues[endpoint][sampled['ordinal']]
  candidate=external_record_candidate(scene.graph,scene.sources,index,region,rom,hidden_depth=hidden_depth)
  owners=endpoint_owners[endpoint] if endpoint_owners is not None else external_model_owners(scene.graph,scene.builders,frames[endpoint],rom)
  matches=[row for row,owner in owners.items() if owner==index]
  if len(matches)>1:raise ValueError('Repeated external owned record')
  if matches:
   original=records(frames[endpoint])['records'][matches[0]]['blocks']
   if any(candidate[k]!=bytes(original[k]) for k in range(11)) or not model_palette_equivalent(candidate,bytes(original[11])):raise ValueError('External candidate differs from original')
  blocks.append(candidate);visible.append(bool(matches))
 if any(blocks[0][k]!=blocks[1][k] for k in (1,4,5,6,7,8,10)):raise ValueError('External topology/material changed')
 activation=None
 if visible==[False,True]:
  base=struct.unpack_from('<I',closed[1].graph.context,60)[0]
  matches=[b for (address,_),values in scenes[1].builders.records.items() if address==base+index*164 for b in values if b.refresh<=closed[1].graph.refresh and b.external_enabled]
  from owned_external_model_projection import external_model_matrix
  matches=[b for b in matches if external_model_matrix(b)==blocks[1][2]]
  clocks={b.refresh for b in matches}
  if len(clocks)!=1:raise ValueError('Ambiguous external activation builder')
  clock=clocks.pop();old,new=(s.graph.refresh for s in closed)
  if not old<clock<=new:raise ValueError('External activation outside source interval')
  activation=(clock-old)/(new-old)
 elif visible==[True,False] and portal_exit:
  visit.portal_exit_verified=True
 elif visible==[True,False]:
  # Original 030045E0 returns zero for unsigned vertex depth >0x6000.
  # Negative depths therefore suppress the model before the capture hook03004770.
  def depths(block):
   m=struct.unpack('<12i',block[2]);out=[]
   for x,y,z in struct.iter_unpack('<3h',block[4]):
    value=(x*m[2]+y*m[5]+z*m[8])&0xffffffff
    if value&0x80000000:value-=0x100000000
    out.append((m[11]+(value>>14))&0xffffffff)
   return out
  old_depth,new_depth=map(depths,blocks)
  if any(z>0x6000 for z in old_depth) or not any(z&0x80000000 for z in new_depth):raise ValueError('Unverified external projection exit')
  if any(0x6000<z<0x80000000 for z in new_depth):raise ValueError('Unverified external far exit')
  visit.projection_vertices=tuple(struct.iter_unpack('<3h',blocks[0][4]))
 elif visible!=[True,True]:raise ValueError('Unverified external disappearance or absent pair')
 return SceneryRecordPair(index,*blocks,*visible),visit,activation

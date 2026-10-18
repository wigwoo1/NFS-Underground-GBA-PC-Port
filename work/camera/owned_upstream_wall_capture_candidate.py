"""Opt-in bounded upstream decisions; inactive without explicit sample context."""
import json,struct,hashlib,time,os
from pathlib import Path
import owned_wall_visibility_candidate as target
original=target.batch;active=None;rows=[];samples=[];dropped=0;graphs={}
CAPTURE_FIRST=int(os.environ.get('NFSUG_UPSTREAM_CAPTURE_FIRST','8869'));CAPTURE_LAST=int(os.environ.get('NFSUG_UPSTREAM_CAPTURE_LAST','8923'))
assert 0<=CAPTURE_FIRST<=CAPTURE_LAST and CAPTURE_LAST-CAPTURE_FIRST<=200
SAMPLE_LIMIT=512 if CAPTURE_LAST-CAPTURE_FIRST>54 else 256
GRAPH_LIMIT=64 if CAPTURE_LAST-CAPTURE_FIRST>54 else 32
output=Path('work/camera/prototype-runs')/('upstream-wall-child-'+str(time.time_ns())+'.json')
def set_context(context):
 global active
 active=context

def batch(calls):
 global dropped
 calls=tuple(calls);result=original(calls)
 if active is not None:
  for call,decision in zip(calls,result):
   if len(rows)>=20000:dropped+=1;continue
   wall,descriptor,edge,fb,bounds,base,reciprocal=call
   rows.append(dict(**active,descriptor=wall.descriptor,edge_index=wall.edge,source_address=wall.address,vertices=bytes(wall.vertices).hex(),offsets=bytes(wall.offsets).hex(),framebuffer=bytes(fb).hex(),base_material=bytes(base).hex(),edge_camera=list(edge),region_bounds=list(bounds),decision=dict(visible=decision.visible,reason=decision.reason,x=list(decision.x),y=list(decision.y),flags=decision.flags)))
 return result

def install():
 import sys
 for name,module in list(sys.modules.items()):
  if module is None or name in ('__main__',__name__):continue
  for key,value in list(vars(module).items()):
   if value is original:setattr(module,key,batch)
 from owned_prepared_world_segmented_candidate import PreparedWorldMotion
 sample=PreparedWorldMotion.sample
 def captured_sample(self,alpha):
  refresh=self.history.refresh
  if not CAPTURE_FIRST<=refresh<=CAPTURE_LAST:return sample(self,alpha)
  if active is not None:raise RuntimeError('Nested wall capture sample')
  set_context(dict(epoch=self.history.epoch,older=refresh,alpha=alpha))
  before=len(rows)
  try:
   result=sample(self,alpha);frame=result[0];prefix=frame.prefix if hasattr(frame,'prefix') else frame[:40+struct.unpack_from('<I',frame,8)[0]]
   digest=hashlib.sha256(prefix).hexdigest();publication=struct.unpack_from('<I',prefix,4)[0]
   regions=self.pair.portal.sample(alpha)
   graph_ids=[]
   for endpoint,graph in enumerate((self.pair.portal.older,self.pair.portal.newer)):
    payload=struct.pack('<4I',len(graph.context),len(graph.geometry),len(graph.offsets),len(graph.viewport_data))+graph.context+graph.geometry+graph.offsets+graph.viewport_data
    graph_id=hashlib.sha256(payload).hexdigest();graph_ids.append(graph_id)
    if graph_id not in graphs:
     if len(graphs)>=GRAPH_LIMIT:raise RuntimeError('Portal graph capture bound exceeded')
     graphs[graph_id]=dict(refresh=graph.refresh,root=graph.root,context=graph.context.hex(),geometry=graph.geometry.hex(),offsets=graph.offsets.hex(),viewport_data=graph.viewport_data.hex(),original_associations=self.pair.scenes[endpoint].associations.hex(),scene_refresh=self.pair.scenes[endpoint].refresh)
   sampled_camera=[] if alpha in (0,1) else list(self.pair.portal.motion.sample(alpha)[1])

   if len(samples)>=SAMPLE_LIMIT:raise RuntimeError('Portal capture sample bound exceeded')
   static_links=[]
   for identifier,sources in self.roads._sources_by_descriptor.items():
    for source in sources:
     static_links.append(dict(parent=identifier,child=struct.unpack_from('<H',source.descriptor_bytes,6)[0],descriptor_bytes=source.descriptor_bytes.hex(),secondary=source.secondary))
   supplemental=[]
   dependencies={(d.parent_descriptor,d.object_index,d.descriptor):d for d in self.pair.dependencies[1 if alpha==1 else 0]}
   for c in self.pair.sample(alpha):
    dependency=dependencies[(c.parent,c.object,c.descriptor)]
    supplemental.append(dict(parent=c.parent,object=c.object,descriptor=c.descriptor,ordinal=c.ordinal,bounds=list(c.bounds),source=dependency.source.hex(),depth=c.depth,eligibility=c.eligibility))
   sample_id=len(samples);samples.append(dict(**active,sample_id=sample_id,source_prefix_sha256=digest,source_publication=publication,portal_regions=[list(region) for region in regions],static_road_links=static_links,hidden_static_children=sorted(self.roads.hidden_children),supplemental_candidates=supplemental,graph_ids=graph_ids,sampled_camera=sampled_camera,endpoint_cameras=[list(c) for c in self.pair.portal.endpoints],linked_viewports=self.pair.portal.linked_viewports))
   for row in rows[before:]:row.update(source_prefix_sha256=digest,source_publication=publication,sample_id=sample_id)
   return result
  finally:set_context(None)
 PreparedWorldMotion.sample=captured_sample

def save():
 output.write_text(json.dumps(dict(rows=rows,samples=samples,graphs=graphs,dropped=dropped,capture_first=CAPTURE_FIRST,capture_last=CAPTURE_LAST,sample_limit=SAMPLE_LIMIT,graph_limit=GRAPH_LIMIT,scope='Bounded original upstream wall decision inputs, only older refresh8869..8923. Copying perturbs preparation; not cadence qualification.'),indent=2));print('UPSTREAM_WALL_CAPTURE',str(output),flush=True)

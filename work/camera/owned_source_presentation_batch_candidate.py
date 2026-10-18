"""Separate owned source-anchor presentation batch; retains every native owner."""
import ctypes as C,struct
import os
from owned_native_presentation_batch import OwnedPresentationBatch
from owned_source_draw_context_candidate import OwnedSourceDraw,SourceDrawContext
from owned_source_model_anchor_candidate import SourceModelAnchors
from owned_source_native_depth_rectangle_candidate import SourceFaceDeterminants
from owned_source_face_mask_candidate import build_source_face_mask
from owned_motion_pairs import records

# The worker normally imports transition-only ownership helpers on the first
# birth/death pair.  The opt-in diagnostic moves that cold Python import work
# into module/startup initialization, before timed scene transitions.
OWNER_TRANSITION_PREWARMED=os.environ.get("NFSUG_OWNER_TRANSITION_PREWARM")=="1"
if OWNER_TRANSITION_PREWARMED:
 import owned_model_record_owners
 import owned_scenery_record_pairs
 import owned_scenery_motion
 import owned_external_record_pair

def rigid_camera(pose):
 x,y,z,w=(getattr(pose.rotation,k) for k in ('x','y','z','w'))
 rows=((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),(2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),(2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)))
 return tuple(rows[r][c] for c in range(3) for r in range(3))+(-pose.position.x,-pose.position.y,-pose.position.z)
class OwnedSourcePresentationBatch(OwnedPresentationBatch):
 def __init__(self,epoch,rows,pair,gpu):
  rows=tuple(rows);super().__init__(epoch,rows)
  gpu.nf_owned_gpu_source_context_size.restype=C.c_size_t
  if gpu.nf_owned_gpu_source_context_size()!=C.sizeof(SourceDrawContext):raise ValueError('Source draw ABI mismatch')
  if hasattr(pair,'source_cameras'):
   rawa,rawb,ra,rb=pair.source_cameras;anchors=classifiers=None
  else:
   motion=pair.pair.portal.motion;plan,_,pa,pb,*_=motion.arguments;rawa=struct.unpack('<12i',plan['camera_older']);rawb=struct.unpack('<12i',plan['camera_newer']);ra=rigid_camera(pa);rb=rigid_camera(pb)
   table=(C.c_uint32*32768)(*struct.unpack('<32768I',__import__('pathlib').Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]))
   anchors,classifiers=prepare_source_models(pair,gpu,table)
  self.source_draws=[];self.source_mask_diagnostics=[]
  for index,row in enumerate(rows):
   _,_,_,_,alpha,value,sky=row;frame,camera,models,bounds,detail=value
   if hasattr(pair,'source_masks'):offsets,mask,total,diagnostic=pair.source_masks[alpha]
   else:
    models=anchors.sample(frame,models,alpha);offsets,mask,total,diagnostic=build_source_face_mask(frame,models,bounds,alpha,classifiers)
   owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],rawa,rawb,ra,rb,alpha,offsets,mask,total).attach_sky(sky);self.source_draws.append(owned);self.draws[index]=owned.context.draw;self.items[index].drawctx=C.addressof(owned.context);self.source_mask_diagnostics.append(diagnostic)


def prepare_source_models(pair,gpu,table,trace=None,endpoint_rows=None):
 import time
 from owned_thread_cycles import read as thread_cycles
 started=time.perf_counter_ns() if trace is not None else None;cpu=time.thread_time_ns() if trace is not None else None;cycles=thread_cycles() if trace is not None else None
 def stage(name):
  nonlocal started,cpu,cycles
  if trace is None:return
  end=time.perf_counter_ns();cpu_end=time.thread_time_ns();cycles_end=thread_cycles()
  if trace is not None:trace.append(dict(name=name,started_ns=started,completed_ns=end,wall_ns=end-started,thread_cpu_ns=cpu_end-cpu,thread_cycles=cycles_end-cycles))
  started=end;cpu=cpu_end;cycles=cycles_end
 # The normal path assembles endpoint worlds before extracting their model rows.
 # An opt-in caller may provide the immutable rows from PreparedMotionPair's
 # already-validated endpoint plan; those rows are exactly what the endpoint
 # assembly returns and let us avoid constructing two throwaway endpoint scenes.
 if endpoint_rows is None:
  endpoints=[records(pair.sample(i)[0])['records'] for i in (0,1)]
 else:
  if len(endpoint_rows)!=2 or any(not isinstance(rows,list) for rows in endpoint_rows):raise ValueError('Invalid validated endpoint rows')
  endpoints=list(endpoint_rows)
 ends=[{r['key']:r for r in rows if r['kind']==3} for rows in endpoints]
 stage('endpoint_sampling_and_decode')
 from owned_model_record_owners import model_record_owners
 owner_maps=model_record_owners(pair.pair,pair.rom) if hasattr(pair,'rom') else None
 if owner_maps is None:
  raise ValueError('Missing complete source ownership')
 stage('model_source_ownership')
 if trace is not None:trace[-1]['model_owner_stages']=list(getattr(pair.pair,'_model_owner_stages',()))
 preanchored=set();source_rows={}
 for owner,source in getattr(pair.pair,'_scenery_record_pairs',{}).items():
  matches=[endpoints[e][index] for e in (0,1) for index,value in owner_maps[e].items() if value==owner]
  if not matches or len({r['key'] for r in matches})!=1:raise ValueError('Ambiguous scenery source identity')
  key=matches[0]['key']
  if any(bytes(r['blocks'][i])!=bytes(source.older_blocks[i]) for r in matches for i in (1,4,5,6,7,8,10)):raise ValueError('Scenery ownership topology mismatch')
  preanchored.add(key)
  source_rows[key]=tuple(dict(matches[0],blocks=blocks) for blocks in (source.older_blocks,source.newer_blocks))
 stage('scenery_source_rows')
 anchors=SourceModelAnchors(pair.pair.portal.motion,preanchored)
 stage('rigid_model_anchors')
 classifiers={k:SourceFaceDeterminants(ends[0][k],ends[1][k],gpu,table) for k in ends[0].keys()&ends[1].keys() if k not in preanchored}
 for key,rows in source_rows.items():classifiers[key]=SourceFaceDeterminants(*rows,gpu,table)
 stage('source_classifiers')
 return anchors,classifiers

"""Complete sampled primary road sequence; original endpoint planner stays separate."""
import ctypes as C,math,struct,time
from owned_thread_cycles import read as thread_cycles
from collections import OrderedDict
from owned_closed_scene_memory import scene_memory
from owned_complete_road_candidates import road_candidates
from owned_complete_road_gpu import encode_road
from owned_sampled_road_camera import sampled_road_camera,sampled_road_far_depths
from owned_sampled_road_clip import Attributes,clipped_camera_road
from owned_road_stream_count import surface_stream_count
RoadWorld=C.c_double*96
class SampledRoadSequence:
 def __init__(self,older,newer,portal,history,assets=None):
  if older.epoch!=newer.epoch or history.epoch!=older.epoch or history.refresh!=older.refresh:raise ValueError('Road history/scene mismatch')
  self.older=older;self.newer=newer;self.portal=portal;self.history=history
  if assets is None:
   self.sources=road_candidates(older,scene_memory(older,history.rom));new_sources=road_candidates(newer,scene_memory(newer,history.rom))
  else:
   old_assets,new_assets=assets
   if old_assets[0] is not older or new_assets[0] is not newer or old_assets[1] is not history.rom or new_assets[1] is not history.rom:raise ValueError('Sampled road asset ownership mismatch')
   self.sources=old_assets[3];new_sources=new_assets[3]
  # Index immutable sources once; preserve encounter order and duplicate checks.
  groups={}
  for source in self.sources:groups.setdefault(source.descriptor,[]).append(source)
  from types import MappingProxyType
  self._sources_by_descriptor=MappingProxyType({key:tuple(value) for key,value in groups.items()})
  new={(x.descriptor,x.secondary):x for x in new_sources}
  for x in self.sources:
   y=new.get((x.descriptor,x.secondary))
   if y is None or (x.vertices,x.offsets,x.face,x.descriptor_bytes)!=(y.vertices,y.offsets,y.face,y.descriptor_bytes):raise ValueError('Moving road source topology unsupported')
  # Original region_setup culls hidden face before any child transform/links.
  self.hidden_children=set()
  if assets is None:old_memory=scene_memory(older,history.rom);new_memory=scene_memory(newer,history.rom)
  else:old_memory=old_assets[2];new_memory=new_assets[2]
  descriptors=[]
  for scene in (older,newer):
   mapping={};at=0
   while at<len(scene.graph.geometry):
    identifier,n,_,_=struct.unpack_from('<4I',scene.graph.geometry,at);mapping[identifier]=scene.graph.geometry[at+16:at+64];at+=64+n*68
   descriptors.append(mapping)
  for source in self.sources:
   child=struct.unpack_from('<H',source.descriptor_bytes,6)[0]
   if child==65535:continue
   faces=[]
   for scene,memory,mapping in zip((older,newer),(old_memory,new_memory),descriptors):
    desc=mapping.get(child)
    if desc is None:break
    fi=struct.unpack_from('<H',desc,10)[0]
    if fi==65535:break
    try:faces.append(memory.read(struct.unpack_from('<I',scene.graph.context,28)[0]+fi*20,20))
    except ValueError:break
   if len(faces)==2 and faces[0]==faces[1] and struct.unpack_from('<H',faces[0],8)[0]&0x40:self.hidden_children.add(child)
  self._records=OrderedDict();self._record_bytes=0;self.record_budget=8*1024*1024
  visited={r[0] for alpha in (0,1) for r in portal.sample(alpha) if not r[5]&8}
  for source in self.sources:
   if source.descriptor in visited and not source.missing:self._record(source)
  self._decoded_sources={};self.source_decode_calls=0;self.source_decode_reuses=0
  self.ma=struct.unpack_from('<12i',older.graph.context,256);self.mb=struct.unpack_from('<12i',newer.graph.context,256)
 def _record(self,source):
  key=(source.descriptor,source.secondary)
  if key in self._records:self._records.move_to_end(key);return self._records[key]
  # All interior surface clips are supplied separately as validated doubles.
  record=encode_road(self.older.graph.context,source,(0,239,0,159))
  if len(record)<=self.record_budget:
   while self._records and self._record_bytes+len(record)>self.record_budget:
    _,old=self._records.popitem(last=False);self._record_bytes-=len(old)
   self._records[key]=record;self._record_bytes+=len(record)
  return record
 def sample(self,alpha):
  if not math.isfinite(alpha) or not 0<alpha<1:raise ValueError('Use original endpoint planner at scene boundaries')
  if self.history.refresh!=self.older.refresh:raise ValueError('Road history advanced beyond prepared interval')
  _,pose,_=self.portal.motion.sample(alpha);context=self.older.graph.context;state=context[:256];near=struct.unpack_from('<i',context,320)[0];base=struct.unpack_from('<I',state,108)[0];branch=self.history.fork();selected=[];details=[]
  self.child_walls=();self._last_road_stages=[];self._road_stage_dropped=0
  child_walls=[]
  def visit(ordinal,region,stack=()):
   identifier=region[0]
   if identifier in stack or len(stack)>=512:raise ValueError('Cyclic sampled static child')
   sources=self._sources_by_descriptor.get(identifier,())
   if not sources:
    if stack:raise ValueError('Static child primary road closure missing')
    return
   if len(sources)!=1:raise ValueError('Sampled secondary road submission unverified')
   x=sources[0]
   if x.missing:raise ValueError('Incomplete sampled road assets')
   if x.secondary or x.descriptor_bytes[18]&8:raise ValueError('Sampled sibling/secondary road submission unverified')
   road_start=time.perf_counter_ns();road_cycles=thread_cycles()
   def road_stage(name):
    nonlocal road_start,road_cycles
    end=time.perf_counter_ns();cycles=thread_cycles()
    if len(self._last_road_stages)<4096:self._last_road_stages.append(dict(name=name,descriptor=identifier,started_ns=road_start,completed_ns=end,wall_ns=end-road_start,thread_cycles=cycles-road_cycles))
    else:self._road_stage_dropped+=1
    road_start=end;road_cycles=cycles
   # World positions and UV inputs are immutable throughout this scene pair.
   # Affine mode belongs to the sampled region; keep both modes separate.
   key=(identifier,region[5]&1);decoded=self._decoded_sources.get(key);d=branch.d
   if decoded is None:
    n=len(x.vertices)//68;mat=bytearray(48);struct.pack_into('<HH',mat,36,struct.unpack_from('<H',x.material,26)[0],struct.unpack_from('<H',x.material,10)[0]);world=RoadWorld();attrs=Attributes()
    d.nf_road_source_decode.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
    if not d.nf_road_source_decode(x.vertices,len(x.vertices),x.offsets,len(x.offsets),x.face,bytes(mat),n,region[5]&1,world,C.byref(attrs)):raise ValueError('Road source decode failed')
    decoded=(tuple(world)[:n*3],bytes(attrs));self._decoded_sources[key]=decoded;self.source_decode_calls+=1
   else:self.source_decode_reuses+=1
   raw,attribute_bytes=decoded;attrs=Attributes.from_buffer_copy(attribute_bytes);n=attrs.count
   road_stage('source_decode')
   far=sampled_road_far_depths(raw,self.ma,self.mb,self.portal.endpoints,pose,alpha)
   camera=sampled_road_camera(raw,self.ma,self.mb,self.portal.endpoints,pose,alpha);count=surface_stream_count(camera,near,face_hidden=bool(struct.unpack_from('<H',x.face,8)[0]&0x40),far_depths=far)
   road_stage('camera_and_visibility')
   if count is None:return
   child_begin=time.perf_counter_ns();child_cycles=thread_cycles()
   depth=len(stack)
   if depth:
    from owned_sampled_graph_wall_visibility import selected_graph_walls
    from owned_scene_gpu_wall import encode_draws
    for candidate,visibility in selected_graph_walls(self.portal,alpha,queue=(region,)):
     from owned_deferred_wall_policy import sampled_wall_emitted
     if not sampled_wall_emitted(visibility.flags,candidate.edge,n):continue
     scratch=bytearray(52);struct.pack_into('<H',scratch,48,visibility.flags)
     vertices,record=encode_draws(context,((ordinal,(identifier,0,239,0,159,0,0),candidate.wall,bytes(scratch)),))[0]
     child_walls.append(dict(ordinal=ordinal,static_depth=depth,descriptor=identifier,edge=candidate.edge,record=record,bounds=tuple(region[1:5])))
   clip_begin=time.perf_counter_ns();clip_cycles=thread_cycles()
   clipped=clipped_camera_road(d,branch.scratch,camera,attrs,region[1:5],base,count,branch.ct,commit_branch=True)
   clip_end=time.perf_counter_ns();clip_end_cycles=thread_cycles()
   road_stage('child_walls_and_clip')
   if self._last_road_stages and self._last_road_stages[-1]['name']=='child_walls_and_clip':self._last_road_stages[-1]['child_clip_stages']=dict(child_wall_ns=clip_begin-child_begin,child_wall_cycles=clip_cycles-child_cycles,clip_ns=clip_end-clip_begin,clip_cycles=clip_end_cycles-clip_cycles,static_depth=depth)
   if clipped['projected_count']!=count:raise ValueError('Sampled road emission count disagrees with camera ring')
   details.append(dict(descriptor=identifier,static_depth=depth,input_count=count,missing=clipped['missing'],clipped_count=clipped['count'],bounds=tuple(region[1:5])))
   if not clipped['missing']:selected.append(dict(ordinal=ordinal,static_depth=depth,descriptor=identifier,secondary=x.secondary,bounds=tuple(region[1:5]),record=self._record(x)))
   road_stage('record_encoding')
   child=struct.unpack_from('<H',x.descriptor_bytes,6)[0]
   if child not in ({65535}|self.hidden_children):
    if child>=512:raise ValueError('Invalid sampled static child')
    if region[5]&128:raise ValueError('Unverified static child object ordering')
    visit(ordinal,(child,*region[1:]),stack+(identifier,))
  try:
   for ordinal,region in reversed(list(enumerate(self.portal.sample(alpha)))):
    if region[5]&8 or region[1]>=region[2] or region[3]>region[4]:continue
    visit(ordinal,region)
   self.child_walls=tuple(child_walls)
   return tuple(selected),tuple(details)
  finally:
   try:branch.close()
   finally:
    # Break the recursive visitor closure before releasing the scene pair.
    visit=None


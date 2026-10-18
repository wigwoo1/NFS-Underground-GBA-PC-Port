"""Complete sampled primary road sequence; original endpoint planner stays separate."""
import ctypes as C,math,struct
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates
from owned_complete_road_gpu import encode_road
from owned_sampled_road_camera import sampled_road_camera,sampled_road_far_depths
from owned_sampled_road_clip import Attributes,clipped_camera_road
from owned_road_stream_count import surface_stream_count
class SampledRoadSequence:
 def __init__(self,older,newer,portal,history):
  if older.epoch!=newer.epoch or history.epoch!=older.epoch or history.refresh!=older.refresh:raise ValueError('Road history/scene mismatch')
  self.older=older;self.newer=newer;self.portal=portal;self.history=history
  self.sources=road_candidates(older,ClosedSceneMemory(older,history.rom));new={(x.descriptor,x.secondary):x for x in road_candidates(newer,ClosedSceneMemory(newer,history.rom))}
  for x in self.sources:
   y=new.get((x.descriptor,x.secondary))
   if y is None or (x.vertices,x.offsets,x.face,x.descriptor_bytes)!=(y.vertices,y.offsets,y.face,y.descriptor_bytes):raise ValueError('Moving road source topology unsupported')
  self.ma=struct.unpack_from('<12i',older.graph.context,256);self.mb=struct.unpack_from('<12i',newer.graph.context,256)
 def sample(self,alpha):
  if not math.isfinite(alpha) or not 0<alpha<1:raise ValueError('Use original endpoint planner at scene boundaries')
  if self.history.refresh!=self.older.refresh:raise ValueError('Road history advanced beyond prepared interval')
  _,pose,_=self.portal.motion.sample(alpha);context=self.older.graph.context;state=context[:256];near=struct.unpack_from('<i',context,320)[0];base=struct.unpack_from('<I',state,108)[0];branch=self.history.fork();selected=[];details=[]
  try:
   for ordinal,region in reversed(list(enumerate(self.portal.sample(alpha)))):
    if region[5]&8:continue
    if region[1]>=region[2] or region[3]>region[4]:continue
    for x in (s for s in self.sources if s.descriptor==region[0]):
     if x.missing:raise ValueError('Incomplete sampled road assets')
     if x.secondary or x.descriptor_bytes[18]&8 or struct.unpack_from('<H',x.descriptor_bytes,6)[0]!=65535:raise ValueError('Sampled secondary/recursive road submission unverified')
     n=len(x.vertices)//68;mat=bytearray(48);struct.pack_into('<HH',mat,36,struct.unpack_from('<H',x.material,26)[0],struct.unpack_from('<H',x.material,10)[0]);world=(C.c_double*96)();attrs=Attributes();d=branch.d
     d.nf_road_source_decode.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
     if not d.nf_road_source_decode(x.vertices,len(x.vertices),x.offsets,len(x.offsets),x.face,bytes(mat),n,region[5]&1,world,C.byref(attrs)):raise ValueError('Road source decode failed')
     raw=tuple(world)[:n*3];far=sampled_road_far_depths(raw,self.ma,self.mb,self.portal.endpoints,pose,alpha)
     if any(z>0x5fff for z in far):continue
     camera=sampled_road_camera(raw,self.ma,self.mb,self.portal.endpoints,pose,alpha);count=surface_stream_count(camera,near,face_hidden=bool(struct.unpack_from('<H',x.face,8)[0]&0x40),far_depths=far)
     if count is None:continue
     clipped=clipped_camera_road(d,branch.scratch,camera,attrs,region[1:5],base,count,branch.ct,commit_branch=True)
     if clipped['projected_count']!=count:raise ValueError('Sampled road emission count disagrees with camera ring')
     details.append(dict(descriptor=x.descriptor,input_count=count,missing=clipped['missing'],clipped_count=clipped['count']))
     if not clipped['missing']:selected.append(dict(ordinal=ordinal,descriptor=x.descriptor,secondary=x.secondary,bounds=tuple(region[1:5]),record=encode_road(context,x,region[1:5])))
   return tuple(selected),tuple(details)
  finally:branch.close()

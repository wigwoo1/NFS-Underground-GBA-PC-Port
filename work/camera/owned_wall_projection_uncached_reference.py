"""Owned wall clipping/projection pipeline over raw graph rings."""
import ctypes as C,struct
from pathlib import Path
from owned_wall_transform import transform
from owned_wall_heights import heights
from owned_wall_region_candidates import regions,source_flags,hidden
from owned_graph_wall_sources import wall_sources

def projected(graph,reciprocal,supplement=None):
 graph.validate();d=C.CDLL(str(Path('work/camera/native_visibility.dll').resolve()))
 d.nfs_visibility_wall_uv.argtypes=[C.c_void_p,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p]
 d.nfs_visibility_wall_clip.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_int,C.c_uint,C.c_uint,C.c_void_p]
 d.nfs_visibility_wall_project.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p]
 table=(C.c_uint32*32768)(*reciprocal[:32768]);camera=graph.context[256:304];fb=graph.context[304:368];rings={};at=offset=0;bases={};cursor=0
 if supplement is None:
  while cursor<len(graph.materials):
   h=struct.unpack_from('<12I',graph.materials,cursor);bases[h[3]]=graph.materials[cursor+48:cursor+80];cursor+=120+(h[8] if h[9]==1 else 0)
  while at<len(graph.geometry):
   h=struct.unpack_from('<4I',graph.geometry,at);desc=graph.geometry[at+16:at+64];at+=64;ring=graph.geometry[at:at+h[1]*68];at+=h[1]*68;o=graph.offsets[offset:offset+h[1]*32];offset+=h[1]*32;rings[h[0]]=(desc,ring,o)
  sources={}
  for w in wall_sources(graph):sources.setdefault(w.descriptor,[]).append(w)
  region_queue=regions(graph,reciprocal)
 else:
  raw,supp_sources=supplement;h=struct.unpack_from('<8I',raw);n=h[4];camera=raw[80:128];fb=raw[128:192];desc=raw[32:80]
  ring=b''.join(raw[976+i*140:1044+i*140] for i in range(n));offsets=b''.join(raw[1044+i*140:1076+i*140] for i in range(n))
  rings={h[3]:(desc,ring,offsets)};sources={h[3]:supp_sources};bases={}
  for i in range(n):bases[struct.unpack_from('<H',ring,i*68+44)[0]]=raw[1076+i*140:1108+i*140]
  region_queue=[struct.unpack_from('<8H',raw,192)[:7]]
 output=[];stats=dict(far=0,hidden=0,near_rejected=0,viewport_rejected=0,visible=0,deferred=0,vertical_rejected=0,inactive_material=0)
 transformed={}
 for ordinal,region in enumerate(region_queue):
  desc,ring,offsets=rings[region[0]]
  if region[0] not in transformed:transformed[region[0]]=transform(ring,offsets,camera)
  status,raw=transformed[region[0]]
  if not status:stats['far']+=1;continue
  params=(C.c_uint32*5)(struct.unpack_from('<I',fb,28)[0],struct.unpack_from('<h',fb,8)[0]&0xffffffff,struct.unpack_from('<h',fb,10)[0]&0xffffffff,region[1],region[2])
  for w in sources.get(region[0],()):
   if hidden(w):stats['hidden']+=1;continue
   scratch=C.create_string_buffer(raw[w.edge*52:(w.edge+1)*52],52);v=w.vertices;anim=w.animation;mi=struct.unpack_from('<H',v,44)[0];material=bases[mi]
   if not struct.unpack_from('<H',material)[0]:stats['inactive_material']+=1;continue
   u=(struct.unpack_from('<H',v,40)[0]<<7)+(struct.unpack_from('<h',anim,4)[0]>>1);vo=struct.unpack_from('<h',anim,6)[0]>>1
   assert d.nfs_visibility_wall_uv(v[:68],material,u&0xffffffff,vo&0xffffffff,struct.unpack_from('<H',v,64)[0],scratch)
   h=(C.c_uint32*4)(*heights(w,desc,camera));a=(C.c_uint32*4)(*struct.unpack_from('<2I',v,32),*struct.unpack_from('<2I',v,100))
   visible=d.nfs_visibility_wall_clip(scratch,h,a,struct.unpack_from('<i',fb,16)[0],source_flags(w),desc[18],table)
   if visible<0:raise ValueError('Unsupported owned near clipping')
   if not visible:stats['near_rejected']+=1;continue
   if not d.nfs_visibility_wall_project(scratch,params,table):raise ValueError('Invalid owned projection')
   flags=struct.unpack_from('<H',scratch.raw,48)[0]
   if flags&4:stats['viewport_rejected']+=1;continue
   ys=struct.unpack_from('<4h',scratch.raw,8)
   if ys[0]>=region[4] and ys[1]>=region[4] and ys[2]<region[3] and ys[3]<region[3]:stats['vertical_rejected']+=1;continue
   stats['visible']+=1;stats['deferred']+=bool(flags&2);output.append((ordinal,region,w,scratch.raw))
 return tuple(output),stats



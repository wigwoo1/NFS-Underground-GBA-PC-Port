"""Diagnostic bounded immutable wall record templates; scratch remains per draw."""
import struct,threading
from collections import OrderedDict
from owned_wall_region_candidates import source_flags
from owned_graph_wall_sources import WallSource
from owned_scene_gpu_wall import encode_draws as recovered
BUDGET=16*1024*1024
_local=threading.local()
def clear_cache():_local.entries=OrderedDict();_local.bytes=0
def encode_draws(context,draws,allow_deferred=False):
 result=[]
 if not hasattr(_local,'entries'):clear_cache()
 entries=_local.entries;retained=_local.bytes
 for ordinal,region,wall,scratch in draws:
  if struct.unpack_from('<H',scratch,48)[0]&2 and not allow_deferred:raise ValueError('Deferred wall ordering not verified')
  fields=('vertices','offsets','animation','resolved','texture')
  valid=type(context) is bytes and type(wall) is WallSource and type(scratch) is bytes and all(type(getattr(wall,n)) is bytes for n in fields)
  valid=valid and len(wall.vertices)>=48 and len(wall.texture)<=65536 and type(wall.shift) is int and type(wall.height) is int and 0<=wall.shift<=65535 and 0<=wall.height<=65535
  valid=valid and len(region[1:5])==4 and all(type(v) is int and 0<=v<=65535 for v in region[1:5])
  if not valid:
   result.extend(recovered(context,((ordinal,region,wall,scratch),),allow_deferred=allow_deferred));continue
  bounds=struct.pack('<4H',*region[1:5])
  key=(id(context),id(wall),bounds);cached=entries.get(key)
  if cached is not None:
   assert cached[0] is context and cached[1] is wall
   entries.move_to_end(key)
  if cached is None:
   material=bytearray(48);struct.pack_into('<HH',material,36,wall.shift,wall.height)
   state=bytearray(260);struct.pack_into('<I',state,256,source_flags(wall))
   if len(wall.texture)>65536:raise ValueError('Wall texture exceeds current GPU ABI')
   blocks=(wall.vertices,wall.offsets,wall.animation,context[256:304],bytes(material),bounds,context[304:368],bytes(32),wall.texture.ljust(65536,b'\x00'),context[384:896])
   prefix=struct.pack('<4I',0x3147534e,2,0,12)+b''.join(struct.pack('<I',len(b))+b for b in blocks)
   suffix=struct.pack('<I',len(state))+bytes(state)
   size=len(context)+sum(len(getattr(wall,n)) for n in fields)+len(prefix)+len(suffix)+128
   cached=(context,wall,bounds,prefix,suffix,size)
   if size<=BUDGET:
    while entries and (len(entries)>=128 or retained+size>BUDGET):retained-=entries.popitem(last=False)[1][5]
    entries[key]=cached;retained+=size;_local.bytes=retained
  result.append((wall.vertices,cached[3]+struct.pack('<I',len(scratch))+scratch+cached[4]))
 _local.entries=entries
 return tuple(result)

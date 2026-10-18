import ctypes as C,struct
from pathlib import Path
from functools import lru_cache
from owned_wall_region_candidates import hidden,source_flags
from owned_continuous_wall_visibility import WallVisibility,select_wall
class Input(C.Structure):_fields_=[('edge',C.c_double*8),('bounds',C.c_double*4),('flags',C.c_uint32),('hidden',C.c_uint32),('active',C.c_uint32)]
class Output(C.Structure):_fields_=[('reason',C.c_uint32),('flags',C.c_uint32),('x',C.c_double*2),('y',C.c_double*4)]
@lru_cache(maxsize=1)
def helper():
 d=C.CDLL(str(Path(__file__).with_name('wall-visibility-batch.dll').resolve()));d.nf_wall_visibility_batch.argtypes=[C.POINTER(Input),C.c_size_t,C.c_int,C.c_uint32,C.c_int,C.c_int,C.POINTER(C.c_uint32),C.c_size_t,C.POINTER(Output)];return d
_table_owner=None
_table_buffer=None
def table(values):
 global _table_owner,_table_buffer
 if not isinstance(values,tuple):raise ValueError('Diagnostic reciprocal must be immutable')
 if _table_owner is not values:
  _table_buffer=(C.c_uint32*len(values))(*values);_table_owner=values
 return _table_buffer
@lru_cache(maxsize=64)
def batch_types(amount):return Input*amount,Output*amount

def batch(calls):
 if not calls:return ()
 framebuffer=calls[0][3];r=calls[0][6]
 # Keep recovered Python semantics outside the validated native fast domain.
 if len(calls)>4096 or not isinstance(r,tuple) or any(c[3]!=framebuffer or (c[6] is not r and c[6]!=r) or any(abs(v)>100000 for v in (*c[2],*c[4])) for c in calls):
  return tuple(select_wall(*c) for c in calls)
 input_type,output_type=batch_types(len(calls))
 packed=input_type()
 for row,c in zip(packed,calls):
  wall,descriptor,edge,fb,bounds,base,reciprocal=c
  row.edge[:]=edge;row.bounds[:]=bounds;row.flags=source_flags(wall);row.hidden=hidden(wall);row.active=bool(struct.unpack_from('<H',base)[0])
 near=struct.unpack_from('<i',framebuffer,16)[0];scale=struct.unpack_from('<I',framebuffer,28)[0];cx,cy=struct.unpack_from('<2h',framebuffer,8)
 out=output_type();status=helper().nf_wall_visibility_batch(packed,len(calls),near,scale,cx,cy,table(r),len(r),out)
 if status!=1:return tuple(select_wall(*c) for c in calls)
 reasons=('visible','hidden','inactive_material','near_rejected','viewport_rejected','vertical_rejected')
 return tuple(WallVisibility(v.reason==0,reasons[v.reason],tuple(v.x) if v.reason in (0,4,5) else (),tuple(v.y) if v.reason in (0,5) else (),v.flags) for v in out)

import ctypes as C,json,struct
from pathlib import Path
p=Path('work/camera')
class View(C.Structure):
 _fields_=[('kind',C.c_uint),('context',C.c_uint),('blocks',C.c_void_p*12),('sizes',C.c_uint32*12)]
lib=C.CDLL(str((p/'native-geometry-view.dll').resolve()));fn=lib.nf_geometry_packet_views;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_uint,C.c_void_p]
checks=[]
for refresh in (8758,8762,8766,8769,8773,8776,8780):
 raw=(p/f'motion-actual-scanline-assets/{refresh}-model-sources.bin').read_bytes();owned=C.create_string_buffer(raw);views=(View*144)();count=C.c_uint()
 assert fn(owned,len(raw),views,144,C.byref(count))
 offset=0
 for view in views[:count.value]:
  magic,kind,context,n=struct.unpack_from('<4I',raw,offset);offset+=16;assert (kind,context)==(view.kind,view.context)
  for i in range(12):
   size=struct.unpack_from('<I',raw,offset)[0];offset+=4;assert view.sizes[i]==size and C.string_at(view.blocks[i],size)==raw[offset:offset+size];offset+=size
 assert offset==len(raw)
 sentinel=bytes(views);count.value=777
 for size in (1,15,len(raw)-1):
  assert not fn(owned,size,views,144,C.byref(count));assert bytes(views)==sentinel and count.value==777
 assert not fn(owned,len(raw),views,0,C.byref(count));assert bytes(views)==sentinel and count.value==777
 checks.append(dict(refresh=refresh,draws=len([v for v in views if v.kind]),owned_bytes=len(raw)))
r=dict(result='PASS_NATIVE_COMPLETE_GEOMETRY_VIEWS',checks=checks,scope='Bounded native immutable GPU source views; entire scene validated before publication; truncation/capacity failures preserve output. No GPU drawing or timing proof.')
(p/'native-geometry-view-tests.json').write_text(json.dumps(r,indent=2));print(r)

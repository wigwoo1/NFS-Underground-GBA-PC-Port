import ctypes as C,struct,json
from pathlib import Path
from owned_graph_wall_sources import WallSource
from owned_scene_gpu_wall import encode_draws
class View(C.Structure):_fields_=[('kind',C.c_uint),('context',C.c_uint),('blocks',C.c_void_p*12),('sizes',C.c_uint32*12)]
d=C.CDLL(str(Path('work/camera/native-geometry-compact-candidate.dll').resolve()));d.nf_geometry_packet_views.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(View),C.c_uint,C.POINTER(C.c_uint)]
w=WallSource(1,0,bytes(136),bytes(64),bytes(8),bytes(32),bytes(range(256)),4,16,0)
legacy=encode_draws(bytes(896),((0,(1,0,239,0,159,0,0),w,bytes(52)),))[0][1]
def blocks(record):
 out=[];at=16
 for i in range(12):n=struct.unpack_from('<I',record,at)[0];at+=4;out.append(record[at:at+n]);at+=n
 assert at==len(record);return out
def packet(tex):
 b=blocks(legacy);b[8]=tex
 return legacy[:16]+b''.join(struct.pack('<I',len(x))+x for x in b)
def validate(record,success):
 buffer=C.create_string_buffer(record);views=(View*4)();views[0].kind=999;count=C.c_uint(777)
 status=d.nf_geometry_packet_views(buffer,len(record),views,4,C.byref(count))
 assert bool(status)==success
 if not success:assert count.value==777 and views[0].kind==999
 return count.value
assert validate(legacy,True)==1
compact=packet(w.texture);assert validate(compact,True)==1
b=blocks(compact);b[8]=b[8].ljust(65536,b'\0');assert b==blocks(legacy)
for tex in (b'',bytes(255),bytes(65537)):
 assert validate(packet(tex),False)==777
 assert validate(legacy+packet(tex),False)==777
assert validate(compact[:-1],False)==777
print(json.dumps(dict(result='PASS',legacy_bytes=len(legacy),compact_bytes=len(compact),saved_bytes=len(legacy)-len(compact),scope='Legacy acceptance, compact material dimensions, normalized payload equality, undersized/oversized/truncated late draw atomic rejection; no GPU pixel or live timing proof')))

from pathlib import Path
import ctypes as C,struct,json
from scene_batches import batches
root=Path('work/camera');d=C.CDLL(str((root/'native_surface.dll').resolve()))
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
d.nf_extract_road.argtypes=[Reader,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.c_uint32,C.POINTER(C.c_void_p),C.POINTER(C.c_size_t)]
d.nf_surface_free.argtypes=[C.c_void_p]
regions=[]
@Reader
def read(context,address,out,size):
 for base,data in regions:
  if base<=address and address+size<=base+len(data):C.memmove(out,data[address-base:address-base+size],size);return 1
 return 0
checked=0;total=0
for scene in batches(root/'world.bin'):
 packet=(root/'packet-sequence'/f"scene-{scene['serial']:03}.packet").read_bytes();offset,length=struct.unpack_from('<2I',packet,48);world=packet[offset:offset+length];position=8
 for e in scene['events']:
  if e['pc']!=0x030032f0:continue
  n,width,height=struct.unpack_from('<3I',world,position);size=12+n*40+width*height*4;expected=world[position:position+size];position+=size
  b=e['blocks'];regions=[value for value in b.values() if value[1]];out=C.c_void_p();out_size=C.c_size_t()
  assert d.nf_extract_road(read,None,b[1][0],b[4][0],b[8][0],b[9][0],C.byref(out),C.byref(out_size)),e['id']
  assert C.string_at(out,out_size.value)==expected,e['id'];d.nf_surface_free(out);checked+=1;total+=size
assert checked
regions=[];out=C.c_void_p(123);out_size=C.c_size_t(456)
assert not d.nf_extract_road(read,None,1,2,3,4,C.byref(out),C.byref(out_size)) and out.value==123 and out_size.value==456
report={'result':'PASS','road_draw_records':checked,'bytes_identical_to_offline_sections':total,'unavailable_memory_rejected':True,'scope':'Native reader-based construction against captured memory. Bridge callback/live publication not connected yet.'}
(root/'native-road-tests.json').write_text(json.dumps(report,indent=2));print(report)

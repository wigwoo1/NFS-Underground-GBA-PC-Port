from pathlib import Path
import ctypes as C,struct,json
from scene_batches import batches
root=Path('work/camera');d=C.CDLL(str((root/'native_surface.dll').resolve()));Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
d.nf_extract_wall.argtypes=[Reader,C.c_void_p]+[C.c_uint32]*6+[C.POINTER(C.c_void_p),C.POINTER(C.c_size_t)]*2;d.nf_surface_free.argtypes=[C.c_void_p]
d.nf_wall_write_states_owned.argtypes=[Reader,C.c_void_p,C.c_uint32,C.c_uint,C.POINTER(C.c_void_p)]+[C.POINTER(C.c_uint32)]*3
regions=[]
@Reader
def read(context,address,out,size):
 for base,data in regions:
  if base<=address and address+size<=base+len(data):C.memmove(out,data[address-base:address-base+size],size);return 1
 return 0
checked=0;lit_count=0;total=0;state_bytes=0
for scene in batches(root/'shading.bin'):
 packet=(root/'packet-sequence'/f"scene-{scene['serial']:03}.packet").read_bytes();wo,ws=struct.unpack_from('<2I',packet,48);lo,ls=struct.unpack_from('<2I',packet,72);world=packet[wo:wo+ws];lighting=packet[lo:lo+ls];wp=lp=8
 roads=sum(e['pc']==0x030032f0 for e in scene['events'])
 for _ in range(roads):n,w,h=struct.unpack_from('<3I',world,wp);wp+=12+n*40+w*h*4;assert struct.unpack_from('<I',lighting,lp)[0]==0;lp+=4
 active={}
 for e in scene['events']:
  b=e['blocks']
  if e['pc']==0x03001800:active[b[1][0]]=b
  if e['pc']!=0x03000304:continue
  n,w,h=struct.unpack_from('<3I',world,wp);size=12+n*40+w*h*4;expected=world[wp:wp+size];wp+=size
  lit=struct.unpack_from('<I',lighting,lp)[0];light_size=20+w*h*64 if lit else 4;expected_light=lighting[lp:lp+light_size];lp+=light_size
  parent=active[b[1][0]];regions=[value for value in b.values() if value[1]]+[value for value in parent.values() if value[1]]
  out=C.c_void_p();out_size=C.c_size_t();light=C.c_void_p();light_length=C.c_size_t()
  assert d.nf_extract_wall(read,None,b[1][0],parent[4][0],b[5][0],b[8][0],b[4][0],e['regs'][2],C.byref(out),C.byref(out_size),C.byref(light),C.byref(light_length)),e['id']
  assert C.string_at(out,out_size.value)==expected,('surface',e['id'])
  assert C.string_at(light,light_length.value)==expected_light,('lighting',e['id'])
  states=C.c_void_p();sw=C.c_uint32();sh=C.c_uint32();planes=C.c_uint32()
  assert d.nf_wall_write_states_owned(read,None,b[8][0],e['regs'][2],C.byref(states),C.byref(sw),C.byref(sh),C.byref(planes))
  assert (sw.value,sh.value,planes.value)==(w,h,17 if lit else 1)
  # This retained table never maps nonzero input to output index0 (verified
  # separately); alpha therefore independently determines skip/nonzero here.
  base=expected[12+n*40:]
  classified=bytes(2 if a else 0 for a in base[3::4])
  if lit:classified+=bytes(2 if a else 0 for a in expected_light[23::4])
  assert C.string_at(states,len(classified))==classified,('write states',e['id'])
  d.nf_surface_free(states);state_bytes+=len(classified)
  d.nf_surface_free(out);d.nf_surface_free(light);checked+=1;lit_count+=bool(lit);total+=size+light_size
assert checked
report={'result':'PASS','wall_records':checked,'shaded_wall_records':lit_count,'identical_surface_and_lighting_bytes':total,'exact_write_state_bytes':state_bytes,'scope':'Native extraction and owned write classifications from captured memory; live bridge test follows. Extended vertical UV mode explicitly unsupported.'}
(root/'native-wall-tests.json').write_text(json.dumps(report,indent=2));print(report)

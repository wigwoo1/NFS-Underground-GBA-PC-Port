from pathlib import Path
import ctypes as C,struct,json
from scene_batches import batches,records
root=Path('work/camera');d=C.CDLL(str((root/'native_surface.dll').resolve()));Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
d.nf_extract_model.argtypes=[Reader,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.POINTER(C.c_void_p),C.POINTER(C.c_size_t)];d.nf_surface_free.argtypes=[C.c_void_p]
regions=[]
@Reader
def read(context,address,out,size):
 for base,data in regions:
  if base<=address and address+size<=base+len(data):C.memmove(out,data[address-base:address-base+size],size);return 1
 return 0
expected={}
for scene in batches(root/'world.bin'):
 event=next(e for e in scene['events'] if e['pc']==0x030045e0);packet=(root/'packet-sequence'/f"scene-{scene['serial']:03}.packet").read_bytes();offset,size=struct.unpack_from('<2I',packet,36);expected[event['frame']]=packet[offset:offset+size]
rotations={};caller=None;checked=0;total=0
for e in records(root/'world.bin'):
 b=e['blocks']
 if e['pc']==0x0806db14:rotations[b[73][0]]=b[71][1]
 elif e['pc']==0x03002628:caller=e
 elif e['pc']==0x030045e0 and e['frame'] in expected:
  cb=caller['blocks'];regions=[v for v in b.values() if v[1]]+[v for v in cb.values() if v[1]];rotation=C.create_string_buffer(rotations[b[53][0]])
  out=C.c_void_p();size=C.c_size_t();assert d.nf_extract_model(read,None,b[51][0],cb[63][0],cb[62][0],rotation,C.byref(out),C.byref(size)),e['id']
  assert C.string_at(out,size.value)==expected[e['frame']],e['id'];d.nf_surface_free(out);checked+=1;total+=size.value
assert checked==48
report={'result':'PASS','model_sections_byte_identical':checked,'total_bytes':total,'scope':'Native mesh, texture and independent camera/object pose extraction from captured memory. Live verification is covered separately by test_live_models.py.'}
(root/'native-model-section-tests.json').write_text(json.dumps(report,indent=2));print(report)

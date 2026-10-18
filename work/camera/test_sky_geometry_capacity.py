import ctypes as C,json,struct,hashlib
from pathlib import Path
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-wall-capture-stages-20261006')
results=[]
for path in [cp/'bridge-before-capacity.dll',Path('work/camera/sky-caller-probe.dll')]:
 d=C.CDLL(str(path.resolve()));d.nf_geometry_sources_append.argtypes=[C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint];d.nf_geometry_sources_read.argtypes=[C.c_uint,C.c_void_p,C.c_size_t,C.c_void_p]
 d.nf_geometry_sources_reset();expected=bytearray()
 for index in range(80):
  raw=[bytes([(index+j)%256])*(65536 if j==8 else 32+j) for j in range(12)]
  buffers=[C.create_string_buffer(x) for x in raw];blocks=(C.c_void_p*12)(*[C.addressof(x) for x in buffers]);sizes=(C.c_uint*12)(*[len(x) for x in raw])
  assert d.nf_geometry_sources_append(2,index,blocks,sizes,12)
  expected.extend(struct.pack('<4I',0x3147534e,2,index,12))
  for x in raw:expected.extend(struct.pack('<I',len(x)));expected.extend(x)
  for x in buffers:C.memset(C.addressof(x),0,len(x))
 assert d.nf_geometry_sources_close(1)
 def read(refresh):
  size=C.c_size_t();assert d.nf_geometry_sources_read(refresh,None,0,C.byref(size));out=C.create_string_buffer(size.value);assert d.nf_geometry_sources_read(refresh,out,len(out),C.byref(size));return out.raw
 assert read(1)==expected
 assert not d.nf_geometry_sources_append(0,0,blocks,sizes,12)
 assert not d.nf_geometry_sources_close(2)
 assert read(1)==expected
 for refresh in range(3,19):
  assert d.nf_geometry_sources_append(1,refresh,blocks,sizes,12);assert d.nf_geometry_sources_close(refresh)
 size=C.c_size_t();assert not d.nf_geometry_sources_read(1,None,0,C.byref(size))
 d.nf_geometry_sources_reset();assert not d.nf_geometry_sources_read(18,None,0,C.byref(size))
 results.append(dict(binary=str(path),record_bytes=len(expected),sha256=hashlib.sha256(expected).hexdigest(),checks=['byte exact80records','borrowed input independence','rejected invalid build','retained snapshot independence','ring overwrite rejection','reset rejection']))
assert results[0]['sha256']==results[1]['sha256'];(cp/'capacity-tests.json').write_text(json.dumps(results,indent=2));print('PASS capacity byte ownership and lifecycle for both bridges')

import ctypes as C,json,hashlib
from pathlib import Path
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-plan-rom-copy-20261006')
setup=Path('work/camera/test_sky_producer_only.py').read_text().split('rows=[]')[0]
results=[]
for binary in [str((cp/'bridge-before.dll').resolve()).replace('\\','/'),'sky-caller-probe.dll']:
 ns={};exec(compile(setup.replace("'sky-caller-probe.dll'",repr(binary)),'equivalence-setup','exec'),ns);d=ns['producer'];d.nf_geometry_sources_read.argtypes=[C.c_uint,C.c_void_p,C.c_size_t,C.c_void_p];frames={}
 try:
  for index in range(120):
   d.nf_frame(1);refresh=d.nf_native_live_latest_frame()
   if not refresh or refresh in frames:continue
   size=C.c_size_t();assert d.nf_geometry_sources_read(refresh,None,0,C.byref(size));out=C.create_string_buffer(size.value);assert d.nf_geometry_sources_read(refresh,out,len(out),C.byref(size));frames[refresh]=dict(bytes=size.value,sha256=hashlib.sha256(out.raw).hexdigest())
   vram=C.create_string_buffer(0x18000);generation=C.c_uint64();d.nf_native_live_frame_vram.argtypes=[C.c_uint,C.c_void_p,C.c_uint,C.c_void_p];assert d.nf_native_live_frame_vram(refresh,vram,len(vram),C.byref(generation));frames[refresh]['legacy_vram_sha256']=hashlib.sha256(vram.raw).hexdigest();frames[refresh]['generation']=generation.value
 finally:d.nf_close()
 assert frames;results.append(frames)
assert results[0]==results[1], 'Actual captured geometry differs'
(cp/'actual-geometry-equivalence.json').write_text(json.dumps(dict(frames=len(results[0]),captured=results[0],exact=True),indent=2));print('PASS actual captured geometry',len(results[0]))

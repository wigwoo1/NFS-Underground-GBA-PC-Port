import ctypes as C,hashlib,json
from pathlib import Path
paths=['owned-d3d-present-profile-candidate.dll','owned-d3d-lazy-readback-candidate.dll'];digests=[]
for name in paths:
 d=C.CDLL(str((Path('work/camera')/name).resolve()));d.nf_d3d_clear.argtypes=[C.c_void_p];d.nf_d3d_read.argtypes=[C.c_void_p,C.c_size_t]
 lazy='lazy' in name
 assert d.nf_d3d_open()==0
 try:
  if lazy:
   assert d.nf_d3d_readback_allocated()==0
   assert d.nf_d3d_read(None,0)==1 and d.nf_d3d_readback_allocated()==0
  color=(C.c_float*4)(.25,.5,.75,1);assert d.nf_d3d_clear(color)==0
  pixels=C.create_string_buffer(3840*2160*4);assert d.nf_d3d_read(pixels,len(pixels))==0
  first=hashlib.sha256(pixels.raw).hexdigest();assert d.nf_d3d_read(pixels,len(pixels))==0 and hashlib.sha256(pixels.raw).hexdigest()==first
  if lazy:assert d.nf_d3d_readback_allocated()==1
  digests.append(first)
 finally:assert d.nf_d3d_close()==0
 if lazy:assert d.nf_d3d_readback_allocated()==0
assert len(set(digests))==1
out=dict(result='PASS_LAZY_READBACK_COMPONENT',rgba_sha256=digests[0],deferred_payload_bytes=3840*2160*4,scope='Actual 4K clear/readback equality with prior renderer, invalid request allocation atomicity and close release. Textured full-scene parity/live timing pending.')
Path('work/camera/prototype-runs/native-lazy-readback-tests.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))

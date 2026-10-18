import ctypes as C
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import owned_source_d3d_texture_backdrop_consumer_memcmp_candidate as candidate

class FakeD3D:
 def __init__(self):self.calls=[]
 def nf_d3d_texture(self,identity,w,h,pixels,n):
  self.calls.append((identity,w,h,C.string_at(pixels,n)))
  return 0

def make():
 c=candidate.OwnedD3DConsumer.__new__(candidate.OwnedD3DConsumer)
 c.texture_cache={};c.texture_cache_bytes=0;c.texture_uploads=0;c.texture_reuses=0;c.d=FakeD3D()
 return c

def ptr(data):
 b=C.create_string_buffer(bytes(data))
 return b,C.cast(b,C.c_void_p)

c=make();a,pa=ptr(bytes(range(256))*600);n=153600
c.upload_texture(7,240,160,pa,n)
assert c.texture_uploads==1 and c.texture_reuses==0 and len(c.d.calls)==1 and c.d.calls[0][3]==bytes(range(256))*600
b,pb=ptr(bytes(range(256))*600)
original=candidate.C.string_at
try:
 candidate.C.string_at=lambda *args:(_ for _ in ()).throw(AssertionError('unchanged-texture path allocated a copy'))
 c.upload_texture(7,240,160,pb,n)
finally:candidate.C.string_at=original
assert c.texture_uploads==1 and c.texture_reuses==1 and len(c.d.calls)==1
changed=bytearray(bytes(range(256))*600);changed[777]^=0x80;cc,pc=ptr(changed)
c.upload_texture(7,240,160,pc,n)
assert c.texture_uploads==2 and c.texture_reuses==1 and len(c.d.calls)==2 and c.d.calls[-1][3]==bytes(changed)
samebytes,dims=ptr(changed)
c.upload_texture(7,120,320,dims,n)
assert c.texture_uploads==3 and len(c.d.calls)==3 and c.texture_cache[7][:2]==(120,320)
assert c.texture_cache_bytes==n
c.texture_cache_bytes=16*1024*1024
over,po=ptr(b'x'*(16*1024*1024+1))
before=len(c.d.calls);c.upload_texture(99,1,1,po,16*1024*1024+1)
assert len(c.d.calls)==before+1 and 99 not in c.texture_cache
c.upload_texture(99,1,1,po,16*1024*1024+1)
assert len(c.d.calls)==before+2 and 99 not in c.texture_cache
print('PASS: unchanged 153600-byte texture reuses via direct memcmp with C.string_at disabled; changed bytes, dimensions, replacement accounting and over-cap behavior preserved.')
print({'uploads':c.texture_uploads,'reuses':c.texture_reuses,'cached_bytes':c.texture_cache_bytes,'fake_upload_calls':len(c.d.calls)})
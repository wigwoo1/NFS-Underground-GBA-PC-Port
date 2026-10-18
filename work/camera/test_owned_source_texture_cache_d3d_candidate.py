import ctypes as C,hashlib,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from owned_source_d3d_texture_backdrop_consumer_memcmp_candidate import OwnedD3DConsumer
c=OwnedD3DConsumer();d=c.d;rgba_bytes=3840*2160*4
d.nf_d3d_texture.argtypes=[C.c_uint]*3+[C.c_void_p,C.c_size_t]
d.nf_d3d_draw.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
d.nf_d3d_clear.argtypes=[C.c_void_p];d.nf_d3d_read.argtypes=[C.c_void_p,C.c_size_t]
pattern=np.array([[255,0,0,255],[0,255,0,255],[0,0,255,255],[255,255,0,255]],dtype=np.uint8).tobytes()
def source(data):
 b=C.create_string_buffer(data);return b,C.cast(b,C.c_void_p)
def render():
 clear=(C.c_float*4)(0,0,0,1);assert d.nf_d3d_clear(clear)==0
 v=np.asarray([[0,0,0,0,0,1,1,1,1,1],[3840,0,1,0,0,1,1,1,1,1],[0,2160,0,1,0,1,1,1,1,1],[3840,0,1,0,0,1,1,1,1,1],[3840,2160,1,1,0,1,1,1,1,1],[0,2160,0,1,0,1,1,1,1,1]],dtype=np.float32)
 config=(C.c_float*8)(0,3840,2160,0,1,0,0,0);rect=(C.c_int*8)(0,0,3840,2160,0,0,3840,2160)
 assert d.nf_d3d_draw(v.ctypes.data,6,3001,0,0,config,rect)==0
 out=C.create_string_buffer(rgba_bytes);assert d.nf_d3d_read(out,rgba_bytes)==0
 return out.raw
try:
 a,pa=source(pattern);c.upload_texture(3001,2,2,pa,len(pattern));first=render()
 b,pb=source(pattern);before=(c.texture_uploads,c.texture_reuses);c.upload_texture(3001,2,2,pb,len(pattern));second=render()
 assert first==second,'unchanged cache hit altered rendered RGBA'
 assert (c.texture_uploads,c.texture_reuses)==(before[0],before[1]+1)
 changed=bytearray(pattern);changed[0:4]=bytes([0,0,0,255]);cc,pc=source(bytes(changed));c.upload_texture(3001,2,2,pc,len(changed));third=render()
 assert third!=second,'changed texture did not alter rendered RGBA'
 print({'result':'PASS_D3D_MEMCMP_CACHE_PIXEL_PARITY','target_rgba_bytes':rgba_bytes,'unchanged_hit_identical':True,'changed_content_reuploaded_and_visible':True,'uploads':c.texture_uploads,'reuses':c.texture_reuses,'first_hash':hashlib.sha256(first).hexdigest(),'same_hash':hashlib.sha256(second).hexdigest(),'changed_hash':hashlib.sha256(third).hexdigest()})
finally:c.close()
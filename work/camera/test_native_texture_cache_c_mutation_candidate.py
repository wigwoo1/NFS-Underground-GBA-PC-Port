"""Real GPU texture identity/content/dimension changes and cache teardown."""
import ctypes as C,json,numpy as np
from pathlib import Path
from owned_source_d3d_native_texture_cache_consumer_candidate import OwnedD3DConsumer
consumer=OwnedD3DConsumer();checks=[]
try:
 d=consumer.d;config=(C.c_float*8)(0,3840,2160,0,1,0,0,0);rect=(C.c_int*8)(0,0,3840,2160,0,0,3840,2160)
 v=np.asarray([[x,y,u,v,0,1,1,1,1,1] for x,y,u,v in [(0,0,0,0),(3840,0,1,0),(0,2160,0,1),(3840,0,1,0),(3840,2160,1,1),(0,2160,0,1)]],np.float32)
 for w,color in [(1,bytes([255,0,0,255])),(1,bytes([255,0,0,255])),(1,bytes([0,255,0,255])),(2,bytes([0,0,255,255])),(1,bytes([255,0,0,255]))]:
  data=C.create_string_buffer(color*w);consumer.upload_texture(7,w,1,data,w*4)
  assert d.nf_d3d_draw(v.ctypes.data,6,7,0,0,config,rect)==0
  rgba=C.create_string_buffer(3840*2160*4);assert d.nf_d3d_read(rgba,len(rgba))==0
  at=(1080*3840+1920)*4;assert rgba.raw[at:at+4]==color
  checks.append(dict(width=w,color=list(color),uploads=consumer.texture_uploads,reuses=consumer.texture_reuses))
 assert consumer.texture_uploads==4 and consumer.texture_reuses==1
 stats=(C.c_uint64*3)();assert d.nf_d3d_texture_cache_stats(stats)==0 and list(stats)==[4,1,4]
finally:consumer.close()
assert consumer.texture_cache_bytes==0 and not consumer.texture_cache
assert d.nf_d3d_texture_cache_stats(stats)==0 and stats[2]==0
out=dict(cache_upload_requests=4,cache_reuses=1,result='PASS_REAL_GPU_CACHE_MUTATIONS',checks=checks,closed_cache_empty=True,scope='Real GPU center pixel validates exact repeat/content change/dimension change/reversion on same texture ID; not broad scene/visible cadence proof')
Path('work/camera/prototype-runs/native-texture-cache-c-mutations.json').write_text(json.dumps(out,indent=2));print(out['result'])

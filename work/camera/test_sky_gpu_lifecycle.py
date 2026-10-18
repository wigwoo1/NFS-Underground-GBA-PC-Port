import ctypes as C,struct,os,json
from pathlib import Path
from owned_sky_sampler import SkySamples
from owned_sky_color import sky_rgba
os.environ['NF_GPU_BACKGROUND_ONLY']='1'
crt=C.CDLL('msvcrt');assert crt._putenv(b'NF_GPU_BACKGROUND_ONLY=1')==0
p=Path('work/camera');raw=bytearray((p/'motion-actual-scanline-assets/8758-owned-background-frame.bin').read_bytes());magic,r,gn,hn,bn=struct.unpack_from('<5I',raw);assert magic==0x3246474e and bn==76800
for y in range(160):
 base=20+gn+y*34944;struct.pack_into('<H',raw,base+8,0x404);struct.pack_into('<3H',raw,base+8+0x50,0,0,0)
bg=20+gn+hn;lower=bytes(raw[bg+10560:bg+25696]);upper=lower[1:]+lower[:1]
raw[bg+38400+10560:bg+38400+25696]=bytes([1])*15136
palettes=b''.join(raw[20+gn+y*34944+128+32768:20+gn+y*34944+128+32768+512] for y in range(160))
d=C.CDLL(str((p/'owned-sky-gpu.dll').resolve()));api=d.nf_owned_gpu_render_sky;api.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_size_t,C.c_double,C.c_void_p,C.c_size_t]
frame=C.create_string_buffer(bytes(raw));a=C.create_string_buffer(lower);b=C.create_string_buffer(upper);out=C.create_string_buffer(3840*2160*3);checks=[]

baseline_api=d.nf_owned_gpu_render;baseline_api.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
assert crt._putenv(b'NF_GPU_BACKGROUND_ONLY=')==0
negative=0
try:
 assert baseline_api(frame,len(raw),out,len(out))==0;baseline=out.raw
 assert api(frame,len(raw),a,b,15136,0,out,len(out))==0 and out.raw==baseline
 for lowerbuf,upperbuf,count,weight in ((None,b,15136,0),(a,None,15136,0),(a,b,15135,0),(a,b,15136,-.1),(a,b,15136,1),(a,b,15136,float('nan')),(a,b,15136,float('inf'))):
  before=out.raw;assert api(frame,len(raw),lowerbuf,upperbuf,count,weight,out,len(out))==41 and out.raw==before;negative+=1
 bad=bytearray(raw);bad[bg+38400+10560]=0;badframe=C.create_string_buffer(bytes(bad));before=out.raw
 assert api(badframe,len(bad),a,b,15136,0,out,len(out))==41 and out.raw==before;negative+=1
 import threading
 results=[]
 thread=threading.Thread(target=lambda:results.append(api(frame,len(raw),a,b,15136,0,out,len(out))));thread.start();thread.join();assert results==[31] and out.raw==before;negative+=1
 assert api(frame,len(raw),a,b,15136,0,out,len(out))==0 and out.raw==baseline
 # Version3 carries explicit epoch/timing and preserved text plane.
 v3=struct.pack('<6I2Q',0x3346474e,r,gn,hn,76800,76800,2,r*280896)+bytes(raw[20:])+bytes(76800);v3buf=C.create_string_buffer(v3)
 assert crt._putenv(b'NF_GPU_EXPECT_EPOCH=3')==0;before=out.raw
 assert api(v3buf,len(v3),a,b,15136,0,out,len(out))==29 and out.raw==before;negative+=1
 assert crt._putenv(b'NF_GPU_EXPECT_EPOCH=2')==0
 assert api(v3buf,len(v3),a,b,15136,0,out,len(out))==0
finally:crt._putenv(b'NF_GPU_EXPECT_EPOCH=');assert d.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-gpu-lifecycle-20261006');cp.mkdir(exist_ok=True)
for name in ('owned_gpu_sky_candidate.c','test_sky_gpu_lifecycle.py'):(cp/name).write_text((p/name).read_text())
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',full_scene_endpoint_bytes=len(baseline),negative_checks=negative,scope='Full geometry/HUD endpoint equals original frame; null/count/fraction/coverage/thread/epoch rejections leave CPU output unchanged; valid retry and close PASS. Not live interpolation/cadence'),indent=2));print('PASS sky GPU lifecycle',negative)

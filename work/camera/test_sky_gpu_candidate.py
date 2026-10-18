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
assert baseline_api(frame,len(raw),out,len(out))==0;baseline=out.raw
try:
 for weight in (0,.25,.5,.75):
  assert api(frame,len(raw),a,b,15136,weight,out,len(out))==0
  pixels=out.raw
  if weight==0:assert pixels==baseline,'Endpoint changed original full framebuffer'
  reference=sky_rgba(SkySamples(lower,upper,weight,0x06002940),palettes);maximum=0;outside=0
  for y in range(160):
   for x in range(240):
    i=y*240+x;at=(int((y+.5)*13.5)*3840+int(300+(x+.5)*13.5))*3;actual=pixels[at:at+3]
    if 10560<=i<25696:expected=reference[(i-10560)*4:(i-10560)*4+3];error=max(abs(v-w) for v,w in zip(actual,expected));maximum=max(maximum,error);assert error<=(0 if weight==0 else 1),(weight,x,y,actual,expected)
    else:
     assert actual==baseline[at:at+3],(weight,x,y,actual,baseline[at:at+3]);outside+=1
  checks.append(dict(weight=weight,sky_centers=15136,unchanged_outside_centers=outside,max_channel_error=maximum))
finally:assert d.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-gpu-color-candidate-20261006');cp.mkdir(exist_ok=True)
for name in ('owned_gpu_sky_candidate.c','build-sky-gpu-candidate.ps1','test_sky_gpu_candidate.py'):(cp/name).write_text((p/name).read_text())
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Isolated 4K GPU background composition: original palette/index endpoint exact, fractional GLblend within1channelunit, all outside centers unchanged. Not live scene interpolation or cadence'),indent=2));print('PASS sky GPU',checks)

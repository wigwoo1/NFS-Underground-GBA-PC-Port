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

from owned_sky_sampler import SkyAsset
recorded={};exec((p/'test_owned_sky_boundary.py').read_text().split("out=Path(")[0],recorded)
records=recorded['records'];rom=recorded['rom'];origin=records[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376]);wraps=[(a,b) for a,b in zip(records,records[1:]) if abs(a.source-b.source)>120];checks=[]
try:
 for older,newer in wraps:
  lo=((older.angle&16383)*240/4096)%240;travel=(((newer.angle-older.angle+8192)&16383)-8192)*240/4096;seam=(240-lo)/travel if travel>0 else -lo/travel
  assert 0<=seam<=1
  for alpha in (0,max(0,seam-1e-6),min(1,seam+1e-6),1):
   samples=asset.sample_continuous(older,newer,alpha);lowerbuf=C.create_string_buffer(samples.lower);upperbuf=C.create_string_buffer(samples.upper)
   assert api(frame,len(raw),lowerbuf,upperbuf,15136,samples.weight,out,len(out))==0
   pixels=out.raw;reference=sky_rgba(samples,palettes);maximum=0
   for i in range(15136):
    y,x=divmod(10560+i,240);at=(int((y+.5)*13.5)*3840+int(300+(x+.5)*13.5))*3
    error=max(abs(a-b) for a,b in zip(pixels[at:at+3],reference[i*4:i*4+3]));maximum=max(maximum,error)
    assert error<=1,(older.refresh,newer.refresh,alpha,i,error)
   checks.append(dict(older=older.refresh,newer=newer.refresh,alpha=alpha,weight=samples.weight,max_channel_error=maximum))
finally:assert d.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-continuous-gpu-readback-20261006');cp.mkdir(exist_ok=True)
for name in ('test_sky_continuous_gpu_readback.py','owned_sky_sampler.py'):(cp/name).write_text((p/name).read_text())
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',wraps=len(wraps),readbacks=len(checks),sky_centers_per_readback=15136,checks=checks,scope='Actual recorded ROM steering wrap source pairs rendered at4K before/after seam; continuous native phase including endpoints; palettecolors within1unit. Background-only diagnostic, not captured live fullscene/scanout'),indent=2));print('PASS continuous sky GPU wraps',len(wraps),'readbacks',len(checks))

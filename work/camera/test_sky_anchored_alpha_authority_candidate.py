import ctypes as C,json,struct,hashlib
from pathlib import Path
import numpy as np
p=Path('work/camera');report=json.loads((p/'prototype-runs/owned-native-1791512193343217400.json').read_text());origin=report['sky_capture_records'][0]['asset_origin']
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();asset=rom[origin-0x08000000:origin-0x08000000+15376];assert len(asset)==15376
frame=(p/'prototype-runs/profile-scene-1791434844226808400/older.frame.bin').read_bytes();gn=struct.unpack_from('<I',frame,8)[0];pal=np.stack([np.frombuffer(frame,dtype='<u2',count=256,offset=40+gn+y*34944+32896) for y in range(160)])
d=C.CDLL(str((p/'owned-d3d-sky-anchored-coverage-candidate.dll').resolve()));P=C.c_void_p
for n,a in [('nf_d3d_clear',[P]),('nf_d3d_texture',[C.c_uint,C.c_uint,C.c_uint,P,C.c_size_t]),('nf_d3d_read',[P,C.c_size_t]),('nf_d3d_sky_pan',[C.c_float]),('nf_d3d_sky_quad',[C.c_uint,C.c_float])]:getattr(d,n).argtypes=a
assert d.nf_d3d_open()==0;buf=C.create_string_buffer(3840*2160*4)
def draw(phase):
 assert d.nf_d3d_clear((C.c_float*4)(0,0,0,1))==0;assert d.nf_d3d_sky_pan(phase)==0;assert d.nf_d3d_read(buf,len(buf))==0
 return np.frombuffer(buf.raw,np.uint8).reshape(2160,3840,4).copy()

def upload(base):
 planes=[]
 for offset in (base,(base+1)%240):
  a=np.zeros((160,240,4),np.uint8);i=np.arange(15136);y=44+i//240;x=i%240;indices=np.frombuffer(asset[offset:offset+15136],np.uint8);colors=pal[y,indices]
  for k in range(3):v=(colors>>(5*k))&31;a[y,x,k]=(v<<3)|(v>>2)
  a[y,x,3]=255;planes.append(a)
 for layer,a in enumerate(planes):assert d.nf_d3d_texture(1001+layer,240,160,a.ctypes.data,a.nbytes)==0
 return planes


rows=[];failures=[]
try:
 lo=np.empty((160,240,4),np.uint8);hi=np.empty_like(lo)
 lo[:]=[220,40,80,255];hi[:]=[30,200,140,255]
 # Four alpha domains, including transparent upper over opaque lower.
 lo[:,np.arange(240)%4<2,3]=0
 hi[:,np.arange(240)%4%2==0,3]=0
 for layer,plane in enumerate((lo,hi)):assert d.nf_d3d_texture(1001+layer,240,160,plane.ctypes.data,plane.nbytes)==0
 x=np.floor((np.arange(3240)+.5)*2/27).astype(int)
 u=(np.arange(3240)+.5)*2/27
 for phase in (0,.125,.5,.875,1):
  assert d.nf_d3d_clear((C.c_float*4)(17/255,51/255,85/255,1))==0
  assert d.nf_d3d_sky_pan(phase)==0;assert d.nf_d3d_read(buf,len(buf))==0
  actual=np.frombuffer(buf.raw,np.uint8).reshape(2160,3840,4)
  lower=lo[0,x];upper=hi[0,x];shift=np.floor(u+phase)>np.floor(u)
  opaque=(lower[:,3]>127)&(upper[:,3]>127)
  edge=(np.floor(u)+1)*13.5;centers=np.arange(3240)+.5;support=np.minimum(1,edge-centers)
  coverage=np.clip((phase*13.5-(edge-centers-support))/support,0,1)
  blended=np.rint(lower.astype(float)+(upper.astype(float)-lower.astype(float))*coverage[:,None]).astype(np.uint8)
  selected=np.where(opaque[:,None],blended,np.where(shift[:,None],upper,lower))
  expected=np.empty((3840,4),np.uint8);expected[:]=[17,51,85,255]
  expected[300:3540]=np.where(selected[:,3:4]>127,selected,expected[300:3540])
  mismatch=int(np.count_nonzero(np.any(np.abs(actual.astype(np.int16)-expected[None,:,:].astype(np.int16))>1,axis=2)))
  rows.append(dict(phase=phase,mismatches=mismatch))
  if mismatch:failures.append(phase)
finally:assert d.nf_d3d_close()==0
out=dict(result='FAIL_SKY_ALPHA_AUTHORITY' if failures else 'PASS_SKY_ALPHA_AUTHORITY',samples=rows,scope='Synthetic four opaque/transparent endpoint domains over nonblack background, actual4K readback; intermediate opaque coverage within1UNORM, alpha selection/discard preserved as discrete authority. Not live occlusions.')
(p/'prototype-runs/sky-anchored-alpha-authority-20261009.json').write_text(json.dumps(out,indent=2));print(out)
assert not failures

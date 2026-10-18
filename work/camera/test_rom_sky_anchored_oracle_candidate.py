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
rows=[]
try:
 for base in (0,58,238,239):
  planes=[]
  for offset in (base,(base+1)%240):
   a=np.zeros((160,240,4),np.uint8);i=np.arange(15136);y=44+i//240;x=i%240;indices=np.frombuffer(asset[offset:offset+15136],np.uint8);colors=pal[y,indices]
   for k in range(3):v=(colors>>(5*k))&31;a[y,x,k]=(v<<3)|(v>>2)
   a[y,x,3]=255;planes.append(a)
  for layer,a in enumerate(planes):assert d.nf_d3d_texture(1001+layer,240,160,a.ctypes.data,a.nbytes)==0
  lo=draw(0);hi=draw(1)
  for phase in (0,.125,.25,.5,.75,.875,1):
   actual=draw(phase);u=(np.arange(3240)+.5)*2/27;v=(np.arange(2160)+.5)*2/27;x=np.floor(u).astype(int);y=np.floor(v).astype(int);shift=np.floor(u+phase)>np.floor(u)
   lower=planes[0][y[:,None],x[None,:]];upper=planes[1][y[:,None],x[None,:]]
   # Independent screen-space area of a translating vertical boundary.
   # Screen distance from each output center to the next source edge.
   centers=np.arange(3240)+.5
   edge=(np.floor(u)+1)*13.5
   support=np.minimum(1,edge-centers)
   overlap=np.minimum(support,np.maximum(0,phase*13.5-(edge-centers-support)))
   coverage=overlap/support
   blended=np.rint(lower.astype(float)+(upper.astype(float)-lower.astype(float))*coverage[None,:,None]).astype(np.uint8)
   selected=np.where(((lower[:,:,3]>127)&(upper[:,:,3]>127))[:,:,None],blended,np.where(shift[None,:,None],upper,lower))
   expected=np.zeros((2160,3840,4),np.uint8);expected[:,:,3]=255;expected[:,300:3540]=np.where(selected[:,:,3:4]>127,selected,expected[:,300:3540]);mismatch=int(np.count_nonzero(np.any(np.abs(actual.astype(np.int16)-expected.astype(np.int16))>1,axis=2)));assert mismatch==0,(base,phase,mismatch)
   rows.append(dict(base=base,phase=phase,sha256=hashlib.sha256(actual.tobytes()).hexdigest(),mismatches=mismatch))
finally:assert d.nf_d3d_close()==0
out=dict(result='PASS_ROM_SKY_ANCHORED_INTERMEDIATE_ORACLE',asset_origin=origin,fixture_palette_frame='profile-scene-1791434844226808400/older.frame.bin',samples=rows,scope='Actual ROM indexed asset and captured scanline palettes, 4K GPU versus independent CPU endpoint-anchored screen-space interval overlap, within1UNORM. Includes239->0 wrap and16byte final row. Endpoint source-plane conversion is Python here, not live callback extraction or physical60fps; alpha boundaries retain discrete behavior.')
(p/'prototype-runs/rom-sky-anchored-oracle-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])


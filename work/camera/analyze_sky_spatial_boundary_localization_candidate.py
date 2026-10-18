import ctypes as C,json,struct,hashlib
from pathlib import Path
import numpy as np
p=Path('work/camera');report=json.loads((p/'prototype-runs/owned-native-1791512193343217400.json').read_text());origin=report['sky_capture_records'][0]['asset_origin']
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();asset=rom[origin-0x08000000:origin-0x08000000+15376];assert len(asset)==15376
frame=(p/'prototype-runs/profile-scene-1791434844226808400/older.frame.bin').read_bytes();gn=struct.unpack_from('<I',frame,8)[0];pal=np.stack([np.frombuffer(frame,dtype='<u2',count=256,offset=40+gn+y*34944+32896) for y in range(160)])
d=C.CDLL(str((p/'owned-d3d-sky-spatial-coverage-candidate.dll').resolve()));P=C.c_void_p
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


rows=[]
try:
 for base in (58,239):
  planes=upload(base);actual=draw(1)
  x=np.floor((np.arange(3240)+.5)*2/27).astype(int);y=np.floor((np.arange(2160)+.5)*2/27).astype(int)
  selected=planes[1][y[:,None],x[None,:]]
  expected=np.zeros_like(actual);expected[:,:,3]=255
  expected[:,300:3540]=np.where(selected[:,:,3:4]>127,selected,expected[:,300:3540])
  mismatch=np.any(actual!=expected,axis=2)
  columns=np.flatnonzero(mismatch.any(axis=0))
  tied=np.zeros(3840,dtype=bool);tied[300+np.arange(13,3240,27)]=True
  outside=int(np.count_nonzero(mismatch[:,~tied]))
  assert outside==0,(base,outside)
  upload((base+1)%240);start=draw(0)
  rollover=int(np.count_nonzero(np.any(actual!=start,axis=2)))
  rows.append(dict(base=base,mismatched_pixels=int(mismatch.sum()),mismatched_columns=columns.tolist(),predicted_tie_columns=120,mismatches_outside_exact_source_boundary_columns=outside,rollover_mismatches=rollover))
finally:assert d.nf_d3d_close()==0
out=dict(result='CONFIRMED_PIXEL_CENTER_BOUNDARY_COVERAGE_MISMATCH',rows=rows,scope='Actual4K GPU mismatch localization. At scale13.5, output centers13+27k coincide with source boundaries. Symmetric area filter returns half coverage atphase1; original nearest endpoint selects full upper. Candidate must remain isolated.')
(p/'prototype-runs/sky-spatial-boundary-localization-20261009.json').write_text(json.dumps(out,indent=2));print(out['result']);print([(r['base'],r['mismatched_pixels'],r['rollover_mismatches']) for r in rows])

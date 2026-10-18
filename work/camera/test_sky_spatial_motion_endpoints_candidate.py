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

rows=[];endpoints=[];seams=[]
try:
 for base in (58,239):
  planes=upload(base);previous=None;holds=0
  for index in range(60):
   phase=index/59;actual=draw(phase)
   digest=hashlib.sha256(actual.tobytes()).hexdigest()
   holds+=digest==previous;previous=digest
   rows.append(dict(base=base,index=index,phase=phase,sha256=digest))
   if index in (0,59):
    plane=planes[index==59]
    x=np.floor((np.arange(3240)+.5)*2/27).astype(int);y=np.floor((np.arange(2160)+.5)*2/27).astype(int)
    selected=plane[y[:,None],x[None,:]]
    expected=np.zeros_like(actual);expected[:,:,3]=255
    expected[:,300:3540]=np.where(selected[:,:,3:4]>127,selected,expected[:,300:3540])
    mismatch=int(np.count_nonzero(np.any(actual!=expected,axis=2)))
    if mismatch:
     delta=np.abs(actual.astype(np.int16)-expected.astype(np.int16))
     failure=dict(result='FAIL_EXACT_ORIGINAL_SKY_ENDPOINT',base=base,index=index,phase=phase,mismatched_pixels=mismatch,max_channel_difference=int(delta.max()),actual_sha256=hashlib.sha256(actual.tobytes()).hexdigest(),expected_sha256=hashlib.sha256(expected.tobytes()).hexdigest(),scope='Full3840x2160 GPU versus exact original nearest endpoint. Prior tolerance1 spatial coverage oracle does not establish exact original endpoint fidelity. Do not promote.')
     (p/'prototype-runs/sky-spatial-endpoint-failure-20261009.json').write_text(json.dumps(failure,indent=2))
    assert mismatch==0,(base,index,mismatch)
    endpoints.append(dict(base=base,index=index,exact_mismatches=mismatch))
   if index==59:end=actual
  upload((base+1)%240);start=draw(0)
  mismatch=int(np.count_nonzero(np.any(end!=start,axis=2)))
  assert mismatch==0,(base,'seam',mismatch)
  seams.append(dict(base=base,next_base=(base+1)%240,exact_mismatches=mismatch,unchanged_transitions=holds))
  print('base',base,'holds',holds,'seam exact',flush=True)
finally:assert d.nf_d3d_close()==0
out=dict(result='PASS_SPATIAL_SKY_ENDPOINTS_AND_ROLLOVER',samples=rows,endpoints=endpoints,seams=seams,scope='120 actual4K diagnostic readbacks; exact original nearest endpoints, ordinary and239->0 source-plane rollover. Hash changes are component image motion, not wall-clock60fps or live fullscene scanout. Transparency boundary policy remains discrete.')
(p/'prototype-runs/sky-spatial-motion-endpoints-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])

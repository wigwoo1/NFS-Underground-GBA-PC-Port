import ctypes as C,json,threading
from pathlib import Path
import numpy as np
p=Path('work/camera');d=C.CDLL(str((p/'owned-d3d-sky-pan-candidate.dll').resolve()));P=C.c_void_p
for n,a in [('nf_d3d_clear',[P]),('nf_d3d_texture',[C.c_uint,C.c_uint,C.c_uint,P,C.c_size_t]),('nf_d3d_read',[P,C.c_size_t]),('nf_d3d_sky_pan',[C.c_float]),('nf_d3d_sky_quad',[C.c_uint,C.c_float])]:getattr(d,n).argtypes=a
assert d.nf_d3d_open()==0
buf=C.create_string_buffer(3840*2160*4)
def read():
 assert d.nf_d3d_read(buf,len(buf))==0
 return np.frombuffer(buf.raw,np.uint8).reshape(2160,3840,4).copy()
def clear():assert d.nf_d3d_clear((C.c_float*4)(0,0,0,1))==0
try:
 assert d.nf_d3d_sky_pan(.5)==1
 for layer,edge in enumerate((120,119)):
  a=np.zeros((160,240,4),np.uint8);a[44:107,edge:]=[255,0,0,255];a[107,:16]=[0,255,0,255]
  assert d.nf_d3d_texture(1001+layer,240,160,a.ctypes.data,a.nbytes)==0
 endpoint_differences=[];positions=[]
 for phase in np.linspace(0,1,61):
  clear();assert d.nf_d3d_sky_pan(float(phase))==0
  frame=read();xs=np.flatnonzero(frame[700,:,0]);positions.append(int(xs[0]))
  assert np.all(np.isin(frame[700,:,0],[0,255])), 'Unexpected color blending'
  if phase in (0,1):
   clear();assert d.nf_d3d_sky_quad(int(phase),1)==0;endpoint_differences.append(int(np.count_nonzero(np.any(frame!=read(),axis=2))))
 assert positions[0]-positions[-1] in (13,14) and len(set(positions))>=13
 assert all(a>=b for a,b in zip(positions,positions[1:]))
 for bad in (-1,2,float('nan')):assert d.nf_d3d_sky_pan(bad)==1
 results=[];t=threading.Thread(target=lambda:results.append(d.nf_d3d_sky_pan(.5)));t.start();t.join();assert results==[1]
finally:assert d.nf_d3d_close()==0
out=dict(result='PASS_NATIVE_SKY_EDGE_TRANSLATION',samples=61,edge_positions=positions,unique_positions=len(set(positions)),legacy_endpoint_changed_pixels=endpoint_differences,endpoint_reference="Independent CPU mapping in test_rom_sky_pan_candidate.py",scope='Synthetic actual 4K GPU readbacks; isolated component, not live ROM sky integration or 60fps gameplay.')
(p/'prototype-runs/native-sky-pan-component-20261008.json').write_text(json.dumps(out,indent=2));print(out)

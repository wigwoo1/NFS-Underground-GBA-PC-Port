import ctypes as C,threading,json
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'owned-d3d-region-read-candidate.dll').resolve()));P=C.c_void_p
for name,args in [('nf_d3d_clear',[P]),('nf_d3d_read',[P,C.c_size_t]),('nf_d3d_read_region',[C.c_uint]*4+[P,C.c_size_t])]:getattr(d,name).argtypes=args
assert d.nf_d3d_open()==0
rows=[]
try:
 assert d.nf_d3d_clear((C.c_float*4)(.2,.4,.6,1))==0
 full=C.create_string_buffer(3840*2160*4);assert d.nf_d3d_read(full,len(full))==0;data=full.raw
 for x,y,w,h in [(0,600,3840,64),(0,1200,3840,64),(3839,2159,1,1),(123,456,17,9)]:
  out=C.create_string_buffer(w*h*4);assert d.nf_d3d_read_region(x,y,w,h,out,len(out))==0
  expected=b''.join(data[((y+r)*3840+x)*4:((y+r)*3840+x+w)*4] for r in range(h));assert out.raw==expected;rows.append([x,y,w,h])
 guard=C.create_string_buffer(b'guard')
 for x,y,w,h,n in [(3840,0,1,1,4),(0,2160,1,1,4),(0,0,0,1,0),(3839,0,2,1,8),(0,0,1,1,3)]:assert d.nf_d3d_read_region(x,y,w,h,guard,n)==37 and guard.raw==b'guard\0'
 foreign=[];t=threading.Thread(target=lambda:foreign.append(d.nf_d3d_read_region(0,0,1,1,guard,4)));t.start();t.join();assert foreign==[37]
finally:assert d.nf_d3d_close()==0
assert d.nf_d3d_read_region(0,0,1,1,guard,4)==37
(p/'prototype-runs/region-read-component-20261009.json').write_text(json.dumps(dict(passed=True,regions=rows,bounds_owner_closed_rejected=True,scope='ActualD3D clear-target region byte parity versusfull4Kread, bounds/no-write/foreignowner/closed checks; notfullscene/live/performance.'),indent=2));print('PASS_NATIVE_REGION_READ')

from pathlib import Path
import ctypes as C,struct,json,math
root=Path('work/camera');d=C.CDLL(str((root/'native_surface.dll').resolve()));f=d.nf_billboard_quad;f.argtypes=[C.c_void_p,C.c_size_t,C.c_uint32,C.c_uint32,C.c_void_p]
def record(rect,bounds=(0,240,0,160)):
 return struct.pack('<4I4i4I4H',0x3142464e,8,4,0,*rect,0,0,8,4,*bounds)+bytes(128)
cases=[((-120,-80,360,240),(0,240,0,160),[0,0,.25,.25,3840,0,.75,.25,3840,2160,.75,.75,0,2160,.25,.75]),((0,0,240,160),(60,180,40,120),[960,540,.25,.25,2880,540,.75,.25,2880,1620,.75,.75,960,1620,.25,.75]),((60,40,180,120),(0,240,0,160),[960,540,0,0,2880,540,1,0,2880,1620,1,1,960,1620,0,1])]
for rect,bounds,expected in cases:
 b=record(rect,bounds);o=(C.c_double*16)();assert f(C.create_string_buffer(b),len(b),3840,2160,o)==1 and all(math.isclose(a,e,abs_tol=1e-12) for a,e in zip(o,expected))
for rect in [(240,0,300,20),(-30,0,0,20),(0,160,20,200),(0,-20,20,0)]:
 b=record(rect);o=(C.c_double*16)(*([123.0]*16));before=bytes(o);assert f(C.create_string_buffer(b),len(b),3840,2160,o)==0 and bytes(o)==before
b=record((0,0,240,160))
for width,height in [(0,2160),(3840,0),(16385,2160),(3840,16385)]:
 o=(C.c_double*16)(*([123.0]*16));before=bytes(o);assert f(C.create_string_buffer(b),len(b),width,height,o)==-1 and bytes(o)==before
report=dict(result='PASS',analytic_4k_quads=3,outside_atomic=4,invalid_target_atomic=4,scope='Continuous captured-pose geometry only; no GPU render, original byte-lane parity or temporal smoothing claimed.')
(root/'billboard-quad-tests.json').write_text(json.dumps(report,indent=2));print(report)

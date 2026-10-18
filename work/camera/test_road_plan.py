"""Native road coverage plan against independently executed original spans."""
from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();recip=rom[0x627700:0x647700]
d=C.CDLL(str((p/'road-polygon-clip.dll').resolve()));fn=d.nf_road_span_plan;fn.argtypes=[C.c_void_p,C.c_uint,C.c_int32,C.c_int32,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
cases=[];atomic=0
for alpha in ('0.25','0.5','0.75'):
 data=json.loads((p/f'road-clip-inputs-{alpha}-motion-spans-plan.json').read_text());total=0
 for c in data['cases']:
  vertices=struct.pack('<'+'i'*len(c['vertices'])*6,*(v for row in c['vertices'] for v in row));fb=struct.pack('<4I',*c['framebuffer']);args=(vertices,len(c['vertices']),*c['bounds'][2:4],*c['plan_flags'],recip,fb)
  out=C.create_string_buffer(b'X'*8192,8192);n=C.c_uint(123);assert fn(*args,out,512,C.byref(n))
  actual=[list(struct.unpack_from('<4I',out.raw,i*16)) for i in range(n.value)];expected=[[s['params'][6],s['params'][7],s['routine'],s['doubled']] for s in c.get('spans',[])];assert actual==expected
  total+=n.value
  if n.value:
   before=C.create_string_buffer(b'X'*8192,8192);count=C.c_uint(123);assert not fn(*args,before,n.value-1,C.byref(count)) and before.raw==b'X'*8192 and count.value==123;atomic+=1
 cases.append(dict(alpha=float(alpha),roads=len(data['cases']),spans=total))
report=dict(result='PASS',cases=cases,atomic_capacity_rejections=atomic,scope='Exact native coverage schedule against original road routine with span texture writers stubbed; destination,width,routine,doubled flag. Texture interpolation, executed-writer side effects and native4K/live timing not verified.')
(p/'road-plan-tests.json').write_text(json.dumps(report,indent=2));print(report)

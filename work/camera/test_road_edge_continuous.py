from pathlib import Path
import ctypes as C,json,struct,random,math,hashlib
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=C.create_string_buffer(rom[0x627700:0x647700]);d=C.CDLL(str((p/'road-edge-continuous.dll').resolve()));fn=d.nf_road_edge_continuous;fn.argtypes=[C.c_void_p]*4;native=C.CDLL(str((p/'road-polygon-clip.dll').resolve()));step=native.nf_road_edge_step;step.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];rng=random.Random(61005);cases=[]
for i in range(500):
 y=rng.randrange(0,80);h=rng.randrange(1,1000);a=[rng.randrange(-1000,1001),y,0]+[rng.randrange(-1000000,1000001) for k in range(3)];b=[rng.randrange(-1000,1001),y+h,0]+[rng.randrange(-1000000,1000001) for k in range(3)];cases.append((a,b))
for road in json.loads((p/'stable-road-full-span-replay.json').read_text())['checks']:
 ring=road['clipped_source_stream']
 for i,a in enumerate(ring):
  b=ring[(i+1)%len(ring)]
  if a[1]>b[1]:a,b=b,a
  if a[1]<160 and b[1]>a[1]:cases.append((a,b))
exact=continuity=0;max_boundary_delta=0.0
for a,b in cases:
 context=(C.c_uint32*18)();context[8]=context[11]=2;context[13]=160;pair=(C.c_int32*12)(*a,*b);fb=(C.c_uint32*4)(0x0600a000,0,0,240);out=(C.c_uint32*18)();assert step(context,0,0,pair,2,table,fb,out)==1
 actual=(C.c_double*4)();aa=(C.c_double*6)(*a);bb=(C.c_double*6)(*b);assert fn(aa,bb,table,actual);si=lambda x:C.c_int32(x).value;expected=[si(out[4])/65536]+[si(out[k]) for k in (5,6,7)];assert list(actual)==expected;exact+=1
 if b[1]-a[1]<=1:continue
 for field in (0,1,3,4,5):
  epsilon=1e-9;values=[]
  for sign in (-1,1):
   adjusted=list(b);adjusted[field]+=sign*epsilon;v=(C.c_double*4)();assert fn(aa,(C.c_double*6)(*adjusted),table,v);values.append(list(v))
  # Shared cell boundaries should approach the same integer value.
  for values1 in values:
   max_boundary_delta=max(max_boundary_delta,max(abs(values1[k]-actual[k]) for k in range(4)))
   assert all(abs(values1[k]-actual[k])<0.01 for k in range(4))
  continuity+=1
invalid=0
for a,b in [([0]*6,[0]*6),([0]*6,[0,32767,0,1,1,1]),([float('nan')]*6,[0,5,0,1,1,1]),([0]*6,[0,5,0,2147483647,1,1])]:
 out=(C.c_double*4)(123,456,789,1011);assert not fn((C.c_double*6)(*a),(C.c_double*6)(*b),table,out);assert list(out)==[123,456,789,1011];invalid+=1
report=dict(boundary_epsilon=1e-9,max_boundary_delta=max_boundary_delta,result='PASS',integer_native_edge_cases=exact,two_sided_cell_boundary_checks=continuity,atomic_invalid_cases=invalid,component_sha256=hashlib.sha256((p/'road-edge-continuous.dll').read_bytes()).hexdigest(),scope='Exact original slope arithmetic at tested integer endpoints and continuous cell-boundary extension. Includes actual clipped source edges. Does not yet generate native source projections, spans, interior textures, GPU or fullscene motion. Nonpositive heights or>=32767 rejected.');(p/'road-edge-continuous-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))



from pathlib import Path
import ctypes as C,json,struct,random,math
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=C.create_string_buffer(rom[0x627700:0x647700]);clip=C.CDLL(str((p/'road-clip-continuous.dll').resolve())).nf_road_clip_continuous;clip.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];edge=C.CDLL(str((p/'road-edge-continuous.dll').resolve())).nf_road_edge_continuous;edge.argtypes=[C.c_void_p]*4
r=struct.unpack_from('<I',rom,0x627700)[0];assert r==16777216
short=0
for h in (.000001,.001,.1,.25,.5,.75,.999999,1,1.000001):
 a=(C.c_double*6)(0,0,0,10000,20000,30000);b=(C.c_double*6)(10,h,0,11000,22000,33000);out=(C.c_double*4)();assert edge(a,b,table,out);assert all(math.isfinite(v) for v in out);short+=1
rng=random.Random(61007);checked=0;maximum=0
for i in range(200):
 rows=[[rng.randrange(-100,340)+.25]+[rng.randrange(-100000,100000)+.25 for k in range(5)] for j in range(6)];results=[]
 for epsilon in (-1e-8,0,1e-8):
  values=[v+(epsilon if k==0 else 0) for row in rows for k,v in enumerate(row)];out=(C.c_double*768)();n=C.c_uint();assert clip((C.c_double*36)(*values),6,0,238,table,out,128,C.byref(n));results.append(list(out)[:n.value*6])
 assert len(results[0])==len(results[1])==len(results[2])
 for result in (results[0],results[2]):
  difference=max((abs(a-b) for a,b in zip(result,results[1])),default=0);maximum=max(maximum,difference);assert difference<.1
 checked+=1
# Explicit classification crossing; test topology and finite bounded x, not motion fidelity.
topologies=[]
for boundary in (0,238):
 counts=[]
 for epsilon in (-1e-8,0,1e-8):
  rows=[[boundary+epsilon,20,20,10000,20000,30000],[100,30,30,12000,25000,35000],[120,60,60,15000,30000,40000]];out=(C.c_double*768)();n=C.c_uint();assert clip((C.c_double*18)(*[v for row in rows for v in row]),3,0,238,table,out,128,C.byref(n));values=list(out)[:n.value*6];assert all(math.isfinite(v) for v in values);assert all(0<=values[k]<=238 for k in range(0,len(values),6));counts.append(n.value)
 topologies.append(dict(boundary=boundary,counts=counts))
report=dict(result='PASS',reciprocal_zero=r,short_positive_height_cases=short,fractional_translation_cases=checked,translation_epsilon=1e-8,max_attribute_delta=maximum,classification_crossings=topologies,scope='Continuous clipping translation limits with fixed topology, boundary classification validity, positive subpixel edge extension. Boundary topology transition UV continuity/fullscene motion not established. Production unchanged.');(p/'road-fractional-boundaries-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

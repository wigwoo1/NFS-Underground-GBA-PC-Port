from pathlib import Path
import ctypes as C,json,random,struct
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=C.create_string_buffer(rom[0x627700:0x647700]);d=C.CDLL(str((p/'road-clip-continuous.dll').resolve()));fn=d.nf_road_clip_continuous;fn.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];native=C.CDLL(str((p/'road-polygon-clip.dll').resolve()));oracle=native.nf_road_polygon_clip;oracle.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_int,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];rng=random.Random(61006);cases=[]
for i in range(500):
 n=rng.randrange(3,17);rows=[[rng.randrange(-200,441)]+[rng.randrange(-1000000,1000001) for k in range(5)] for j in range(n)];left=rng.randrange(100);right=rng.randrange(left,241);cases.append((rows,left,right))
for m,r in zip(json.loads((p/'stable-road-emission-source-map.json').read_text())['checks'],json.loads((p/'stable-road-full-span-replay.json').read_text())['checks']):cases.append(([v['six_words'] for v in m['mapping']],*r['bounds'][:2]))
vertices=guards=0
for rows,left,right in cases:
 n=len(rows);flat=[v for row in rows for v in row];expected=(C.c_int32*768)();en=C.c_uint();assert oracle((C.c_int32*(n*6))(*flat),n,left,right,table,expected,128,C.byref(en));actual=(C.c_double*768)();an=C.c_uint();assert fn((C.c_double*(n*6))(*flat),n,left,right,table,actual,128,C.byref(an));assert an.value==en.value and list(actual)[:an.value*6]==list(expected)[:en.value*6];vertices+=an.value
 if an.value:
  out=(C.c_double*768)(*([123]*768));count=C.c_uint(999);assert not fn((C.c_double*(n*6))(*flat),n,left,right,table,out,an.value-1,C.byref(count));assert count.value==999 and list(out)==[123]*768;guards+=1
report=dict(result='PASS',integer_original_component_cases=len(cases),output_vertices=vertices,atomic_capacity_guards=guards,scope='Bounded integer clipping exact against recovered original component, including three actual source rings. Continuous trilinear extension implemented but fractional topology/motion not verified. Input magnitude<=1e8, edge distance<32767, overflow rejected. No production integration or GPU proof.');(p/'road-clip-continuous-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

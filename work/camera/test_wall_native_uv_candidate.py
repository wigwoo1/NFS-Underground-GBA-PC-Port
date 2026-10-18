import ctypes as C,struct,random,json,sys
from pathlib import Path
sys.path.insert(0,'work/camera')
from owned_motion_pairs import records
d=C.CDLL(str(Path('work/camera/owned-gpu-wall-uv-candidate.dll').resolve()))
f=d.nf_wall_native_uv;f.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_void_p]
raw=d.nf_wall_source_uv;raw.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p]
cases=[]
for name in ('older','newer'):
 p=Path('work/camera/prototype-runs/child-scene-1791604003744272300')/(name+'.frame.bin')
 for r in records(p.read_bytes())['records']:
  if r['kind']==2:
   b=r['blocks'];shift,height=struct.unpack_from('<HH',b[4],36);flags=struct.unpack_from('<I',b[11],256)[0]
   cases.append((bytes(b[0][:68]),bytes(b[2]),shift,height,flags))
actual=len(cases);rng=random.Random(91039106)
for i in range(512):
 s=bytearray(68);a=bytearray(8)
 struct.pack_into('<4i',s,16,*(rng.randint(-100000,100000) for _ in range(4)))
 struct.pack_into('<H',s,40,rng.randrange(256));struct.pack_into('<H',s,64,rng.randrange(256))
 struct.pack_into('<hh',a,4,rng.randint(-32768,32767),rng.randint(-32768,32767))
 cases.append((bytes(s),bytes(a),rng.randint(0,10),rng.randint(1,1024),rng.choice((0,2))))
for s,a,shift,height,flags in cases:
 sb=C.create_string_buffer(s);ab=C.create_string_buffer(a);out=(C.c_double*8)();v=(C.c_uint32*6)()
 assert raw(sb,ab,shift,flags,v)==1 and f(sb,ab,shift,height,flags,out)==1
 signed=lambda v:C.c_int32(v).value
 w=128*(1<<shift);h=128*height;l,r=signed(v[0])/w,signed(v[1])/w;lt,rt=signed(v[2])/h,signed(v[4])/h
 expected=[l,lt,r,rt,r,rt+signed(v[5])/h,l,lt+signed(v[3])/h]
 assert list(out)==expected
for shift,height,flags in ((11,1,0),(1,0,0),(1,1025,0),(1,1,65536)):
 out=(C.c_double*8)(*([123.]*8));assert f(sb,ab,shift,height,flags,out)==0 and list(out)==[123.]*8
report={'result':'PASS_SOURCE_DERIVED_WALL_UV','actual_captured_cases':actual,'asymmetric_animated_synthetic_cases':512,'shift0_synthetic_cases_included':True,'invalid_atomic_cases':4,'scope':'Normalized native corners checked against original-ARM-verified raw wall UV helper. Shift 0 is covered by synthetic cases and the dedicated original ARM boundary test; no shift-0 wall has been observed in live captures.'}
Path('work/camera/prototype-runs/wall-native-uv-tests-20261009.json').write_text(json.dumps(report,indent=2));print(report)
s=Path('work/camera/capture_aligned_moving_4k_candidate.py').read_text().replace('owned-gpu-hud-borrowed-rows-candidate.dll','owned-gpu-wall-uv-candidate.dll').replace('aligned-moving-fullscene-parity-20261009.json','wall-uv-moving-fullscene-parity-20261009.json').replace('native-near-endpoint-','wall-uv-near-endpoint-').replace('eight new fractional phases repeated','two fractional phases repeated').replace('PASS_SOURCE_SETUP_PROFILE_FULL4K_PARITY','PASS_WALL_UV_SYMMETRIC_CAPTURE_FULL4K_PARITY')
Path('work/camera/capture_wall_uv_parity_candidate.py').write_text(s)

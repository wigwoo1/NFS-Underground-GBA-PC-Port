"""Exact scanline candidates/metadata/window parity plus bounded component timings."""
import ctypes as C,json,struct,random,time,statistics
from pathlib import Path
p=Path('work/camera');cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/4k-hud-palette-20261008');cp.mkdir(exist_ok=True)
P=C.c_void_p;functions=[]
for name in ('obj-tile-reference-component.dll','obj-tile-palette-component.dll'):
 d=C.CDLL(str((p/name).resolve()));f=d.nf_obj_window_scanline_prepared;f.argtypes=[P,C.c_size_t,P,C.c_size_t,P,C.c_size_t,C.c_uint16,C.c_uint,P,C.c_uint,C.c_uint,P,P,P,P];functions.append((d,f))
def case(v,palette,oam,display,y,window,blend,brightness):
 return (C.create_string_buffer(v),C.create_string_buffer(palette),C.create_string_buffer(oam),display,y,(C.c_uint16*6)(*window),blend,brightness)
def call(f,c):
 v,pal,o,d,y,w,b,e=c;colors=(C.c_uint32*240)();tags=(C.c_uint32*240)();ctrl=(C.c_uint8*240)();bd=(C.c_uint8*240)()
 rc=f(v,len(v)-1,pal,len(pal)-1,o,len(o)-1,d,y,w,b,e,colors,tags,ctrl,bd)
 return rc,bytes(colors),bytes(tags),bytes(ctrl),bytes(bd)
r=json.loads((p/'prototype-runs/owned-native-1791267744113946700.json').read_text());cases=[]
for item in r['wall_diagnostic_frames']:
 raw=Path(item['regenerated']).read_bytes();gn,hn=struct.unpack_from('<2I',raw,8);head=40 if struct.unpack_from('<I',raw)[0]==0x3346474e else 20
 assert hn==160*34944
 for y in range(160):
  row=raw[head+gn+y*34944:head+gn+(y+1)*34944];reg=row[8:104]
  cases.append(case(bytes(0x10000)+row[128:32896],row[32896:33920],row[33920:34944],struct.unpack_from('<H',reg)[0],y,struct.unpack_from('<6H',reg,64),struct.unpack_from('<H',reg,80)[0],struct.unpack_from('<H',reg,84)[0]))
actual=len(cases);rng=random.Random(20261008)
for i in range(240):
 v=bytes(0x10000)+rng.randbytes(32768);pal=rng.randbytes(1024);o=bytearray(1024)
 for k in range(128):struct.pack_into('<H',o,k*8,512)
 y=rng.randrange(160)
 for k in range(12):
  affine=rng.randrange(2);color8=rng.randrange(2);shape=rng.randrange(3);size=rng.randrange(4)
  a=((y-rng.randrange(16))&255)|(affine<<8)|(rng.randrange(2)<<10)|(color8<<13)|(shape<<14)
  b=rng.randrange(512)|(rng.randrange(32)<<9)|(size<<14);c=rng.randrange(512,1024)|(rng.randrange(4)<<10)|(rng.randrange(16)<<12)
  struct.pack_into('<3H',o,k*8,a,b,c)
 for k in range(32):
  for j,m in enumerate((256,32,-32,256)):struct.pack_into('<h',o,k*32+6+j*8,m)
 display=4|0x1000|(rng.randrange(2)<<6)|(rng.randrange(4)<<13)
 cases.append(case(v,pal,bytes(o),display,y,[rng.randrange(65536) for _ in range(6)],rng.randrange(65536),rng.randrange(32)))
counts={0:0,1:0}
for i,c in enumerate(cases):
 a=call(functions[0][1],c);b=call(functions[1][1],c);assert a==b,(i,'Scanline mismatch');counts[a[0]]+=1
# Timings exclude Python allocation by using fixed output buffers and retained inputs.
outputs=[(C.c_uint32*240)(),(C.c_uint32*240)(),(C.c_uint8*240)(),(C.c_uint8*240)()]
times=[[],[]]
for trial in range(6):
 for ix in ((0,1) if trial%2==0 else (1,0)):
  f=functions[ix][1];start=time.thread_time_ns()
  for c in cases[:actual]*64:
   v,pal,o,d,y,w,b,e=c;assert f(v,len(v)-1,pal,len(pal)-1,o,len(o)-1,d,y,w,b,e,*outputs)==1
  times[ix].append((time.thread_time_ns()-start)/1e6)
out=dict(result='PASS',captured_rows=actual,synthetic_rows=len(cases)-actual,return_counts=counts,benchmark_repetitions=64,reference_thread_ms=times[0],candidate_thread_ms=times[1],reference_median_ms=statistics.median(times[0]),candidate_median_ms=statistics.median(times[1]),scope='Exact240pixelcolor/tag/visible/backdropcontrol parity on16capturedframes plus240deterministic4/8bit affine/flipped/priority/window/effect cases. Component CPU timings only, not live4K pacing proof.')
(cp/'component.json').write_text(json.dumps(out,indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(out)

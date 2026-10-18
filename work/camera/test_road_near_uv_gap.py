"""Compare captured road near-edge UVs with original fixed-point clipping."""
from pathlib import Path
import ctypes as C,json,struct
from scene_batches import records
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));fn=d.nfs_visibility_wall_clip;fn.argtypes=[P:=C.c_void_p,P,P,C.c_int,C.c_uint,C.c_uint,P]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();recip=(C.c_uint32*32768).from_buffer_copy(rom[0x627700:0x647700])
def i(b,o):return struct.unpack_from('<i',b,o)[0]
def h(b,o):return struct.unpack_from('<h',b,o)[0]
def u(b,o):return struct.unpack_from('<H',b,o)[0]
def si(v):return ((v+2**31)%2**32)-2**31
def half(v):return ((v+32768)%65536)-32768
edges=[]
for event in records(p/'world.bin'):
 if event['pc']!=0x030032f0:continue
 blocks=event['blocks'];desc=blocks[4][1];src=blocks[5][1];cam=struct.unpack('<12i',blocks[2][1]);mat=blocks[8][1]
 if u(desc,4) or not u(desc,8):continue
 assert i(blocks[3][1],16)==64,('captured near plane',event['id'],i(blocks[3][1],16))
 vertices=[]
 for j in range(u(desc,2)):
  s=src[j*68:(j+1)*68];o=blocks[10+j][1] or bytes(32)
  x=i(s,0)+h(o,0)+cam[9];z=i(s,4)+h(o,2)+cam[11]
  cz=half(si(x*cam[2]+z*cam[8])>>14)
  vertices.append((cz,i(s,32),i(s,36),u(s,46)))
 for j,a in enumerate(vertices):
  b=vertices[(j+1)%len(vertices)];z0,z1=a[0],b[0]
  if (z0<64)==(z1<64):continue
  delta=abs(z1-z0)
  if delta>=32768:continue
  scratch=bytearray(52);struct.pack_into('<2h',scratch,4,z0,z1);buf=C.create_string_buffer(bytes(scratch));heights=(C.c_uint32*4)();attrs=(C.c_uint32*4)(a[1]&0xffffffff,a[2]&0xffffffff,b[1]&0xffffffff,b[2]&0xffffffff)
  assert fn(buf,heights,attrs,64,a[3],desc[18],recip)==1
  target=0 if z0<64 else 2;t=(64-z0)/(z1-z0);observed=[];ideal=[];bounds=[]
  for axis in (0,1):
   actual=si(attrs[target+axis])/16384;expected=(a[1+axis]+(b[1+axis]-a[1+axis])*t)/16384
   # Exclude signed attribute difference overflow from this real-valued bound.
   difference=b[1+axis]-a[1+axis]
   if not -2**31<=difference<2**31:continue
   factor=(64-min(z0,z1))*int(recip[delta])/2**24
   exact_t=t if z0<64 else 1-t
   bound=(abs(difference)*abs(exact_t-factor)+1)/16384+1e-10
   assert abs(actual-expected)<=bound,(event['id'],j,axis,actual,expected,bound)
   observed.append(actual);ideal.append(expected);bounds.append(bound)
  if len(observed)==2:
   errors=[abs(x-y) for x,y in zip(observed,ideal)]
   edges.append(dict(event=event['id'],edge=j,z=[z0,z1],affine=bool(i(blocks[69][1],0)),uv_error=errors,texel_error=[errors[0]*(1<<u(mat,36)),errors[1]*u(mat,38)/2]))
assert edges
report=dict(result='PASS',captured_crossings=len(edges),affine_crossings=sum(e['affine'] for e in edges),perspective_crossings=sum(not e['affine'] for e in edges),maximum_uv_error=max(max(e['uv_error']) for e in edges),maximum_texel_error=max(max(e['texel_error']) for e in edges),worst_edges=sorted(edges,key=lambda e:max(e['texel_error']),reverse=True)[:10],scope='Captured road edge UV interpolation at depth64: exact native original fixed-point clip versus geometric interpolation using the same integer camera endpoints; isolates interpolation arithmetic rather than complete current renderer coordinates. No screen projection, rectangle clipping or pixel oracle; does not prove renderer output parity.')
(p/'road-near-uv-gap-tests.json').write_text(json.dumps(report,indent=2));print(report)

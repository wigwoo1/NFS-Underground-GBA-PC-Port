"""Native builder versus original ARM builder from immutable entry-time inputs."""
import ctypes as C,json,struct
from pathlib import Path
p=Path(__file__).resolve().parent;out=p/'prototype-runs/paired-lifecycle';report=json.loads((out/'report.json').read_text());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t);d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nfs_visibility_build.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p];recip=(C.c_uint32*32768).from_buffer_copy(rom[0x627700:0x647700]);results=[]
for c in report['checks']:
 name=Path(c['state']).stem;before=(out/(name+'-builder-source.bin')).read_bytes();after=(out/(name+'-builder-end-source.bin')).read_bytes()
 def get(ram,a,n):
  for base,b in [(0x02000000,ram[:0x40000]),(0x03000000,ram[0x40000:]),(0x08000000,rom)]:
   if base<=a and a+n<=base+len(b):return b[a-base:a-base+n]
  raise ValueError(hex(a))
 @Read
 def read(ctx,a,dst,n):
  try:C.memmove(dst,get(before,a,n),n);return 1
  except ValueError:return 0
 state_address=c['diagnostics']['builder_registers'][0];initial=get(before,state_address,256);qa,ga=struct.unpack_from('<2I',initial,96);s=C.create_string_buffer(initial,256);q=C.create_string_buffer(get(before,qa,512),512);g=C.create_string_buffer(get(before,ga,4096),4096);ok=d.nfs_visibility_build(s,q,g,read,None,recip)
 matches=dict(state=s.raw==get(after,state_address,256),queue=q.raw==get(after,qa,512),groups=g.raw==get(after,ga,4096));results.append(dict(state=name,native_success=bool(ok),matches=matches));print(name,ok,matches)
(out/'native-prepared-builder-test.json').write_text(json.dumps(dict(result='PASS' if all(x['native_success'] and all(x['matches'].values()) for x in results) else 'MEASURED',checks=results,scope='Native builder state/512bytequeue/4096bytegroups against actual original ARM entry/end snapshots. No query or rendering proof.'),indent=2))

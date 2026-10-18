"""Measure verified block UV versus per-sample unprojection; no renderer claims."""
from pathlib import Path
import ctypes as C,struct,json,random,hashlib
p=Path('work/camera');rompath=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');rom=rompath.read_bytes();table=rom[0x627700:0x647700];recip=struct.unpack('<32768I',table)
d=C.CDLL(str((p/'road-polygon-clip.dll').resolve()));fn=d.nf_road_perspective_plan;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
def si(x):return ((x+2**31)%2**32)-2**31
def unproject(q,a):return si(recip[si(q)>>4]*(si(a)>>8))>>4
rng=random.Random(3190);errors=[];cases=[]
for case in range(200):
 width=rng.randrange(17,121);q=rng.randrange(5000,200000);end=rng.randrange(q*4//5,q*6//5);a=rng.randrange(-500000,500001);b=rng.randrange(-500000,500001);ae=rng.randrange(-500000,500001);be=rng.randrange(-500000,500001)
 c=[0]*16;c[4]=recip[width]>>8;c[7]=width;c[8]=a&0xffffffff;c[9]=b&0xffffffff;c[10]=q;c[11]=ae&0xffffffff;c[12]=be&0xffffffff;c[13]=end
 out=C.create_string_buffer(2048);final=C.create_string_buffer(64);n=C.c_uint();assert fn(struct.pack('<16I',*c),table,out,32,C.byref(n),final)
 dq=si(((end-q)*c[4])>>12);da=si((si(((ae-a)>>8)*c[4]))>>4);db=si((si(((be-b)>>8)*c[4]))>>4)
 at=0;diff=[]
 for r in range(n.value):
  run=struct.unpack_from('<16I',out.raw,r*64)
  for k in range(run[7]):
   # Fractional advance of the SAME block-level q/u/v slopes, before lookup.
   qq=si(q+(dq*at)//16);aa=si(a+(da*at)//16);bb=si(b+(db*at)//16)
   ideal=(unproject(qq,aa),unproject(qq,bb));block=(si(run[8]+k*run[10]),si(run[9]+k*run[11]))
   diff.append(max(abs(x-y) for x,y in zip(block,ideal))/65536);at+=1
 assert at==width;errors.extend(diff);cases.append(dict(case=case,pairs=width,max_fixed_texel_difference=max(diff)))
errors.sort();report=dict(result='MEASURED',cases=cases,samples=len(errors),nonzero_samples=sum(x>0 for x in errors),max_fixed_texel_difference=max(errors),p95_fixed_texel_difference=errors[int(.95*(len(errors)-1))],rom_sha256=hashlib.sha256(rom).hexdigest(),component_sha256=hashlib.sha256((p/'road-polygon-clip.dll').read_bytes()).hexdigest(),scope='Deterministic synthetic perspective contexts; verified original16sample run versus per-sample reciprocal lookup at same block slopes. Fixed units/65536, before material masks or texture lookup. This is NOT actual GPU UV, retained live endpoint data, smoothness or causal full-scene evidence.')
assert hashlib.sha256(rompath.read_bytes()).hexdigest()==report['rom_sha256'];(p/'road-block-sampling-differences.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='cases'})

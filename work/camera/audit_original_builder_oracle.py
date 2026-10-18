"""Original ARM versus native C builder on immutable RAM fixtures."""
from pathlib import Path
import ctypes as C,struct,json,subprocess,hashlib
p=Path(__file__).resolve().parent
rompath=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');rom=rompath.read_bytes();d=C.CDLL(str(p/'visibility-probe-wide.dll'));P=C.c_void_p;Read=C.CFUNCTYPE(C.c_int,P,C.c_uint32,P,C.c_size_t)
d.nfs_visibility_build.argtypes=[P,P,P,Read,P,P];d.nf_visibility_view_sample.argtypes=[P,P,C.c_double,P];recip=C.create_string_buffer(rom[0x627700:0x647700]);checks=[]
def offset(address):
 if 0x02000000<=address<0x02040000:return address-0x02000000
 if 0x03000000<=address<0x03008000:return 0x40000+address-0x03000000
 raise ValueError(hex(address))
def view(raw):
 address=struct.unpack_from('<I',raw,offset(0x030000c0)+84)[0];return raw[offset(address):offset(address)+48]
def check(label,raw):
 before=p/('arm-oracle-'+label+'-before.bin');after=p/('arm-oracle-'+label+'-after.bin');before.write_bytes(raw)
 run=subprocess.run([str(p/'original-builder-oracle.exe'),str(rompath),str(before),'0x030000c0',str(after)],capture_output=True,text=True,timeout=15);assert run.returncode==0,run.stdout+run.stderr
 expected=after.read_bytes();state=0x030000c0;initial=raw[offset(state):offset(state)+256];qa,ga=struct.unpack_from('<2I',initial,96)
 @Read
 def read(ctx,address,out,size):
  try:
   data=rom[address-0x08000000:address-0x08000000+size] if address>=0x08000000 else raw[offset(address):offset(address)+size]
   assert len(data)==size;C.memmove(out,data,size);return 1
  except:return 0
 s=C.create_string_buffer(initial,256);q=C.create_string_buffer(raw[offset(qa):offset(qa)+512],512);g=C.create_string_buffer(raw[offset(ga):offset(ga)+4096],4096);assert d.nfs_visibility_build(s,q,g,read,None,recip)
 matches=dict(state=s.raw==expected[offset(state):offset(state)+256],queue=q.raw==expected[offset(qa):offset(qa)+512],groups=g.raw==expected[offset(ga):offset(ga)+4096]);count=struct.unpack_from('<H',s.raw,238)[0];regions=[struct.unpack_from('<H',q.raw,i*16)[0] for i in range(count)]
 checks.append(dict(label=label,input_sha256=hashlib.sha256(raw).hexdigest(),matches=matches,queue_count=count,regions=regions,arm_result=run.stdout.strip()));assert all(matches.values()),checks[-1]
for serial in [16,17,64,65]:check(str(serial),(p/('oracle-builder-'+str(serial)+'.bin')).read_bytes())
for older,newer in [(16,17),(64,65)]:
 a=(p/('oracle-builder-'+str(older)+'.bin')).read_bytes();b=(p/('oracle-builder-'+str(newer)+'.bin')).read_bytes()
 for alpha in [.23,.5,.51,.99]:
  av=C.create_string_buffer(view(a),48);bv=C.create_string_buffer(view(b),48);sample=(C.c_uint32*12)();assert d.nf_visibility_view_sample(av,bv,alpha,sample)
  changed=bytearray(a);address=struct.unpack_from('<I',a,offset(0x030000c0)+84)[0];changed[offset(address):offset(address)+48]=bytes(sample);check(str(older)+'-'+str(newer)+'-'+str(alpha),bytes(changed))
result=dict(result='PASS_BUILDER_COMPONENT',checks=checks,scope='Original ARM queue builder versus C with identical captured seeds and sampled view matrices. Query/root reselection and object traversal are not verified; no native60fps proof.');(p/'original-builder-oracle-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

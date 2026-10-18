"""Owned road material resolution atomic read-failure checks."""
from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');fixture=p/'visibility-overflow-171-wide';state=(fixture/'result-0.5.bin').read_bytes()[:256]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();regions=[(0x08000000,rom),(0x02000000,(fixture/'ewram.bin').read_bytes()),(0x03000000,(fixture/'iwram.bin').read_bytes())]
Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t);d=C.CDLL(str((p/'road-polygon-clip.dll').resolve()));fn=d.nf_road_material_seed;fn.argtypes=[C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p];reads=0;fail_at=None
@Read
def read(ctx,address,out,size):
 global reads
 reads+=1
 if fail_at==reads:return 0
 for base,data in regions:
  if base<=address and address+size<=base+len(data):C.memmove(out,data[address-base:address-base+size],size);return 1
 return 0
cases=json.loads((p/'road-clip-inputs-0.5-motion-writes-full.json').read_text())['cases'];atomic=0
for c in cases:
 descriptor=rom[c['source']-0x08000000:c['source']-0x08000000+48];out=C.create_string_buffer(64);reads=0;assert fn(state,descriptor,read,None,out)
 for stage in (1,2,3):
  rejected=C.create_string_buffer(b'X'*64,64);reads=0;fail_at=stage
  assert not fn(state,descriptor,read,None,rejected) and rejected.raw==b'X'*64;atomic+=1
 fail_at=None
bad=bytearray(descriptor);struct.pack_into('<H',bad,8,0);out=C.create_string_buffer(b'X'*64,64);assert not fn(state,bytes(bad),read,None,out) and out.raw==b'X'*64;atomic+=1
report=dict(result='PASS',owned_primary_materials=len(cases),atomic_rejections=atomic,scope='Retained scene primary material/animation resolution, failed reads and absent primary rejection. Animation scheduling and alternate road materials not verified.')
(p/'road-material-tests.json').write_text(json.dumps(report,indent=2));print(report)

"""Layer selection checked against captured original second road draw arguments."""
import ctypes as C,json,struct
from pathlib import Path
p=Path(__file__).resolve().parent;out=p/'prototype-runs/quick-race-context';report=json.loads((out/'road-layer-source-fixture.json').read_text());case=report['checks'][2];regs=case['road_registers'];source=bytes.fromhex(case['road_diagnostic']['bytes_hex']);rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();ewram=(out/'quick-1-release-road-event-ewram.bin').read_bytes();iwram=(out/'quick-1-release-road-event-iwram.bin').read_bytes();overrides={}
Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
@Read
def read(ctx,address,dst,size):
 for base,data in list(overrides.items())+[(0x02000000,ewram),(0x03000000,iwram),(0x08000000,rom)]:
  if base<=address and address+size<=base+len(data):C.memmove(dst,data[address-base:address-base+size],size);return 1
 return 0
h=lambda b,o:struct.unpack_from('<H',b,o)[0];w=lambda b,o:struct.unpack_from('<I',b,o)[0]
d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_road_material_plan_layer.argtypes=[Read,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint,C.c_void_p];d.nf_road_material_plan.argtypes=[Read,C.c_void_p,C.c_uint32,C.c_uint32,C.c_void_p]
state,descriptor=regs[1],regs[7];plan=(C.c_uint32*5)();assert d.nf_road_material_plan_layer(read,None,state,descriptor,1,plan)
# Original call's live UV pointer and expanded draw material are direct evidence.
assert plan[1]==regs[2] and plan[2]==w(source,344) and plan[3]==h(source,340) and plan[4]==h(source,342),(list(plan),regs)
primary=(C.c_uint32*5)(1,2,3,4,5);legacy=(C.c_uint32*5)(1,2,3,4,5);assert not d.nf_road_material_plan_layer(read,None,state,descriptor,0,primary) and not d.nf_road_material_plan(read,None,state,descriptor,legacy) and list(primary)==list(legacy)==[1,2,3,4,5]
primary_descriptor=bytearray(source[256:304]);struct.pack_into('<H',primary_descriptor,8,h(primary_descriptor,4));overrides[descriptor]=bytes(primary_descriptor);assert d.nf_road_material_plan_layer(read,None,state,descriptor,0,primary) and d.nf_road_material_plan(read,None,state,descriptor,legacy) and list(primary)==list(legacy)==list(plan);overrides.clear()
checks=['second material UV/texture/size exact original draw arguments','absent primary atomic rejection and primary wrapper exact legacy output on equivalent material']
for layer in [2,0xffffffff]:
 sentinel=(C.c_uint32*5)(1,2,3,4,5);assert not d.nf_road_material_plan_layer(read,None,state,descriptor,layer,sentinel) and list(sentinel)==[1,2,3,4,5]
checks.append('invalid layer atomic rejection')
copy=bytearray(source[256:304]);struct.pack_into('<H',copy,4,0);overrides[descriptor]=bytes(copy);sentinel=(C.c_uint32*5)(1,2,3,4,5);assert not d.nf_road_material_plan_layer(read,None,state,descriptor,1,sentinel) and list(sentinel)==[1,2,3,4,5];checks.append('absent second layer atomic rejection')
(out/'road-material-layer-test.json').write_text(json.dumps(dict(result='PASS',checks=checks,primary=list(primary),second=list(plan),scope='Material selection only; second-pass geometry/UV attributes and live native render remain incomplete.'),indent=2));print('PASS',checks)

from pathlib import Path
import sys,ctypes as C,struct,json
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
from wall_native_prepared import prepared_edge
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,s in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x1000000)]:u.mem_map(a,s)
u.mem_write(0x08000000,rom);u.mem_write(0x03000000,(p/'motion-original-span-iwram.bin').read_bytes())
table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes())
f=C.CDLL(str((p/'native_wall.dll').resolve())).nfs_wall_default_plan;f.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint32,C.c_void_p,C.c_void_p]
actual=[]
def hook(cpu,address,size,data):
 if address==0x030053e8:
  state=bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R0),68));w=struct.unpack('<17I',state)
  actual.append([w[1],w[13],w[11],cpu.reg_read(UC_ARM_REG_R1),cpu.reg_read(UC_ARM_REG_R2),cpu.reg_read(UC_ARM_REG_R3)])
  cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook)
checks=[]
for scene in json.loads((p/'motion-wall-snapshots.json').read_text())['scenes']:
 for wall in scene['walls']:
  edge=prepared_edge(wall,table);mat=bytearray.fromhex(wall['material_hex']);struct.pack_into('<II',mat,8,0x02031000,0x02032000)
  state=bytearray(256);struct.pack_into('<4H',state,226,*wall['bounds']);fb=bytearray(32);struct.pack_into('<I',fb,0,0x06000000);struct.pack_into('<I',fb,12,240)
  descriptor=bytearray.fromhex(wall['offset_hex'])
  for a,b in [(0x02030000,mat),(0x02031000,fb),(0x02032000,edge),(0x02033000,state),(0x02034000,descriptor)]:u.mem_write(a,bytes(b))
  for reg,v in [(UC_ARM_REG_R0,0x02030000),(UC_ARM_REG_R1,0x02033000),(UC_ARM_REG_R2,wall['flags']),(UC_ARM_REG_R3,0x02034000),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03007ffc)]:u.reg_write(reg,v)
  actual.clear();u.emu_start(0x03000304,0x03007ffc,count=1000000)
  out=(C.c_uint32*720)();n=C.c_uint();assert f(edge,table,(C.c_uint*4)(*wall['bounds']),0x06000000,out,C.byref(n))
  expected=[list(out[i*6:i*6+6]) for i in range(n.value)]
  checks.append(dict(event=wall['event'],columns=n.value,original_columns=len(actual),exact=expected==actual,first_difference=next(((a,b) for a,b in zip(expected,actual) if a!=b),None)))
r=dict(result='PASS_NATIVE_WALL_COLUMN_PLANS' if all(c['exact'] for c in checks) else 'WALL_COLUMN_PLAN_DIFFERENCE',columns=sum(c['columns'] for c in checks),checks=checks,scope='Native world preparededge to default unshaded column plan against original ARM planner with isolated supplied materials and scene bounds. No full scene or timing proof.')
(p/'motion-wall-plan-tests.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(r['result'],r['columns']);print([c for c in checks if not c['exact']][:2])

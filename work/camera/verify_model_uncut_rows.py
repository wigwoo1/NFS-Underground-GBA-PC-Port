from pathlib import Path
import ctypes as C,struct,json,sys
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();code=(p/'motion-original-model-spans-iwram.bin').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x1000000)]:u.mem_map(a,n)
u.mem_write(0x03000000,code);u.mem_write(0x08000000,rom);table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());d=C.CDLL(str((p/'native_model.dll').resolve()));edge=d.nfs_model_edge_plan;edge.argtypes=[C.c_void_p]*4+[C.c_uint,C.c_uint,C.c_void_p,C.c_void_p];row=d.nfs_model_row_plan;row.argtypes=[C.c_uint32]*7+[C.c_void_p]*2;captured=[]
def hook(cpu,address,size,data):
 if address==0x03005920:
  q=[struct.unpack('<I',bytes(cpu.mem_read(struct.unpack_from('<I',code,0x5a34+i*4)[0],4)))[0] for i in range(4)]
  captured.append([cpu.reg_read(UC_ARM_REG_R1),cpu.reg_read(UC_ARM_REG_R2),*q]);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook)
ring=d.nfs_model_ring_rows;ring.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_uint32,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
def native(poly,base):
 points=poly['ring'];uv=poly['uv'];n=len(points);out=(C.c_uint32*6000)();count=C.c_uint()
 assert ring((C.c_int16*(n*2))(*[v for pair in points for v in pair]),(C.c_uint16*(n*2))(*[v&65535 for pair in uv for v in pair]),n,poly['shift'],poly['height'],base,table,out,1000,C.byref(count))
 return [list(out[i*6:(i+1)*6]) for i in range(count.value)]
checks=[];native_calls=[];snap={m['event']:m for scene in json.loads((p/'motion-model-snapshots.json').read_text())['scenes'] for m in scene['models']}
for model in json.loads((p/'native-motion-model-polygons.json').read_text())['models']:
 for fi,poly in enumerate(model['polygons']):
  points=poly['ring'];n=len(points);rect=model['rectangle']
  if any(not(rect[0]<=x<rect[2] and rect[1]<=y<rect[3]) for x,y in points):continue
  base=struct.unpack_from('<I',bytes.fromhex(snap[model['event']]['framebuffer_descriptor_hex']))[0];context=bytearray(48);struct.pack_into('<2I',context,8,0x02001000,0x02002000);struct.pack_into('<2H',context,36,poly['shift'],poly['height']);struct.pack_into('<I',context,40,poly['texture']);fb=bytearray(32);struct.pack_into('<2I',fb,0,base,0x02003000);struct.pack_into('<I',fb,12,240);polygon=bytearray(32);struct.pack_into('<4I',polygon,0,0x02004000,0x02005000,0x02006000,0x02006000);struct.pack_into('<I',polygon,20,n)
  data=[(0x02000000,bytes(context)),(0x02001000,bytes(fb)),(0x02002000,bytes(polygon)),(0x02003000,struct.pack('<4i',*rect)),(0x02004000,struct.pack('<'+'h'*n*2,*[v for xy in points for v in xy])),(0x02005000,struct.pack('<'+'H'*n*2,*[v&65535 for xy in poly['uv'] for v in xy])),(0x02006000,struct.pack('<'+'H'*n,*range(n)))]
  for address,b in data:u.mem_write(address,b)
  for reg,v in [(UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03007000)]:u.reg_write(reg,v)
  captured.clear();u.emu_start(0x03003d24,0x03007000,count=100000);expected=native(poly,base);native_calls.extend(dict(event=model['event'],polygon=fi,params=call) for call in expected);checks.append(dict(event=model['event'],polygon=fi,rows=len(expected),original_rows=len(captured),exact=expected==captured,first_difference=next(((a,b) for a,b in zip(expected,captured) if a!=b),None)))
r=dict(result='PASS_NATIVE_UNCUT_MODEL_ROWS' if all(c['exact'] for c in checks) else 'MODEL_ROW_SEQUENCE_DIFFERENCE',polygons=len(checks),rows=sum(c['rows'] for c in checks),checks=checks,scope='Native edge and row arithmetic with native C source-ring walker vs complete original polygon rasterizer with span writes stubbed. Uncut faces only; no actual capture sequence or clipped/fullscene/timing proof.')
(p/'native-model-writer-calls.json').write_text(json.dumps(native_calls,indent=2),encoding='utf-8')
(p/'model-uncut-row-tests.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(r['result'],r['polygons'],r['rows']);print([c for c in checks if not c['exact']][:2])

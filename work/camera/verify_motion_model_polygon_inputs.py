from pathlib import Path
import ctypes as C,struct,json,sys
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
from scene_batches import records
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,s in ((0x02000000,0x40000),(0x03000000,0x10000),(0x05000000,4096),(0x08000000,0x1000000)):u.mem_map(a,s)
u.mem_write(0x08000000,rom);u.mem_write(0x03000000,(p/'motion-original-model-rect-iwram.bin').read_bytes())
models={m['event']:m for m in json.loads((p/'native-motion-model-faces.json').read_text())['models']};snap={m['event']:m for s in json.loads((p/'motion-model-snapshots.json').read_text())['scenes'] for m in s['models']};dispatch={d['event']:d['dispatched_faces'] for d in json.loads((p/'motion-model-face-dispatch-tests.json').read_text())['draws']};captured=[]
def hook(cpu,address,size,data):
 if address==0x03003d24:
  context=cpu.reg_read(UC_ARM_REG_R0);raw=bytes(cpu.mem_read(context,48));poly=bytes(cpu.mem_read(struct.unpack_from('<I',raw,12)[0],32));points,uv,indices,uvidx,unused,count=struct.unpack_from('<6I',poly)
  vi=list(struct.unpack('<'+'H'*count,bytes(cpu.mem_read(indices,count*2))));ui=list(struct.unpack('<'+'H'*count,bytes(cpu.mem_read(uvidx,count*2))))
  ring=[list(struct.unpack('<2h',bytes(cpu.mem_read(points+i*4,4)))) for i in vi];uvs=[list(struct.unpack('<2h',bytes(cpu.mem_read(uv+i*4,4)))) for i in ui]
  captured.append(dict(vertices=vi,uv_indices=ui,ring=ring,uv=uvs,shift=struct.unpack_from('<H',raw,36)[0],height=struct.unpack_from('<H',raw,38)[0],texture=struct.unpack_from('<I',raw,40)[0]));cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook);checks=[];native_inputs=[]
regs=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_R12,UC_ARM_REG_SP,UC_ARM_REG_LR]
for e in records(p/'motion-original-model-rect-world.bin'):
 if e['id'] not in models:continue
 m=models[e['id']];source=snap[e['id']]
 for tag,(a,b) in e['blocks'].items():
  if b and a and tag!=68:u.mem_write(a,b)
 points=struct.pack('<'+'h'*len(m['points'])*2,*[v for xy in m['points'] for v in xy]);u.mem_write(e['blocks'][55][0],points)
 for reg,v in zip(regs,e['regs']):u.reg_write(reg,v)
 captured.clear();u.emu_start(0x03004770,0x030048b0,count=100000)
 uvdata=Path(source['uv_asset']['path']).read_bytes();expected=[];context=bytes.fromhex(source['context_hex'])
 for face_index in dispatch[e['id']]:
  face=source['faces'][face_index];expected.append(dict(vertices=face['vertices'],uv_indices=face['uv'],ring=[m['points'][i] for i in face['vertices']],uv=[list(struct.unpack_from('<2h',uvdata,i*4)) for i in face['uv']],shift=source['width'].bit_length()-1,height=source['height'],texture=struct.unpack_from('<I',context,52)[0]))
 assert expected==captured,(e['id'],expected[:1],captured[:1])
 checks.append(dict(event=e['id'],faces=len(expected),exact=True));native_inputs.append(dict(event=e['id'],rectangle=source['rectangle'],polygons=expected))
r=dict(result='PASS_NATIVE_MODEL_POLYGON_INPUTS',checks=checks,polygons=sum(c['faces'] for c in checks),scope='Whole original model face dispatch loop replayed using native projected vertices and captured raw source topology/material/UV. Ordered selected face rings, raw UV pairs and texture shape/pointer exact. Original polygon raster calls stubbed; no clipping/pixel/fullscene proof.')
(p/'motion-model-polygon-input-tests.json').write_text(json.dumps(r,indent=2),encoding='utf-8');(p/'native-motion-model-polygons.json').write_text(json.dumps(dict(models=native_inputs),indent=2),encoding='utf-8');print(r['result'],r['polygons'])

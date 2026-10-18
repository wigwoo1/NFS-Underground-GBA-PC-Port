from pathlib import Path
import ctypes as C,struct,json,sys
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
from scene_batches import records,batches
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in ((0x02000000,0x40000),(0x03000000,0x10000),(0x06000000,0x20000),(0x08000000,0x1000000)):u.mem_map(a,n)
u.mem_write(0x08000000,rom);u.mem_write(0x03000000,(p/'motion-original-span-iwram.bin').read_bytes())
events={e['id']:e for e in records(p/'motion-original-source-8750-8781.bin')};snap=json.loads((p/'motion-wall-snapshots.json').read_text());wallcalls=json.loads((p/'native-wall-writer-calls.json').read_text());wallmap={d['event']:d for d in wallcalls['draws']}
roads={}
for c in json.loads((p/'native-road-writer-calls.json').read_text()):roads.setdefault(c['event'],[]).append(c)
scene_keys={(s['begin'],s['end']) for s in snap['scenes']}
closed=[e for b in batches(p/'motion-original-source-8750-8781.bin') if (b['begin_refresh'],b['end_refresh']) in scene_keys for e in b['events']]
raw=(p/'motion-original-span-hooks.bin').read_bytes();originalwall=[]
for off in range(0,len(raw),140):
 w=struct.unpack_from('<35I',raw,off)
 if w[1]==0x030053e8:originalwall.append(w)
start=json.loads((p/'motion-wall-sequence-tests.json').read_text())['exact_contiguous_start_candidates'][0]
Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
@Read
def reader(ctx,a,out,n):
 off=a-0x08000000
 if not 0<=off<=len(rom)-n:return 0
 C.memmove(out,rom[off:off+n],n);return 1
rf=C.CDLL(str((p/'road-polygon-clip.dll').resolve())).nf_road_span_pixels;rf.argtypes=[C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_uint]
wf=C.CDLL(str((p/'native_wall.dll').resolve())).nfs_wall_unshaded_addresses;wf.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint,C.c_void_p,C.c_void_p]
native=bytearray(0x20000);checks=[];road_count=wall_count=wall_rows=wall_writes=0
for event in closed:
 eid=event['id']
 if eid in roads:
  for call in roads[eid]:
   params=call['params'];bits=struct.pack('<16I',*params);width=params[7];double=call['signature'][-1];out=(C.c_uint16*512)();assert rf(bits,reader,None,out,512);pixels=bytes(out)[:width*2]
   u.mem_write(0x02001000,bits);u.mem_write(0x03007098,struct.pack('<I',double))
   for reg,v in ((UC_ARM_REG_R0,0x02001000),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)):u.reg_write(reg,v)
   u.emu_start(0x030056d8,0x03006000,count=200000)
   at=params[6]-0x06000000;native[at:at+width*2]=pixels
   if double:native[at+240:at+240+width*2]=pixels
   road_count+=1
 elif eid in wallmap:
  d=wallmap[eid];mat=event['blocks'][8][1];fb=event['blocks'][3][1];desc=event['blocks'][4][1];shift,height=struct.unpack_from('<2H',mat,36);texture=struct.unpack_from('<I',mat,40)[0]
  asset_addr,asset=event['blocks'][66]
  if 0x02000000<=asset_addr<0x02040000:u.mem_write(asset_addr,asset)
  for i in range(d['count']):
   ci=d['start']+i;top,U,step,destination,V,count=wallcalls['columns'][ci]
   state=[0]*17
   for k,v in {1:top,2:struct.unpack_from('<I',fb,12)[0]>>1,3:shift,4:height,6:((struct.unpack_from('<H',desc,2)[0]>>4)^1)&1,7:height<<shift,9:texture,11:step,13:U,16:(1<<(shift+15))-1}.items():state[k]=v
   src=(C.c_uint32*320)();dst=(C.c_uint32*320)();assert wf(struct.pack('<17I',*state),destination,V,count,src,dst)
   for j in range(count):
    address=src[j]
    if 0x08000000<=address<0x08000000+len(rom):value=rom[address-0x08000000]
    else:
     off=address-asset_addr;assert 0<=off<len(asset),(eid,address,asset_addr,len(asset));value=asset[off]
    if value:native[dst[j]-0x06000000]=value;wall_writes+=1
   original=originalwall[start+ci];regs=original[2:18];u.mem_write(0x02001000,struct.pack('<17I',*original[18:]))
   for reg,v in ((UC_ARM_REG_R0,0x02001000),(UC_ARM_REG_R1,regs[1]),(UC_ARM_REG_R2,regs[2]),(UC_ARM_REG_R3,regs[3]),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)):u.reg_write(reg,v)
   u.emu_start(0x030053e8,0x03006000,count=200000)
   wall_count+=1;wall_rows+=count
 else:continue
 assert bytes(u.mem_read(0x06000000,0x20000))==native,eid
 checks.append(dict(event=eid,kind='wall' if eid in wallmap else 'road',exact=True))
(p/'native-road-wall-buffer.bin').write_bytes(native)
r=dict(result='PASS_ORDERED_ROAD_WALL_BUFFERS',draws=checks,road_writer_calls=road_count,wall_columns=wall_count,wall_texture_rows=wall_rows,wall_nonzero_writes=wall_writes,buffer_comparison_bytes=len(checks)*len(native),scope='Zero-initialized persistent 128KiB VRAM; ordered road and wall writes across closed capture range compared after every draw with original ARM writers. Native wall source geometry and column plan, original captured wall writer states only used by oracle. No models, clears, HUD, palette/display semantics, full-scene or timing proof.')
(p/'native-road-wall-buffer-tests.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print({k:v for k,v in r.items() if k not in ('draws','scope')})

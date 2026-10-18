from pathlib import Path
import ctypes as C,struct,json,sys
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
from scene_batches import records,batches
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in ((0x02000000,0x40000),(0x03000000,0x10000),(0x06000000,0x20000),(0x08000000,0x1000000)):u.mem_map(a,n)
wall_bus_active=False
def gba_wall_bus(cpu,access,address,size,value,data):
 if wall_bus_active and size==1:cpu.mem_write(address&~1,bytes([value&255])*2)
u.hook_add(UC_HOOK_MEM_WRITE,gba_wall_bus,begin=0x06000000,end=0x0601ffff)
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
wall_store=C.CDLL(str((p/'native_wall.dll').resolve())).nfs_wall_mode4_write;wall_store.argtypes=[C.c_uint32,C.c_uint8,C.c_void_p,C.c_void_p,C.c_void_p]
model_code=(p/'motion-original-span-iwram.bin').read_bytes()
mf=C.CDLL(str((p/'native_model.dll').resolve())).nfs_model_span_addresses;mf.argtypes=[C.c_uint32,C.c_uint32,C.c_uint,C.c_uint]+[C.c_uint32]*4+[C.c_void_p]*2
modelmap={}
for call in json.loads((p/'native-model-joined-writer-calls.json').read_text()):modelmap.setdefault(call['event'],[]).append(call)
model_count=model_samples=0
native=bytearray(0x20000);checks=[];road_count=wall_count=wall_rows=wall_writes=0
first_events=set();closing={}
display_events={e['frame']:e for e in records(p/'motion-original-display-world.bin') if e['pc']==0x04000000}
for scene in batches(p/'motion-original-source-8750-8781.bin'):
 if (scene['begin_refresh'],scene['end_refresh']) not in scene_keys:continue
 surface=[e for e in scene['events'] if e['pc'] in (0x030032f0,0x03000304,0x03004770)]
 first_events.add(surface[0]['id']);closing[surface[-1]['id']]=display_events[scene['end_refresh']]
initial_dll=C.CDLL(str((p/'native_initial_page.dll').resolve()))
initial_dll.nfs_initial_fill.argtypes=[C.c_void_p,C.c_size_t,C.c_uint32,C.c_uint32,C.c_uint32]
initial_dll.nfs_initial_copy.argtypes=[C.c_void_p,C.c_size_t,C.c_uint32,C.c_void_p,C.c_size_t]+[C.c_uint32]*4
initial_ops={};initial_seeded=False
for b in batches(p/'motion-original-initial-inputs-world.bin'):
 key=(b['begin_refresh'],b['end_refresh'])
 if key not in scene_keys:continue
 ref=next(x for x in batches(p/'motion-original-source-8750-8781.bin') if (x['begin_refresh'],x['end_refresh'])==key)
 eid=next(e['id'] for e in ref['events'] if e['pc'] in (0x030032f0,0x03000304,0x03004770))
 initial_ops[eid]=[e for e in b['events'] if e['pc']==0xffff0095]
display_checks=[]
actual_draws=json.loads((p/'motion-draw-page-tests.json').read_text())['draws'];actual_checks=[]
for event in closed:
 eid=event['id']
 if eid in first_events:
  baseline=Path(actual_draws[str(eid)]['before_path']).read_bytes()
  if not initial_seeded:native[:len(baseline)]=baseline;initial_seeded=True
  out=(C.c_uint8*len(native)).from_buffer(native)
  for op in initial_ops[eid]:
   pc,_,_=struct.unpack('<3I',op['blocks'][95][1]);r=op['regs'];offset=r[0]-0x06000000
   if pc==0x030002c0:assert initial_dll.nfs_initial_fill(out,len(native),offset,r[1],r[2])
   else:
    ss,ds=struct.unpack('<2I',op['blocks'][96][1]);src=op['blocks'][97][1]
    assert initial_dll.nfs_initial_copy(out,len(native),offset,src,len(src),r[2],r[3],ss,ds)
  del out
  if native[:len(baseline)]!=baseline:
   differences=[i for i,(a,b) in enumerate(zip(native,baseline)) if a!=b]
   report=dict(result='NATIVE_PERSISTENT_INITIAL_PAGE_DIFFERENCE',event=eid,refresh=event['frame'],different_bytes=len(differences),first_offset=hex(differences[0]),last_offset=hex(differences[-1]),page0=sum(i<0xa000 for i in differences),page1=sum(0xa000<=i<0x14000 for i in differences),outside_pages=sum(i>=0x14000 for i in differences),scope='One initial VRAM seed, native ordered surfaces and native initialization; further retained-page producers remain missing.')
   (p/'native-persistent-initial-page-difference.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report);raise AssertionError(('initial page lifecycle',eid))
  u.mem_write(0x06000000,bytes(native))
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
    if value:
     store_addresses=(C.c_uint32*2)();store_values=(C.c_uint8*2)();store_count=C.c_uint();assert wall_store(dst[j],value,store_addresses,store_values,C.byref(store_count));assert store_count.value==2
     for lane in range(store_count.value):native[store_addresses[lane]-0x06000000]=store_values[lane]
     wall_writes+=1
   original=originalwall[start+ci];regs=original[2:18];u.mem_write(0x02001000,struct.pack('<17I',*original[18:]))
   for reg,v in ((UC_ARM_REG_R0,0x02001000),(UC_ARM_REG_R1,regs[1]),(UC_ARM_REG_R2,regs[2]),(UC_ARM_REG_R3,regs[3]),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)):u.reg_write(reg,v)
   wall_bus_active=True;u.emu_start(0x030053e8,0x03006000,count=200000);wall_bus_active=False
   wall_count+=1;wall_rows+=count
 elif eid in modelmap:
  asset_addr,asset=event['blocks'][66]
  if 0x02000000<=asset_addr<0x02040000:u.mem_write(asset_addr,asset)
  for call in modelmap[eid]:
   destination,count,U,V,du,dv=call['params'];src=(C.c_uint32*240)();dst=(C.c_uint32*240)();assert mf(call['texture'],destination,count,call['shift'],U,V,du,dv,src,dst)
   for i in range(count):
    address=src[i]
    if 0x08000000<=address<0x08000000+len(rom):value=rom[address-0x08000000]
    else:
     off=address-asset_addr;assert 0<=off<len(asset);value=asset[off]
    native[dst[i]-0x06000000]=value
   for i,value in enumerate(call['oracle_globals']):u.mem_write(struct.unpack_from('<I',model_code,0x5a30+i*4)[0],struct.pack('<I',value))
   for reg,val in ((UC_ARM_REG_R0,call['oracle_regs'][0]),(UC_ARM_REG_R1,call['oracle_regs'][1]),(UC_ARM_REG_R2,call['oracle_regs'][2]),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)):u.reg_write(reg,val)
   u.emu_start(0x03005920,0x03006000,count=20000);model_count+=1;model_samples+=count
 else:continue
 assert bytes(u.mem_read(0x06000000,0x20000))==native,eid
 actual=Path(actual_draws[str(eid)]['after_path']).read_bytes();difference=sum(a!=b for a,b in zip(native,actual));actual_checks.append(dict(event=eid,different_bytes=difference,exact=difference==0))
 if eid in closing:
  flip=closing[eid];page=1 if flip['regs'][1]&16 else 0;expected_display=flip['blocks'][92][1];assert native[page*0xa000:page*0xa000+38400]==expected_display;display_checks.append(dict(refresh=flip['frame'],page=page,exact=True))
 checks.append(dict(event=eid,kind='wall' if eid in wallmap else 'model' if eid in modelmap else 'road',exact=True))
(p/'native-persistent-initialized-scene-buffer.bin').write_bytes(native)
r=dict(result='PASS_NATIVE_SCENES_WITH_ONE_INITIAL_VRAM_SEED' if all(c['exact'] for c in actual_checks) else 'ACTUAL_DRAW_PIXEL_DIFFERENCE',display_checks=display_checks,captured_initial_scene_baselines=len(first_events),actual_draw_checks=actual_checks,exact_actual_draws=sum(c['exact'] for c in actual_checks),draws=checks,model_spans=model_count,model_texture_samples=model_samples,road_writer_calls=road_count,wall_columns=wall_count,wall_texture_rows=wall_rows,wall_nonzero_writes=wall_writes,buffer_comparison_bytes=len(checks)*len(native),scope='Only first surface draw in each scene seeded with captured initial VRAM; ordered road and wall writes across closed capture range compared after every draw with original ARM writers. Native wall source geometry and column plan, original captured wall writer states only used by oracle. All captured road/wall/model draws included; clears, HUD, palette/display semantics and full-scene timing remain unverified. Native model ring walking is diagnostic Python/ctypes.')
(p/'native-persistent-initialized-scene-buffer-tests.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print({k:v for k,v in r.items() if k not in ('draws','scope','actual_draw_checks')})

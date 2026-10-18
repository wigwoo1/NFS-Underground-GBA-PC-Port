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
from live_road_commands import road_commands
native_roads=road_commands(p);reference_roads=json.loads((p/'native-road-writer-calls.json').read_text());assert native_roads==reference_roads
for c in native_roads:roads.setdefault(c['event'],[]).append(c)
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
model_writer=C.CDLL(str((p/'native_model.dll').resolve())).nfs_model_rows_write;model_writer.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_uint32,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
wall_writer=C.CDLL(str((p/'native_wall.dll').resolve())).nfs_wall_columns_write;wall_writer.argtypes=[C.c_void_p,C.c_uint,C.c_uint32,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p]
road_writer=C.CDLL(str((p/'road-polygon-clip.dll').resolve())).nf_road_spans_write;road_writer.argtypes=[C.c_void_p,C.c_uint,Read,C.c_void_p,C.c_void_p,C.c_size_t]
from native_scene_executor import road as road_writer, wall as wall_writer, model as model_writer
from live_wall_commands import wall_commands
live_wall_plans=wall_commands(p)
from wall_native_prepared import prepared_edge
wall_sources={wall['event']:wall for scene in snap['scenes'] for wall in scene['walls']}
wall_table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes())
wall_plan=C.CDLL(str((p/'native_wall.dll').resolve())).nfs_wall_source_columns
wall_plan.argtypes=[C.c_void_p]*7+[C.c_uint,C.c_void_p]
modelmap={}
from live_model_commands import model_commands
native_model_calls=model_commands(p);oracle_model_calls=json.loads((p/'native-model-joined-writer-calls.json').read_text());assert len(native_model_calls)==len(oracle_model_calls)
for call,reference in zip(native_model_calls,oracle_model_calls):
 assert all(call[k]==reference[k] for k in ('event','polygon','params','texture','shift'))
 call['oracle_regs']=reference['oracle_regs'];call['oracle_globals']=reference['oracle_globals'];modelmap.setdefault(call['event'],[]).append(call)
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
initial_dll.nfs_initial_block_copy.argtypes=[C.c_void_p,C.c_size_t,C.c_uint32,C.c_void_p,C.c_size_t,C.c_uint32]
from native_scene_executor import bind, closing_snapshot, fill as scene_fill, copy as scene_copy, block_copy as scene_block_copy
initial_ops={};initial_seeded=False;sprite_copy_count=0;cursor=0;pending=[]
for item in records(p/'motion-original-sprite-inputs-world.bin'):
 if item['pc'] in (0xffff0095,0xffff0102):pending.append(item)
 if cursor>=len(closed):continue
 expected=closed[cursor]
 if item['pc']==expected['pc'] and item['frame']==expected['frame'] and item['regs']==expected['regs'] and all(item['blocks'].get(k)==v for k,v in expected['blocks'].items()):
  initial_ops[expected['id']]=pending;pending=[];cursor+=1
assert cursor==len(closed)
closing_sprite_ops={};closing_sprite_state={};sprite_display_checks=[]
for batch in batches(p/'motion-original-sprite-inputs-world.bin'):
 key=(batch['begin_refresh'],batch['end_refresh'])
 if key not in scene_keys:continue
 ref=next(b for b in batches(p/'motion-original-source-8750-8781.bin') if (b['begin_refresh'],b['end_refresh'])==key)
 last=next(e for e in reversed(ref['events']) if e['pc'] in (0x030032f0,0x03000304,0x03004770))
 position=next(i for i,e in enumerate(batch['events']) if e['pc']==last['pc'] and e['frame']==last['frame'] and e['regs']==last['regs'])
 closing_sprite_ops[last['id']]=[e for e in batch['events'][position+1:] if e['pc']==0xffff0102]
for e in records(p/'motion-original-sprite-inputs-world.bin'):
 if e['pc']==0x04000000:closing_sprite_state[e['frame']]=e
display_checks=[]
actual_draws=json.loads((p/'motion-draw-page-tests.json').read_text())['draws'];actual_checks=[]
for event in closed:
 eid=event['id']
 if eid in first_events:
  baseline=Path(actual_draws[str(eid)]['before_path']).read_bytes()
  if not initial_seeded:native[:len(baseline)]=baseline;initial_seeded=True;owned_scene=bind(native)
 out=(C.c_uint8*len(native)).from_buffer(native)
 for op in initial_ops[eid]:
  r=op['regs'];offset=r[0]-0x06000000
  if op['pc']==0xffff0102:
   src=op['blocks'][102][1];assert scene_block_copy(out,len(native),offset,src,len(src),r[2]);sprite_copy_count+=1;continue
  pc,_,_=struct.unpack('<3I',op['blocks'][95][1])
  if pc==0x030002c0:assert scene_fill(out,len(native),offset,r[1],r[2])
  else:
   ss,ds=struct.unpack('<2I',op['blocks'][96][1]);src=op['blocks'][97][1];assert scene_copy(out,len(native),offset,src,len(src),r[2],r[3],ss,ds)
 del out
 if eid in first_events:assert native[:len(baseline)]==baseline,('persistent VRAM initial',eid)
 u.mem_write(0x06000000,bytes(native))
 if eid in roads:
  calls=roads[eid];packed=(C.c_uint32*(len(calls)*17))(*[v for call in calls for v in [*call['params'],call['signature'][-1]]]);vram=(C.c_uint8*len(native)).from_buffer(native);assert road_writer(packed,len(calls),reader,None,vram,0x18000);del vram
  for call in roads[eid]:
   params=call['params'];bits=struct.pack('<16I',*params);width=params[7];double=call['signature'][-1];out=(C.c_uint16*512)();assert rf(bits,reader,None,out,512);pixels=bytes(out)[:width*2]
   u.mem_write(0x02001000,bits);u.mem_write(0x03007098,struct.pack('<I',double))
   for reg,v in ((UC_ARM_REG_R0,0x02001000),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)):u.reg_write(reg,v)
   u.emu_start(0x030056d8,0x03006000,count=200000)
   road_count+=1
 elif eid in wallmap:
  d=wallmap[eid];mat=event['blocks'][8][1];fb=event['blocks'][3][1];desc=event['blocks'][4][1];shift,height=struct.unpack_from('<2H',mat,36);texture=struct.unpack_from('<I',mat,40)[0]
  asset_addr,asset=event['blocks'][66]
  if 0x02000000<=asset_addr<0x02040000:u.mem_write(asset_addr,asset)
  planned=(C.c_uint32*2400)();planned_count=C.c_uint();wall_source=wall_sources[eid]
  assert wall_plan(prepared_edge(wall_source,wall_table),wall_table,(C.c_uint*4)(*wall_source['bounds']),mat,fb,desc,planned,120,C.byref(planned_count))
  assert planned_count.value==d['count']
  native_columns=[]
  for i in range(d['count']):
   ci=d['start']+i;top,U,step,destination,V,count=wallcalls['columns'][ci]
   state=[0]*17
   for k,v in {1:top,2:struct.unpack_from('<I',fb,12)[0]>>1,3:shift,4:height,6:((struct.unpack_from('<H',desc,2)[0]>>4)^1)&1,7:height<<shift,9:texture,11:step,13:U,16:(1<<(shift+15))-1}.items():state[k]=v
   native_columns.extend([*state,destination,V,count])
   original=originalwall[start+ci];regs=original[2:18];u.mem_write(0x02001000,struct.pack('<17I',*original[18:]))
   for reg,v in ((UC_ARM_REG_R0,0x02001000),(UC_ARM_REG_R1,regs[1]),(UC_ARM_REG_R2,regs[2]),(UC_ARM_REG_R3,regs[3]),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)):u.reg_write(reg,v)
   wall_bus_active=True;u.emu_start(0x030053e8,0x03006000,count=200000);wall_bus_active=False
   wall_count+=1;wall_rows+=count
  assert list(planned[:planned_count.value*20])==native_columns
  live_words=live_wall_plans[eid];assert list(live_words)==native_columns
  packed=(C.c_uint32*len(live_words))(*live_words);pixels=(C.c_uint8*len(native)).from_buffer(native);writes=C.c_uint()
  source_address,source_bytes=(0x08000000,rom) if 0x08000000<=asset_addr<0x08000000+len(rom) else (asset_addr,asset)
  assert wall_writer(packed,d['count'],source_address,source_bytes,len(source_bytes),pixels,0x18000,C.byref(writes));del pixels;wall_writes+=writes.value
 elif eid in modelmap:
  asset_addr,asset=event['blocks'][66]
  if 0x02000000<=asset_addr<0x02040000:u.mem_write(asset_addr,asset)
  calls=modelmap[eid];packed=(C.c_uint32*(len(calls)*7))(*[v for call in calls for v in [call['polygon'],*call['params']]])
  texture=calls[0]['texture'];assert all(call['texture']==texture and call['shift']==calls[0]['shift'] for call in calls)
  pixels=(C.c_uint8*len(native)).from_buffer(native);assert model_writer(packed,len(calls),calls[0]['shift'],asset_addr,asset,len(asset),pixels,0x18000);del pixels
  for call in modelmap[eid]:
   destination,count,U,V,du,dv=call['params'];src=(C.c_uint32*240)();dst=(C.c_uint32*240)();assert mf(call['texture'],destination,count,call['shift'],U,V,du,dv,src,dst)
   for i,value in enumerate(call['oracle_globals']):u.mem_write(struct.unpack_from('<I',model_code,0x5a30+i*4)[0],struct.pack('<I',value))
   for reg,val in ((UC_ARM_REG_R0,call['oracle_regs'][0]),(UC_ARM_REG_R1,call['oracle_regs'][1]),(UC_ARM_REG_R2,call['oracle_regs'][2]),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)):u.reg_write(reg,val)
   u.emu_start(0x03005920,0x03006000,count=20000);model_count+=1;model_samples+=count
 else:continue
 assert bytes(u.mem_read(0x06000000,0x20000))==native,eid
 actual=Path(actual_draws[str(eid)]['after_path']).read_bytes();difference=sum(a!=b for a,b in zip(native,actual));actual_checks.append(dict(event=eid,different_bytes=difference,exact=difference==0))
 if eid in closing:
  flip=closing[eid];page=1 if flip['regs'][1]&16 else 0;expected_display=flip['blocks'][92][1];assert native[page*0xa000:page*0xa000+38400]==expected_display;display_checks.append(dict(refresh=flip['frame'],page=page,exact=True))
 if eid in closing:
  operations=[]
  for op in closing_sprite_ops[eid]:
   regs=op['regs'];src=op['blocks'][102][1];operations.append((regs[0]-0x06000000,src,regs[2]))
  final=closing_snapshot(owned_scene,operations)
  expected=closing_sprite_state[closing[eid]['frame']]['blocks'][98][1]
  assert final[0x14000:0x18000]==expected,('closing OBJ',eid)
  assets=p/'native-closing-vram-assets';assets.mkdir(exist_ok=True);(assets/f"{closing[eid]['frame']}-vram.bin").write_bytes(final[:0x18000])
  sprite_display_checks.append(dict(refresh=closing[eid]['frame'],exact=True,post_surface_copy_calls=len(closing_sprite_ops[eid])))
 checks.append(dict(event=eid,kind='wall' if eid in wallmap else 'model' if eid in modelmap else 'road',exact=True))
(p/'native-closing-vram-scene-buffer.bin').write_bytes(native)
r=dict(result='PASS_NATIVE_CLOSING_BG_AND_OBJ_ONE_SEED' if all(c['exact'] for c in actual_checks) else 'ACTUAL_DRAW_PIXEL_DIFFERENCE',display_checks=display_checks,sprite_display_checks=sprite_display_checks,captured_initial_scene_baselines=1, native_initialized_scenes=len(first_events), comparison_region_bytes=0x18000,sprite_copy_calls=sprite_copy_count,actual_draw_checks=actual_checks,exact_actual_draws=sum(c['exact'] for c in actual_checks),draws=checks,model_spans=model_count,model_texture_samples=model_samples,road_writer_calls=road_count,wall_columns=wall_count,wall_texture_rows=wall_rows,wall_nonzero_writes=wall_writes,buffer_comparison_bytes=len(checks)*len(native),actual_vram_comparison_bytes=len(actual_checks)*0x18000,scope='One initial captured VRAM seed only. Native fill/copy plus native road/wall/model operations carry both BG pages across all seven scenes. Actual complete 98KiB VRAM compared after every draw and seven closing display index pages. OAM, palette composition and live 4K/full-scene timing remain excluded. Model row traversal is native C from owned polygon sources; source projection/topology adapter remains diagnostic.')
(p/'native-closing-vram-scene-buffer-tests.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print({k:v for k,v in r.items() if k not in ('draws','scope','actual_draw_checks')})

assert owned_scene.generation>69
ownership=dict(result='PASS_PERSISTENT_NATIVE_HANDLE_ACTUAL_SCENES',initial_seeds=1,committed_event_submissions=owned_scene.generation,exact_draws=len(actual_checks),actual_vram_bytes=len(actual_checks)*0x18000,scope='Persistent native handle carries primary fill/copy/road/wall/model stream; all seven closing sprite-copy batches execute on independent native forks. Road, wall and model execution consume coherent live-hook-generated command records.')
(p/'native-persistent-handle-replay-tests.json').write_text(json.dumps(ownership,indent=2));print(ownership);owned_scene.close()

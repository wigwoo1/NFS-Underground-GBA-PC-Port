from pathlib import Path
import ctypes as C,json,struct
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
d=C.CDLL(str((root/'visibility-snapshot.dll').resolve()))
a=d.nf_visibility_assets_create;a.argtypes=[C.c_void_p,C.c_size_t];a.restype=C.c_void_p
release=d.nf_visibility_assets_release;release.argtypes=[C.c_void_p]
create=d.nf_visibility_snapshot_create;create.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.c_void_p,C.c_void_p];create.restype=C.c_void_p
destroy=d.nf_visibility_snapshot_destroy;destroy.argtypes=[C.c_void_p]
evaluate=d.nf_visibility_snapshot_evaluate;evaluate.argtypes=[C.c_void_p,C.c_void_p]
read=d.nf_visibility_snapshot_read;read.argtypes=[C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t]
class Identity(C.Structure):
 _fields_=[('epoch',C.c_uint64),('serial',C.c_uint32),('begin',C.c_uint32),('end',C.c_uint32),('query',C.c_uint32),('builder',C.c_uint32)]
bind=d.nf_visibility_snapshot_bind;bind.argtypes=[C.c_void_p,C.c_void_p]
checked=d.nf_visibility_snapshot_evaluate_for;checked.argtypes=[C.c_void_p,C.c_uint64,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p]
identities={i['serial']:i for i in json.loads((root/'pipeline-packet-identities.json').read_text())};guards=0
budget_for=d.nf_visibility_history_budget;budget_for.argtypes=[C.c_void_p,C.c_uint];budget_for.restype=C.c_size_t
history_create=d.nf_visibility_history_create;history_create.argtypes=[C.c_void_p,C.c_size_t];history_create.restype=C.c_void_p
push=d.nf_visibility_history_push;push.argtypes=[C.c_void_p,C.c_void_p]
history_eval=d.nf_visibility_history_evaluate;history_eval.argtypes=[C.c_void_p,C.c_uint64,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p]
usage=d.nf_visibility_history_bytes;usage.argtypes=[C.c_void_p];usage.restype=C.c_size_t
history_destroy=d.nf_visibility_history_destroy;history_destroy.argtypes=[C.c_void_p]
history_ids=[]
rom_input=C.create_string_buffer(rom);assets=a(rom_input,len(rom));assert assets
budget=budget_for(assets,2);history=history_create(assets,budget);assert history
assert not history_create(assets,budget_for(assets,1)-1)
empty_bytes=budget_for(assets,0);one_bytes=budget_for(assets,1)
C.memset(rom_input,0,len(rom));snapshots=[];invalid=0
for name in json.loads((root/'pipeline-capture-manifest.json').read_text()):
 data=(root/'pipeline-corpus'/name).read_bytes();stride=88+0x48000;h=struct.unpack_from('<22I',data)
 def memory(stage,address,n):
  off=address-0x02000000 if address<0x03000000 else 0x40000+address-0x03000000
  return data[stage*stride+88+off:stage*stride+88+off+n]
 def word(stage,address):return struct.unpack('<I',memory(stage,address,4))[0]
 def half(stage,address):return struct.unpack('<H',memory(stage,address,2))[0]
 sp=h[19];state=h[4];table=word(0,state+0x60);groups=word(0,state+0x64)
 ram=C.create_string_buffer(data[88:stride]);base=(C.c_uint32*2)(h[7],h[6])
 query=C.create_string_buffer(memory(0,word(0,sp+0x98),48));view=C.create_string_buffer(memory(2,word(2,state+0x54),48))
 selected=half(0,0x03005d44);recovery=half(0,word(0,sp+0xa4)+0x78)
 snapshot=create(assets,ram,0x48000,state,selected,recovery,base,query,view);assert snapshot
 item=identities[h[5]];last=struct.unpack_from('<22I',data,3*stride)
 identity=Identity(item['epoch'],item['serial'],item['begin'],item['end'],h[3],last[3])
 sentinel=C.create_string_buffer(b'\xcc'*4676)
 assert not checked(snapshot,identity.epoch,identity.serial,identity.begin,identity.end,sentinel)
 assert sentinel.raw[:4676]==b'\xcc'*4676;guards+=1
 bad_id=Identity(identity.epoch,identity.serial,identity.begin,identity.end,identity.end+1,identity.end)
 assert not bind(snapshot,C.byref(bad_id));guards+=1
 assert bind(snapshot,C.byref(identity))
 assert not bind(snapshot,C.byref(identity));guards+=1
 for epoch,serial,begin,end in [(identity.epoch+1,identity.serial,identity.begin,identity.end),(identity.epoch,identity.serial+1,identity.begin,identity.end),(identity.epoch,identity.serial,identity.begin+1,identity.end),(identity.epoch,identity.serial,identity.begin,identity.end+1)]:
  assert not checked(snapshot,epoch,serial,begin,end,sentinel) and sentinel.raw[:4676]==b'\xcc'*4676;guards+=1
 result=C.create_string_buffer(4676);assert checked(snapshot,identity.epoch,identity.serial,identity.begin,identity.end,result)
 expected=memory(3,state,256)+memory(3,table,320)+memory(3,groups,4096)+struct.pack('<I',half(3,0x03005d44))
 assert result.raw[:4676]==expected
 snapshots.append((snapshot,expected));history_ids.append((identity.epoch,identity.serial,identity.begin,identity.end))
 assert push(history,snapshot) and usage(history)<=budget
 assert usage(history)==(one_bytes if len(snapshots)==1 else budget)
 assert not push(history,snapshot) # Duplicate cannot evict a valid scene.
 if len(snapshots)>2:
  guard=C.create_string_buffer(b'\xcc'*4676)
  assert not history_eval(history,*history_ids[-3],guard) and guard.raw[:4676]==b'\xcc'*4676
 if len(snapshots)==24:
  reset=create(assets,ram,0x48000,state,selected,recovery,base,query,view);assert reset
  reset_id=Identity(identity.epoch+1,0,identity.begin,identity.end,identity.query,identity.builder)
  assert bind(reset,C.byref(reset_id))
  epoch_history=history_create(assets,budget);assert epoch_history
  assert push(epoch_history,snapshot) and push(epoch_history,reset)
  assert not push(epoch_history,snapshot) and usage(epoch_history)==one_bytes
  history_destroy(epoch_history)
 if len(snapshots)==1:
  for size,address in [(0x47fff,state),(0x48000,0x08000000),(0x48000,0x03007fff)]:
   assert not create(assets,ram,size,address,selected,recovery,base,query,view);invalid+=1
  # A structurally retained snapshot with invalid queue pointer must fail atomically.
  off=state-0x02000000 if state<0x03000000 else 0x40000+state-0x03000000
  C.memmove(C.addressof(ram)+off+0x60,struct.pack('<I',0xffffffff),4)
  bad=create(assets,ram,0x48000,state,selected,recovery,base,query,view);assert bad
  sentinel=C.create_string_buffer(b'\xcc'*4676)
  assert not evaluate(bad,sentinel) and sentinel.raw[:4676]==b'\xcc'*4676;destroy(bad)
 C.memset(ram,0,0x48000);C.memset(query,0,48);C.memset(view,0,48);C.memset(base,0,8)
assert not push(history,snapshots[0][0]) and usage(history)==budget
release(assets) # Snapshots must keep the shared ROM alive independently.
for snapshot,expected in snapshots:
 for repeat in range(2):
  result=C.create_string_buffer(4676);assert evaluate(snapshot,result)
  assert result.raw[:4676]==expected
 for addr,n in [(0xffffffff,4),(0x0203ffff,2),(0x03007fff,2),(0x04000000,4),(0x087fffff,2),(0x02000000,2**63)]:
  sentinel=C.create_string_buffer(b'\xcc'*8);assert not read(snapshot,addr,sentinel,n) and sentinel.raw[:8]==b'\xcc'*8;invalid+=1
 destroy(snapshot)
# History remains valid after all source snapshots and caller assets are released.
for ident,expected in zip(history_ids[-2:],[p[1] for p in snapshots[-2:]]):
 result=C.create_string_buffer(4676);assert history_eval(history,*ident,result) and result.raw[:4676]==expected
assert push(history,reset) and usage(history)==one_bytes
guard=C.create_string_buffer(b'\xcc'*4676)
assert not history_eval(history,*history_ids[-1],guard) and guard.raw[:4676]==b'\xcc'*4676
result=C.create_string_buffer(4676);assert history_eval(history,reset_id.epoch,reset_id.serial,reset_id.begin,reset_id.end,result)
assert result.raw[:4676]==snapshots[-1][1]
destroy(reset);history_destroy(history)
report=dict(history_budget_bytes=budget,history_evictions=22,epoch_reset_clears_history=True,source_destruction_safe=True,result='PASS' ,owned_snapshots_exact=len(snapshots),scene_identity_guard_checks=guards,repeat_evaluations=len(snapshots)*2,invalid_ranges_or_creation=invalid,
 source_buffers_overwritten=True,caller_asset_reference_released_before_evaluation=True,invalid_queue_failure_atomic=True,
 scope='Owned visibility snapshot and shared immutable ROM lifecycle. Does not include VRAM/render packet assets or live capture integration; complete scene snapshots remain unfinished.')
(root/'visibility-history-tests.json').write_text(json.dumps(report,indent=2));print(report)

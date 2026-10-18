from pathlib import Path
import ctypes as C,os,struct,json,hashlib
source=Path(__file__).parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-retention-tests';fixtures=base/'NFSUG-background-owner-api-fixtures';native=base/'NFSUG-android-background-jni-native-local'
with os.add_dll_directory('C:/msys64/mingw64/bin'):dll=C.CDLL(str(out/'source-retention.dll'));core=C.CDLL(str(native/'capture-host.dll'))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint;Q=C.c_uint64;I=C.c_int
def fn(d,n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
decode=fn(dll,'nf_pc_retention_decode',[P,S,P,S,P,U,U,U,S],P);free=fn(dll,'nf_pc_retention_free',[P],None);info=fn(dll,'nf_pc_retention_info',[P,P]);buffer=fn(dll,'nf_pc_retention_buffer',[P,U,C.POINTER(P),C.POINTER(S)])
prepare=fn(dll,'nf_pc_source_retention',[P,U,U,S],P);bind=fn(dll,'nf_pc_source_api_bind_owner',[P]);capture=fn(dll,'nf_pc_source_frame_capture',[P,S],P);release_frame=fn(dll,'nf_pc_source_frame_free',[P],None)
def blob(h,kind):p=P();n=S();assert buffer(h,kind,C.byref(p),C.byref(n));return C.string_at(p,n.value)
def sha(b):return hashlib.sha256(b).hexdigest()
references={}
for path in (out/'references').glob('*.ret'):
 data=path.read_bytes();refresh,owner,kind=map(int,path.stem.split('-'));meta=struct.unpack('>5Q4I',data[:56]);rgba=data[56:153656];records=data[153656:];assert len(records)==meta[8]*16;references[refresh,owner,kind]=(meta,rgba,records)
assert len(references)==34
cells=0;rejected=0;held=[];cases=[]
def check(h,g):
 m=(Q*10)();assert h and info(h,m);meta,rgba,records=g;assert tuple(m[:9])==meta and blob(h,0)==rgba and blob(h,1)==records;return m[9]
for key,g in sorted(references.items()):
 refresh,owner,kind=key;meta,rgba,records=g;o=(Q*5)(*meta[:5]);serial=meta[1];history=(fixtures/(f'owner-{serial}'+('.nrh' if kind==2 else '.nwh'))).read_bytes();proof=(fixtures/f'owner-{serial}.nrp').read_bytes()
 # Independently owned mutable input, overwritten before output comparison.
 hb=C.create_string_buffer(history);pb=C.create_string_buffer(proof);h=decode(hb,len(history),pb,len(proof),o,kind,meta[6],meta[7],64*1024*1024);budget=check(h,g);C.memset(hb,0,len(history));C.memset(pb,0,len(proof));assert check(h,g)==budget;held.append((h,g));cells+=meta[8];cases.append(dict(refresh=refresh,owner=owner,kind=kind,cells=meta[8],index_sha256=sha(rgba),records_sha256=sha(records)))
 assert not decode(history,len(history),proof,len(proof),o,kind,meta[6],meta[7],budget-1);exact=decode(history,len(history),proof,len(proof),o,kind,meta[6],meta[7],budget);assert exact;free(exact)
 if len(cases)==1 or (kind==3 and sum(c['kind']==3 for c in cases)==1):
  for offset,value in [(0,0),(8,2),(16,len(history)-1),(24,meta[0]+1),(32,1025),(40,65537),(48,1),(56,1),(64,9),(72,63)]:
   bad=bytearray(history);struct.pack_into('<Q',bad,offset,value);assert not decode(bytes(bad),len(bad),proof,len(proof),o,kind,meta[6],meta[7],64*1024*1024);rejected+=1
  event=64
  while struct.unpack_from('<Q',history,event)[0]!=2:event+=struct.unpack_from('<Q',history,event+8)[0]
  for relative in [8,16,24,32,48,56,64,72,80,88]:
   bad=bytearray(history);struct.pack_into('<Q',bad,event+relative,0xffffffffffffffff);assert not decode(bytes(bad),len(bad),proof,len(proof),o,kind,meta[6],meta[7],64*1024*1024);rejected+=1
  for relative in ([96,100,104,120,124,160] if kind==2 else [108,112,132,172]):
   bad=bytearray(history);struct.pack_into('<I',bad,event+relative,0xffffffff);assert not decode(bytes(bad),len(bad),proof,len(proof),o,kind,meta[6],meta[7],64*1024*1024);rejected+=1
  for offset,value in [(0,0),(24,meta[0]+1),(32,serial+1),(40,meta[2]+1),(48,meta[3]+1),(56,meta[3]),(64,1-meta[4]),(72,38399)]:
   bad=bytearray(proof);struct.pack_into('<Q',bad,offset,value);assert not decode(history,len(history),bytes(bad),len(bad),o,kind,meta[6],meta[7],64*1024*1024);rejected+=1
  for offset,value in [(80,7),(38480,meta[3]+1)]:
   bad=bytearray(proof)
   if offset==80:bad[offset]=value
   else:struct.pack_into('<I',bad,offset,value)
   assert not decode(history,len(history),bytes(bad),len(bad),o,kind,meta[6],meta[7],64*1024*1024);rejected+=1
  # A valid proof kind but no matching command/refresh must reject even outside the output band.
  occupied=next(i for i in range(38400) if rgba[i*4+3]);bad=bytearray(proof);struct.pack_into('<I',bad,38480+occupied*4,0);assert not decode(history,len(history),bytes(bad),len(bad),o,kind,160,160,64*1024*1024);rejected+=1
 assert not decode(None,len(history),proof,len(proof),o,kind,0,160,64*1024*1024) and not decode(history,len(history),proof,len(proof)-1,o,kind,0,160,64*1024*1024)
 assert not decode(history,len(history),proof,len(proof),o,4,0,160,64*1024*1024) and not decode(history,len(history),proof,len(proof),o,kind,161,160,64*1024*1024) and not decode(history,len(history),proof,len(proof),o,kind,0,160,64*1024*1024+1)
 sentinel=(Q*10)(*[77]*10);assert not info(None,sentinel) and list(sentinel)==[77]*10;p=P(123);n=S(456);assert not buffer(h,2,C.byref(p),C.byref(n)) and p.value==123 and n.value==456
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
op=fn(core,'nfa_core_open',[C.c_char_p],P);close=fn(core,'nfa_core_close',[P],None);load=fn(core,'nfa_core_load_state',[P,P,S]);step=fn(core,'nfa_core_step',[P,U]);pixels=fn(core,'nfa_core_pixels',[P],P);timing=fn(core,'nfa_core_timing',[P,P]);audio=fn(core,'nfa_core_read_audio',[P,P,S],S);layer=fn(core,'nfa_core_capture_layer_info',[P,P])
for name in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS']:os.environ.pop(name,None)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=(root/'work/integration-0.state').read_bytes();assert sha(rom.read_bytes())=='53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593' and sha(state)=='49e85564032a383626709b183f37aff34601c6e97cabdfcb17c117f72d996104'
h=op(os.fsencode(rom));assert h;api=API(C.sizeof(API),h,*[C.cast(getattr(core,'nfa_core_'+n),P).value for n in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));seen=set();live=[];pcm=(C.c_int16*8192)()
try:
 assert load(h,state,len(state))
 for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(core,'nfa_core_'+name,[P,I])(h,1)
 initial=(Q*4)();assert timing(h,initial)
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1;assert C.string_at(pixels(h),153600)==oracle.read(153600)
   while audio(h,pcm,4096):pass
   tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+index+1 and tick[3]==index+1;display=(Q*5)()
   if not layer(h,display) or display[1] not in {k[0] for k in references} or display[1] in seen:continue
   refresh=display[1];frame=capture(C.byref(api),64*1024*1024);assert frame
   for key,g in references.items():
    if key[0]!=refresh:continue
    retained=prepare(frame,key[1],key[2],64*1024*1024);assert check(retained,g);live.append((retained,g))
   assert not prepare(frame,2,2,64*1024*1024) and not prepare(frame,0,4,64*1024*1024);release_frame(frame);after=(Q*4)();assert timing(h,after) and tuple(after)==tuple(tick);seen.add(refresh)
   if len(seen)==9:break
 assert load(h,state,len(state)) and not capture(C.byref(api),64*1024*1024)
finally:close(h)
assert len(live)==34 and index+1==296
for retained,g in live+held:check(retained,g);free(retained)
r=dict(result='PASS_PC_SOURCE_RETENTION',cases=34,cells=cells,live_cases=len(live),original_prefix_frames=index+1,all_indices_and_source_records_exact=True,mutable_inputs_overwritten_before_comparison=True,owned_after_core_close=True,exact_budget_and_short_budget_verified=True,malformed_history_proof_cases=rejected,invalid_requests_preserve_outputs=True,original_pixels_exact=True,clock_hz=16777216,cycles_per_step=280896,decode_never_steps_logic=True,state_reload_rejects_stale_capture=True,maximum_retained_bytes=budget,dll_sha256=sha((out/'source-retention.dll').read_bytes()),core_sha256=sha((native/'capture-host.dll').read_bytes()),gpu_submitted=False,playable_native_release=False,full_scene_60fps=False,frames=cases)
(out/'retention-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='frames'},indent=2))

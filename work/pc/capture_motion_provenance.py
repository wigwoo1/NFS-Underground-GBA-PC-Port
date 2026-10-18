from pathlib import Path
import os,ctypes as C,json,hashlib,struct,collections
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-motion-provenance-tests'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((out/'provenance-build-report.json').read_text());assert receipt['core_sha256']==sha(out/'capture-host.dll')
for key in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TEST_DIRECT_CAPTURE_ROM']:os.environ.pop(key,None)
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'capture-host.dll'));reader=C.CDLL(str(base/'NFSUG-pc-reader-tests/source-reader.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint32;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
class Event(C.Structure):_fields_=[('cycles',Q),('type',U),('pass_id',U),('ordinal',U),('kind',U),('source',U),('page',U)]
assert C.sizeof(Event)==32
def fn(d,n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
op=fn(d,'nfa_core_open',[C.c_char_p],P);close=fn(d,'nfa_core_close',[P],None);load=fn(d,'nfa_core_load_state',[P,P,S]);step=fn(d,'nfa_core_step',[P,U]);pixels=fn(d,'nfa_core_pixels',[P],P);audio=fn(d,'nfa_core_read_audio',[P,P,S],S);timing=fn(d,'nfa_core_timing',[P,P]);operations=fn(d,'nf_live_completed_operation_order',[Q,U,P,U,P]);detail=fn(d,'nf_live_operation_order_detail',[P],None);bind=fn(reader,'nf_pc_source_api_bind_owner',[P]);rop=fn(reader,'nf_pc_source_reader_open',[P,S],P);rcap=fn(reader,'nf_pc_source_reader_capture',[P,S],P);rclose=fn(reader,'nf_pc_source_reader_close',[P],None);frame_info=fn(reader,'nf_pc_source_frame_info',[P,P]);owner_info=fn(reader,'nf_pc_source_frame_owner',[P,U,P]);component=fn(reader,'nf_pc_source_frame_component',[P,U,U,P,P]);frame_free=fn(reader,'nf_pc_source_frame_free',[P],None)
def word(p,at):return struct.unpack_from('<I',p,at)[0]
commands=fn(d,'nf_pc_original_command_provenance',[Q,U,U,P,U,P])
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(p):sha(p) for p in [rom,state]};data=state.read_bytes();h=op(os.fsencode(rom));assert h and load(h,data,len(data));pcm=(C.c_int16*8192)();digest=hashlib.sha256();samples=0;rows=[];seen=set();failures=[];pair_rows=[];previous=None
for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(d,'nfa_core_'+name,[P,I])(h,1)
api=API(C.sizeof(API),h,*[C.cast(getattr(d,'nfa_core_'+name),P).value for name in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));r=rop(C.byref(api),64*1024*1024);assert r;initial=(Q*4)();assert timing(h,initial)
try:
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1;assert C.string_at(pixels(h),153600)==oracle.read(153600);tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+index+1 and tick[3]==index+1
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    samples+=n;digest.update(C.string_at(pcm,n*4))
   frame=rcap(r,64*1024*1024)
   if not frame:continue
   try:
    fi=(Q*8)();assert frame_info(frame,fi)
    for owner in range(fi[4]):
     oi=(Q*5)();assert owner_info(frame,owner,oi);key=tuple(oi)
     if key in seen:continue
     seen.add(key);events=(Event*608)();count=U()
     if not operations(oi[0],oi[1],events,608,C.byref(count)):
      why=(U*8)();detail(why);failures.append(dict(owner=list(oi),detail=list(why)));continue
     after=(Q*4)();assert timing(h,after) and tuple(after)==tuple(tick)
     p=P();n=S();assert component(frame,owner,1,C.byref(p),C.byref(n));packet=C.string_at(p,n.value);world=word(packet,48);surfaces=word(packet,world+4);ids=word(packet,84);order=word(packet,60);amount=word(packet,order+4);geometry=[event for event in events[:count.value] if event.type>=3]
     assert len(geometry)==amount,(key,len(geometry),amount);identities=[struct.unpack_from('<5I',packet,ids+8+i*20) for i in range(word(packet,ids+4))];models=identities[surfaces:];draws=[]
     command_views={}
     for pass_id in {event.pass_id for event in geometry}:
      data=(U*(144*22))();amount=U();assert commands(oi[0],oi[1],pass_id,data,144,C.byref(amount));command_views[pass_id]=[list(data[i*22:(i+1)*22]) for i in range(amount.value)]
     for i,event in enumerate(geometry):
      target=word(packet,order+8+i*4);is_model=target>=0xfffffff0;target=(0xffffffff-target+surfaces) if is_model else target;identity=identities[target]
      assert event.page==oi[4] and event.source==identity[2] and identity[0]==(3 if is_model else event.kind) and event.type==(4 if is_model else 3),(key,i,list(identity),event.type,event.kind,event.source)
      assert event.pass_id<len(models);pass_identity=models[event.pass_id];command=command_views[event.pass_id][event.ordinal];assert command[0]==event.kind and command[5]==event.source
      ownership=command[:6];record=command[13:17];draws.append(dict(identity=list(identity),pass_identity=list(pass_identity),source_ownership=ownership,source_record=record,original_command_words=command,pass_id=event.pass_id,ordinal=event.ordinal,type=event.type,command=i,surface=target if not is_model else None,cycles=event.cycles))
     assert timing(h,after) and tuple(after)==tuple(tick)
     def duplicates(names):
      counts=collections.Counter(tuple(tuple(v[name]) for name in names) for v in draws if v['type']==3);return sum(n for n in counts.values() if n>1)
     raw_duplicates=duplicates(['identity']);pass_duplicates=duplicates(['identity','pass_identity']);ownership_duplicates=duplicates(['identity','pass_identity','source_ownership']);record_duplicates=duplicates(['identity','pass_identity','source_ownership','source_record'])
     row=dict(owner=list(oi),geometry_sha256=hashlib.sha256(packet).hexdigest(),event_count=count.value,draws=draws,raw_duplicate_rows=raw_duplicates,pass_duplicate_rows=pass_duplicates,ownership_duplicate_rows=ownership_duplicates,record_duplicate_rows=record_duplicates);rows.append(row)
     if previous and previous['owner'][0]==oi[0] and previous['owner'][1]<oi[1] and 0<oi[3]-previous['owner'][3]<=8:
      old=[v for v in previous['draws'] if v['type']==3];new=[v for v in draws if v['type']==3]
      def audit(names):
       def k(v):return tuple(tuple(v[n]) for n in names)
       a=collections.Counter(k(v) for v in old);b=collections.Counter(k(v) for v in new);return dict(unique_shared=sum(n==1 and b[x]==1 for x,n in a.items()),ambiguous_old=sum(n for x,n in a.items() if n>1 or b[x]>1),old_only=sum(n for x,n in a.items() if not b[x]),new_only=sum(n for x,n in b.items() if not a[x]))
      pair_rows.append(dict(older=previous['owner'],newer=list(oi),identity=audit(['identity']),identity_and_pass_model=audit(['identity','pass_identity']),identity_pass_ownership=audit(['identity','pass_identity','source_ownership']),identity_pass_ownership_record=audit(['identity','pass_identity','source_ownership','source_record'])))
     previous=row
   finally:frame_free(frame)
finally:rclose(r);close(h)
assert samples==443007 and digest.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e';assert before=={str(p):sha(p) for p in [rom,state]};assert len(rows)>20
report=dict(result='PARTIAL_ORIGINAL_OPERATION_SOURCE_PROVENANCE_AUDIT' if failures else 'PASS_ORIGINAL_OPERATION_SOURCE_PROVENANCE_AUDIT',original_frames=600,original_pixels_exact=True,audio_frames=samples,audio_sha256=digest.hexdigest(),owners=len(rows),requested_owners=len(seen),failed_owners=len(failures),failures=failures,pairs=len(pair_rows),raw_duplicate_rows=sum(row['raw_duplicate_rows'] for row in rows),pass_duplicate_rows=sum(row['pass_duplicate_rows'] for row in rows),raw_ambiguous_old_rows=sum(row['identity']['ambiguous_old'] for row in pair_rows),pass_ambiguous_old_rows=sum(row['identity_and_pass_model']['ambiguous_old'] for row in pair_rows),source_order_events_bound_to_each_available_owner_command=True,complete_owner_coverage=not failures,no_extra_logic_steps=True,rom_state_sha256=before,core_sha256=sha(out/'capture-host.dll'),build_report_sha256=sha(out/'provenance-build-report.json'),script_sha256=sha(Path(__file__)),owners_data=rows,pair_data=pair_rows,live_integration=False,full_scene_60fps=False)
report['ownership_duplicate_rows']=sum(row['ownership_duplicate_rows'] for row in rows);report['record_duplicate_rows']=sum(row['record_duplicate_rows'] for row in rows)
report['association_totals']={variant:{field:sum(row[variant][field] for row in pair_rows) for field in ['unique_shared','ambiguous_old','old_only','new_only']} for variant in ['identity','identity_and_pass_model','identity_pass_ownership','identity_pass_ownership_record']}
(out/'provenance-audit-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['owners_data','pair_data','failures']},indent=2))

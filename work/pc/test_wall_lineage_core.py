from pathlib import Path
import os,ctypes as C,json,hashlib,struct,zlib,collections
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-wall-lineage-tests'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'lineage-build-report.json').read_text());assert sha(out/'capture-host.dll')==build['core_sha256']
for k in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TEST_DIRECT_CAPTURE_ROM']:os.environ.pop(k,None)
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'capture-host.dll'));reader=C.CDLL(str(base/'NFSUG-pc-reader-tests/source-reader.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint32;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(lib,name,args,r=I):f=getattr(lib,name);f.argtypes=args;f.restype=r;return f
op=fn(d,'nfa_core_open',[C.c_char_p],P);close=fn(d,'nfa_core_close',[P],None);load=fn(d,'nfa_core_load_state',[P,P,S]);step=fn(d,'nfa_core_step',[P,U]);pixels=fn(d,'nfa_core_pixels',[P],P);audio=fn(d,'nfa_core_read_audio',[P,P,S],S);timing=fn(d,'nfa_core_timing',[P,P]);read=fn(d,'nf_pc_wall_lineage_read',[P,S,P]);consume=fn(d,'nf_pc_wall_lineage_consume',[],None);status=fn(d,'nf_pc_wall_lineage_status',[P]);bind=fn(reader,'nf_pc_source_api_bind_owner',[P]);rop=fn(reader,'nf_pc_source_reader_open',[P,S],P);capture=fn(reader,'nf_pc_source_reader_capture',[P,S],P);rclose=fn(reader,'nf_pc_source_reader_close',[P],None);finfo=fn(reader,'nf_pc_source_frame_info',[P,P]);oinfo=fn(reader,'nf_pc_source_frame_owner',[P,U,P]);component=fn(reader,'nf_pc_source_frame_component',[P,U,U,P,P]);ffree=fn(reader,'nf_pc_source_frame_free',[P],None)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(p):sha(p) for p in [rom,state]};state_bytes=state.read_bytes();h=op(os.fsencode(rom));assert h and load(h,state_bytes,len(state_bytes))
for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(d,'nfa_core_'+name,[P,I])(h,1)
api=API(C.sizeof(API),h,*[C.cast(getattr(d,'nfa_core_'+name),P).value for name in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));r=rop(C.byref(api),64*1024*1024);assert r
initial=(Q*4)();assert timing(h,initial);pcm=(C.c_int16*8192)();digest=hashlib.sha256();samples=entries=recipes=columns=returns=checks=old_checks=guards=shaded=0;stack=[];calls={};mapping={};opcode=collections.Counter();return_pcs=collections.Counter();targets={int(p.stem) for p in (base/'NFSUG-pc-scene-tests/references').glob('*.scene')};assert len(targets)==9;max_depth=0;raw_digest=hashlib.sha256()
try:
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle,(out/'wall-source-lineage.wclz').open('wb') as archive:
  archive.write(b'WCLZ\x01\0\0\0')
  for index in range(600):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1;assert C.string_at(pixels(h),153600)==oracle.read(153600)
   tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+index+1 and tick[3]==index+1
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    samples+=n;digest.update(C.string_at(pcm,n*4))
   stat=(Q*8)();assert status(stat);n=S()
   if not read(None,0,C.byref(n)):
    (out/'failed-lineage-status.json').write_text(json.dumps(dict(index=index,status=list(stat)),indent=2));raise AssertionError(('Lineage capture rejected',index,list(stat)))
   raw=C.create_string_buffer(n.value);assert read(raw,n.value,C.byref(n));blob=raw.raw;raw_digest.update(blob);packed=zlib.compress(blob);archive.write(struct.pack('<I',len(packed)));archive.write(packed);at=0
   while at<len(blob):
    tag,size=struct.unpack_from('<2Q',blob,at);assert 64<=size<=len(blob)-at;record=blob[at:at+size];epoch,refresh,invocation=struct.unpack_from('<3Q',record,16)
    if tag==1:
     a=struct.unpack_from('<14Q',record);assert size==112 and invocation==entries+1 and a[13]==len(stack)+1;calls[invocation]=dict(entry=a,columns=0,texture=None);stack.append(invocation);entries+=1;max_depth=max(max_depth,len(stack));opcode[hex(a[12])]+=1
    elif tag==2:
     a=struct.unpack_from('<8Q',record);assert stack[-1]==invocation and calls[invocation]['texture'] is None and a[6:]==(65536,12);pos=64;blocks=[]
     for block in range(12):length=struct.unpack_from('<I',record,pos)[0];pos+=4;blocks.append(record[pos:pos+length]);pos+=length
     assert pos==len(record) and [len(b) for b in blocks]==[136,64,8,48,48,8,64,32,65536,512,52,260];assert struct.unpack_from('<I',blocks[4],40)[0]==a[5] and struct.unpack_from('<I',blocks[11],256)[0]==calls[invocation]['entry'][11]
     calls[invocation]['texture']=hashlib.sha256(blocks[8]).hexdigest();calls[invocation]['address']=a[5];recipes+=1
    elif tag==3:
     a=struct.unpack_from('<10Q',record);assert stack[-1]==invocation and calls[invocation]['texture'] and a[8]==1 and a[9]==(4081 if a[6] else 0) and size==160+a[9] and a[7]==calls[invocation]['address'];assert a[5]==columns+1
     command=record[80:160];assert struct.unpack_from('<I',command,36)[0]==a[7];shade=hashlib.sha256(record[160:]).hexdigest() if a[9] else None
     mapping[(epoch,a[5])]=(refresh,command,calls[invocation]['texture'],shade);calls[invocation]['columns']+=1;columns+=1;shaded+=bool(a[6])
    elif tag==4:
     a=struct.unpack_from('<8Q',record);assert size==64 and stack.pop()==invocation and a[5]==(calls[invocation]['entry'][6]&~1) and a[6]==calls[invocation]['entry'][5] and a[7]==calls[invocation]['columns'];return_pcs[hex(a[5])]+=1;returns+=1
    else:raise AssertionError(tag)
    at+=size
   assert at==len(blob) and list(stat[1:6])==[entries,recipes,columns,returns,len(stack)] and not stat[6] and stat[7]==columns,('Missing or unscoped columns',index,list(stat),columns)
   if n.value and not guards:
    tiny=C.create_string_buffer(b'\xa5'*8);unchanged=S(123);assert not read(tiny,8,C.byref(unchanged)) and unchanged.value==123 and tiny.raw==b'\xa5'*8+b'\0';guards+=1;assert not read(raw,n.value,None);guards+=1
   consume();empty=S(123);assert read(None,0,C.byref(empty)) and not empty.value
   if tick[2] in targets or index==599:
    frame=capture(r,64*1024*1024);assert frame;fi=(Q*8)();assert finfo(frame,fi)
    try:
     for owner in range(fi[4]):
      oi=(Q*5)();assert oinfo(frame,owner,oi);p=P();length=S();assert component(frame,owner,3,C.byref(p),C.byref(length));history=C.string_at(p,length.value);header=struct.unpack_from('<8Q',history);assert header[0]==0x3148574e and header[3]==oi[0];ha=64;assets={}
      while ha<len(history):
       tag,size=struct.unpack_from('<2Q',history,ha)
       if tag==1:asset=struct.unpack_from('<Q',history,ha+16)[0];assets[asset]=hashlib.sha256(history[ha+64:ha+size]).hexdigest()
       else:
        assert tag==2;ordinal,refresh,asset,shade=struct.unpack_from('<4Q',history,ha+16);assert mapping[(oi[0],ordinal)]==(refresh,history[ha+96:ha+176],assets[asset],assets[shade] if shade else None);checks+=1;old_checks+=refresh<oi[2]
       ha+=size
      assert ha==len(history)
    finally:ffree(frame)
   after=(Q*4)();assert timing(h,after) and tuple(after)==tuple(tick)
  assert entries>100 and recipes>100 and columns>1000 and returns==entries and not stack and checks>100
  assert load(h,state_bytes,len(state_bytes));empty=S(123);stat=(Q*8)();assert read(None,0,C.byref(empty)) and empty.value==0 and status(stat) and list(stat[1:])==[0]*7;guards+=1
finally:rclose(r);close(h)
archive=(out/'wall-source-lineage.wclz').read_bytes();assert archive[:8]==b'WCLZ\x01\0\0\0';at=8;frames=0;saved_digest=hashlib.sha256()
while at<len(archive):length=struct.unpack_from('<I',archive,at)[0];at+=4;blob=zlib.decompress(archive[at:at+length]);at+=length;saved_digest.update(blob);frames+=1
assert at==len(archive) and frames==600 and saved_digest.digest()==raw_digest.digest()
assert samples==443007 and digest.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e' and before=={str(p):sha(p) for p in [rom,state]}
report=dict(result='PASS_EXPLICIT_ORIGINAL_WALL_CALL_LINEAGE',entries=entries,owned_source_recipes=recipes,columns=columns,shaded_columns=shaded,returns=returns,max_call_depth=max_depth,entry_opcodes=dict(opcode),return_pcs=dict(return_pcs),all_accepted_columns_scoped=True,all_scope_returns_match_entry_lr_and_sp=True,history_command_texture_and_shade_checks=checks,historical_history_checks=old_checks,negative_and_reset_checks=guards,archive_frames=frames,archive_sha256=sha(out/'wall-source-lineage.wclz'),archive_raw_sha256=raw_digest.hexdigest(),original_frames=600,original_pixels_exact=True,audio_frames=samples,audio_sha256=digest.hexdigest(),original_timing_exact=True,no_extra_logic_steps=True,rom_state_sha256=before,core_sha256=sha(out/'capture-host.dll'),build_report_sha256=sha(out/'lineage-build-report.json'),script_sha256=sha(Path(__file__)),runtime_retention_lifetime_implemented=False,fractional_wall_projection=False,live_integration=False,full_scene_60fps=False,scope='Actual wall entry/LR+SP return lineage, exact accepted column command/material ownership and retained-history checks. Does not regenerate original columns from raw source geometry or prove fractional motion.')
(out/'lineage-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

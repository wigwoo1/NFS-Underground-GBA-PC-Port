from pathlib import Path
import ctypes as C,os,json,hashlib,struct,zlib
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-road-recipe-tests'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'recipe-build-report.json').read_text());assert sha(out/'capture-host.dll')==build['core_sha256']
for k in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TEST_DIRECT_CAPTURE_ROM']:os.environ.pop(k,None)
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'capture-host.dll'));reader=C.CDLL(str(base/'NFSUG-pc-reader-tests/source-reader.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint32;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(lib,name,args,r=I):f=getattr(lib,name);f.argtypes=args;f.restype=r;return f
op=fn(d,'nfa_core_open',[C.c_char_p],P);close=fn(d,'nfa_core_close',[P],None);load=fn(d,'nfa_core_load_state',[P,P,S]);step=fn(d,'nfa_core_step',[P,U]);pixels=fn(d,'nfa_core_pixels',[P],P);audio=fn(d,'nfa_core_read_audio',[P,P,S],S);timing=fn(d,'nfa_core_timing',[P,P]);read=fn(d,'nf_pc_road_recipes_read',[P,S,P]);consume=fn(d,'nf_pc_road_recipes_consume',[],None);table_get=fn(d,'nf_pc_road_recipes_table',[P,S]);replay=fn(d,'nf_pc_road_recipe_replay',[P,S,P,S,P,S,P]);progress=fn(d,'nf_pc_road_recipe_progress',[P]);bind=fn(reader,'nf_pc_source_api_bind_owner',[P]);rop=fn(reader,'nf_pc_source_reader_open',[P,S],P);capture=fn(reader,'nf_pc_source_reader_capture',[P,S],P);rclose=fn(reader,'nf_pc_source_reader_close',[P],None);finfo=fn(reader,'nf_pc_source_frame_info',[P,P]);oinfo=fn(reader,'nf_pc_source_frame_owner',[P,U,P]);component=fn(reader,'nf_pc_source_frame_component',[P,U,U,P,P]);ffree=fn(reader,'nf_pc_source_frame_free',[P],None)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(p):sha(p) for p in [rom,state]};state_bytes=state.read_bytes();h=op(os.fsencode(rom));assert h and load(h,state_bytes,len(state_bytes))
for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(d,'nfa_core_'+name,[P,I])(h,1)
api=API(C.sizeof(API),h,*[C.cast(getattr(d,'nfa_core_'+name),P).value for name in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));r=rop(C.byref(api),64*1024*1024);assert r
table_reference=None
initial=(Q*4)();assert timing(h,initial);table=C.create_string_buffer(131072);output=C.create_string_buffer(8192*68);pcm=(C.c_int16*8192)();digest=hashlib.sha256();samples=records=runs=checks=old_checks=guards=0;max_age=0;last=0;mapping={};retained_packet=None;owners=set();targets={int(p.stem) for p in (base/'NFSUG-pc-scene-tests/references').glob('*.scene')};assert len(targets)==9
try:
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle,(out/'road-source-recipes.nrrz').open('wb') as archive:
  archive.write(b'NRRZ\x01\0\0\0')
  for index in range(600):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1;assert C.string_at(pixels(h),153600)==oracle.read(153600)
   tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+index+1 and tick[3]==index+1
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    samples+=n;digest.update(C.string_at(pcm,n*4))
   n=S();assert read(None,0,C.byref(n));raw=C.create_string_buffer(n.value);assert read(raw,n.value,C.byref(n));blob=raw.raw;at=0
   assert table_get(table,len(table))
   if table_reference is None:table_reference=table.raw
   assert table.raw==table_reference
   while at<len(blob):
    hdr=struct.unpack_from('<10Q',blob,at);magic,size,epoch,refresh,first,count,context,source,descriptor,shift=hdr;assert magic==0x3152524e and 80<size<=len(blob)-at and first==last+1 and count>0
    packet=blob[at:at+size];commands=packet[80:80+count*68];written=U();assert replay(packet,len(packet),table,len(table),output,len(output),C.byref(written)) and written.value==count and output.raw[:count*68]==commands
    source_at=80+count*68;blocks=[]
    for block in range(12):
     length=struct.unpack_from('<I',packet,source_at)[0];source_at+=4;blocks.append(packet[source_at:source_at+length]);source_at+=length
    scratch_size=struct.unpack_from('<I',packet,source_at)[0];assert source_at+4+scratch_size==len(packet);texture_digest=hashlib.sha256(blocks[7]).hexdigest()
    for j in range(count):mapping[(epoch,first+j)]=(refresh,commands[j*68:(j+1)*68],texture_digest)
    packed=zlib.compress(packet);archive.write(struct.pack('<I',len(packed)));archive.write(packed);retained_packet=packet;records+=1;runs+=count;last=first+count-1;at+=size
   assert at==len(blob)
   stat=(Q*3)();assert progress(stat) and not stat[2] and stat[1]==last,('Uncaptured submitted road run',index,list(stat),last)
   if n.value and guards==0:
    tiny=C.create_string_buffer(b'\xa5'*8);unchanged=S(123);assert not read(tiny,8,C.byref(unchanged)) and unchanged.value==123 and tiny.raw==b'\xa5'*8+b'\0';guards+=1
    assert not read(raw,n.value,None);guards+=1
   consume();empty=S(123);assert read(None,0,C.byref(empty)) and empty.value==0
   if tick[2] in targets or index==599:
    frame=capture(r,64*1024*1024);assert frame;fi=(Q*8)();assert finfo(frame,fi)
    try:
     for owner in range(fi[4]):
      oi=(Q*5)();assert oinfo(frame,owner,oi);owners.add(tuple(oi));p=P();length=S();assert component(frame,owner,2,C.byref(p),C.byref(length));history=C.string_at(p,length.value);header=struct.unpack_from('<8Q',history);assert header[0]==0x3148524e and header[3]==oi[0];ha=64;assets={}
      while ha<len(history):
       tag,size=struct.unpack_from('<2Q',history,ha)
       if tag==2:
        ordinal,refresh,asset=struct.unpack_from('<3Q',history,ha+16);assert mapping[(oi[0],ordinal)]==(refresh,history[ha+96:ha+164],assets[asset]);checks+=1
        if refresh<oi[2]:old_checks+=1;max_age=max(max_age,oi[3]-refresh)
       else:
        assert tag==1;asset=struct.unpack_from('<Q',history,ha+16)[0];assets[asset]=hashlib.sha256(history[ha+64:ha+size]).hexdigest()
       ha+=size
      assert ha==len(history)
    finally:ffree(frame)
   after=(Q*4)();assert timing(h,after) and tuple(after)==tuple(tick)
  assert records>100 and checks>100 and old_checks>0 and max_age>=45
  assert load(h,state_bytes,len(state_bytes));n=S(123);assert read(None,0,C.byref(n)) and n.value==0;guards+=1
finally:rclose(r);close(h)
assert retained_packet;written=U();assert replay(retained_packet,len(retained_packet),table,len(table),output,len(output),C.byref(written)) and output.raw[:written.value*68]==retained_packet[80:80+written.value*68]
cache_at=80+written.value*68
for block in range(12):cache_at+=4+struct.unpack_from('<I',retained_packet,cache_at)[0]
cache_size=struct.unpack_from('<I',retained_packet,cache_at)[0];cache=retained_packet[cache_at+4:];assert len(cache)==cache_size
cache_read=fn(d,'nf_pc_road_scratch_read',[P,S],P);cache_write=fn(d,'nf_pc_road_scratch_write',[P,P,S,P]);cache_free=fn(d,'nf_road_scratch_destroy',[P],None)
cache_handle=cache_read(cache,len(cache));assert cache_handle;copy=C.create_string_buffer(6148);n=S();assert cache_write(cache_handle,copy,len(copy),C.byref(n)) and copy.raw[:n.value]==cache;cache_free(cache_handle)
invalid=[cache[:-1],struct.pack('<I',513)+cache[4:]]
if len(cache)>=16:bad=bytearray(cache);struct.pack_into('<d',bad,8,float('nan'));invalid.append(bytes(bad))
if len(cache)>=28:bad=bytearray(cache);bad[16:20]=bad[4:8];invalid.append(bytes(bad))
for bad in invalid:assert not cache_read(bad,len(bad));guards+=1
(out/'source-reciprocals.bin').write_bytes(table.raw)
# All archive records survive process-local core/source queue destruction.
archive=(out/'road-source-recipes.nrrz').read_bytes();assert archive[:8]==b'NRRZ\x01\0\0\0';at=8;archived=0
while at<len(archive):
 length=struct.unpack_from('<I',archive,at)[0];at+=4;packet=zlib.decompress(archive[at:at+length]);at+=length;assert struct.unpack_from('<Q',packet,8)[0]==len(packet);archived+=1
assert at==len(archive) and archived==records
assert samples==443007 and digest.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e' and before=={str(p):sha(p) for p in [rom,state]}
report=dict(result='PASS_EXPLICIT_OWNED_ROAD_RECIPE_PROVENANCE',records=records,road_runs=runs,all_submitted_road_ordinals_covered=True,all_source_replays_byte_exact=True,history_event_checks=checks,historical_event_checks=old_checks,max_historical_age_original_refreshes=max_age,owners=len(owners),negative_and_reset_checks=guards,owned_replay_after_core_close=True,archive_records=archived,archive_sha256=sha(out/'road-source-recipes.nrrz'),reciprocal_table_sha256=sha(out/'source-reciprocals.bin'),original_frames=600,original_pixels_exact=True,audio_frames=samples,audio_sha256=digest.hexdigest(),original_timing_exact=True,no_extra_logic_steps=True,rom_state_sha256=before,core_sha256=sha(out/'capture-host.dll'),build_report_sha256=sha(out/'recipe-build-report.json'),script_sha256=sha(Path(__file__)),runtime_retention_lifetime_implemented=False,wall_association_implemented=False,live_integration=False,full_scene_60fps=False,scope='Explicit same-call road source-to-successful-history ordinal binding and owned offline recipe retention. Original source-run implementation reused for completeness, not an independent raster algorithm oracle. No fractional road projection yet.')
(out/'recipe-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

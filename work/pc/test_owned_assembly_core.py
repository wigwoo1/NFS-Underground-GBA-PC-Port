from pathlib import Path
import ctypes as C,os,json,hashlib,argparse,time
source=Path(__file__).resolve().parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-owned-assembly-core-tests';normal=base/'NFSUG-android-background-jni-native-local/capture-host.dll'
parser=argparse.ArgumentParser();parser.add_argument('--candidate-dir',type=Path,default=out);parser.add_argument('--baseline-core',type=Path,default=normal);options=parser.parse_args();out=options.candidate_dir;normal=options.baseline_core
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((out/'owned-core-build-report.json').read_text());assert receipt['core_sha256']==sha(out/'capture-host.dll') and receipt['baseline_core_sha256']==sha(normal)
for name,digest in receipt['staged_input_sha256'].items():assert sha(out/'source'/name)==digest
for key in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TEST_DIRECT_CAPTURE_RAM','NF_TEST_DIRECT_CAPTURE_ROM','NF_TEST_VERIFY_CAPTURE_RAM','NF_TEST_VERIFY_CAPTURE_ROM']:os.environ.pop(key,None)
with os.add_dll_directory('C:/msys64/mingw64/bin'):old=C.CDLL(str(normal));new=C.CDLL(str(out/'capture-host.dll'));adapter=C.CDLL(str(base/'NFSUG-pc-reader-tests/source-reader.dll'))
assert old._handle!=new._handle
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(d,n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
bind=fn(adapter,'nf_pc_source_api_bind_owner',[P]);rop=fn(adapter,'nf_pc_source_reader_open',[P,S],P);rcap=fn(adapter,'nf_pc_source_reader_capture',[P,S],P);rclose=fn(adapter,'nf_pc_source_reader_close',[P],None);free=fn(adapter,'nf_pc_source_frame_free',[P],None);meta=fn(adapter,'nf_pc_source_frame_info',[P,P]);component=fn(adapter,'nf_pc_source_frame_component',[P,U,U,C.POINTER(P),C.POINTER(S)])
def blob(frame,owner,kind):p=P();n=S();assert component(frame,owner,kind,C.byref(p),C.byref(n));return C.string_at(p,n.value)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=(root/'work/integration-0.state').read_bytes();before=sha(rom);cores=[]
for dll in [old,new]:
 functions={n:fn(dll,'nfa_core_'+n,args,r) for n,args,r in [('open',[C.c_char_p],P),('close',[P],None),('load_state',[P,P,S],I),('step',[P,U],I),('timing',[P,P],I),('pixels',[P],P),('read_audio',[P,P,S],S)]};h=functions['open'](os.fsencode(rom));assert h and functions['load_state'](h,state,len(state))
 for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(dll,'nfa_core_'+name,[P,I])(h,1)
 api=API(C.sizeof(API),h,*[C.cast(getattr(dll,'nfa_core_'+name),P).value for name in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));reader=rop(C.byref(api),64*1024*1024);assert reader;initial=(Q*4)();assert functions['timing'](h,initial);cores.append(dict(dll=dll,h=h,f=functions,api=api,reader=reader,initial=tuple(initial),audio=hashlib.sha256(),samples=0))
frames=owners=components=compared_bytes=0;held=[];pcm=(C.c_int16*8192)();bad_requests=0;step_costs=[[],[]];capture_costs=[[],[]]
try:
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   expected=oracle.read(153600);packets=[];ticks=[]
   for core_index,item in enumerate(cores):
    f=item['f'];h=item['h'];began=time.perf_counter();assert f['step'](h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1;step_costs[core_index].append((time.perf_counter()-began)*1000);assert C.string_at(f['pixels'](h),153600)==expected;tick=(Q*4)();assert f['timing'](h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==item['initial'][2]+index+1 and tick[3]==index+1;ticks.append(tuple(tick))
    while True:
     n=f['read_audio'](h,pcm,4096)
     if not n:break
     item['samples']+=n;item['audio'].update(C.string_at(pcm,n*4))
    began=time.perf_counter();packets.append(rcap(item['reader'],64*1024*1024));capture_costs[core_index].append((time.perf_counter()-began)*1000)
   assert bool(packets[0])==bool(packets[1]),('Capture availability changed',index)
   if not packets[0]:continue
   a=(Q*8)();b=(Q*8)();assert meta(packets[0],a) and meta(packets[1],b) and tuple(a)==tuple(b);frames+=1;owners+=a[4]
   for owner in range(a[4]):
    for kind in range(5):
     if owner and kind==0:continue
     first=blob(packets[0],owner,kind);second=blob(packets[1],owner,kind);assert first==second,('Source bytes differ',index,owner,kind);compared_bytes+=len(first);components+=1
   if frames==1:
    for item in cores:
     for name in ['capture_bundle','capture_sky_scene','capture_background_scene']:
      read=fn(item['dll'],'nfa_core_'+name,[P,Q,U,P,S],S);assert read(item['h'],a[0],a[1],None,0)>8
      for ep,refresh in [(a[0],a[1]),(a[0]+1,a[1]),(a[0],0xffffffff)]:
       sentinel=C.create_string_buffer(b'unchanged');assert read(item['h'],ep,refresh,sentinel,8)==0 and sentinel.raw.startswith(b'unchanged');bad_requests+=1
    held=[(packets[0],blob(packets[0],0,0)),(packets[1],blob(packets[1],0,0))]
   else:
    for packet in packets:free(packet)
   for item,tick in zip(cores,ticks):
    after=(Q*4)();assert item['f']['timing'](item['h'],after) and tuple(after)==tick
  for item in cores:
   dll=item['dll'];h=item['h'];assert item['f']['load_state'](h,state,len(state)) and not rcap(item['reader'],64*1024*1024);assert fn(dll,'nfa_core_capture_enable',[P,I])(h,0) and not rcap(item['reader'],64*1024*1024)
   for name in ['capture_bundle','capture_sky_scene','capture_background_scene']:
    read=fn(dll,'nfa_core_'+name,[P,Q,U,P,S],S);sentinel=C.create_string_buffer(b'unchanged');assert read(h,1,0,sentinel,8)==0 and sentinel.raw.startswith(b'unchanged');bad_requests+=1
finally:
 for item in cores:rclose(item['reader']);item['f']['close'](item['h'])
for frame,expected in held:assert blob(frame,0,0)==expected;free(frame)
assert frames==590 and all(item['samples']==443007 and item['audio'].hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e' for item in cores);assert sha(rom)==before
r=dict(result='PASS_OWNED_ASSEMBLY_CORE_PARITY',original_frames=600,complete_source_frames=frames,owners=owners,source_components=components,source_bytes_compared=compared_bytes,all_original_pixels_exact=True,all_complete_source_bytes_exact=True,audio_frames=443007,audio_sha256=cores[0]['audio'].hexdigest(),clock_hz=16777216,cycles_per_step=280896,no_capture_logic_steps=True,reset_disable_stale_requests_rejected=True,invalid_requests_untouched=bad_requests,held_frames_outlive_both_cores=True,baseline_core_sha256=sha(normal),core_sha256=sha(out/'capture-host.dll'),build_report_sha256=sha(out/'owned-core-build-report.json'),test_source_sha256=sha(Path(__file__)),rom_sha256=before,game_logic_changed=False)
r['diagnostic_costs']={name:{phase:dict(count=len(values),mean_ms=sum(values)/len(values),max_ms=max(values)) for phase,values in [('core_step',step_costs[i]),('source_capture',capture_costs[i])]} for i,name in enumerate(['baseline','candidate'])}
r['timing_limit']='Paired offscreen replay, baseline first each step; diagnostic costs exclude live rendering and do not prove real-time pacing.'
(out/'owned-core-test-report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))

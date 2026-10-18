from pathlib import Path
import os,ctypes as C,hashlib,json,time
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-core-hook-profile-tests';receipt=json.loads((out/'hook-build-report.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert receipt['core_sha256']==sha(out/'capture-host.dll')
for key in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS']:os.environ.pop(key,None)
with os.add_dll_directory('C:/msys64/mingw64/bin'):dll=C.CDLL(str(out/'capture-host.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;I=C.c_int;U=C.c_uint
def fn(n,args,r=I):f=getattr(dll,n);f.argtypes=args;f.restype=r;return f
op=fn('nfa_core_open',[C.c_char_p],P);close=fn('nfa_core_close',[P],None);load=fn('nfa_core_load_state',[P,P,S]);step=fn('nfa_core_step',[P,U]);timing=fn('nfa_core_timing',[P,P]);pixels=fn('nfa_core_pixels',[P],P);audio=fn('nfa_core_read_audio',[P,P,S],S);stats=fn('nf_pc_core_hook_profile',[P],None);reset=fn('nf_pc_core_hook_reset',[],None)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=(root/'work/integration-0.state').read_bytes();h=op(os.fsencode(rom));assert h;pcm=(C.c_int16*8192)();digest=hashlib.sha256();samples=0;costs=[];per_frame=[]
try:
 assert load(h,state,len(state))
 for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn('nfa_core_'+name,[P,I])(h,1)
 enable_details=fn('nf_capture_profile_enable',[U],None);details=fn('nf_capture_profile_read',[P]);events=fn('nf_capture_event_profile_read',[U,P]);enable_details(1)
 detail_rows=[];previous_detail=(Q*6)();assert details(previous_detail)
 reset();initial=(Q*4)();assert timing(h,initial);previous=(Q*10)();stats(previous)
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   t=time.perf_counter();assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1;cost=(time.perf_counter()-t)*1000;costs.append(cost);assert C.string_at(pixels(h),153600)==oracle.read(153600);tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+index+1 and tick[3]==index+1
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    samples+=n;digest.update(C.string_at(pcm,n*4))
   cumulative_detail=(Q*6)();assert details(cumulative_detail)
   detail=[cumulative_detail[i]-previous_detail[i] for i in range(6)];previous_detail=cumulative_detail;detail_rows.append(detail)
   current=(Q*10)();stats(current);per_frame.append(dict(frame=index+1,step_ms=cost,hook_ms={name:(current[1+i*3+1]-previous[1+i*3+1])*1000/current[0] for i,name in enumerate(receipt['phases'])},selective_ms={name:detail[i*2]/1e6 for i,name in enumerate(['visibility_events','layer_scanlines','original_scanlines'])}));previous=current
 final=(Q*10)();stats(final);event_rows=[]
 for i in range(64):
  event=(Q*3)()
  if events(i,event):event_rows.append(dict(pc=f'0x{event[0]:08x}',calls=event[1],total_ms=event[2]/1e6))
finally:close(h)
assert samples==443007 and digest.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e';phases={}
for i,name in enumerate(receipt['phases']):count,total,maximum=final[1+i*3:1+i*3+3];phases[name]=dict(count=count,total_ms=total*1000/final[0],mean_per_logic_frame_ms=total*1000/final[0]/600,max_call_ms=maximum*1000/final[0])
r=dict(result='PASS_CORE_HOOK_PROFILE_ORIGINAL_PIXELS_PCM_EXACT',frames=600,step_mean_ms=sum(costs)/600,step_max_ms=max(costs),audio_frames=samples,audio_sha256=digest.hexdigest(),clock_hz=16777216,cycles_per_step=280896,phases=phases,slowest_frames=sorted(per_frame,key=lambda row:row['step_ms'],reverse=True)[:20],core_sha256=sha(out/'capture-host.dll'),build_report_sha256=sha(out/'hook-build-report.json'),profile_source_sha256=sha(Path(__file__)),profiling_only=True,shipping_packages_modified=False,hook_times_may_be_nested=True,full_scene_60fps=False)
r['selective_phases']={name:dict(total_ms=sum(row[i*2] for row in detail_rows)/1e6,mean_per_logic_frame_ms=sum(row[i*2] for row in detail_rows)/1e6/600,calls=sum(row[i*2+1] for row in detail_rows)) for i,name in enumerate(['visibility_events','layer_scanlines','original_scanlines'])}
r['visibility_events']=sorted(event_rows,key=lambda row:row['total_ms'],reverse=True)
assert r['selective_phases']['layer_scanlines']['calls']==96000
assert r['selective_phases']['original_scanlines']['calls']==96000
assert r['selective_phases']['visibility_events']['calls']==sum(row['calls'] for row in event_rows)
assert abs(r['selective_phases']['visibility_events']['total_ms']-sum(row['total_ms'] for row in event_rows))<0.001
for row in per_frame:
 for cost in row['selective_ms'].values():assert 0<=cost<=row['step_ms']+0.01
r['per_frame']=per_frame
r['counter_accounting']='Capture counters are cumulative in nfa_core_step; per-frame values are differences, not sums of cumulative samples. Counts/event totals and phase bounds checked.'
r['rom_sha256']=sha(rom);r['state_sha256']=sha(root/'work/integration-0.state')
assert r['rom_sha256']=='53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593'
assert r['state_sha256']=='49e85564032a383626709b183f37aff34601c6e97cabdfcb17c117f72d996104'
r['instrumentation_limit']='Selective event and scanline counters add clock overhead; nested phases must not be summed. No per-instruction ARM timers enabled.'
(out/'hook-profile-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['slowest_frames','per_frame','visibility_events']},indent=2))

from pathlib import Path
import os,ctypes as C,json,hashlib,time,statistics
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-recipe-wall-share-tests'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for key in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TEST_DIRECT_CAPTURE_ROM']:os.environ.pop(key,None)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(p):sha(p) for p in [rom,state]};data=state.read_bytes();rows=[]
for name,folder in [('baseline',base/'NFSUG-pc-direct-ram-core-tests'),('reference',base/'NFSUG-pc-recipe-alias-tests'),('optimized',out)]:
 dll=folder/'capture-host.dll'
 with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(dll))
 P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;I=C.c_int
 def fn(n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
 op=fn('nfa_core_open',[C.c_char_p],P);close=fn('nfa_core_close',[P],None);load=fn('nfa_core_load_state',[P,P,S]);step=fn('nfa_core_step',[P,I]);pixels=fn('nfa_core_pixels',[P],P);audio=fn('nfa_core_read_audio',[P,P,S],S);timing=fn('nfa_core_timing',[P,P]);h=op(os.fsencode(rom));assert h and load(h,data,len(data))
 for n in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn('nfa_core_'+n,[P,I])(h,1)
 start=(Q*4)();assert timing(h,start);pcm=(C.c_int16*8192)();digest=hashlib.sha256();samples=0;cost=[]
 try:
  with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
   for i in range(600):
    began=time.perf_counter();assert step(h,1|(16 if 60<=i<120 else 0)|(32 if 480<=i<540 else 0))==1;cost.append((time.perf_counter()-began)*1000);assert C.string_at(pixels(h),153600)==oracle.read(153600);tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==start[2]+i+1 and tick[3]==i+1
    while True:
     n=audio(h,pcm,4096)
     if not n:break
     samples+=n;digest.update(C.string_at(pcm,n*4))
  row=dict(name=name,core_sha256=sha(dll),mean_ms=statistics.mean(cost),median_ms=statistics.median(cost),p95_ms=sorted(cost)[569],max_ms=max(cost),over_original_step_budget=sum(c>280896/16777216*1000 for c in cost),step_ms=cost,original_pixels_exact=True,audio_frames=samples,audio_sha256=digest.hexdigest(),original_timing_exact=True)
  if name!='baseline':
   st=(Q*11)();assert fn('nf_pc_live_recipe_info',[P])(st) and not st[1] and st[2:5]==[47214,27027,148];row['recipe_stats']=list(st)
  if name!='baseline':
   a=(Q*7)();b=(Q*4)();assert fn('nf_pc_recipe_profile_read',[P])(a) and fn('nf_pc_recipe_hash_profile',[P])(b);row['stages']={n:dict(calls=a[j],total_ms=a[j+3]/a[6]*1000,mean_per_game_step_ms=a[j+3]/a[6]*1000/600) for j,n in enumerate(['road','wall','owner_close'])};row['hash']=dict(calls=b[0],bytes=b[1],total_ms=b[2]/b[3]*1000,mean_per_game_step_ms=b[2]/b[3]*1000/600);row['hash_ms_nested_in_capture_stages']=True
  assert samples==443007 and digest.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e';rows.append(row);print(json.dumps({k:v for k,v in row.items() if k!='step_ms'}),flush=True)
 finally:close(h)
assert before=={str(p):sha(p) for p in [rom,state]}
r=dict(result='PASS_SAME_SESSION_WALL_SOURCE_SHARING_COMPARISON',rows=rows,rom_state_sha256=before,script_sha256=sha(Path(__file__)),profile_build_report_sha256=sha(out/'live-recipe-build-report.json'),baseline_vs_reference_mean_delta_ms=rows[1]['mean_ms']-rows[0]['mean_ms'],scope='Sequential unpaced600-step tests on one machine/session. Profiler adds counters/QPC overhead; hash timings are nested inside capture-stage timings. No presentation/render workload or60-fps gameplay verification.',full_scene_60fps=False)
r['reference_to_optimized_mean_reduction_ms']=rows[1]['mean_ms']-rows[2]['mean_ms'];r['profile_to_optimized_hash_byte_reduction']=rows[1]['hash']['bytes']-rows[2]['hash']['bytes']
(out/'capture-cost-profile.json').write_text(json.dumps(r,indent=2))

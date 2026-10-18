from pathlib import Path
import os,json,hashlib,shutil,subprocess
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');baseline=base/'NFSUG-pc-live-recipe-tests';out=base/'NFSUG-pc-recipe-profile-tests';source=out/'source';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((baseline/'live-recipe-build-report.json').read_text());assert sha(baseline/'capture-host.dll')==r['core_sha256']
for name,h in r['source_sha256'].items():assert sha(baseline/'source'/name)==h
shutil.copytree(baseline/'source',source,dirs_exist_ok=True)
def replace(t,a,b):assert t.count(a)==1,a;return t.replace(a,b,1)
p=source/'live_recipe_capture.inc';text=p.read_text();text='static uint64_t pc_profile_calls[3],pc_profile_ticks[3];\nextern void nf_pc_recipe_hash_reset(void);\n'+text
text=replace(text,'void nf_pc_road_recipe_reset(void){','void nf_pc_road_recipe_reset(void){memset(pc_profile_calls,0,sizeof(pc_profile_calls));memset(pc_profile_ticks,0,sizeof(pc_profile_ticks));nf_pc_recipe_hash_reset();')
for a,b in [('void nf_pc_road_recipe_capture(', 'static void pc_profile_road('),('void nf_pc_wall_lineage_event(', 'static void pc_profile_wall('),('void nf_pc_live_recipe_owner_close(', 'static void pc_profile_close(')]:text=replace(text,a,b)
text=replace(text,'nf_recipe_snapshot_free(pc_recipe_owner[0].data);pc_recipe_owner[0]=pc_recipe_owner[1];','pc_recipe_usage();nf_recipe_snapshot_free(pc_recipe_owner[0].data);pc_recipe_owner[0]=pc_recipe_owner[1];')
text+='''
static void pc_profile_end(unsigned stage,LARGE_INTEGER start){LARGE_INTEGER end;QueryPerformanceCounter(&end);pc_profile_calls[stage]++;pc_profile_ticks[stage]+=(uint64_t)(end.QuadPart-start.QuadPart);}
void nf_pc_road_recipe_capture(uint64_t last,unsigned refresh,unsigned state,unsigned source,unsigned descriptor,const uint32_t*commands,unsigned count,unsigned shift,const uint8_t*const*blocks,const unsigned*sizes,const void*scratch,unsigned scratch_bytes){LARGE_INTEGER start;QueryPerformanceCounter(&start);pc_profile_road(last,refresh,state,source,descriptor,commands,count,shift,blocks,sizes,scratch,scratch_bytes);pc_profile_end(0,start);}
void nf_pc_wall_lineage_event(uint64_t epoch,unsigned refresh,uint64_t ordinal,const NFSceneEvent*e){LARGE_INTEGER start;QueryPerformanceCounter(&start);pc_profile_wall(epoch,refresh,ordinal,e);pc_profile_end(1,start);}
void nf_pc_live_recipe_owner_close(uint64_t epoch,const NFScenePacket*packet,const void*road,size_t rn,const void*wall,size_t wn){LARGE_INTEGER start;QueryPerformanceCounter(&start);pc_profile_close(epoch,packet,road,rn,wall,wn);pc_profile_end(2,start);}
__declspec(dllexport) int nf_pc_recipe_profile_read(uint64_t out[7]){if(!out||pc_recipe_thread!=GetCurrentThreadId())return 0;LARGE_INTEGER f;QueryPerformanceFrequency(&f);memcpy(out,pc_profile_calls,24);memcpy(out+3,pc_profile_ticks,24);out[6]=(uint64_t)f.QuadPart;return 1;}
''';p.write_text(text)
p=source/'recipe_store.c';text=p.read_text();text=replace(text,'static uint64_t hash(const void*data,size_t n){','static uint64_t pc_raw_hash(const void*data,size_t n){')
needle='static unsigned bucket(unsigned kind,uint64_t ordinal)'
extra='''static uint64_t pc_hash_calls,pc_hash_bytes,pc_hash_ticks;
__declspec(dllexport) void nf_pc_recipe_hash_reset(void){pc_hash_calls=pc_hash_bytes=pc_hash_ticks=0;}
static uint64_t hash(const void*data,size_t n){LARGE_INTEGER a,b;QueryPerformanceCounter(&a);uint64_t h=pc_raw_hash(data,n);QueryPerformanceCounter(&b);pc_hash_calls++;pc_hash_bytes+=n;pc_hash_ticks+=(uint64_t)(b.QuadPart-a.QuadPart);return h;}
__declspec(dllexport) int nf_pc_recipe_hash_profile(uint64_t out[4]){if(!out)return 0;LARGE_INTEGER f;QueryPerformanceFrequency(&f);out[0]=pc_hash_calls;out[1]=pc_hash_bytes;out[2]=pc_hash_ticks;out[3]=(uint64_t)f.QuadPart;return 1;}
'''
text=replace(text,needle,extra+needle);p.write_text(text)
args=[a.replace(str(baseline/'source'),str(source)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for a in r['command']];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(args,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
report=dict(result='BUILT_DIAGNOSTIC_RECIPE_CAPTURE_PROFILE',core_sha256=sha(out/'capture-host.dll'),baseline_build_report_sha256=sha(baseline/'live-recipe-build-report.json'),source_sha256={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()},script_sha256=sha(Path(__file__)),command=args,shipping_packages_changed=False)
(out/'live-recipe-build-report.json').write_text(json.dumps(report,indent=2));print(report['result'],report['core_sha256'])

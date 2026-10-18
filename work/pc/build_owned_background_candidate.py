# Isolated background ownership transfer. Release provider stays loaded through frame destruction.
from pathlib import Path
import hashlib,json,os,shutil,subprocess
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace')
out=base/'NFSUG-pc-owned-background-tests';out.mkdir(exist_ok=True);reference=base/'NFSUG-pc-cadence-audit-tests';baseline=base/'NFSUG-pc-owned-assembly-core-tests'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((baseline/'owned-core-build-report.json').read_text());assert sha(baseline/'capture-host.dll')==r['core_sha256']
for n,h in r['staged_input_sha256'].items():assert sha(baseline/'source'/n)==h,n
core=out/'core-source';shutil.copytree(baseline/'source',core,dirs_exist_ok=True)
stage=out/'host-source';pc=stage/'work/pc';pc.mkdir(parents=True,exist_ok=True)
for pattern in ('*.c','*.h','*.inc'):
 for p in here.glob(pattern):shutil.copy2(p,pc/p.name)
(pc.parent/'camera').mkdir(exist_ok=True);(stage/'outputs/nfsug-research').mkdir(parents=True,exist_ok=True)
for n in ('obj_tile.c','obj_tile.h'):shutil.copy2(root/'work/camera'/n,pc.parent/'camera'/n)
shutil.copy2(root/'outputs/nfsug-research/controller.h',stage/'outputs/nfsug-research/controller.h')
def edit(p,changes):
 s=p.read_text()
 for a,b in changes:
  assert s.count(a)==1,(p.name,a);s=s.replace(a,b,1)
 p.write_text(s)
with (core/'observer.c').open('a') as f:f.write('''
size_t nf_android_observer_background_take(uint64_t epoch,unsigned refresh,void**owned){
 if(!owned)return 0;*owned=NULL;uint8_t*packet=NULL;
 size_t bytes=android_background_scene_owned(epoch,refresh,&packet);
 if(!bytes)return 0;*owned=packet;return bytes;
}
''')
with (core/'nfsug_android_core.c').open('a') as f:f.write('''
extern size_t nf_android_observer_background_take(uint64_t,unsigned,void**);
NFA_API size_t nfa_core_capture_background_take(NFAAndroidCore*s,uint64_t epoch,unsigned refresh,void**owned){
 if(!valid(s)||!s->capture||!owned)return 0;return nf_android_observer_background_take(epoch,refresh,owned);
}
NFA_API void nfa_core_capture_owned_free(void*owned){free(owned);}
''')
edit(pc/'source_frame.h',[
 ('typedef struct NFPCSourceFrame NFPCSourceFrame;','''typedef struct NFPCSourceFrame NFPCSourceFrame;
/* Transfers exactly reported allocated bytes. Any non-NULL failure allocation
   is also released. The release provider DLL must outlive every frame. */
typedef size_t (*NFPCBackgroundTake)(void*,uint64_t,unsigned,void**);
typedef void (*NFPCOwnedRelease)(void*);
NFPC_API NFPCSourceFrame* nf_pc_source_frame_capture_take_background(const NFPCSourceAPI*,size_t,NFPCBackgroundTake,NFPCOwnedRelease);''')])
edit(pc/'source_frame.c',[
 ('size_t used,limit;Blob background;','size_t used,limit;NFPCOwnedRelease background_release;Blob background;'),
 ('NFPCSourceFrame* nf_pc_source_frame_capture(const NFPCSourceAPI*a,size_t maximum){','static NFPCSourceFrame* capture(const NFPCSourceAPI*a,size_t maximum,NFPCBackgroundTake take,NFPCOwnedRelease release){'),
 ('size_t n=a->background(a->core,f->epoch,(unsigned)f->refresh,NULL,0);if(!allocate(f,&f->background,n)||a->background(a->core,f->epoch,(unsigned)f->refresh,f->background.p,n)!=n)goto fail;','''size_t n;
 if(take){void*owned=NULL;n=take(a->core,f->epoch,(unsigned)f->refresh,&owned);
  if(!n||!owned||n>f->limit-f->used){if(owned)release(owned);goto fail;}
  f->background.p=owned;f->background.n=n;f->background_release=release;f->used+=n;
 }else{n=a->background(a->core,f->epoch,(unsigned)f->refresh,NULL,0);if(!allocate(f,&f->background,n)||a->background(a->core,f->epoch,(unsigned)f->refresh,f->background.p,n)!=n)goto fail;}'''),
 ('void nf_pc_source_frame_free(NFPCSourceFrame*f){if(!f)return;free(f->background.p);','''NFPCSourceFrame* nf_pc_source_frame_capture(const NFPCSourceAPI*a,size_t maximum){return capture(a,maximum,NULL,NULL);}
NFPCSourceFrame* nf_pc_source_frame_capture_take_background(const NFPCSourceAPI*a,size_t maximum,NFPCBackgroundTake take,NFPCOwnedRelease release){if(!take||!release)return NULL;return capture(a,maximum,take,release);}
void nf_pc_source_frame_free(NFPCSourceFrame*f){if(!f)return;if(f->background_release)f->background_release(f->background.p);else free(f->background.p);''')])
edit(pc/'source_reader.h',[
 ('NFPC_API NFPCSourceFrame* nf_pc_source_reader_capture','''/* Opt-in transfer; release provider DLL must outlive every frame. */
NFPC_API NFPCSourceReader* nf_pc_source_reader_open_owned_background(const NFPCSourceAPI*,size_t,NFPCBackgroundTake,NFPCOwnedRelease);
/* attempts, successful transfers, bytes. */
NFPC_API int nf_pc_source_reader_owned_background_info(const NFPCSourceReader*,uint64_t out[3]);
NFPC_API NFPCSourceFrame* nf_pc_source_reader_capture''')])
edit(pc/'source_reader.c',[
 ('size_t pending;};','size_t pending;NFPCBackgroundTake take;NFPCOwnedRelease release;uint64_t owned_stats[3];};'),
 ('NFPCSourceFrame* nf_pc_source_reader_capture','''static size_t take_background(void*context,uint64_t epoch,unsigned refresh,void**owned){
 NFPCSourceReader*r=context;if(!owns(r))return 0;
 size_t n=r->take(r->raw.core,epoch,refresh,owned);r->stats[1]++;r->owned_stats[0]++;
 if(!n||!*owned||n>r->bytes){r->stats[3]++;uint64_t failure[6]={0,epoch,refresh,0,0,n};memcpy(r->failure,failure,sizeof(failure));return 0;}
 if(n>r->stats[5])r->stats[5]=n;
 r->owned_stats[1]++;r->owned_stats[2]+=n;return n;
}
NFPCSourceReader* nf_pc_source_reader_open_owned_background(const NFPCSourceAPI*a,size_t bytes,NFPCBackgroundTake take,NFPCOwnedRelease release){
 if(!take||!release)return NULL;
 NFPCSourceReader*r=nf_pc_source_reader_open(a,bytes);if(r){r->take=take;r->release=release;}return r;
}
int nf_pc_source_reader_owned_background_info(const NFPCSourceReader*r,uint64_t out[3]){if(!owns(r)||!out)return 0;memcpy(out,r->owned_stats,sizeof(r->owned_stats));return 1;}
NFPCSourceFrame* nf_pc_source_reader_capture'''),
 ('NFPCSourceFrame*f=nf_pc_source_frame_capture(&r->wrapped,maximum);','NFPCSourceFrame*f=r->take?nf_pc_source_frame_capture_take_background(&r->wrapped,maximum,take_background,r->release):nf_pc_source_frame_capture(&r->wrapped,maximum);')])
edit(pc/'live_host.c',[
 ('static Core core;','static NFPCBackgroundTake background_take;static NFPCOwnedRelease background_release;static int owned_background;static uint64_t background_stats[3];\nstatic Core core;'),
 ('else if(!strcmp(argv[i],"--original"))','else if(!strcmp(argv[i],"--owned-background"))owned_background=1;else if(!strcmp(argv[i],"--original"))'),
 ('if(!rom||!controller_check()','if((owned_background&&uncached_capture)||!rom||!controller_check()'),
 ('stage="ROM open";','''if(owned_background){stage="owned background ABI";if(!symbol(dll,"nfa_core_capture_background_take",&background_take,sizeof(background_take))||!symbol(dll,"nfa_core_capture_owned_free",&background_release,sizeof(background_release)))goto fail;}
 stage="ROM open";'''),
 ('if(!uncached_capture)reader=nf_pc_source_reader_open(&api,64u*1024*1024);reader_enabled=reader!=NULL;','if(!uncached_capture)reader=owned_background?nf_pc_source_reader_open_owned_background(&api,64u*1024*1024,background_take,background_release):nf_pc_source_reader_open(&api,64u*1024*1024);reader_enabled=reader!=NULL;if(owned_background&&!reader)goto fail;'),
 ('if(reader){nf_pc_source_reader_info(reader,reader_stats);','if(reader){nf_pc_source_reader_owned_background_info(reader,background_stats);nf_pc_source_reader_info(reader,reader_stats);'),
 ('fputs("}\\n",f);fclose(f);','fprintf(f,",\\"owned_background_capture\\":%s,\\"background_transfer_attempts\\":%llu,\\"background_transfers\\":%llu,\\"background_transferred_bytes\\":%llu",owned_background&&reader_enabled?"true":"false",(unsigned long long)background_stats[0],(unsigned long long)background_stats[1],(unsigned long long)background_stats[2]);fputs("}\\n",f);fclose(f);')])
# Count allocation/release across main and renderer threads in the live candidate.
edit(core/'nfsug_android_core.c',[
 ('extern size_t nf_android_observer_background_take(uint64_t,unsigned,void**);','static uint64_t nfa_owned_background_counts[3];\nextern size_t nf_android_observer_background_take(uint64_t,unsigned,void**);'),
 ('if(!valid(s)||!s->capture||!owned)return 0;return nf_android_observer_background_take(epoch,refresh,owned);','''if(!valid(s)||!s->capture||!owned)return 0;
 size_t bytes=nf_android_observer_background_take(epoch,refresh,owned);
 if(bytes&&*owned){__atomic_fetch_add(nfa_owned_background_counts,1,__ATOMIC_RELAXED);__atomic_fetch_add(nfa_owned_background_counts+2,bytes,__ATOMIC_RELAXED);}return bytes;'''),
 ('NFA_API void nfa_core_capture_owned_free(void*owned){free(owned);}','''NFA_API void nfa_core_capture_owned_free(void*owned){if(owned){__atomic_fetch_add(nfa_owned_background_counts+1,1,__ATOMIC_RELAXED);free(owned);}}
NFA_API int nfa_core_capture_owned_background_info(uint64_t out[3]){if(!out)return 0;for(unsigned i=0;i<3;i++)out[i]=__atomic_load_n(nfa_owned_background_counts+i,__ATOMIC_RELAXED);return 1;}''')])
edit(pc/'live_host.c',[
 ('static NFPCBackgroundTake background_take;', 'static int(*background_lifetime_info)(uint64_t*);static uint64_t background_lifetime_stats[3];\nstatic NFPCBackgroundTake background_take;'),
 ('!symbol(dll,"nfa_core_capture_owned_free",&background_release,sizeof(background_release))', '!symbol(dll,"nfa_core_capture_owned_free",&background_release,sizeof(background_release))||!symbol(dll,"nfa_core_capture_owned_background_info",&background_lifetime_info,sizeof(background_lifetime_info))'),
 ('if(report_path){FILE*f=fopen(report_path,"w");', 'if(background_lifetime_info&&(!background_lifetime_info(background_lifetime_stats)||background_lifetime_stats[0]!=background_lifetime_stats[1]))result=2;\n if(report_path){FILE*f=fopen(report_path,"w");'),
 ('fputs("}\\n",f);fclose(f);', 'fprintf(f,",\\"background_allocations\\":%llu,\\"background_releases\\":%llu",(unsigned long long)background_lifetime_stats[0],(unsigned long long)background_lifetime_stats[1]);fputs("}\\n",f);fclose(f);')])
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
cmd=[a.replace(str(baseline/'source'),str(core)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for a in r['command']]
with (out/'core-build.log').open('w') as log:subprocess.run(cmd,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
b=json.loads((reference/'live-build-report.json').read_text());args=[]
for a in b['command']:
 if a.endswith('.c'):
  n=Path(a.replace('\\','/')).name;a=str(pc.parent/'camera'/n if n=='obj_tile.c' else pc/n)
 elif a==b['command'][b['command'].index('-o')+1]:a=str(out/'NFSUG-Source-Native-Preview.exe')
 args.append(a)
with (out/'host-build.log').open('w') as log:subprocess.run(args,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
for n in ('libgcc_s_seh-1.dll','libwinpthread-1.dll'):shutil.copy2(reference/n,out/n)
subprocess.run(['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-shared',str(pc/'source_frame.c'),str(pc/'source_reader.c'),'-o',str(out/'source-reader.dll')],env=env,check=True)
result=dict(result='BUILT_ISOLATED_OWNED_BACKGROUND_CANDIDATE',core_command=cmd,host_command=args,baseline_core_sha256=r['core_sha256'],baseline_exe_sha256=b['exe_sha256'],core_sha256=sha(out/'capture-host.dll'),exe_sha256=sha(out/'NFSUG-Source-Native-Preview.exe'),source_reader_dll_sha256=sha(out/'source-reader.dll'),staged_source_sha256={str(p.relative_to(stage)):sha(p) for p in stage.rglob('*') if p.is_file()},core_changed_sha256={p.name:sha(p) for p in [core/'observer.c',core/'nfsug_android_core.c']},production_sources_changed=False,full_scene_60fps=False)
(out/'owned-background-build-report.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('core_command','host_command','staged_source_sha256')},indent=2))

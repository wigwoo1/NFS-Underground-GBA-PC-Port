# Extends the verified isolated background transfer to owned source geometry.
from pathlib import Path
import hashlib,json,os,shutil,subprocess
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');prior=base/'NFSUG-pc-owned-background-tests';out=base/'NFSUG-pc-owned-sources-tests';out.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((prior/'owned-background-build-report.json').read_text());m=json.loads((prior/'ownership-milestone-report.json').read_text());assert m['core_sha256']==b['core_sha256']==sha(prior/'capture-host.dll') and m['exe_sha256']==b['exe_sha256']==sha(prior/'NFSUG-Source-Native-Preview.exe')
for n,h in b['staged_source_sha256'].items():assert sha(prior/'host-source'/n)==h,n
for n,h in b['core_changed_sha256'].items():assert sha(prior/'core-source'/n)==h,n
core=out/'core-source';stage=out/'host-source';shutil.copytree(prior/'core-source',core,dirs_exist_ok=True);shutil.copytree(prior/'host-source',stage,dirs_exist_ok=True);pc=stage/'work/pc'
def edit(p,changes):
 s=p.read_text()
 for a,z in changes:assert s.count(a)==1,(p.name,a);s=s.replace(a,z,1)
 p.write_text(s)
with (core/'observer.c').open('a') as f:f.write('''
size_t nf_android_observer_source_world_take(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void**owned){
 if(!owned)return 0;*owned=NULL;
 if(!c||!android_source_world||epoch!=nf_native_scene_epoch()||begin>end)return 0;
 void*packet=NULL;size_t bytes=0;unsigned stage;
 if(!nf_live_completed_native_multimodel_world_classified_owned(epoch,serial,begin,end,&packet,&bytes,&stage))return 0;
 if(!packet||!bytes){nf_scene_packet_free(packet);return 0;}*owned=packet;return bytes;
}
void nf_android_observer_source_world_free(void*packet){nf_scene_packet_free(packet);}
''')
with (core/'nfsug_android_core.c').open('a') as f:f.write('''
static uint64_t nfa_owned_geometry_counts[3];
extern size_t nf_android_observer_source_world_take(uint64_t,unsigned,unsigned,unsigned,void**);
extern void nf_android_observer_source_world_free(void*);
NFA_API size_t nfa_core_capture_source_world_take(NFAAndroidCore*s,uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void**owned){
 if(!valid(s)||!s->capture||!owned)return 0;
 size_t bytes=nf_android_observer_source_world_take(epoch,serial,begin,end,owned);
 if(bytes&&*owned){__atomic_fetch_add(nfa_owned_geometry_counts,1,__ATOMIC_RELAXED);__atomic_fetch_add(nfa_owned_geometry_counts+2,bytes,__ATOMIC_RELAXED);}return bytes;
}
NFA_API void nfa_core_capture_source_world_free(void*owned){if(owned){__atomic_fetch_add(nfa_owned_geometry_counts+1,1,__ATOMIC_RELAXED);nf_android_observer_source_world_free(owned);}}
NFA_API int nfa_core_capture_owned_geometry_info(uint64_t out[3]){if(!out)return 0;for(unsigned i=0;i<3;i++)out[i]=__atomic_load_n(nfa_owned_geometry_counts+i,__ATOMIC_RELAXED);return 1;}
''')
edit(pc/'source_frame.h',[
 ('typedef void (*NFPCOwnedRelease)(void*);','typedef void (*NFPCOwnedRelease)(void*);\ntypedef size_t (*NFPCOwnerTake)(void*,uint64_t,unsigned,unsigned,unsigned,void**);\nNFPC_API NFPCSourceFrame* nf_pc_source_frame_capture_take_sources(const NFPCSourceAPI*,size_t,NFPCBackgroundTake,NFPCOwnedRelease,NFPCOwnerTake,NFPCOwnedRelease);')])
edit(pc/'source_frame.c',[
 ('Blob part[4];} Owner;','Blob part[4];NFPCOwnedRelease geometry_release;} Owner;'),
 ('static NFPCSourceFrame* capture(const NFPCSourceAPI*a,size_t maximum,NFPCBackgroundTake take,NFPCOwnedRelease release){','''static int take_geometry(const NFPCSourceAPI*a,NFPCSourceFrame*f,Owner*o,NFPCOwnerTake take,NFPCOwnedRelease release){
 void*owned=NULL;size_t n=take(a->core,f->epoch,(unsigned)o->serial,(unsigned)o->begin,(unsigned)o->end,&owned);
 if(!n||!owned||n>f->limit-f->used){if(owned)release(owned);return 0;}
 o->part[0].p=owned;o->part[0].n=n;o->geometry_release=release;f->used+=n;return 1;
}
static NFPCSourceFrame* capture(const NFPCSourceAPI*a,size_t maximum,NFPCBackgroundTake take,NFPCOwnedRelease release,NFPCOwnerTake geometry_take,NFPCOwnedRelease geometry_release){'''),
 ('if(!copy_owner(a,f,o,a->geometry,0)||','if(!(geometry_take?take_geometry(a,f,o,geometry_take,geometry_release):copy_owner(a,f,o,a->geometry,0))||'),
 ('return capture(a,maximum,NULL,NULL);','return capture(a,maximum,NULL,NULL,NULL,NULL);'),
 ('return capture(a,maximum,take,release);','return capture(a,maximum,take,release,NULL,NULL);'),
 ('void nf_pc_source_frame_free(NFPCSourceFrame*f){','''NFPCSourceFrame* nf_pc_source_frame_capture_take_sources(const NFPCSourceAPI*a,size_t maximum,NFPCBackgroundTake take,NFPCOwnedRelease release,NFPCOwnerTake geometry_take,NFPCOwnedRelease geometry_release){if(!take||!release||!geometry_take||!geometry_release)return NULL;return capture(a,maximum,take,release,geometry_take,geometry_release);}
void nf_pc_source_frame_free(NFPCSourceFrame*f){'''),
 ('for(unsigned j=0;j<4;j++)free(f->owners[i].part[j].p);','for(unsigned j=0;j<4;j++){if(j==0&&f->owners[i].geometry_release)f->owners[i].geometry_release(f->owners[i].part[j].p);else free(f->owners[i].part[j].p);}')])
edit(pc/'source_reader.h',[
 ('/* attempts, successful transfers, bytes. */','''NFPC_API NFPCSourceReader* nf_pc_source_reader_open_owned_sources(const NFPCSourceAPI*,size_t,NFPCBackgroundTake,NFPCOwnedRelease,NFPCOwnerTake,NFPCOwnedRelease);
NFPC_API int nf_pc_source_reader_owned_geometry_info(const NFPCSourceReader*,uint64_t out[3]);
/* attempts, successful transfers, bytes. */''')])
edit(pc/'source_reader.c',[
 ('uint64_t owned_stats[3];};','uint64_t owned_stats[3];NFPCOwnerTake geometry_take;NFPCOwnedRelease geometry_release;uint64_t geometry_stats[3];};'),
 ('NFPCSourceFrame* nf_pc_source_reader_capture','''static size_t take_geometry(void*context,uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void**owned){
 NFPCSourceReader*r=context;if(!owns(r))return 0;
 size_t n=r->geometry_take(r->raw.core,epoch,serial,begin,end,owned);r->stats[1]++;r->geometry_stats[0]++;
 if(!n||!*owned||n>r->bytes){r->stats[3]++;uint64_t failure[6]={1,epoch,serial,begin,end,n};memcpy(r->failure,failure,sizeof(failure));return 0;}
 if(n>r->stats[5])r->stats[5]=n;
 r->geometry_stats[1]++;r->geometry_stats[2]+=n;return n;
}
NFPCSourceReader* nf_pc_source_reader_open_owned_sources(const NFPCSourceAPI*a,size_t bytes,NFPCBackgroundTake take,NFPCOwnedRelease release,NFPCOwnerTake geometry_take,NFPCOwnedRelease geometry_release){
 if(!geometry_take||!geometry_release)return NULL;
 NFPCSourceReader*r=nf_pc_source_reader_open_owned_background(a,bytes,take,release);if(r){r->geometry_take=geometry_take;r->geometry_release=geometry_release;}return r;
}
int nf_pc_source_reader_owned_geometry_info(const NFPCSourceReader*r,uint64_t out[3]){if(!owns(r)||!out)return 0;memcpy(out,r->geometry_stats,sizeof(r->geometry_stats));return 1;}
NFPCSourceFrame* nf_pc_source_reader_capture'''),
 ('NFPCSourceFrame*f=r->take?', 'NFPCSourceFrame*f=r->geometry_take?nf_pc_source_frame_capture_take_sources(&r->wrapped,maximum,take_background,r->release,take_geometry,r->geometry_release):r->take?')])
edit(pc/'live_host.c',[
 ('static Core core;','static int owned_geometry;static NFPCOwnerTake geometry_take;static NFPCOwnedRelease geometry_release;static int(*geometry_lifetime_info)(uint64_t*);static uint64_t geometry_stats[3],geometry_lifetime_stats[3];\nstatic Core core;'),
 ('else if(!strcmp(argv[i],"--owned-background"))','else if(!strcmp(argv[i],"--owned-geometry")){owned_geometry=1;owned_background=1;}else if(!strcmp(argv[i],"--owned-background"))'),
 ('stage="ROM open";','''if(owned_geometry){stage="owned geometry ABI";if(!symbol(dll,"nfa_core_capture_source_world_take",&geometry_take,sizeof(geometry_take))||!symbol(dll,"nfa_core_capture_source_world_free",&geometry_release,sizeof(geometry_release))||!symbol(dll,"nfa_core_capture_owned_geometry_info",&geometry_lifetime_info,sizeof(geometry_lifetime_info)))goto fail;}
 stage="ROM open";'''),
 ('reader=owned_background?', 'reader=owned_geometry?nf_pc_source_reader_open_owned_sources(&api,64u*1024*1024,background_take,background_release,geometry_take,geometry_release):owned_background?'),
 ('if(reader){nf_pc_source_reader_owned_background_info', 'if(reader){nf_pc_source_reader_owned_geometry_info(reader,geometry_stats);nf_pc_source_reader_owned_background_info'),
 ('if(report_path){FILE*f=fopen(report_path,"w");','if(geometry_lifetime_info&&(!geometry_lifetime_info(geometry_lifetime_stats)||geometry_lifetime_stats[0]!=geometry_lifetime_stats[1]))result=2;\n if(report_path){FILE*f=fopen(report_path,"w");'),
 ('fputs("}\\n",f);fclose(f);','fprintf(f,",\\"owned_geometry_capture\\":%s,\\"geometry_transfer_attempts\\":%llu,\\"geometry_transfers\\":%llu,\\"geometry_transferred_bytes\\":%llu,\\"geometry_allocations\\":%llu,\\"geometry_releases\\":%llu",owned_geometry&&reader_enabled?"true":"false",(unsigned long long)geometry_stats[0],(unsigned long long)geometry_stats[1],(unsigned long long)geometry_stats[2],(unsigned long long)geometry_lifetime_stats[0],(unsigned long long)geometry_lifetime_stats[1]);fputs("}\\n",f);fclose(f);')])
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
cmd=[a.replace(str(prior/'core-source'),str(core)).replace(str(prior/'capture-host.dll'),str(out/'capture-host.dll')) for a in b['core_command']]
with (out/'core-build.log').open('w') as log:subprocess.run(cmd,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
args=[a.replace(str(prior/'host-source'),str(stage)).replace(str(prior/'NFSUG-Source-Native-Preview.exe'),str(out/'NFSUG-Source-Native-Preview.exe')) for a in b['host_command']]
with (out/'host-build.log').open('w') as log:subprocess.run(args,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
for n in ('libgcc_s_seh-1.dll','libwinpthread-1.dll'):shutil.copy2(prior/n,out/n)
subprocess.run(['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-shared',str(pc/'source_frame.c'),str(pc/'source_reader.c'),'-o',str(out/'source-reader.dll')],env=env,check=True)
r=dict(result='BUILT_ISOLATED_OWNED_SOURCES_CANDIDATE',core_command=cmd,host_command=args,baseline_core_sha256=b['core_sha256'],baseline_exe_sha256=b['exe_sha256'],core_sha256=sha(out/'capture-host.dll'),exe_sha256=sha(out/'NFSUG-Source-Native-Preview.exe'),source_reader_dll_sha256=sha(out/'source-reader.dll'),staged_source_sha256={str(p.relative_to(stage)):sha(p) for p in stage.rglob('*') if p.is_file()},core_changed_sha256={n:sha(core/n) for n in ('observer.c','nfsug_android_core.c')},production_sources_changed=False,full_scene_60fps=False)
(out/'owned-sources-build-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ('core_command','host_command','staged_source_sha256')},indent=2))

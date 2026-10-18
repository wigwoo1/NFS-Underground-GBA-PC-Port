# Direct final-frame writes for already-closed cached road/wall/proof packets.
from pathlib import Path
import hashlib,json,os,shutil,subprocess
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');prior=base/'NFSUG-pc-owned-sources-tests';out=base/'NFSUG-pc-direct-cached-tests';out.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((prior/'owned-sources-build-report.json').read_text());m=json.loads((prior/'ownership-milestone-report.json').read_text());assert b['exe_sha256']==m['exe_sha256']==sha(prior/'NFSUG-Source-Native-Preview.exe') and b['core_sha256']==m['core_sha256']==sha(prior/'capture-host.dll')
for n,h in b['staged_source_sha256'].items():assert sha(prior/'host-source'/n)==h,n
stage=out/'host-source';shutil.copytree(prior/'host-source',stage,dirs_exist_ok=True);pc=stage/'work/pc'
def edit(path,changes):
 s=path.read_text()
 for a,z in changes:assert s.count(a)==1,(path.name,a);s=s.replace(a,z,1)
 path.write_text(s)
edit(pc/'source_reader.h',[
 ('/* attempts, successful transfers, bytes. */','''/* Core must guarantee stable cheap cached size/query writes on its owner thread.
   No scratch allocation; background/geometry still use immutable ownership transfer. */
NFPC_API NFPCSourceReader* nf_pc_source_reader_open_direct_sources(const NFPCSourceAPI*,size_t,NFPCBackgroundTake,NFPCOwnedRelease,NFPCOwnerTake,NFPCOwnedRelease);
/* cached size-query attempts, successful final writes, final write bytes. */
NFPC_API int nf_pc_source_reader_direct_cached_info(const NFPCSourceReader*,uint64_t out[3]);
/* attempts, successful transfers, bytes. */''')])
edit(pc/'source_reader.c',[
 ('uint64_t geometry_stats[3];};','uint64_t geometry_stats[3];int direct_cached;uint64_t direct_stats[3];};'),
 ('static size_t packet(','''static size_t cached_error(NFPCSourceReader*r,const uint64_t key[6],size_t n){
 r->stats[3]++;uint64_t failure[6]={key[0],key[1],key[2],key[3],key[4],n};memcpy(r->failure,failure,sizeof(failure));return 0;
}
static size_t cached_packet(NFPCSourceReader*r,unsigned kind,uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void*out,size_t capacity){
 if(kind<2||kind>4)return 0;
 uint64_t key[6]={kind,epoch,serial,begin,end,0};NFPCOwnerRead read=kind==2?r->raw.road:kind==3?r->raw.wall:r->raw.proof;
 if(!out){r->pending=0;r->direct_stats[0]++;r->stats[1]++;size_t n=read(r->raw.core,epoch,serial,begin,end,NULL,0);
  if(!n||n>r->bytes)return cached_error(r,key,n);
  r->pending=n;memcpy(r->key,key,sizeof(key));if(n>r->stats[5])r->stats[5]=n;return n;
 }
 if(!r->pending||capacity<r->pending||memcmp(key,r->key,sizeof(key)))return 0;
 size_t expected=r->pending;r->pending=0;size_t n=read(r->raw.core,epoch,serial,begin,end,out,capacity);
 if(n!=expected)return cached_error(r,key,n);
 r->direct_stats[1]++;r->direct_stats[2]+=n;return n;
}
static size_t packet('''),
 ('if(!owns(r))return 0;\n uint64_t key[6]={kind,epoch,serial,begin,end,0};','if(!owns(r))return 0;\n if(r->direct_cached)return cached_packet(r,kind,epoch,serial,begin,end,out,capacity);\n uint64_t key[6]={kind,epoch,serial,begin,end,0};'),
 ('NFPCSourceReader* nf_pc_source_reader_open(const NFPCSourceAPI*a,size_t bytes){','static NFPCSourceReader* reader_open(const NFPCSourceAPI*a,size_t bytes,int allocate_scratch){'),
 ('r->scratch=malloc(bytes);if(!r->scratch){free(r);return NULL;}','if(allocate_scratch){r->scratch=malloc(bytes);if(!r->scratch){free(r);return NULL;}}'),
 ('r->stats[0]=bytes;','r->stats[0]=allocate_scratch?bytes:0;'),
 ('static size_t take_background(', 'NFPCSourceReader* nf_pc_source_reader_open(const NFPCSourceAPI*a,size_t bytes){return reader_open(a,bytes,1);}\nstatic size_t take_background('),
 ('int nf_pc_source_reader_owned_geometry_info(','''NFPCSourceReader* nf_pc_source_reader_open_direct_sources(const NFPCSourceAPI*a,size_t bytes,NFPCBackgroundTake take,NFPCOwnedRelease release,NFPCOwnerTake geometry_take,NFPCOwnedRelease geometry_release){
 if(!take||!release||!geometry_take||!geometry_release)return NULL;
 NFPCSourceReader*r=reader_open(a,bytes,0);if(r){r->take=take;r->release=release;r->geometry_take=geometry_take;r->geometry_release=geometry_release;r->direct_cached=1;}return r;
}
int nf_pc_source_reader_direct_cached_info(const NFPCSourceReader*r,uint64_t out[3]){if(!owns(r)||!out)return 0;memcpy(out,r->direct_stats,sizeof(r->direct_stats));return 1;}
int nf_pc_source_reader_owned_geometry_info(''')])
edit(pc/'live_host.c',[
 ('static Core core;','static int direct_cached;static uint64_t direct_cached_stats[3];\nstatic Core core;'),
 ('else if(!strcmp(argv[i],"--owned-geometry"))','else if(!strcmp(argv[i],"--direct-cached")){direct_cached=1;owned_geometry=1;owned_background=1;}else if(!strcmp(argv[i],"--owned-geometry"))'),
 ('reader=owned_geometry?', 'reader=direct_cached?nf_pc_source_reader_open_direct_sources(&api,64u*1024*1024,background_take,background_release,geometry_take,geometry_release):owned_geometry?'),
 ('if(reader){nf_pc_source_reader_owned_geometry_info', 'if(reader){nf_pc_source_reader_direct_cached_info(reader,direct_cached_stats);nf_pc_source_reader_owned_geometry_info'),
 ('fputs("}\\n",f);fclose(f);','fprintf(f,",\\"direct_cached_capture\\":%s,\\"cached_size_queries\\":%llu,\\"cached_final_writes\\":%llu,\\"cached_final_write_bytes\\":%llu",direct_cached&&reader_enabled?"true":"false",(unsigned long long)direct_cached_stats[0],(unsigned long long)direct_cached_stats[1],(unsigned long long)direct_cached_stats[2]);fputs("}\\n",f);fclose(f);')])
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
args=[a.replace(str(prior/'host-source'),str(stage)).replace(str(prior/'NFSUG-Source-Native-Preview.exe'),str(out/'NFSUG-Source-Native-Preview.exe')) for a in b['host_command']]
with (out/'host-build.log').open('w') as log:subprocess.run(args,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
for n in ('capture-host.dll','libgcc_s_seh-1.dll','libwinpthread-1.dll'):shutil.copy2(prior/n,out/n)
shim=out/'reader-protocol-shim.c';shim.write_text('#include "'+(pc/'source_reader.c').as_posix()+'"\nNFPC_API size_t nf_pc_test_cached_packet(NFPCSourceReader*r,unsigned k,uint64_t e,unsigned s,unsigned b,unsigned end,void*out,size_t n){return packet(r,k,e,s,b,end,out,n);}\n')
subprocess.run(['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-shared',str(pc/'source_frame.c'),str(shim),'-o',str(out/'source-reader.dll')],env=env,check=True)
r=dict(result='BUILT_ISOLATED_DIRECT_CACHED_CANDIDATE',host_command=args,baseline_exe_sha256=b['exe_sha256'],baseline_core_sha256=b['core_sha256'],core_sha256=sha(out/'capture-host.dll'),exe_sha256=sha(out/'NFSUG-Source-Native-Preview.exe'),source_reader_dll_sha256=sha(out/'source-reader.dll'),staged_source_sha256={str(p.relative_to(stage)):sha(p) for p in stage.rglob('*') if p.is_file()},protocol_shim_sha256=sha(shim),core_unchanged=True,production_sources_changed=False,full_scene_60fps=False)
(out/'direct-cached-build-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ('host_command','staged_source_sha256')},indent=2))

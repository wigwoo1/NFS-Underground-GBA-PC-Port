from pathlib import Path
import os,json,hashlib,shutil,subprocess
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');baseline=base/'NFSUG-pc-direct-ram-live-tests';capture=base/'NFSUG-pc-recipe-runtime-tests';out=base/'NFSUG-pc-live-recipe-host-tests';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((baseline/'live-build-report.json').read_text());cr=json.loads((capture/'live-recipe-test-report.json').read_text());assert cr['result']=='PASS_DIRECT_CAPTURE_OWNED_ROAD_WALL_RECIPES' and sha(capture/'capture-host.dll')==cr['core_sha256']
for name,h in r['source_sha256'].items():assert sha(here/name)==h,name
text=(here/'live_host.c').read_text()
def replace(a,b):
 global text
 assert text.count(a)==1,a
 text=text.replace(a,b,1)
replace('#include "../../outputs/nfsug-research/controller.h"','#include "controller.h"')
replace('} Core;','''} Core;
typedef struct {void*(*acquire)(const uint64_t*);void(*release)(void*);int(*info)(const void*,uint64_t*);int(*writer)(const void*,size_t,uint64_t*);int(*block)(const void*,size_t,unsigned,const void**,size_t*);} RecipeAPI;
static RecipeAPI recipe;
typedef struct {NFPCSourceFrame*source;unsigned owners;uint64_t key[2][5];void*recipe[2];} OwnedFrame;
static volatile LONG64 recipe_created,recipe_freed,recipe_acquired,recipe_released,recipe_attach_failed,recipe_worker_checks,recipe_worker_failed;
''')
replace('static NFPCSourceFrame*pending;','static OwnedFrame*pending;')
needle='static void invalidate(void)'
helpers='''static void owned_free(OwnedFrame*f){if(!f)return;for(unsigned i=0;i<2;i++)if(f->recipe[i]){recipe.release(f->recipe[i]);InterlockedIncrement64(&recipe_released);}nf_pc_source_frame_free(f->source);InterlockedIncrement64(&recipe_freed);free(f);}
static OwnedFrame*owned_take(NFPCSourceFrame*source){if(!source)return NULL;uint64_t info[8];if(!nf_pc_source_frame_info(source,info)||info[4]<1||info[4]>2){nf_pc_source_frame_free(source);InterlockedIncrement64(&recipe_attach_failed);return NULL;}OwnedFrame*f=calloc(1,sizeof(*f));if(!f){nf_pc_source_frame_free(source);InterlockedIncrement64(&recipe_attach_failed);return NULL;}InterlockedIncrement64(&recipe_created);f->source=source;f->owners=(unsigned)info[4];for(unsigned i=0;i<f->owners;i++){if(!nf_pc_source_frame_owner(source,i,f->key[i])||!(f->recipe[i]=recipe.acquire(f->key[i]))){InterlockedIncrement64(&recipe_attach_failed);owned_free(f);return NULL;}InterlockedIncrement64(&recipe_acquired);}return f;}
static int owned_validate(const OwnedFrame*f){InterlockedIncrement64(&recipe_worker_checks);for(unsigned owner=0;owner<f->owners;owner++){uint64_t info[5];if(!recipe.info(f->recipe[owner],info)||info[0]!=f->key[owner][0]||!info[1])goto fail;size_t samples[2]={0,(size_t)info[1]-1};for(unsigned k=0;k<2;k++){uint64_t w[3];if(!recipe.writer(f->recipe[owner],samples[k],w)||w[0]<1||w[0]>2||!w[1]||!w[2])goto fail;for(unsigned b=0;b<w[2];b++){const void*p;size_t n;if(!recipe.block(f->recipe[owner],samples[k],b,&p,&n)||!p||!n)goto fail;/* Touch owned bytes on the worker without core/state access. */volatile const unsigned char*v=p;volatile unsigned sample=v[0]^v[n/2]^v[n-1];(void)sample;}}}return 1;
fail:InterlockedIncrement64(&recipe_worker_failed);return 0;}
'''
replace(needle,helpers+needle)
replace('static void invalidate(void){NFPCSourceFrame*old;','static void invalidate(void){OwnedFrame*old;')
replace('double begin=now();uint64_t m[8];int valid=f&&nf_pc_source_frame_info(f,m);NFPCSourceFrame*old;', 'double begin=now();OwnedFrame*incoming=owned_take(f);f=incoming?incoming->source:NULL;uint64_t m[8];int valid=f&&nf_pc_source_frame_info(f,m);OwnedFrame*old;')
replace('old=pending;pending=f;if(old)dropped++;','old=pending;pending=incoming;if(old)dropped++;')
assert text.count('nf_pc_source_frame_free(old);')==2;text=text.replace('nf_pc_source_frame_free(old);','owned_free(old);')
replace('NFPCScene*scene=NULL;uint64_t scene_gen=0,scene_epoch=0;','NFPCScene*scene=NULL;OwnedFrame*scene_sources=NULL;uint64_t scene_gen=0,scene_epoch=0;')
replace('  NFPCSourceFrame*f;uint64_t gen,seq;','  OwnedFrame*f;uint64_t gen,seq;')
replace('NFPCScene*next=nf_pc_scene_prepare(f,64u*1024*1024);','NFPCScene*next=owned_validate(f)?nf_pc_scene_prepare(f->source,64u*1024*1024):NULL;')
replace('nf_pc_source_frame_free(f);uint64_t m[8];','nf_pc_source_frame_free(f->source);f->source=NULL;uint64_t m[8];')
replace('if(accept){nf_pc_scene_free(scene);scene=next;','if(accept){nf_pc_scene_free(scene);owned_free(scene_sources);scene_sources=f;scene=next;')
replace('else{nf_pc_scene_free(scene);scene=NULL;prepare_failed++;}}else nf_pc_scene_free(next);','else{nf_pc_scene_free(scene);scene=NULL;owned_free(scene_sources);scene_sources=NULL;prepare_failed++;}}else{nf_pc_scene_free(next);owned_free(f);}')
replace(' nf_pc_scene_free(scene);nf_pc_scene_gpu_close(g);free(backup);return 0;',' nf_pc_scene_free(scene);owned_free(scene_sources);nf_pc_scene_gpu_close(g);free(backup);return 0;')
replace('nf_pc_source_frame_free(pending);pending=NULL;','owned_free(pending);pending=NULL;')
needle='CORE(open,"open");'
load='''stage="owned recipe ABI";if(!symbol(dll,"nf_pc_live_recipe_acquire",&recipe.acquire,sizeof(recipe.acquire))||!symbol(dll,"nf_recipe_snapshot_free",&recipe.release,sizeof(recipe.release))||!symbol(dll,"nf_recipe_snapshot_info",&recipe.info,sizeof(recipe.info))||!symbol(dll,"nf_recipe_snapshot_writer",&recipe.writer,sizeof(recipe.writer))||!symbol(dll,"nf_recipe_snapshot_block",&recipe.block,sizeof(recipe.block)))goto fail;
 '''
replace(needle,load+needle)
needle='fputs("}\\n",f);fclose(f);'
extra='''fprintf(f,",\\"recipe_frames_created\\":%llu,\\"recipe_frames_freed\\":%llu,\\"recipe_handles_acquired\\":%llu,\\"recipe_handles_released\\":%llu,\\"recipe_attach_failures\\":%llu,\\"recipe_worker_checks\\":%llu,\\"recipe_worker_failures\\":%llu,\\"owned_recipe_publication\\":true,\\"recipe_fractional_rendering\\":false",(unsigned long long)recipe_created,(unsigned long long)recipe_freed,(unsigned long long)recipe_acquired,(unsigned long long)recipe_released,(unsigned long long)recipe_attach_failed,(unsigned long long)recipe_worker_checks,(unsigned long long)recipe_worker_failed);'''
replace(needle,extra+needle)
staged=out/'live_recipe_host.c';staged.write_text(text);shutil.copy2(root/'outputs/nfsug-research/controller.h',out/'controller.h')
args=[a.replace(str(here/'live_host.c'),str(staged)).replace(str(baseline/'NFSUG-Source-Native-Preview.exe'),str(out/'NFSUG-Source-Native-Preview.exe')) for a in r['command']];assert str(staged) in args;args.insert(1,'-I'+str(here));env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
for name,original in [('capture-host.dll',capture/'capture-host.dll'),('libgcc_s_seh-1.dll',Path('C:/msys64/mingw64/bin/libgcc_s_seh-1.dll')),('libwinpthread-1.dll',Path('C:/msys64/mingw64/bin/libwinpthread-1.dll'))]:shutil.copy2(original,out/name)
report=dict(result='BUILT_OWNED_RECIPE_FRAME_HANDOFF_HOST',command=args,exe_sha256=sha(out/'NFSUG-Source-Native-Preview.exe'),core_sha256=sha(out/'capture-host.dll'),staged_host_sha256=sha(staged),baseline_host_report_sha256=sha(baseline/'live-build-report.json'),core_test_report_sha256=sha(capture/'live-recipe-test-report.json'),script_sha256=sha(Path(__file__)),runtime_sha256=sha(out/'libgcc_s_seh-1.dll'),pthread_sha256=sha(out/'libwinpthread-1.dll'),source_sha256=r['source_sha256'],live_readback=False,recipe_fractional_rendering=False,full_scene_60fps=False,shipping_packages_changed=False)
(out/'live-build-report.json').write_text(json.dumps(report,indent=2));print(report['result'],report['exe_sha256'])

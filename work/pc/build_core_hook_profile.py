"""Build isolated capture-hook timers; no shipping core or source is overwritten."""
from pathlib import Path
import os,sys,subprocess,shutil,json,hashlib
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');baseline=base/'NFSUG-pc-owned-assembly-core-tests';out=base/'NFSUG-pc-core-hook-profile-tests';source=out/'source';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((baseline/'owned-core-build-report.json').read_text());assert sha(baseline/'capture-host.dll')==receipt['core_sha256']
for name,digest in receipt['staged_input_sha256'].items():assert sha(baseline/'source'/name)==digest
shutil.copytree(baseline/'source',source,dirs_exist_ok=True)
(source/'pc_hook_profile.h').write_text('#include <stdint.h>\nuint64_t nf_pc_hook_tick(void);\nvoid nf_pc_hook_record(unsigned,uint64_t);\n')
(source/'pc_hook_profile.c').write_text('''#include <windows.h>
#include <stdint.h>
#include <string.h>
static uint64_t stats[9];
uint64_t nf_pc_hook_tick(void){LARGE_INTEGER t;QueryPerformanceCounter(&t);return (uint64_t)t.QuadPart;}
void nf_pc_hook_record(unsigned phase,uint64_t start){if(phase>=3)return;uint64_t dt=nf_pc_hook_tick()-start;stats[phase*3]++;stats[phase*3+1]+=dt;if(dt>stats[phase*3+2])stats[phase*3+2]=dt;}
__declspec(dllexport) void nf_pc_core_hook_reset(void){memset(stats,0,sizeof(stats));}
__declspec(dllexport) void nf_pc_core_hook_profile(uint64_t out[10]){if(!out)return;LARGE_INTEGER f;QueryPerformanceFrequency(&f);out[0]=(uint64_t)f.QuadPart;memcpy(out+1,stats,sizeof(stats));}
''')
def wrap(file,signature,implementation,wrapper):
 p=source/file;text=p.read_text(encoding='utf-8');start=text.index(signature);end=text.index('\n}',start)+2;body=text[start:end];new=body.replace(signature,implementation,1);text=text[:start]+new+'\n'+wrapper+text[end:];text='#include "pc_hook_profile.h"\n'+text;p.write_text(text,encoding='utf-8')
wrap('camera/layer_snapshot.c','int nf_layer_snapshot_add_dirty(NFLayerSnapshot*s,const void*header,const void*vram,const void*palette,const void*oam,uint32_t dirty,unsigned verify)','static int pc_layer_add_impl(NFLayerSnapshot*s,const void*header,const void*vram,const void*palette,const void*oam,uint32_t dirty,unsigned verify)','int nf_layer_snapshot_add_dirty(NFLayerSnapshot*s,const void*h,const void*v,const void*p,const void*o,uint32_t dirty,unsigned verify){uint64_t t=nf_pc_hook_tick();int result=pc_layer_add_impl(s,h,v,p,o,dirty,verify);nf_pc_hook_record(0,t);return result;}')
wrap('camera/layer_snapshot.c','NFLayerSnapshot*nf_layer_snapshot_clone(const NFLayerSnapshot*s)','static NFLayerSnapshot*pc_layer_clone_impl(const NFLayerSnapshot*s)','NFLayerSnapshot*nf_layer_snapshot_clone(const NFLayerSnapshot*s){uint64_t t=nf_pc_hook_tick();NFLayerSnapshot*result=pc_layer_clone_impl(s);nf_pc_hook_record(1,t);return result;}')
wrap('observer.c','static void android_wall_close_owner(uint64_t epoch,const NFScenePacket*packet)','static void pc_wall_close_impl(uint64_t epoch,const NFScenePacket*packet)','static void android_wall_close_owner(uint64_t epoch,const NFScenePacket*packet){uint64_t t=nf_pc_hook_tick();pc_wall_close_impl(epoch,packet);nf_pc_hook_record(2,t);}')
# Export only the existing selective-event/scanline diagnostic counters. Do not
# enable the per-ARM-instruction timers, whose clock overhead would bias this run.
p=source/'observer.c';text=p.read_text(encoding='utf-8')
for signature in ['void nf_capture_profile_enable(', 'int nf_capture_profile_read(', 'int nf_capture_event_profile_read(']:
 assert text.count('API '+signature)==1
 text=text.replace('API '+signature,'__declspec(dllexport) '+signature,1)
p.write_text(text,encoding='utf-8')
old_source=baseline/'source';args=[]
for arg in receipt['command']:
 if arg==str(baseline/'capture-host.dll'):arg=str(out/'capture-host.dll')
 elif str(old_source) in arg:arg=arg.replace(str(old_source),str(source))
 args.append(arg)
args.insert(args.index('-lws2_32'),str(source/'pc_hook_profile.c'));env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(args,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
b=dict(result='BUILT_CORE_HOOK_PROFILING_ONLY',core_sha256=sha(out/'capture-host.dll'),baseline_core_sha256=sha(baseline/'capture-host.dll'),baseline_build_receipt_sha256=sha(baseline/'owned-core-build-report.json'),source_sha256={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()},command=args,script_sha256=sha(Path(__file__)),shipping_packages_modified=False,phases=['layer_row_add','layer_clone','wall_owner_close'])
(out/'hook-build-report.json').write_text(json.dumps(b,indent=2));print(json.dumps({k:v for k,v in b.items() if k not in ['source_sha256','command']},indent=2))

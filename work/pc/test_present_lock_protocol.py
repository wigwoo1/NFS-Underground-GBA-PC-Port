"""Actual host commit/publication functions with a deliberately blocked swap."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');source=root/'work/pc';base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-present-lock-tests';out.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--baseline-only',action='store_true');args=parser.parse_args()
def function(text,signature):
 a=text.index(signature);start=text.index('{',a);depth=0
 for end in range(start,len(text)):
  if text[end]=='{':depth+=1
  elif text[end]=='}':
   depth-=1
   if not depth:return text[a:end+1]
 raise AssertionError(signature)
prefix=r'''
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
typedef struct {uint64_t epoch;} NFPCSourceFrame;
typedef void NFPCSceneGPU;typedef void NFPCScene;
static CRITICAL_SECTION mutex,presentation_mutex;static HANDLE wake,swap_entered,swap_release,caller_entered,caller_done;
static uint64_t generation=1,epoch=100,sequence,processed,published,dropped,capture_gap_fallback_count,capture_gap_hold_frames;
static int enabled=1,native_allowed=1,capture_failure_streak;static NFPCSourceFrame initial={100},incoming={100},*pending=&initial;
static uint32_t original[38400],fake_pixels[38400];static void*game;
static uint64_t native_presented,fallback_presented,present_failed;static int swap_info_valid;static int64_t swap_info[10];static char worker_message[256];static double last_present;
static struct {const void*(*pixels)(void*);}core;
static unsigned mode;static int last_native,last_pixel;static LONG frees;
#define NFPC_CAPTURE_GAP_GRACE_STEPS 12
enum {M_LOCK,M_PUBLISH,M_PRESENT,M_INTERVAL};
static double now(void){return GetTickCount64()/1000.0;}
static void measured(int metric,double start){(void)metric;(void)start;}
static const void* pixels(void*h){(void)h;return fake_pixels;}
static int nf_pc_source_frame_info(NFPCSourceFrame*f,uint64_t*out){if(!f)return 0;memset(out,0,8*sizeof(*out));out[0]=f->epoch;return 1;}
static void nf_pc_source_frame_free(NFPCSourceFrame*f){if(f)InterlockedIncrement(&frees);}
static const char* nf_pc_scene_gpu_error(void){return "mock";}
static int nf_pc_scene_gpu_swap_info(NFPCSceneGPU*g,int64_t*out,size_t bytes){(void)g;memset(out,0,bytes);return 1;}
static int nf_pc_scene_gpu_present(NFPCSceneGPU*g,const void*rgba,size_t bytes,unsigned w,unsigned h){(void)g;(void)bytes;(void)w;(void)h;SetEvent(swap_entered);assert(WaitForSingleObject(swap_release,5000)==WAIT_OBJECT_0);last_native=rgba==NULL;last_pixel=rgba?((const unsigned char*)rgba)[0]:-1;return 1;}
'''
suffix=r'''
static DWORD WINAPI render(void*unused){(void)unused;uint32_t backup[38400];commit_present(NULL,mode==5?NULL:(NFPCScene*)1,1,100,backup,0,&last_present);return 0;}
static DWORD WINAPI caller(void*unused){(void)unused;SetEvent(caller_entered);if(mode==1)invalidate();else publish(mode==3||mode==4?NULL:&incoming,1);SetEvent(caller_done);return 0;}
int main(int argc,char**argv){assert(argc==2);mode=(unsigned)atoi(argv[1]);assert(mode<6);core.pixels=pixels;if(mode==2)incoming.epoch=200;if(mode==3)capture_failure_streak=12;if(mode==4)capture_failure_streak=2;
 InitializeCriticalSection(&mutex);InitializeCriticalSection(&presentation_mutex);wake=CreateEvent(NULL,FALSE,FALSE,NULL);swap_entered=CreateEvent(NULL,TRUE,FALSE,NULL);swap_release=CreateEvent(NULL,TRUE,FALSE,NULL);caller_entered=CreateEvent(NULL,TRUE,FALSE,NULL);caller_done=CreateEvent(NULL,TRUE,FALSE,NULL);
 HANDLE worker=CreateThread(NULL,0,render,NULL,0,NULL);assert(worker&&WaitForSingleObject(swap_entered,5000)==WAIT_OBJECT_0);
 int free_state=TryEnterCriticalSection(&mutex)!=0;if(free_state)LeaveCriticalSection(&mutex);assert(free_state==NF_RELEASE_STATE);
 memset(fake_pixels,0x44,sizeof(fake_pixels));HANDLE producer=CreateThread(NULL,0,caller,NULL,0,NULL);assert(producer&&WaitForSingleObject(caller_entered,5000)==WAIT_OBJECT_0);
 int ordinary=mode==0||mode==4||mode==5;
 if(ordinary&&NF_RELEASE_STATE)assert(WaitForSingleObject(caller_done,1000)==WAIT_OBJECT_0);else assert(WaitForSingleObject(caller_done,50)==WAIT_TIMEOUT);
 SetEvent(swap_release);assert(WaitForSingleObject(worker,5000)==WAIT_OBJECT_0&&WaitForSingleObject(producer,5000)==WAIT_OBJECT_0);CloseHandle(worker);CloseHandle(producer);
 if(mode==1||mode==2||mode==3){assert(generation==2);uint32_t backup[38400];commit_present(NULL,(NFPCScene*)1,1,100,backup,sequence,&last_present);assert(!last_native);}
 else {assert(generation==1&&native_allowed);if(mode==5)assert(!last_native&&last_pixel==0);}
 if(mode==2){assert(epoch==200);}
 if(mode==1||mode==3){assert(!native_allowed);}
 if(mode==4){assert(capture_gap_hold_frames==1&&!capture_gap_fallback_count);}
 if(mode==3){assert(capture_gap_fallback_count==1);}
 if(mode==1){assert(pending==NULL);}else{assert(sequence==1&&original[0]==0x44444444u);}
 CloseHandle(wake);CloseHandle(swap_entered);CloseHandle(swap_release);CloseHandle(caller_entered);CloseHandle(caller_done);DeleteCriticalSection(&mutex);DeleteCriticalSection(&presentation_mutex);
 printf("{\"case\":%u,\"state_mutex_free_during_swap\":%s,\"ordinary_publication_completed_during_swap\":%s,\"generation_transition_waited_for_swap\":%s,\"stale_after_transition_rejected\":%s}\n",mode,free_state?"true":"false",ordinary&&NF_RELEASE_STATE?"true":"false",!ordinary?"true":"false",!ordinary?"true":"false");return 0;}
'''
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');rows={}
before=root/'outputs/nfsug-native-renderer/camera-research/pc-present-lock-20261017/before/live_host.c'
paths=[('baseline',before if before.exists() else source/'live_host.c')]
if not args.baseline_only:paths.append(('candidate',source/'live_host.c'))
for name,path in paths:
 text=path.read_text();parts=[function(text,'static void invalidate('),function(text,'static void publish('),function(text,'static int current(')]
 if name=='candidate':parts.append(function(text,'static void commit_present('))
 else:
  start=text.index('EnterCriticalSection(&mutex);int use_native=');end=text.index('LeaveCriticalSection(&mutex);',start)+len('LeaveCriticalSection(&mutex);');parts.append('static void commit_present(NFPCSceneGPU*g,NFPCScene*scene,uint64_t scene_gen,uint64_t scene_epoch,uint32_t*backup,uint64_t seq,double*stamp){(void)stamp;'+text[start:end]+'}')
 staged=out/(name+'.c');staged.write_text(prefix+'\n'.join(parts)+suffix,encoding='utf-8');exe=out/(name+'.exe')
 command=['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-O2','-Wall','-Wextra','-Werror','-DNF_RELEASE_STATE='+('1' if name=='candidate' else '0'),str(staged),'-o',str(exe)]
 run=subprocess.run(command,env=env,capture_output=True,text=True);(out/(name+'-compile.log')).write_text(run.stdout+run.stderr,encoding='utf-8');run.check_returncode();rows[name]=[]
 for case in range(6):
  run=subprocess.run([str(exe),str(case)],env=env,capture_output=True,text=True,timeout=12);(out/(name+'-'+str(case)+'.log')).write_text(run.stdout+run.stderr,encoding='utf-8');run.check_returncode();rows[name].append(json.loads(run.stdout))
report=dict(result='VERIFIED_ACTUAL_PRESENT_PUBLICATION_PROTOCOL',rows=rows,baseline_only=args.baseline_only,source_sha256={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in paths},script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),real_gl=False,visible_cadence_verified=False,limits='Exact extracted host functions with deterministic Win32 events and a deliberately blocked presentation callback. Proves lock/provenance protocol, not actual monitor latency, input lag, audio quality or smooth60.')
(out/('baseline-report.json' if args.baseline_only else 'protocol-report.json')).write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

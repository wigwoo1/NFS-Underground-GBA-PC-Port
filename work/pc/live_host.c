#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <mmsystem.h>
#include <xinput.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "source_frame.h"
#include "source_background.h"
#include "source_reader.h"
#include "source_scene.h"
#include "scene_gpu.h"
#include "present_deadline.h"
#include "../../outputs/nfsug-research/controller.h"
#define NFPC_CAPTURE_GAP_GRACE_STEPS 12

/* Core and input/audio live exclusively on main thread. Render owns its WGL
   context and receives only copied frames. One-slot mailbox bounds backlog. */
typedef struct {
 void*(*open)(const char*);void(*close)(void*);int(*step)(void*,uint32_t);
 int(*timing)(void*,uint64_t*);const uint32_t*(*pixels)(void*);
 int(*load)(void*,const void*,size_t);size_t(*audio)(void*,int16_t*,size_t);
 int(*enable)(void*,int);int(*layers)(void*,int);int(*world)(void*,int);
 int(*wall)(void*,int);int(*sky)(void*,int);
} Core;
static int(*background_lifetime_info)(uint64_t*);static uint64_t background_lifetime_stats[3];
static NFPCBackgroundTake background_take;static NFPCOwnedRelease background_release;static int owned_background;static uint64_t background_stats[3];
static int owned_geometry;static NFPCOwnerTake geometry_take;static NFPCOwnedRelease geometry_release;static int(*geometry_lifetime_info)(uint64_t*);static uint64_t geometry_stats[3],geometry_lifetime_stats[3];
/* Deterministic diagnostics only; normal controller input is unchanged. */
static unsigned scripted_input(uint64_t segment,int mode){
 if(mode==2){unsigned phase=(unsigned)(segment%1200);return 1u|(phase>=180&&phase<500?32u:phase>=500&&phase<720?16u:0u);}
 return 1u|(segment>=60&&segment<120?16u:0u)|(segment>=480&&segment<540?32u:0u);
}
static int geometry_cache;static int(*geometry_cache_enable)(void*,int);static int(*geometry_cache_info)(uint64_t*);static uint64_t geometry_cache_stats[12];
static int direct_cached;static uint64_t direct_cached_stats[3];
static Core core;static void*game;static NFPCSourceAPI api;static NFPCSourceReader*reader;static uint64_t reader_stats[8];static int uncached_capture,reader_enabled;
static HWND window;static LARGE_INTEGER frequency;static LONG running=1;
static int paused,focus_paused,selftest,hidden,enabled=1,reload_pending;
static CRITICAL_SECTION mutex,presentation_mutex;static HANDLE wake,render_ready;
static NFPCSourceFrame*pending;static uint32_t original[38400];
static uint64_t generation=1,epoch,sequence,processed;
static int swap_info_valid;static int64_t swap_info[10];
static int native_allowed,worker_busy,worker_error;
static uint64_t published,dropped,prepared,prepare_failed,rendered,native_presented,fallback_presented,stale_rejected,present_failed;static uint64_t capture_failure_log[32][7],capture_failure_kind_counts[6];static uint64_t capture_failure_count,capture_failure_streak,capture_failure_max_streak,capture_failure_first_frame,capture_failure_last_frame;static unsigned capture_failure_log_count;
static uint64_t capture_gap_hold_frames,capture_gap_fallback_count;static unsigned prepare_delay,capture_gap_steps;static uint64_t capture_gap_at;static int capture_native;static char worker_message[512],renderer_name[256];static const char*capture_path;
/* Optional owner-thread diagnostic. It samples immutable captured bytes before
   publication; no render-thread/core sharing or GPU readback is introduced.
   Hashing/CSV work adds overhead, so these runs are not performance evidence. */
static FILE*logic_audit;static unsigned char*logic_audit_sky;
static uint64_t logic_audit_rows;static int logic_audit_failed;
static uint64_t logic_audit_hash(const void*bytes,size_t n){
 const unsigned char*p=bytes;uint64_t h=14695981039346656037ull;
 for(size_t i=0;i<n;i++){h^=p[i];h*=1099511628211ull;}return h;
}
static void logic_audit_record(uint64_t frame,uint64_t segment,uint64_t clock_frame,const NFPCSourceFrame*source){
 if(!logic_audit||logic_audit_failed)return;
 uint64_t m[8]={0};int captured=source&&nf_pc_source_frame_info(source,m);
 int sky=captured&&nf_pc_source_sky_rgba(source,logic_audit_sky,153600);
 const uint32_t*p=core.pixels(game);
 uint64_t display=logic_audit_hash(p,153600),upper=logic_audit_hash(p,240u*64*4);
 uint64_t sky_hash=sky?logic_audit_hash(logic_audit_sky,153600):0;
 if(fprintf(logic_audit,"%llu,%llu,%llu,%016llx,%016llx,%d,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%d,%016llx\n",
   (unsigned long long)frame,(unsigned long long)segment,(unsigned long long)clock_frame,
   (unsigned long long)display,(unsigned long long)upper,captured,
   (unsigned long long)m[0],(unsigned long long)m[1],(unsigned long long)m[2],
   (unsigned long long)m[3],(unsigned long long)m[4],(unsigned long long)m[6],
   (unsigned long long)m[7],sky,(unsigned long long)sky_hash)<0)logic_audit_failed=1;
 else logic_audit_rows++;
}
static DWORD(WINAPI*getpad)(DWORD,XINPUT_STATE*);static HWAVEOUT audio_device;
static WAVEHDR wave[8];static int16_t samples[8][8192];static uint64_t audio_frames,audio_dropped;
static int16_t audio_ring[65536*2];static unsigned audio_read,audio_count;
/* Sampled output-queue diagnostics. An empty observation is evidence of no
 * queued driver buffer at that poll, not a measurement of audible gap length.
 * Ignore initial fill and deliberate reset. Never touches PCM or game timing. */
static uint64_t audio_queue_polls,audio_queue_empty_polls,audio_queue_empty_events,audio_queue_empty_pcm[32];
static unsigned audio_queue_started,audio_queue_empty_active,audio_queue_min=8,audio_queue_max,audio_queue_log_count;
/* Event context is sampled BEFORE pulling more core PCM or requeueing buffers.
   Frame counts below describe producer/ring state, not hardware playback position. */
static double audio_queue_last_time,audio_queue_empty_interval_ms[32];
static uint64_t audio_queue_last_pcm,audio_queue_empty_context[32][5];
static unsigned audio_queue_last_valid,audio_queue_last_queued,audio_queue_last_pending;
#include "audio_queue_duration.h"
static NFAudioQueueClock audio_clock;
static uint64_t audio_duration_queries,audio_duration_valid,audio_duration_unknown;
static int audio_buffered_frames(uint64_t*remaining){
 audio_duration_queries++;MMTIME position;memset(&position,0,sizeof(position));position.wType=TIME_SAMPLES;
 if(waveOutGetPosition(audio_device,&position,sizeof(position))!=MMSYSERR_NOERROR||position.wType!=TIME_SAMPLES){audio_duration_unknown++;return 0;}
 int valid=nf_audio_clock_remaining(&audio_clock,position.u.sample,remaining);if(valid)audio_duration_valid++;else audio_duration_unknown++;return valid;
}
static void audio_reset(void){nf_audio_clock_reset(&audio_clock);if(audio_device)waveOutReset(audio_device);audio_read=audio_count=0;audio_queue_started=audio_queue_empty_active=0;audio_queue_last_valid=audio_queue_last_queued=audio_queue_last_pending=0;audio_queue_last_time=0;audio_queue_last_pcm=0;}
static double now(void){LARGE_INTEGER t;QueryPerformanceCounter(&t);return (double)t.QuadPart/frequency.QuadPart;}
enum {M_CORE,M_CAPTURE,M_PUBLISH,M_LOCK,M_PREPARE,M_GPU,M_PRESENT,M_AUDIO,M_LOGIC,M_INTERVAL,M_COUNT};
static const char*metric_names[M_COUNT]={"core_step","source_capture","publish_total","publish_lock_wait","scene_prepare","gpu_submit","present_commit","audio_drain","logic_iteration","present_interval"};
typedef struct {uint64_t count,over16,over33;double total,max;} Metric;
static Metric metrics[M_COUNT];
static void measured(unsigned phase,double start){double ms=(now()-start)*1000;Metric*m=metrics+phase;m->count++;m->total+=ms;if(ms>m->max)m->max=ms;if(ms>16.667)m->over16++;if(ms>33.333)m->over33++;}
static void print_metrics(FILE*f){fputc('{',f);for(unsigned i=0;i<M_COUNT;i++){Metric*m=metrics+i;fprintf(f,"%s\"%s\":{\"count\":%llu,\"mean_ms\":%.6f,\"max_ms\":%.6f,\"over16_667_ms\":%llu,\"over33_333_ms\":%llu}",i?",":"",metric_names[i],(unsigned long long)m->count,m->count?m->total/m->count:0,m->max,(unsigned long long)m->over16,(unsigned long long)m->over33);}fputc('}',f);}
/* Commit lock always precedes metadata lock; ordinary publication needs only
   metadata. Epoch/reset/real-fallback transitions serialize with accepted swaps. */
static void invalidate(void){NFPCSourceFrame*old;EnterCriticalSection(&presentation_mutex);EnterCriticalSection(&mutex);generation++;native_allowed=0;old=pending;pending=NULL;LeaveCriticalSection(&mutex);LeaveCriticalSection(&presentation_mutex);nf_pc_source_frame_free(old);SetEvent(wake);}
static void publish(NFPCSourceFrame*f,int captured){double begin=now();uint64_t m[8];int valid=f&&nf_pc_source_frame_info(f,m);NFPCSourceFrame*old;int commit_locked=0;double lock_start=now();EnterCriticalSection(&mutex);
 if((valid&&epoch&&epoch!=m[0])||(captured&&!valid&&native_allowed&&!(enabled&&capture_failure_streak<NFPC_CAPTURE_GAP_GRACE_STEPS))){
  LeaveCriticalSection(&mutex);EnterCriticalSection(&presentation_mutex);EnterCriticalSection(&mutex);commit_locked=1;
 }
 measured(M_LOCK,lock_start);if(valid&&epoch&&epoch!=m[0])generation++;if(valid)epoch=m[0];old=NULL;if(captured){int hold_native=!valid&&native_allowed&&enabled&&capture_failure_streak<NFPC_CAPTURE_GAP_GRACE_STEPS;if(!valid&&native_allowed&&!hold_native){generation++;capture_gap_fallback_count++;}if(hold_native)capture_gap_hold_frames++;else native_allowed=valid&&enabled;old=pending;pending=f;if(old)dropped++;}memcpy(original,core.pixels(game),sizeof(original));sequence++;if(valid)published++;LeaveCriticalSection(&mutex);if(commit_locked)LeaveCriticalSection(&presentation_mutex);nf_pc_source_frame_free(old);SetEvent(wake);measured(M_PUBLISH,begin);}
static int current(uint64_t gen,uint64_t ep){return enabled&&native_allowed&&gen==generation&&ep==epoch;}
/* The accepted image is immutable on this worker. Keep invalidation atomic
   with the swap, but let ordinary core publication proceed during driver waits. */
static void commit_present(NFPCSceneGPU*g,NFPCScene*scene,uint64_t scene_gen,uint64_t scene_epoch,uint32_t*backup,uint64_t seq,double*stamp){
 EnterCriticalSection(&presentation_mutex);
 EnterCriticalSection(&mutex);int use_native=scene&&current(scene_gen,scene_epoch);memcpy(backup,original,153600);LeaveCriticalSection(&mutex);double present_start=now();int ok=nf_pc_scene_gpu_present(g,use_native?NULL:backup,use_native?0:153600,3240,2160);measured(M_PRESENT,present_start);EnterCriticalSection(&mutex);swap_info_valid=nf_pc_scene_gpu_swap_info(g,swap_info,sizeof(swap_info));if(ok){if(*stamp)measured(M_INTERVAL,*stamp);*stamp=now();if(use_native)native_presented++;else fallback_presented++;}else{present_failed++;snprintf(worker_message,sizeof(worker_message),"%s",nf_pc_scene_gpu_error());}if(seq>processed)processed=seq;LeaveCriticalSection(&mutex);
 LeaveCriticalSection(&presentation_mutex);
}
static DWORD WINAPI render_thread(void*unused){
 (void)unused;NFPCSceneGPU*g=nf_pc_scene_gpu_open_window(window);NFPCScene*scene=NULL;uint64_t scene_gen=0,scene_epoch=0;uint32_t*backup=malloc(153600);if(!g||!backup){EnterCriticalSection(&mutex);worker_error=1;snprintf(worker_message,sizeof(worker_message),"%s",g?"Render copy allocation":nf_pc_scene_gpu_error());LeaveCriticalSection(&mutex);SetEvent(render_ready);if(g)nf_pc_scene_gpu_close(g);free(backup);return 1;}
 snprintf(renderer_name,sizeof(renderer_name),"%s",nf_pc_scene_gpu_renderer(g));SetEvent(render_ready);double last_present=0;NFPresentDeadline deadline={now()};
 while(InterlockedCompareExchange(&running,0,0)){
  NFPCSourceFrame*f;uint64_t gen,seq;EnterCriticalSection(&mutex);f=pending;pending=NULL;gen=generation;seq=sequence;worker_busy=f!=NULL;LeaveCriticalSection(&mutex);
  if(f){if(prepare_delay)Sleep(prepare_delay);double prepare_start=now();NFPCScene*next=nf_pc_scene_prepare(f,64u*1024*1024);measured(M_PREPARE,prepare_start);nf_pc_source_frame_free(f);uint64_t m[8];EnterCriticalSection(&mutex);worker_busy=0;int accept=next&&nf_pc_scene_info(next,m)&&current(gen,m[0]);if(next&&!accept)stale_rejected++;if(!next)prepare_failed++;LeaveCriticalSection(&mutex);
   if(accept){nf_pc_scene_free(scene);scene=next;scene_gen=gen;scene_epoch=m[0];prepared++;double gpu_start=now();int drawn=nf_pc_scene_gpu_render(g,scene,3840,2160,3240,2160);measured(M_GPU,gpu_start);if(drawn)rendered++;else{nf_pc_scene_free(scene);scene=NULL;prepare_failed++;}}else nf_pc_scene_free(next);
  }
  /* Acceptance and buffer swap are one commit relative to reset/toggle. Main
     can continue logic while preparation and native GPU work are in flight. */
  if(nf_present_due(&deadline,now())){
   commit_present(g,scene,scene_gen,scene_epoch,backup,seq,&last_present);
   nf_present_completed(&deadline,now());
  }
  WaitForSingleObject(wake,nf_present_wait(&deadline,now()));
 }
 if(capture_path){EnterCriticalSection(&mutex);int valid=scene&&current(scene_gen,scene_epoch);memcpy(backup,original,153600);LeaveCriticalSection(&mutex);size_t n=valid?3840u*2160*4:153600;unsigned char*image=malloc(n);if(image){int ok=valid?nf_pc_scene_gpu_draw(g,scene,3840,2160,3240,2160,image,n):1;if(!valid)memcpy(image,backup,n);if(ok){FILE*f=fopen(capture_path,"wb");if(f){if(fwrite(image,1,n,f)==n)capture_native=valid;fclose(f);}}free(image);}}
 nf_pc_scene_free(scene);nf_pc_scene_gpu_close(g);free(backup);return 0;
}
static void audio_init(void){WAVEFORMATEX f={WAVE_FORMAT_PCM,2,44100,176400,4,16,0};if(waveOutOpen(&audio_device,WAVE_MAPPER,&f,0,0,CALLBACK_NULL)!=MMSYSERR_NOERROR){audio_device=NULL;return;}for(unsigned i=0;i<8;i++){wave[i].lpData=(char*)samples[i];wave[i].dwBufferLength=sizeof(samples[i]);waveOutPrepareHeader(audio_device,wave+i,sizeof(WAVEHDR));}}
static void audio_drain(FILE*dump){
 if(audio_device&&audio_queue_started){double polled=now();unsigned queued=0;for(unsigned i=0;i<8;i++)queued+=(wave[i].dwFlags&WHDR_INQUEUE)!=0;audio_queue_polls++;if(queued<audio_queue_min)audio_queue_min=queued;if(queued>audio_queue_max)audio_queue_max=queued;if(!queued){audio_queue_empty_polls++;if(!audio_queue_empty_active){audio_queue_empty_events++;if(audio_queue_log_count<32){unsigned event=audio_queue_log_count++;audio_queue_empty_pcm[event]=audio_frames;audio_queue_empty_interval_ms[event]=audio_queue_last_valid?(polled-audio_queue_last_time)*1000:0;uint64_t*context=audio_queue_empty_context[event];context[0]=audio_queue_last_pcm;context[1]=audio_queue_last_queued;context[2]=audio_queue_last_pending;context[3]=audio_count;context[4]=audio_queue_last_valid;}}audio_queue_empty_active=1;}else audio_queue_empty_active=0;audio_queue_last_valid=1;audio_queue_last_time=polled;audio_queue_last_pcm=audio_frames;audio_queue_last_queued=queued;audio_queue_last_pending=audio_count;}
 int16_t pcm[8192];size_t n;while((n=core.audio(game,pcm,4096))!=0){audio_frames+=n;if(dump)fwrite(pcm,4,n,dump);if(audio_device){for(size_t i=0;i<n;i++){if(audio_count==65536){audio_read=(audio_read+1)%65536;audio_count--;audio_dropped++;}unsigned at=(audio_read+audio_count)%65536;audio_ring[at*2]=pcm[i*2];audio_ring[at*2+1]=pcm[i*2+1];audio_count++;}}}
 /* Preserve the existing two-block startup reserve. Once running, buffer
    count cannot describe duration when tails have variable lengths. Retain a
    partial tail only when a valid device position proves 4096 frames remain.
    Unknown positions submit ready PCM; this never generates future audio. */
 if(audio_device&&(audio_queue_started||audio_count>=4096)){
  for(unsigned i=0;i<8&&audio_count;i++)if(!(wave[i].dwFlags&WHDR_INQUEUE)){
   if(audio_count<2048){uint64_t remaining=0;if(!audio_queue_started||(audio_buffered_frames(&remaining)&&remaining>=4096))break;}
   unsigned count=audio_count<2048?audio_count:2048;
   for(unsigned j=0;j<count;j++){samples[i][j*2]=audio_ring[audio_read*2];samples[i][j*2+1]=audio_ring[audio_read*2+1];audio_read=(audio_read+1)%65536;}
   audio_count-=count;wave[i].dwBufferLength=count*4;
   if(waveOutWrite(audio_device,wave+i,sizeof(WAVEHDR))!=MMSYSERR_NOERROR)audio_dropped+=count;
   else {nf_audio_clock_submit(&audio_clock,count);audio_queue_started=1;audio_queue_empty_active=0;}
  }
 }
}
static int controller_check(void){return nfs_map_controller(0,0,0,40,40)==0&&nfs_map_controller(0,0,0,41,41)==3&&nfs_map_controller(0,9000,-9000,0,0)==0&&nfs_map_controller(0,9001,-9001,0,0)==(16|128)&&nfs_map_controller(0xffff,0,0,0,0)==1023&&nfs_map_controller(0x0100|0x4000,0,0,0,0)==512&&nfs_map_controller(0x0200|0x8000,0,0,0,0)==256;}
static unsigned input(int*connected){*connected=0;if(GetForegroundWindow()!=window||paused)return 0;unsigned keys=0;const int vk[]={'Z','X',VK_BACK,VK_RETURN,VK_RIGHT,VK_LEFT,VK_UP,VK_DOWN,'S','A'};for(unsigned i=0;i<10;i++)if(GetAsyncKeyState(vk[i])&0x8000)keys|=1u<<i;if(getpad)for(DWORD i=0;i<4;i++){XINPUT_STATE p;if(getpad(i,&p)==ERROR_SUCCESS){*connected=1;keys|=nfs_map_controller(p.Gamepad.wButtons,p.Gamepad.sThumbLX,p.Gamepad.sThumbLY,p.Gamepad.bLeftTrigger,p.Gamepad.bRightTrigger);break;}}return keys;}
static LRESULT CALLBACK proc(HWND w,UINT msg,WPARAM key,LPARAM data){
 if(msg==WM_CLOSE){InterlockedExchange(&running,0);return 0;}
 if(msg==WM_KILLFOCUS&&!selftest&&!paused){focus_paused=paused=1;audio_reset();}
 if(msg==WM_SETFOCUS&&focus_paused){focus_paused=paused=0;}
 if(msg==WM_KEYDOWN&&!(data&(1L<<30))){if(key==VK_SPACE){paused=!paused;focus_paused=0;audio_reset();}if(key==VK_F3){EnterCriticalSection(&mutex);enabled=!enabled;LeaveCriticalSection(&mutex);invalidate();}if(key==VK_F8)reload_pending=1;if(key==VK_F1){paused=1;MessageBoxA(w,"Xbox: RT/A accelerate; LT/B brake\nLeft stick/D-pad steer\nLB/X=L; RB/Y=R; Menu=Start; View=Select\nKeyboard: arrows, Z=A, X=B, A=L, S=R\nEnter=Start; Backspace=Select\nF3 native/original; Space pause; F8 reload initial checkpoint\n\nOriginal game logic uses mGBA. Native rendering is experimental.\nA brief capture gap holds the last native scene for up to 12 logic steps before fallback.\nNo 60-fps motion interpolation or upscaled texture pack yet.\nThis preview does not write game saves.","NFSUG source renderer preview",MB_OK);}}
 return DefWindowProc(w,msg,key,data);
}
static void* read_file(const char*path,size_t*n){FILE*f=fopen(path,"rb");if(!f)return NULL;if(fseek(f,0,SEEK_END)||ftell(f)<=0){fclose(f);return NULL;}long length=ftell(f);rewind(f);void*p=malloc((size_t)length);if(!p||fread(p,1,(size_t)length,f)!=(size_t)length){free(p);p=NULL;}fclose(f);if(p)*n=(size_t)length;return p;}
static int symbol(HMODULE dll,const char*name,void*target,size_t bytes){FARPROC p=GetProcAddress(dll,name);if(!p||bytes!=sizeof(p))return 0;memcpy(target,&p,bytes);return 1;}
#define CORE(field,name) stage="core ABI: " name;if(!symbol(dll,"nfa_core_" name,&core.field,sizeof(core.field)))goto fail
#define CAPTURE(field,name) stage="capture ABI: " name;if(!symbol(dll,"nfa_core_" name,&api.field,sizeof(api.field)))goto fail
int main(int argc,char**argv){
 const char*stage="arguments";const char*rom=NULL,*state_path=NULL,*report_path=NULL,*oracle_path=NULL,*audio_path=NULL,*logic_audit_path=NULL;unsigned test_frames=0,reload_at=0,toggle_at=0;int fast=0,script=0,no_audio=0,reload_busy=0;char directory[MAX_PATH],dllpath[MAX_PATH];FILE*oracle=NULL,*dump=NULL;void*state=NULL;size_t state_bytes=0;HMODULE dll=NULL,xi=NULL;HANDLE thread=NULL;int result=1,pad=0,reloaded=0,toggled=0;uint64_t frames=0,segment=0,base_timing[4]={0};unsigned original_mismatches=0,timing_errors=0;double start=0,elapsed=0,max_step_ms=0;
 QueryPerformanceFrequency(&frequency);SetProcessDPIAware();InitializeCriticalSection(&mutex);InitializeCriticalSection(&presentation_mutex);wake=CreateEvent(NULL,FALSE,FALSE,NULL);render_ready=CreateEvent(NULL,TRUE,FALSE,NULL);
 for(int i=1;i<argc;i++){if(!strcmp(argv[i],"--rom")&&i+1<argc)rom=argv[++i];else if(!strcmp(argv[i],"--state")&&i+1<argc)state_path=argv[++i];else if(!strcmp(argv[i],"--frames")&&i+1<argc)test_frames=(unsigned)strtoul(argv[++i],NULL,10);else if(!strcmp(argv[i],"--reload-at")&&i+1<argc)reload_at=(unsigned)strtoul(argv[++i],NULL,10);else if(!strcmp(argv[i],"--toggle-at")&&i+1<argc)toggle_at=(unsigned)strtoul(argv[++i],NULL,10);else if(!strcmp(argv[i],"--prepare-delay-ms")&&i+1<argc)prepare_delay=(unsigned)strtoul(argv[++i],NULL,10);else if(!strcmp(argv[i],"--capture-gap-at")&&i+1<argc)capture_gap_at=strtoull(argv[++i],NULL,10);else if(!strcmp(argv[i],"--capture-gap-steps")&&i+1<argc)capture_gap_steps=(unsigned)strtoul(argv[++i],NULL,10);else if(!strcmp(argv[i],"--reload-after-prepare"))reload_busy=1;else if(!strcmp(argv[i],"--hidden"))hidden=1;else if(!strcmp(argv[i],"--fast"))fast=1;else if(!strcmp(argv[i],"--script"))script=1;else if(!strcmp(argv[i],"--script-diverse"))script=2;else if(!strcmp(argv[i],"--no-audio"))no_audio=1;else if(!strcmp(argv[i],"--geometry-cache")){geometry_cache=1;direct_cached=1;owned_geometry=1;owned_background=1;}else if(!strcmp(argv[i],"--direct-cached")){direct_cached=1;owned_geometry=1;owned_background=1;}else if(!strcmp(argv[i],"--owned-geometry")){owned_geometry=1;owned_background=1;}else if(!strcmp(argv[i],"--owned-background"))owned_background=1;else if(!strcmp(argv[i],"--original"))enabled=0;else if(!strcmp(argv[i],"--uncached-capture"))uncached_capture=1;else if(!strcmp(argv[i],"--audit-logic")&&i+1<argc)logic_audit_path=argv[++i];else if(!strcmp(argv[i],"--report")&&i+1<argc)report_path=argv[++i];else if(!strcmp(argv[i],"--oracle")&&i+1<argc)oracle_path=argv[++i];else if(!strcmp(argv[i],"--audio-dump")&&i+1<argc)audio_path=argv[++i];else if(!strcmp(argv[i],"--capture")&&i+1<argc)capture_path=argv[++i];else goto fail;}
 selftest=test_frames!=0;if((owned_background&&uncached_capture)||!rom||!controller_check()||prepare_delay>1000||((capture_gap_at==0)!=(capture_gap_steps==0))||capture_gap_steps>600)goto fail;
 GetModuleFileNameA(NULL,directory,sizeof(directory));char*slash=strrchr(directory,'\\');if(!slash)goto fail;*slash=0;if(snprintf(dllpath,sizeof(dllpath),"%s\\capture-host.dll",directory)>=(int)sizeof(dllpath))goto fail;stage="packaged core DLL dependencies";dll=LoadLibraryA(dllpath);if(!dll)goto fail;
 CORE(open,"open");CORE(close,"close");CORE(step,"step");CORE(timing,"timing");CORE(pixels,"pixels");CORE(load,"load_state");CORE(audio,"read_audio");CORE(enable,"capture_enable");CORE(layers,"capture_layers");CORE(world,"capture_source_world_enable");CORE(wall,"capture_wall_history_enable");CORE(sky,"capture_sky_enable");CAPTURE(layer_info,"capture_layer_info");CAPTURE(background,"capture_background_scene");CAPTURE(geometry,"capture_source_world");CAPTURE(road,"capture_road_history");CAPTURE(wall,"capture_wall_history");CAPTURE(proof,"capture_write_ownership");
 if(owned_background){stage="owned background ABI";if(!symbol(dll,"nfa_core_capture_background_take",&background_take,sizeof(background_take))||!symbol(dll,"nfa_core_capture_owned_free",&background_release,sizeof(background_release))||!symbol(dll,"nfa_core_capture_owned_background_info",&background_lifetime_info,sizeof(background_lifetime_info)))goto fail;}
 if(owned_geometry){stage="owned geometry ABI";if(!symbol(dll,"nfa_core_capture_source_world_take",&geometry_take,sizeof(geometry_take))||!symbol(dll,"nfa_core_capture_source_world_free",&geometry_release,sizeof(geometry_release))||!symbol(dll,"nfa_core_capture_owned_geometry_info",&geometry_lifetime_info,sizeof(geometry_lifetime_info)))goto fail;}
 if(geometry_cache){stage="geometry cache ABI";if(!symbol(dll,"nfa_core_geometry_cache_enable",&geometry_cache_enable,sizeof(geometry_cache_enable))||!symbol(dll,"nfa_core_geometry_cache_info",&geometry_cache_info,sizeof(geometry_cache_info)))goto fail;}
 stage="ROM open";game=core.open(rom);if(!game)goto fail;if(state_path){stage="checkpoint load";state=read_file(state_path,&state_bytes);if(!state||!core.load(game,state,state_bytes))goto fail;}
 stage="capture enable";if(!core.enable(game,1)||!core.layers(game,1)||!core.world(game,1)||!core.wall(game,1)||!core.sky(game,1))goto fail;
 if(geometry_cache){stage="geometry cache enable";if(!geometry_cache_enable(game,1))goto fail;}
 api.size=sizeof(api);api.core=game;if(!nf_pc_source_api_bind_owner(&api))goto fail;if(!uncached_capture)reader=direct_cached?nf_pc_source_reader_open_direct_sources(&api,64u*1024*1024,background_take,background_release,geometry_take,geometry_release):owned_geometry?nf_pc_source_reader_open_owned_sources(&api,64u*1024*1024,background_take,background_release,geometry_take,geometry_release):owned_background?nf_pc_source_reader_open_owned_background(&api,64u*1024*1024,background_take,background_release):nf_pc_source_reader_open(&api,64u*1024*1024);reader_enabled=reader!=NULL;if(owned_background&&!reader)goto fail;
 if(logic_audit_path){stage="logic audit open";logic_audit=fopen(logic_audit_path,"w");logic_audit_sky=malloc(153600);if(!logic_audit||!logic_audit_sky)goto fail;if(fputs("logic_frame,segment_frame,clock_frame,original_rgba_hash,original_upper64_hash,captured,epoch,source_refresh,kind,split_row,owner_count,serial0,serial1,sky_decoded,source_sky_rgba_hash\n",logic_audit)<0)goto fail;}
 if(oracle_path){oracle=fopen(oracle_path,"rb");if(!oracle)goto fail;}if(audio_path){dump=fopen(audio_path,"wb");if(!dump)goto fail;}
 WNDCLASSA wc={0};wc.lpfnWndProc=proc;wc.hInstance=GetModuleHandle(NULL);wc.lpszClassName="NFSUGSourceNativeHost";wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.style=CS_OWNDC;if(!RegisterClassA(&wc)&&GetLastError()!=ERROR_CLASS_ALREADY_EXISTS)goto fail;window=CreateWindowA(wc.lpszClassName,"NFSUG source-native preview | original game timing",WS_OVERLAPPEDWINDOW,CW_USEDEFAULT,CW_USEDEFAULT,1216,839,NULL,NULL,wc.hInstance,NULL);if(!window)goto fail;
 stage="render thread startup";publish(NULL,1);thread=CreateThread(NULL,0,render_thread,NULL,0,NULL);if(!thread||WaitForSingleObject(render_ready,15000)!=WAIT_OBJECT_0||worker_error)goto fail;
 xi=LoadLibraryA("xinput1_4.dll");if(!xi)xi=LoadLibraryA("xinput9_1_0.dll");if(xi)symbol(xi,"XInputGetState",&getpad,sizeof(getpad));if(!hidden)ShowWindow(window,SW_SHOW);if(!no_audio)audio_init();timeBeginPeriod(1);if(!core.timing(game,base_timing)||base_timing[0]!=16777216||base_timing[1]!=280896)goto fail;
 stage="running";start=now();double next=start+280896.0/16777216.0,title=start;
 while(InterlockedCompareExchange(&running,0,0)&&(!selftest||frames<test_frames)){
  MSG msg;while(PeekMessage(&msg,NULL,0,0,PM_REMOVE)){TranslateMessage(&msg);DispatchMessage(&msg);}double t=now();
  EnterCriticalSection(&mutex);int busy=worker_busy;LeaveCriticalSection(&mutex);
  if(!reloaded&&((reload_at&&frames>=reload_at)||(reload_busy&&busy)))reload_pending=1;
  if(reload_pending){reload_pending=0;if(state){invalidate();audio_reset();if(!core.load(game,state,state_bytes)||!core.timing(game,base_timing))goto fail;segment=0;reloaded=1;if(oracle)rewind(oracle);publish(NULL,1);next=now()+280896.0/16777216.0;}}
  if(toggle_at&&frames>=toggle_at&&!toggled){EnterCriticalSection(&mutex);enabled=!enabled;LeaveCriticalSection(&mutex);invalidate();publish(NULL,1);toggled=1;}
  if(paused){next=t+280896.0/16777216.0;Sleep(2);continue;}
  if(fast||t>=next){double step_start=now();unsigned keys=script?scripted_input(segment,script):selftest?0:input(&pad);double core_start=now();if(core.step(game,keys)!=1)goto fail;measured(M_CORE,core_start);frames++;segment++;next+=280896.0/16777216.0;double audio_start=now();audio_drain(dump);measured(M_AUDIO,audio_start);uint64_t tick[4]={0};if(!core.timing(game,tick)||tick[0]!=16777216||tick[1]!=280896||tick[2]!=base_timing[2]+segment||tick[3]!=segment)timing_errors++;
   if(oracle){uint32_t expected[38400];if(fread(expected,1,sizeof(expected),oracle)!=sizeof(expected)||memcmp(expected,core.pixels(game),sizeof(expected)))original_mismatches++;}
   if(enabled){double capture_start=now();int synthetic_gap=capture_gap_steps&&frames>=capture_gap_at&&frames-capture_gap_at<capture_gap_steps;NFPCSourceFrame*frame=synthetic_gap?NULL:(reader?nf_pc_source_reader_capture(reader,64u*1024*1024):nf_pc_source_frame_capture(&api,64u*1024*1024));measured(M_CAPTURE,capture_start);if(!frame){uint64_t d[6]={5,0,0,0,0,0};if(reader&&!synthetic_gap)nf_pc_source_reader_last_failure(reader,d);if(!capture_failure_count)capture_failure_first_frame=frames;capture_failure_last_frame=frames;capture_failure_streak++;capture_failure_count++;if(capture_failure_streak>capture_failure_max_streak)capture_failure_max_streak=capture_failure_streak;unsigned kind=d[0]<5?(unsigned)d[0]:5;capture_failure_kind_counts[kind]++;if(capture_failure_log_count<32){capture_failure_log[capture_failure_log_count][0]=frames;memcpy(capture_failure_log[capture_failure_log_count]+1,d,sizeof(d));capture_failure_log_count++;}}else capture_failure_streak=0;logic_audit_record(frames,segment,tick[2],frame);publish(frame,1);}else{uint64_t display[5];int valid=enabled&&api.layer_info(game,display);EnterCriticalSection(&mutex);int same=valid&&display[0]==epoch;LeaveCriticalSection(&mutex);capture_failure_streak=0;logic_audit_record(frames,segment,tick[2],NULL);publish(NULL,!same);}measured(M_LOGIC,step_start);double cost=(now()-step_start)*1000;if(cost>max_step_ms)max_step_ms=cost;
  }else Sleep(1);
  if(!hidden&&t-title>=1){char text[256];EnterCriticalSection(&mutex);uint64_t np=native_presented,fp=fallback_presented;int native=enabled&&native_allowed;LeaveCriticalSection(&mutex);snprintf(text,sizeof(text),"NFSUG | %s | native %llu / original %llu presents | %s | F3 compare, Space pause, F1 help",native?"source-native endpoint":"original-display fallback",(unsigned long long)np,(unsigned long long)fp,pad?"Xbox connected":"keyboard");SetWindowTextA(window,text);title=t;}
 }
 elapsed=now()-start;
 if(selftest){double until=now()+15;for(;;){EnterCriticalSection(&mutex);int done=processed>=sequence;LeaveCriticalSection(&mutex);if(done||now()>=until)break;Sleep(1);}}
 if(logic_audit&&fflush(logic_audit))logic_audit_failed=1;
 result=(original_mismatches||timing_errors||present_failed||logic_audit_failed)?2:0;
fail:
 if(result&&worker_message[0]==0)snprintf(worker_message,sizeof(worker_message),"Startup stage: %s (Windows error %lu)",stage,(unsigned long)GetLastError());
 InterlockedExchange(&running,0);if(thread){WaitForSingleObject(thread,INFINITE);CloseHandle(thread);}if(reader){nf_pc_source_reader_direct_cached_info(reader,direct_cached_stats);nf_pc_source_reader_owned_geometry_info(reader,geometry_stats);nf_pc_source_reader_owned_background_info(reader,background_stats);nf_pc_source_reader_info(reader,reader_stats);nf_pc_source_reader_close(reader);reader=NULL;}if(game)core.close(game);if(audio_device){waveOutReset(audio_device);for(unsigned i=0;i<8;i++)waveOutUnprepareHeader(audio_device,wave+i,sizeof(WAVEHDR));waveOutClose(audio_device);}timeEndPeriod(1);nf_pc_source_frame_free(pending);pending=NULL;if(oracle)fclose(oracle);if(dump)fclose(dump);if(logic_audit){if(fclose(logic_audit)){logic_audit_failed=1;if(!result)result=2;}logic_audit=NULL;}free(logic_audit_sky);logic_audit_sky=NULL;free(state);
 if(background_lifetime_info&&(!background_lifetime_info(background_lifetime_stats)||background_lifetime_stats[0]!=background_lifetime_stats[1]))result=2;
 if(geometry_lifetime_info&&(!geometry_lifetime_info(geometry_lifetime_stats)||geometry_lifetime_stats[0]!=geometry_lifetime_stats[1]))result=2;
 if(geometry_cache_info&&(!geometry_cache_info(geometry_cache_stats)||geometry_cache_stats[0]||geometry_cache_stats[11]||geometry_cache_stats[6]>geometry_cache_stats[8]||geometry_cache_stats[7]>geometry_cache_stats[8]))result=2;
 if(report_path){FILE*f=fopen(report_path,"w");if(f){fprintf(f,"{\"scripted_input_mode\":%d,",script);fprintf(f,"\"startup_stage\":\"%s\",\"exit_code\":%d,\"logic_frames\":%llu,\"elapsed_seconds\":%.6f,\"max_logic_capture_ms\":%.3f,\"clock_hz\":16777216,\"cycles_per_step\":280896,\"timing_errors\":%u,\"original_frame_mismatches\":%u,\"published_frames\":%llu,\"mailbox_replacements\":%llu,\"prepared_scenes\":%llu,\"prepare_failures\":%llu,\"native_renders\":%llu,\"native_presents\":%llu,\"fallback_presents\":%llu,\"stale_rejections\":%llu,\"present_failures\":%llu,\"final_sequence\":%llu,\"processed_sequence\":%llu,\"audio_frames\":%llu,\"audio_dropped_frames\":%llu,\"audio_device_opened\":%s,\"controller_mapping_checks\":%s,\"xinput_loaded\":%s,\"reloaded\":%s,\"toggled\":%s,\"capture_native\":%s,\"render_thread_owns_gl\":true,\"live_readback\":false,\"capture_every_logic_steps\":1,\"full_scene_60fps\":false,\"automatic_save_writes\":false,\"renderer\":\"%s\",\"phases\":",stage,result,(unsigned long long)frames,elapsed,max_step_ms,timing_errors,original_mismatches,(unsigned long long)published,(unsigned long long)dropped,(unsigned long long)prepared,(unsigned long long)prepare_failed,(unsigned long long)rendered,(unsigned long long)native_presented,(unsigned long long)fallback_presented,(unsigned long long)stale_rejected,(unsigned long long)present_failed,(unsigned long long)sequence,(unsigned long long)processed,(unsigned long long)audio_frames,(unsigned long long)audio_dropped,audio_device?"true":"false",controller_check()?"true":"false",getpad?"true":"false",reloaded?"true":"false",toggled?"true":"false",capture_native?"true":"false",renderer_name);print_metrics(f);fprintf(f,",\"single_build_reader\":%s,\"reader_scratch_bytes\":%llu,\"reader_packet_builds\":%llu,\"reader_cached_copies\":%llu,\"reader_failed_builds\":%llu,\"reader_copied_bytes\":%llu,\"reader_largest_packet\":%llu",reader_enabled?"true":"false",(unsigned long long)reader_stats[0],(unsigned long long)reader_stats[1],(unsigned long long)reader_stats[2],(unsigned long long)reader_stats[3],(unsigned long long)reader_stats[4],(unsigned long long)reader_stats[5]);fprintf(f,",\"capture_gap_grace_steps\":%u,\"capture_gap_hold_frames\":%llu,\"capture_gap_fallback_count\":%llu,\"synthetic_capture_gap_at\":%llu,\"synthetic_capture_gap_steps\":%u",NFPC_CAPTURE_GAP_GRACE_STEPS,(unsigned long long)capture_gap_hold_frames,(unsigned long long)capture_gap_fallback_count,(unsigned long long)capture_gap_at,capture_gap_steps);fprintf(f,",\"capture_failure_count\":%llu,\"capture_failure_log_count\":%u,\"capture_failure_max_streak\":%llu,\"capture_failure_first_frame\":%llu,\"capture_failure_last_frame\":%llu,\"capture_failure_kind_counts\":[%llu,%llu,%llu,%llu,%llu,%llu],\"capture_failure_log\":[",(unsigned long long)capture_failure_count,capture_failure_log_count,(unsigned long long)capture_failure_max_streak,(unsigned long long)capture_failure_first_frame,(unsigned long long)capture_failure_last_frame,(unsigned long long)capture_failure_kind_counts[0],(unsigned long long)capture_failure_kind_counts[1],(unsigned long long)capture_failure_kind_counts[2],(unsigned long long)capture_failure_kind_counts[3],(unsigned long long)capture_failure_kind_counts[4],(unsigned long long)capture_failure_kind_counts[5]);for(unsigned j=0;j<capture_failure_log_count;j++){uint64_t*d=capture_failure_log[j];fprintf(f,"%s[%llu,%llu,%llu,%llu,%llu,%llu,%llu]",j?",":"",(unsigned long long)d[0],(unsigned long long)d[1],(unsigned long long)d[2],(unsigned long long)d[3],(unsigned long long)d[4],(unsigned long long)d[5],(unsigned long long)d[6]);}fputs("]",f);fprintf(f,",\"logic_audit_enabled\":%s,\"logic_audit_rows\":%llu,\"logic_audit_failed\":%s",logic_audit_path?"true":"false",(unsigned long long)logic_audit_rows,logic_audit_failed?"true":"false");fprintf(f,",\"owned_background_capture\":%s,\"background_transfer_attempts\":%llu,\"background_transfers\":%llu,\"background_transferred_bytes\":%llu",owned_background&&reader_enabled?"true":"false",(unsigned long long)background_stats[0],(unsigned long long)background_stats[1],(unsigned long long)background_stats[2]);fprintf(f,",\"background_allocations\":%llu,\"background_releases\":%llu",(unsigned long long)background_lifetime_stats[0],(unsigned long long)background_lifetime_stats[1]);fprintf(f,",\"owned_geometry_capture\":%s,\"geometry_transfer_attempts\":%llu,\"geometry_transfers\":%llu,\"geometry_transferred_bytes\":%llu,\"geometry_allocations\":%llu,\"geometry_releases\":%llu",owned_geometry&&reader_enabled?"true":"false",(unsigned long long)geometry_stats[0],(unsigned long long)geometry_stats[1],(unsigned long long)geometry_stats[2],(unsigned long long)geometry_lifetime_stats[0],(unsigned long long)geometry_lifetime_stats[1]);fprintf(f,",\"direct_cached_capture\":%s,\"cached_size_queries\":%llu,\"cached_final_writes\":%llu,\"cached_final_write_bytes\":%llu",direct_cached&&reader_enabled?"true":"false",(unsigned long long)direct_cached_stats[0],(unsigned long long)direct_cached_stats[1],(unsigned long long)direct_cached_stats[2]);fprintf(f,",\"geometry_cache_enabled\":%s,\"geometry_cache_statistics\":[",geometry_cache&&reader_enabled?"true":"false");for(unsigned j=0;j<12;j++)fprintf(f,"%s%llu",j?",":"",(unsigned long long)geometry_cache_stats[j]);fputs("]",f);fprintf(f,",\"audio_queue_observations\":%llu,\"audio_queue_empty_observations\":%llu,\"audio_queue_empty_events\":%llu,\"audio_queue_min_buffers\":%u,\"audio_queue_max_buffers\":%u,\"audio_queue_empty_pcm_frames\":[",(unsigned long long)audio_queue_polls,(unsigned long long)audio_queue_empty_polls,(unsigned long long)audio_queue_empty_events,audio_queue_polls?audio_queue_min:0,audio_queue_max);for(unsigned j=0;j<audio_queue_log_count;j++)fprintf(f,"%s%llu",j?",":"",(unsigned long long)audio_queue_empty_pcm[j]);fputs("],\"audio_queue_empty_context\":[",f);for(unsigned j=0;j<audio_queue_log_count;j++){const uint64_t*c=audio_queue_empty_context[j];fprintf(f,"%s{\"pcm_frame\":%llu,\"poll_interval_ms\":%.6f,\"previous_pcm_frame\":%llu,\"previous_queued_buffers\":%llu,\"previous_pending_frames\":%llu,\"pending_frames\":%llu,\"previous_poll_valid\":%s}",j?",":"",(unsigned long long)audio_queue_empty_pcm[j],audio_queue_empty_interval_ms[j],(unsigned long long)c[0],(unsigned long long)c[1],(unsigned long long)c[2],(unsigned long long)c[3],c[4]?"true":"false");}fputs("]",f);fprintf(f,",\"audio_duration_queries\":%llu,\"audio_duration_valid\":%llu,\"audio_duration_unknown\":%llu",(unsigned long long)audio_duration_queries,(unsigned long long)audio_duration_valid,(unsigned long long)audio_duration_unknown);fprintf(f,",\"presentation_sync\":{\"observed\":%s,\"setter_available\":%lld,\"getter_available\":%lld,\"requested_interval\":%lld,\"cached_interval\":%lld,\"reported_interval\":%lld,\"set_attempts\":%lld,\"set_failures\":%lld,\"readbacks\":%lld,\"visible_presents\":%lld,\"hidden_presents\":%lld}",swap_info_valid?"true":"false",(long long)swap_info[0],(long long)swap_info[1],(long long)swap_info[2],(long long)swap_info[3],(long long)swap_info[4],(long long)swap_info[5],(long long)swap_info[6],(long long)swap_info[7],(long long)swap_info[8],(long long)swap_info[9]);fputs("}\n",f);fclose(f);}}
 if(result&&!hidden)MessageBoxA(window,worker_message[0]?worker_message:"Preview could not start. Check the ROM, checkpoint and packaged DLLs.","NFSUG preview",MB_ICONERROR);
 if(window)DestroyWindow(window);
 if(xi)FreeLibrary(xi);
 if(dll)FreeLibrary(dll);
 if(wake)CloseHandle(wake);
 if(render_ready)CloseHandle(render_ready);
 DeleteCriticalSection(&presentation_mutex);DeleteCriticalSection(&mutex);return result;
}

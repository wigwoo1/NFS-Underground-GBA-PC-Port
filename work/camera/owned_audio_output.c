#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <mmsystem.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#define API __declspec(dllexport)
#define SLOTS 32
#define FRAMES 4096
typedef struct {WAVEHDR header;int16_t pcm[FRAMES*2];unsigned state,frames;uint64_t epoch,generation,refresh,first_sample,deadline,sequence;} Block;
typedef struct {CRITICAL_SECTION lock;HANDLE stop,wake,thread;HWAVEOUT device;DWORD producer;unsigned rate,capacity,ready,error,paused,cleanup_ok,started;uint64_t epoch,generation,applied,next_sample,last_refresh,last_deadline,sequence,accepted,submitted,completed,retired;uint64_t last_submission[8],position[8];unsigned position_valid,position_enabled;uint64_t position_next_query;Block blocks[SLOTS];} Audio;
API uint64_t nf_audio_output_now(void){LARGE_INTEGER t,f;QueryPerformanceCounter(&t);QueryPerformanceFrequency(&f);return (uint64_t)(t.QuadPart*1000000000.0/f.QuadPart);}
static DWORD WINAPI run(void*arg){
 Audio*a=arg;WAVEFORMATEX format={WAVE_FORMAT_PCM,2,a->rate,a->rate*4,4,16,0};MMRESULT error=waveOutOpen(&a->device,WAVE_MAPPER,&format,0,0,CALLBACK_NULL);
 unsigned prepared=0;if(!error)for(;prepared<a->capacity;prepared++){Block*b=a->blocks+prepared;b->header.lpData=(char*)b->pcm;b->header.dwBufferLength=sizeof(b->pcm);error=waveOutPrepareHeader(a->device,&b->header,sizeof(WAVEHDR));if(error)break;}
 EnterCriticalSection(&a->lock);a->error=error;a->ready=!error;a->applied=a->generation;LeaveCriticalSection(&a->lock);SetEvent(a->wake);
 HANDLE events[2]={a->stop,a->wake};
 while(!error&&WaitForSingleObject(a->stop,0)!=WAIT_OBJECT_0){
  EnterCriticalSection(&a->lock);uint64_t wanted=a->generation;int reset=wanted!=a->applied;LeaveCriticalSection(&a->lock);
  if(reset){
   error=waveOutReset(a->device);
   EnterCriticalSection(&a->lock);
   if(!error){for(unsigned i=0;i<a->capacity;i++){Block*b=a->blocks+i;if(b->state){a->retired+=b->frames;b->state=0;}}a->applied=wanted;a->started=0;}else a->error=error;
   LeaveCriticalSection(&a->lock);continue;
  }
  /* Device position is advisory driver evidence, never an audible timestamp.
     Read outside producer lock; publish only in the matching reset generation. */
  EnterCriticalSection(&a->lock);uint64_t query_now=nf_audio_output_now();int query=a->position_enabled&&query_now>=a->position_next_query;if(query)a->position_next_query=query_now+100000000;LeaveCriticalSection(&a->lock);
  if(query){
  MMTIME position={0};position.wType=TIME_SAMPLES;
  uint64_t position_begin=nf_audio_output_now();MMRESULT position_error=waveOutGetPosition(a->device,&position,sizeof(position));uint64_t position_end=nf_audio_output_now();
  EnterCriticalSection(&a->lock);
  if(a->position_enabled&&wanted==a->generation&&wanted==a->applied){uint64_t values[8]={a->epoch,wanted,position.wType,position.u.sample,position_begin,position_end,position_error,a->position[7]+1};memcpy(a->position,values,sizeof(values));a->position_valid=1;}
  LeaveCriticalSection(&a->lock);
  }
  EnterCriticalSection(&a->lock);Block*next=NULL;
  for(unsigned i=0;i<a->capacity;i++){Block*b=a->blocks+i;if(b->state==2&&(b->header.dwFlags&WHDR_DONE)){a->completed+=b->frames;b->state=0;}if(b->state==1&&(!next||b->sequence<next->sequence))next=b;}
  uint64_t now=nf_audio_output_now();unsigned wait=4;
  if(next&&!a->paused&&next->generation==a->generation){if(a->started||now>=next->deadline){next->state=2;next->header.dwBufferLength=next->frames*4;}else{uint64_t ms=(next->deadline-now)/1000000;wait=ms>4?4:(unsigned)ms+1;next=NULL;}}else next=NULL;
  LeaveCriticalSection(&a->lock);
  /* Gate generation onset only. Subsequent contiguous PCM must be queued
     ahead for continuous device-rate playback; per-chunk just-in-time writes
     introduce avoidable underruns. Deadlines retain intended sample timing. */
  if(next){
   uint64_t write_begin=nf_audio_output_now();error=waveOutWrite(a->device,&next->header,sizeof(WAVEHDR));uint64_t write_end=nf_audio_output_now();
   EnterCriticalSection(&a->lock);if(error)a->error=error;else{a->started=1;a->submitted+=next->frames;uint64_t event[8]={next->epoch,next->generation,next->refresh,next->first_sample,next->frames,next->deadline,write_begin,write_end};memcpy(a->last_submission,event,sizeof(event));}LeaveCriticalSection(&a->lock);continue;
  }
  WaitForMultipleObjects(2,events,FALSE,wait);
 }
 int cleanup=1;
 if(a->device){if(waveOutReset(a->device))cleanup=0;for(unsigned i=0;i<prepared;i++)if(waveOutUnprepareHeader(a->device,&a->blocks[i].header,sizeof(WAVEHDR)))cleanup=0;if(cleanup&&waveOutClose(a->device))cleanup=0;}
 EnterCriticalSection(&a->lock);a->ready=0;a->cleanup_ok=cleanup;if(!cleanup&&!a->error)a->error=0xffffffffu;LeaveCriticalSection(&a->lock);return 0;
}
API Audio*nf_audio_output_create(uint64_t epoch,unsigned rate,unsigned capacity){
 if(!epoch||(rate!=44100&&rate!=48000)||capacity<2||capacity>SLOTS)return NULL;
 Audio*a=calloc(1,sizeof(*a));if(!a)return NULL;InitializeCriticalSection(&a->lock);a->epoch=epoch;a->generation=1;a->rate=rate;a->capacity=capacity;a->producer=GetCurrentThreadId();
 a->stop=CreateEvent(NULL,TRUE,FALSE,NULL);a->wake=CreateEvent(NULL,FALSE,FALSE,NULL);
 if(a->stop&&a->wake)a->thread=CreateThread(NULL,0,run,a,0,NULL);
 if(!a->thread){if(a->stop)CloseHandle(a->stop);if(a->wake)CloseHandle(a->wake);DeleteCriticalSection(&a->lock);free(a);return NULL;}return a;
}
/* Status values: 1 accepted, 0 not ready/paused, -1 invalid input, -2 stale,
   -3 busy lock, -4 full, -5 device failed. No producer/device waits or borrowing. */
API int nf_audio_output_push(Audio*a,uint64_t epoch,uint64_t generation,uint64_t refresh,uint64_t first_sample,uint64_t deadline,const int16_t*pcm,unsigned frames){
 if(!a||!pcm||!frames||frames>FRAMES||a->producer!=GetCurrentThreadId())return -1;
 if(!TryEnterCriticalSection(&a->lock))return -3;
 int result=0;Block*b=NULL;
 if(a->error)result=-5;
 else if(epoch!=a->epoch||generation!=a->generation)result=-2;
 else if(first_sample!=a->next_sample||refresh<a->last_refresh||deadline<a->last_deadline)result=-1;
 else if(a->ready&&!a->paused&&a->applied==a->generation){
  for(unsigned i=0;i<a->capacity;i++)if(!a->blocks[i].state){b=a->blocks+i;break;}
  if(!b)result=-4;
  else{memcpy(b->pcm,pcm,frames*4);b->frames=frames;b->epoch=epoch;b->generation=generation;b->refresh=refresh;b->first_sample=first_sample;b->deadline=deadline;b->sequence=++a->sequence;b->state=1;a->next_sample+=frames;a->last_refresh=refresh;a->last_deadline=deadline;a->accepted+=frames;result=1;}
 }
 LeaveCriticalSection(&a->lock);if(result==1)SetEvent(a->wake);return result;
}
/* Retire is asynchronous; resume is prohibited until worker/device flush ack. */
API uint64_t nf_audio_output_retire(Audio*a,uint64_t epoch){
 if(!a||!epoch||a->producer!=GetCurrentThreadId())return 0;
 EnterCriticalSection(&a->lock);uint64_t result=0;if(epoch>=a->epoch&&!a->error){a->paused=1;a->position_valid=0;memset(a->position,0,sizeof(a->position));a->epoch=epoch;result=++a->generation;a->next_sample=a->last_refresh=a->last_deadline=0;}LeaveCriticalSection(&a->lock);SetEvent(a->wake);return result;
}
API int nf_audio_output_resume(Audio*a,uint64_t epoch,uint64_t generation){
 if(!a||a->producer!=GetCurrentThreadId())return 0;EnterCriticalSection(&a->lock);int ok=a->ready&&!a->error&&epoch==a->epoch&&generation==a->generation&&generation==a->applied;if(ok)a->paused=0;LeaveCriticalSection(&a->lock);return ok;
}
/* epoch,generation,flush_ack,ready,error,paused,occupied,accepted,submitted,
   device_completed,retired,next_sample,producer_id,worker_id. */
API int nf_audio_output_status(Audio*a,uint64_t out[14]){
 if(!a||!out)return 0;EnterCriticalSection(&a->lock);unsigned occupied=0;for(unsigned i=0;i<a->capacity;i++)occupied+=a->blocks[i].state!=0;
 uint64_t values[14]={a->epoch,a->generation,a->applied,a->ready,a->error,a->paused,occupied,a->accepted,a->submitted,a->completed,a->retired,a->next_sample,a->producer,GetThreadId(a->thread)};memcpy(out,values,sizeof(values));LeaveCriticalSection(&a->lock);return 1;
}
/* Last device submission evidence, not a hardware audible timestamp. */
API int nf_audio_output_last_submission(Audio*a,uint64_t out[8]){if(!a||!out)return 0;EnterCriticalSection(&a->lock);memcpy(out,a->last_submission,sizeof(a->last_submission));LeaveCriticalSection(&a->lock);return 1;}
/* epoch, reset generation, returned MMTIME type, raw 32-bit position,
   query begin/end QPC ns, MMRESULT, publication sequence. No units assumed
   when a driver returns a different type. Position may wrap at 32 bits. */
/* Optional diagnostic driver call may block: off in normal playback. */
API int nf_audio_output_position_enable(Audio*a,int enabled){
 if(!a||a->producer!=GetCurrentThreadId()||(enabled!=0&&enabled!=1))return 0;
 EnterCriticalSection(&a->lock);a->position_enabled=enabled;a->position_valid=0;a->position_next_query=0;memset(a->position,0,sizeof(a->position));LeaveCriticalSection(&a->lock);SetEvent(a->wake);return 1;
}
API int nf_audio_output_position(Audio*a,uint64_t epoch,uint64_t generation,uint64_t out[8]){
 if(!a||!out)return 0;int ok=0;EnterCriticalSection(&a->lock);
 if(a->position_valid&&epoch==a->epoch&&generation==a->generation&&generation==a->applied){memcpy(out,a->position,sizeof(a->position));ok=1;}
 LeaveCriticalSection(&a->lock);return ok;
}
/* Diagnostic owned pending copy: no output playback or borrowing. */
API int nf_audio_output_pending_read(Audio*a,uint64_t epoch,uint64_t generation,uint64_t first_sample,int16_t*out,unsigned capacity,unsigned*frames){
 if(!a||!out||!frames)return 0;int ok=0;EnterCriticalSection(&a->lock);
 if(epoch==a->epoch&&generation==a->generation)for(unsigned i=0;i<a->capacity;i++){Block*b=a->blocks+i;if(b->state==1&&b->generation==generation&&b->first_sample==first_sample){if(capacity>=b->frames){memcpy(out,b->pcm,b->frames*4);*frames=b->frames;ok=1;}break;}}
 LeaveCriticalSection(&a->lock);return ok;
}
/* Failed joins/device cleanup retain resources; caller must not free or reuse. */
API int nf_audio_output_close(Audio*a,unsigned timeout){
 if(!a||a->producer!=GetCurrentThreadId()||timeout>5000)return 0;SetEvent(a->stop);SetEvent(a->wake);if(WaitForSingleObject(a->thread,timeout)!=WAIT_OBJECT_0||!a->cleanup_ok)return 0;
 CloseHandle(a->thread);CloseHandle(a->stop);CloseHandle(a->wake);DeleteCriticalSection(&a->lock);free(a);return 1;
}

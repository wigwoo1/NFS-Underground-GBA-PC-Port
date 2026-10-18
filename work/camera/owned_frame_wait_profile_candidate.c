#include <windows.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
typedef struct {CRITICAL_SECTION lock,presentation;uint64_t epoch,generation;unsigned count,closed,capacity,paused;void*frames[8];size_t sizes[8];uint64_t last_sample[8];unsigned sample_valid;} NFOwnedFrameHandoff;
__declspec(dllexport) void*nf_owned_handoff_create(uint64_t epoch){if(!epoch)return NULL;NFOwnedFrameHandoff*q=calloc(1,sizeof(*q));if(q){InitializeCriticalSection(&q->lock);InitializeCriticalSection(&q->presentation);q->epoch=epoch;q->generation=1;q->capacity=3;}return q;}
__declspec(dllexport) void*nf_owned_handoff_create_capacity(uint64_t epoch,unsigned capacity){if(!capacity||capacity>8)return NULL;NFOwnedFrameHandoff*q=nf_owned_handoff_create(epoch);if(q)q->capacity=capacity;return q;}
static void drain(NFOwnedFrameHandoff*q){for(unsigned i=0;i<q->count;i++)free(q->frames[i]);q->count=0;}
/* Copies complete immutable frame; no caller memory retained. Bounded FIFO. */
static int handoff_push(NFOwnedFrameHandoff*q,const void*p,size_t n,uint64_t*timing,uint64_t*v2){
 LARGE_INTEGER begin,locked,copied,end,frequency,vbegin,eliglocked,eligend,copyend,finalbegin;if(timing){memset(timing,0,4*sizeof(uint64_t));QueryPerformanceFrequency(&frequency);QueryPerformanceCounter(&begin);}
 if(v2){memset(v2,0,8*sizeof(uint64_t));QueryPerformanceFrequency(&frequency);QueryPerformanceCounter(&vbegin);}
 if(!q||!p||n<40||n>0x1000000){return 0;}
 uint32_t h[6];uint64_t epoch,ticks;memcpy(h,p,24);memcpy(&epoch,(const uint8_t*)p+24,8);memcpy(&ticks,(const uint8_t*)p+32,8);
 if(h[0]!=0x3346474e||!epoch||ticks!=(uint64_t)h[1]*280896||h[3]!=160*34944u||h[4]!=76800||h[5]!=76800||40ull+h[2]+h[3]+h[4]+h[5]!=n)return 0;
 int ok=0;uint64_t generation;
 EnterCriticalSection(&q->lock);if(v2)QueryPerformanceCounter(&eliglocked);int eligible=!q->closed&&!q->paused&&q->epoch==epoch&&q->count<q->capacity;generation=q->generation;LeaveCriticalSection(&q->lock);if(v2)QueryPerformanceCounter(&eligend);
 if(!eligible)return 0;
 void*copy=malloc(n);if(!copy)return 0;memcpy(copy,p,n);if(v2){QueryPerformanceCounter(&copyend);QueryPerformanceCounter(&finalbegin);}
 EnterCriticalSection(&q->lock);if(timing||v2)QueryPerformanceCounter(&locked);
 if(!q->closed&&!q->paused&&q->epoch==epoch&&q->generation==generation&&q->count<q->capacity){q->frames[q->count]=copy;q->sizes[q->count++]=n;copy=NULL;ok=1;}
 if(timing||v2){QueryPerformanceCounter(&copied);}
 LeaveCriticalSection(&q->lock);free(copy);
 if(v2){QueryPerformanceCounter(&end);v2[0]=eliglocked.QuadPart-vbegin.QuadPart;v2[1]=eligend.QuadPart-eliglocked.QuadPart;v2[2]=copyend.QuadPart-eligend.QuadPart;v2[3]=locked.QuadPart-finalbegin.QuadPart;v2[4]=copied.QuadPart-locked.QuadPart;v2[5]=end.QuadPart-vbegin.QuadPart;v2[6]=frequency.QuadPart;v2[7]=generation;}
 if(timing){QueryPerformanceCounter(&end);timing[0]=locked.QuadPart-begin.QuadPart;timing[1]=copied.QuadPart-locked.QuadPart;timing[2]=end.QuadPart-begin.QuadPart;timing[3]=frequency.QuadPart;}return ok;
}
__declspec(dllexport) int nf_owned_handoff_push(NFOwnedFrameHandoff*q,const void*p,size_t n){return handoff_push(q,p,n,NULL,NULL);}
__declspec(dllexport) int nf_owned_handoff_push_timed(NFOwnedFrameHandoff*q,const void*p,size_t n,uint64_t*timing){if(!timing)return 0;return handoff_push(q,p,n,timing,NULL);}
/* Consumer receives exclusive ownership; epoch changes cannot free popped data. */
__declspec(dllexport) void*nf_owned_handoff_pop(NFOwnedFrameHandoff*q,size_t*size){if(!q||!size)return NULL;void*p=NULL;EnterCriticalSection(&q->lock);if(q->count){p=q->frames[0];*size=q->sizes[0];q->count--;memmove(q->frames,q->frames+1,q->count*sizeof(void*));memmove(q->sizes,q->sizes+1,q->count*sizeof(size_t));}LeaveCriticalSection(&q->lock);return p;}
__declspec(dllexport) void nf_owned_frame_free(void*p){free(p);}
__declspec(dllexport) int nf_owned_handoff_epoch(NFOwnedFrameHandoff*q,uint64_t epoch){if(!q||!epoch)return 0;int ok=0;EnterCriticalSection(&q->presentation);EnterCriticalSection(&q->lock);if(!q->closed&&epoch>=q->epoch){if(epoch!=q->epoch){drain(q);q->epoch=epoch;q->generation++;q->sample_valid=0;memset(q->last_sample,0,sizeof(q->last_sample));}ok=1;}LeaveCriticalSection(&q->lock);LeaveCriticalSection(&q->presentation);return ok;}
/* Presentation serializes with epoch/pause/close. Queue lock is released
   before the callback so producer pushes can proceed during presentation.
   Lock order is presentation then queue; callbacks must not mutate lifecycle. */
__declspec(dllexport) int nf_owned_handoff_commit(NFOwnedFrameHandoff*q,uint64_t epoch,int(*fn)(void*),void*ctx){if(!q||!fn)return -1;int ok=0;EnterCriticalSection(&q->presentation);EnterCriticalSection(&q->lock);int valid=!q->closed&&!q->paused&&epoch==q->epoch;LeaveCriticalSection(&q->lock);if(valid)ok=fn(ctx)?1:-1;LeaveCriticalSection(&q->presentation);return ok;}
__declspec(dllexport) void nf_owned_handoff_close(NFOwnedFrameHandoff*q){if(!q)return;EnterCriticalSection(&q->presentation);EnterCriticalSection(&q->lock);q->closed=1;drain(q);LeaveCriticalSection(&q->lock);LeaveCriticalSection(&q->presentation);}
/* Join producer/consumer before destroy. */
__declspec(dllexport) void nf_owned_handoff_destroy(NFOwnedFrameHandoff*q){if(q){nf_owned_handoff_close(q);DeleteCriticalSection(&q->presentation);DeleteCriticalSection(&q->lock);free(q);}}

/* Pause retires pending content and invalidates already popped commit tokens.
   Popped ownership remains consumer's; resume cannot revive old content. */
__declspec(dllexport) int nf_owned_handoff_pause(NFOwnedFrameHandoff*q,unsigned paused){if(!q||paused>1)return 0;int ok=0;EnterCriticalSection(&q->presentation);EnterCriticalSection(&q->lock);if(!q->closed){if(q->paused!=paused){q->paused=paused;q->generation++;drain(q);}ok=1;}LeaveCriticalSection(&q->lock);LeaveCriticalSection(&q->presentation);return ok;}
__declspec(dllexport) void*nf_owned_handoff_pop_token(NFOwnedFrameHandoff*q,size_t*size,uint64_t*generation){if(!q||!size||!generation)return NULL;void*p=NULL;EnterCriticalSection(&q->lock);if(!q->paused&&q->count){p=q->frames[0];*size=q->sizes[0];*generation=q->generation;q->count--;memmove(q->frames,q->frames+1,q->count*sizeof(void*));memmove(q->sizes,q->sizes+1,q->count*sizeof(size_t));}LeaveCriticalSection(&q->lock);return p;}
__declspec(dllexport) int nf_owned_handoff_commit_token(NFOwnedFrameHandoff*q,uint64_t epoch,uint64_t generation,int(*fn)(void*),void*ctx){if(!q||!fn)return -1;int ok=0;EnterCriticalSection(&q->presentation);EnterCriticalSection(&q->lock);int valid=!q->closed&&!q->paused&&epoch==q->epoch&&generation==q->generation;LeaveCriticalSection(&q->lock);if(valid)ok=fn(ctx)?1:-1;LeaveCriticalSection(&q->presentation);return ok;}

/* Diagnostic token commit: same lock order and validation; no timing shared
   between callers. Outputs raw QPC ticks and frequency, including callback. */
__declspec(dllexport) int nf_owned_handoff_commit_token_timed(NFOwnedFrameHandoff*q,uint64_t epoch,uint64_t generation,int(*fn)(void*),void*ctx,uint64_t*out){
 if(!out){return -1;}
 memset(out,0,6*sizeof(uint64_t));if(!q||!fn)return -1;
 LARGE_INTEGER a,b,c,d,e,f,h;QueryPerformanceFrequency(&h);QueryPerformanceCounter(&a);
 EnterCriticalSection(&q->presentation);QueryPerformanceCounter(&b);
 EnterCriticalSection(&q->lock);QueryPerformanceCounter(&c);
 int valid=!q->closed&&!q->paused&&epoch==q->epoch&&generation==q->generation;
 LeaveCriticalSection(&q->lock);QueryPerformanceCounter(&d);
 int ok=valid?(fn(ctx)?1:-1):0;QueryPerformanceCounter(&e);
 LeaveCriticalSection(&q->presentation);QueryPerformanceCounter(&f);
 out[0]=b.QuadPart-a.QuadPart;out[1]=c.QuadPart-b.QuadPart;out[2]=d.QuadPart-c.QuadPart;out[3]=e.QuadPart-d.QuadPart;out[4]=f.QuadPart-a.QuadPart;out[5]=h.QuadPart;return ok;
}

__declspec(dllexport) int nf_owned_handoff_push_stages(NFOwnedFrameHandoff*q,const void*p,size_t n,uint64_t*out){if(!out)return 0;return handoff_push(q,p,n,NULL,out);}

/* Exact comparison against independent immutable producer storage. No locks,
   device calls, allocation or borrowed pointer retained; bounded16MiB. */
__declspec(dllexport) int nf_owned_frame_matches(const void*native,size_t n,const void*owned,size_t owned_n){
 if(!native||!owned||n<40||n>0x1000000||n!=owned_n)return 0;
 return memcmp(native,owned,n)==0;
}

/* Nonblocking pop: -1 invalid, -2 busy, 0 empty/paused, 1 ownership transfer.
   No output mutation unless a complete token was transferred. */
__declspec(dllexport) int nf_owned_handoff_try_pop_token(NFOwnedFrameHandoff*q,void**frame,size_t*size,uint64_t*generation){
 if(!q||!frame||!size||!generation)return -1;
 if(!TryEnterCriticalSection(&q->lock))return -2;
 int result=0;if(!q->paused&&q->count){*frame=q->frames[0];*size=q->sizes[0];*generation=q->generation;q->count--;memmove(q->frames,q->frames+1,q->count*sizeof(void*));memmove(q->sizes,q->sizes+1,q->count*sizeof(size_t));result=1;}
 LeaveCriticalSection(&q->lock);return result;
}

/* Cancelable original-clock wait outside the presentation/publication locks.
   1 deadline reached, 0 retired token, -1 invalid; no presentation here.
   Timing: begin_ns, requested deadline_ns, return_ns, sleep count. */
static uint64_t owned_qpc_ns(LARGE_INTEGER frequency){LARGE_INTEGER t;QueryPerformanceCounter(&t);return (uint64_t)(t.QuadPart*1000000000.0/frequency.QuadPart);}
static __thread uint64_t wait_profile[12];
__declspec(dllexport) int nf_wait_profile_read(uint64_t*out){if(!out)return 0;memcpy(out,wait_profile,sizeof(wait_profile));return 1;}
__declspec(dllexport) int nf_owned_handoff_wait_token(NFOwnedFrameHandoff*q,uint64_t epoch,uint64_t generation,uint64_t deadline,uint64_t*out){
 if(!q||!epoch||!generation||!out)return -1;
 LARGE_INTEGER frequency;QueryPerformanceFrequency(&frequency);uint64_t begin=owned_qpc_ns(frequency),sleeps=0;
 out[0]=begin;out[1]=deadline;out[2]=begin;out[3]=0;
 if(deadline>begin&&deadline-begin>2000000000ull)return -1;
 HANDLE timer=NULL;memset(wait_profile,0,sizeof(wait_profile));wait_profile[0]=begin;wait_profile[2]=deadline;ULONG64 cycle_begin=0,cycle_end=0;int cycles_ok=QueryThreadCycleTime(GetCurrentThread(),&cycle_begin);
 if(deadline>begin){timer=CreateWaitableTimerExW(NULL,NULL,2,TIMER_ALL_ACCESS);wait_profile[8]=!!timer;if(!timer){timer=CreateWaitableTimerW(NULL,FALSE,NULL);wait_profile[9]=!!timer;}}
 int result;
 for(;;){
  uint64_t lock_begin=owned_qpc_ns(frequency);EnterCriticalSection(&q->lock);int valid=!q->closed&&!q->paused&&epoch==q->epoch&&generation==q->generation;LeaveCriticalSection(&q->lock);uint64_t lock_elapsed=owned_qpc_ns(frequency)-lock_begin;if(lock_elapsed>wait_profile[4])wait_profile[4]=lock_elapsed;
  if(!valid){result=0;break;}
  uint64_t now=owned_qpc_ns(frequency);if(now>=deadline){result=1;break;}
  uint64_t remaining=deadline-now,slice=remaining>2000000?2000000:remaining;
  LARGE_INTEGER due;due.QuadPart=-(LONGLONG)((slice+99)/100);
  uint64_t sleep_begin=owned_qpc_ns(frequency);int armed=timer&&SetWaitableTimer(timer,&due,0,NULL,NULL,FALSE);if(!armed){wait_profile[10]++;Sleep(1);}else if(WaitForSingleObject(timer,INFINITE)!=WAIT_OBJECT_0){wait_profile[11]++;Sleep(1);}uint64_t elapsed=owned_qpc_ns(frequency)-sleep_begin;wait_profile[6]+=elapsed;if(elapsed>wait_profile[5])wait_profile[5]=elapsed;
  sleeps++;
 }
 if(timer)CloseHandle(timer);
 out[2]=owned_qpc_ns(frequency);out[3]=sleeps;wait_profile[1]=out[2];wait_profile[7]=sleeps;cycles_ok=QueryThreadCycleTime(GetCurrentThread(),&cycle_end)&&cycles_ok;wait_profile[3]=cycles_ok?cycle_end-cycle_begin:UINT64_MAX;return result;
}

/* Atomic metadata of actual successful presentation: epoch,generation,
   older/newer refresh,display index,double alpha bits,completionQPCns,serial.
   Publication occurs while lifecycle is excluded by presentation lock. */
static int handoff_commit_sample(NFOwnedFrameHandoff*q,uint64_t epoch,uint64_t generation,uint64_t older,uint64_t newer,uint64_t index,double alpha,int(*fn)(void*),void*ctx,uint64_t*out,uint64_t*stages){
 if(!q||!fn||!out||!epoch||!generation||older>=newer||newer>UINT32_MAX||!isfinite(alpha)||alpha<0||alpha>1)return -1;
 LARGE_INTEGER stage_frequency;if(stages){QueryPerformanceFrequency(&stage_frequency);stages[0]=owned_qpc_ns(stage_frequency);}
 EnterCriticalSection(&q->presentation);if(stages)stages[1]=owned_qpc_ns(stage_frequency);
 EnterCriticalSection(&q->lock);if(stages)stages[2]=owned_qpc_ns(stage_frequency);
 int valid=!q->closed&&!q->paused&&q->epoch==epoch&&q->generation==generation;
 int order=!q->sample_valid||(q->last_sample[4]!=UINT64_MAX&&index==q->last_sample[4]+1);
 LeaveCriticalSection(&q->lock);
 if(stages)stages[3]=owned_qpc_ns(stage_frequency);
 int result=valid?(order?(fn(ctx)?1:-1):-1):0;
 if(stages)stages[4]=owned_qpc_ns(stage_frequency);
 if(result==1){
  LARGE_INTEGER frequency;QueryPerformanceFrequency(&frequency);uint64_t finished=owned_qpc_ns(frequency),bits;memcpy(&bits,&alpha,sizeof(bits));
  EnterCriticalSection(&q->lock);uint64_t serial=q->sample_valid?q->last_sample[7]+1:1;
  uint64_t sample[8]={epoch,generation,older,newer,index,bits,finished,serial};memcpy(q->last_sample,sample,sizeof(sample));q->sample_valid=1;memcpy(out,sample,sizeof(sample));LeaveCriticalSection(&q->lock);
 }
 if(stages)stages[5]=owned_qpc_ns(stage_frequency);
 LeaveCriticalSection(&q->presentation);if(stages)stages[6]=owned_qpc_ns(stage_frequency);return result;
}
__declspec(dllexport) int nf_owned_handoff_commit_sample(NFOwnedFrameHandoff*q,uint64_t epoch,uint64_t generation,uint64_t older,uint64_t newer,uint64_t index,double alpha,int(*fn)(void*),void*ctx,uint64_t*out){return handoff_commit_sample(q,epoch,generation,older,newer,index,alpha,fn,ctx,out,NULL);}
/* Optional absolute QPC nanoseconds: entry,presentation lock,queue lock,
   validation done,callback done,publication done,presentation released. */
__declspec(dllexport) int nf_owned_handoff_commit_sample_stages(NFOwnedFrameHandoff*q,uint64_t epoch,uint64_t generation,uint64_t older,uint64_t newer,uint64_t index,double alpha,int(*fn)(void*),void*ctx,uint64_t*out,uint64_t*stages){if(!stages)return -1;return handoff_commit_sample(q,epoch,generation,older,newer,index,alpha,fn,ctx,out,stages);}
__declspec(dllexport) int nf_owned_handoff_last_sample(NFOwnedFrameHandoff*q,uint64_t*out){
 if(!q||!out){return 0;}
 EnterCriticalSection(&q->lock);int valid=!q->closed&&q->sample_valid&&q->last_sample[0]==q->epoch;if(valid)memcpy(out,q->last_sample,sizeof(q->last_sample));LeaveCriticalSection(&q->lock);return valid;
}

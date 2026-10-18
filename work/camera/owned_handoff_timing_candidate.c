#include <windows.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
typedef struct {CRITICAL_SECTION lock,presentation;uint64_t epoch,generation;unsigned count,closed,capacity,paused;void*frames[8];size_t sizes[8];} NFOwnedFrameHandoff;
__declspec(dllexport) void*nf_owned_handoff_create(uint64_t epoch){if(!epoch)return NULL;NFOwnedFrameHandoff*q=calloc(1,sizeof(*q));if(q){InitializeCriticalSection(&q->lock);InitializeCriticalSection(&q->presentation);q->epoch=epoch;q->generation=1;q->capacity=3;}return q;}
__declspec(dllexport) void*nf_owned_handoff_create_capacity(uint64_t epoch,unsigned capacity){if(!capacity||capacity>8)return NULL;NFOwnedFrameHandoff*q=nf_owned_handoff_create(epoch);if(q)q->capacity=capacity;return q;}
static void drain(NFOwnedFrameHandoff*q){for(unsigned i=0;i<q->count;i++)free(q->frames[i]);q->count=0;}
/* Copies complete immutable frame; no caller memory retained. Bounded FIFO. */
static int handoff_push(NFOwnedFrameHandoff*q,const void*p,size_t n,uint64_t*timing){
 LARGE_INTEGER begin,locked,copied,end,frequency;if(timing){memset(timing,0,4*sizeof(uint64_t));QueryPerformanceFrequency(&frequency);QueryPerformanceCounter(&begin);}
 if(!q||!p||n<40||n>0x1000000)return 0;uint32_t h[6];uint64_t epoch,ticks;memcpy(h,p,24);memcpy(&epoch,(const uint8_t*)p+24,8);memcpy(&ticks,(const uint8_t*)p+32,8);
 if(h[0]!=0x3346474e||!epoch||ticks!=(uint64_t)h[1]*280896||h[3]!=160*34944u||h[4]!=76800||h[5]!=76800||40ull+h[2]+h[3]+h[4]+h[5]!=n)return 0;
 int ok=0;EnterCriticalSection(&q->lock);if(timing)QueryPerformanceCounter(&locked);if(!q->closed&&!q->paused&&q->epoch==epoch&&q->count<q->capacity){void*copy=malloc(n);if(copy){memcpy(copy,p,n);q->frames[q->count]=copy;q->sizes[q->count++]=n;ok=1;}}if(timing)QueryPerformanceCounter(&copied);LeaveCriticalSection(&q->lock);if(timing){QueryPerformanceCounter(&end);timing[0]=locked.QuadPart-begin.QuadPart;timing[1]=copied.QuadPart-locked.QuadPart;timing[2]=end.QuadPart-begin.QuadPart;timing[3]=frequency.QuadPart;}return ok;
}
__declspec(dllexport) int nf_owned_handoff_push(NFOwnedFrameHandoff*q,const void*p,size_t n){return handoff_push(q,p,n,NULL);}
__declspec(dllexport) int nf_owned_handoff_push_timed(NFOwnedFrameHandoff*q,const void*p,size_t n,uint64_t*timing){if(!timing)return 0;return handoff_push(q,p,n,timing);}
/* Consumer receives exclusive ownership; epoch changes cannot free popped data. */
__declspec(dllexport) void*nf_owned_handoff_pop(NFOwnedFrameHandoff*q,size_t*size){if(!q||!size)return NULL;void*p=NULL;EnterCriticalSection(&q->lock);if(q->count){p=q->frames[0];*size=q->sizes[0];q->count--;memmove(q->frames,q->frames+1,q->count*sizeof(void*));memmove(q->sizes,q->sizes+1,q->count*sizeof(size_t));}LeaveCriticalSection(&q->lock);return p;}
__declspec(dllexport) void nf_owned_frame_free(void*p){free(p);}
__declspec(dllexport) int nf_owned_handoff_epoch(NFOwnedFrameHandoff*q,uint64_t epoch){if(!q||!epoch)return 0;int ok=0;EnterCriticalSection(&q->presentation);EnterCriticalSection(&q->lock);if(!q->closed&&epoch>=q->epoch){if(epoch!=q->epoch){drain(q);q->epoch=epoch;q->generation++;}ok=1;}LeaveCriticalSection(&q->lock);LeaveCriticalSection(&q->presentation);return ok;}
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
 if(!out)return -1;memset(out,0,6*sizeof(uint64_t));if(!q||!fn)return -1;
 LARGE_INTEGER a,b,c,d,e,f,h;QueryPerformanceFrequency(&h);QueryPerformanceCounter(&a);
 EnterCriticalSection(&q->presentation);QueryPerformanceCounter(&b);
 EnterCriticalSection(&q->lock);QueryPerformanceCounter(&c);
 int valid=!q->closed&&!q->paused&&epoch==q->epoch&&generation==q->generation;
 LeaveCriticalSection(&q->lock);QueryPerformanceCounter(&d);
 int ok=valid?(fn(ctx)?1:-1):0;QueryPerformanceCounter(&e);
 LeaveCriticalSection(&q->presentation);QueryPerformanceCounter(&f);
 out[0]=b.QuadPart-a.QuadPart;out[1]=c.QuadPart-b.QuadPart;out[2]=d.QuadPart-c.QuadPart;out[3]=e.QuadPart-d.QuadPart;out[4]=f.QuadPart-a.QuadPart;out[5]=h.QuadPart;return ok;
}

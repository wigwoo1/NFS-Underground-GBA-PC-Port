#include <math.h>
#define nf_d3d_close nf_d3d_floor_original_close
#include "owned_d3d_clock_present_batch_candidate.c"
#undef nf_d3d_close
/* Called only after source preparation, on the D3D owner thread.
   The supplied original authority owns all cancellation/order/pause locks.
   Both callbacks are native: no Python entry at the presentation deadline. */
typedef int (*NFTransaction)(void*,uint64_t,uint64_t,uint64_t,uint64_t,uint64_t,double,uint64_t,int(*)(void*),void*,int(*)(void*),void*,uint64_t*,uint64_t*,uint64_t*);
typedef struct { HWND window; uint64_t *batch; int batch_result; unsigned calls; uint64_t epoch,generation,index; } NFPresentContext;

static HANDLE floor_timer;static uint64_t floor_last,floor_epoch,floor_generation,floor_index,floor_calls,floor_waits,floor_wait_ns,floor_max_wait,floor_resets;
static int floor_wait(uint64_t epoch,uint64_t generation,uint64_t index){
 if(epoch!=floor_epoch||generation!=floor_generation||index<=floor_index){floor_last=0;floor_epoch=epoch;floor_generation=generation;floor_resets++;}
 floor_index=index;floor_calls++;uint64_t begin=draw_profile_ns();
 if(floor_last&&begin<floor_last+16666667ULL){
  if(!floor_timer)floor_timer=CreateWaitableTimerExW(NULL,NULL,2,TIMER_ALL_ACCESS);
  if(!floor_timer)return 0;
  uint64_t due_ns=floor_last+16666667ULL;floor_waits++;
  for(;;){uint64_t now=draw_profile_ns();if(now>=due_ns)break;LARGE_INTEGER due;due.QuadPart=-(LONGLONG)((due_ns-now+99)/100);if(!SetWaitableTimer(floor_timer,&due,0,NULL,NULL,FALSE)||WaitForSingleObject(floor_timer,100)!=WAIT_OBJECT_0)return 0;}
  uint64_t elapsed=draw_profile_ns()-begin;floor_wait_ns+=elapsed;if(elapsed>floor_max_wait)floor_max_wait=elapsed;
 }
 return 1;
}
__declspec(dllexport) int nf_d3d_floor_stats(uint64_t*out,size_t bytes){if(!out||bytes!=64)return 1;uint64_t x[8]={floor_calls,floor_waits,floor_wait_ns,floor_max_wait,floor_resets,floor_index,floor_last,floor_timer!=NULL};memcpy(out,x,64);return 0;}
__declspec(dllexport) int nf_d3d_close(void){int status=nf_d3d_floor_original_close();if(!status){if(floor_timer)CloseHandle(floor_timer);floor_timer=NULL;floor_last=0;floor_epoch=floor_generation=floor_index=0;}return status;}
static int nf_prepared_native(void*unused){return 0;}
static int nf_present_native(void*opaque){
 NFPresentContext*c=opaque;c->calls++;
 if(!floor_wait(c->epoch,c->generation,c->index))return 0;
 uint64_t admitted=draw_profile_ns();
 c->batch_result=nf_d3d_present_batch(c->window,c->batch,27*sizeof(uint64_t));
 if(c->batch_result==0&&c->batch[0]==0)floor_last=admitted;
 return c->batch_result==0&&c->batch[0]==0;
}
__declspec(dllexport) int nf_d3d_native_transaction(
 NFTransaction authority,void*owner,HWND window,uint64_t epoch,uint64_t generation,
 uint64_t older,uint64_t newer,uint64_t index,double alpha,uint64_t deadline,
 uint64_t*out,size_t bytes){
 /* 8 commit + 4 wait + 7 commit stages + 27 batch + callback count/result.
    Rejected arguments do not modify caller memory. */
 if(!valid()||!authority||!owner||!window||!out||bytes!=48*sizeof(uint64_t)
 ||!epoch||!generation||older>=newer||newer>UINT32_MAX||!isfinite(alpha)||alpha<0||alpha>1)return -2;
 memset(out,0,bytes);
 NFPresentContext context={window,out+19,-1,0,epoch,generation,index};
 int result=authority(owner,epoch,generation,older,newer,index,alpha,deadline,
 nf_prepared_native,NULL,nf_present_native,&context,out,out+8,out+12);
 out[46]=context.calls;out[47]=(uint64_t)(int64_t)context.batch_result;
 return result;
}


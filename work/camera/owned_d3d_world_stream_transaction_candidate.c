#include <math.h>
#include "owned_d3d_world_stream_batch_candidate.c"
/* Called only after source preparation, on the D3D owner thread.
   The supplied original authority owns all cancellation/order/pause locks.
   Both callbacks are native: no Python entry at the presentation deadline. */
typedef int (*NFTransaction)(void*,uint64_t,uint64_t,uint64_t,uint64_t,uint64_t,double,uint64_t,int(*)(void*),void*,int(*)(void*),void*,uint64_t*,uint64_t*,uint64_t*);
typedef struct { HWND window; uint64_t *batch; int batch_result; unsigned calls; } NFPresentContext;
static int nf_prepared_native(void*unused){return 0;}
static int nf_present_native(void*opaque){
 NFPresentContext*c=opaque;c->calls++;
 c->batch_result=nf_d3d_present_batch(c->window,c->batch,27*sizeof(uint64_t));
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
 NFPresentContext context={window,out+19,-1,0};
 int result=authority(owner,epoch,generation,older,newer,index,alpha,deadline,
 nf_prepared_native,NULL,nf_present_native,&context,out,out+8,out+12);
 out[46]=context.calls;out[47]=(uint64_t)(int64_t)context.batch_result;
 return result;
}

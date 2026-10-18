#include "owned_frame_handoff.c"
/* Caller must execute on the graphics owner thread and retain both DLLs.
   The native no-argument graphics function returns 0 for S_OK,3 for occlusion.
   No Python callback is entered after the deadline wait. */
typedef int (*NativePresentFn)(void);
typedef struct {NativePresentFn fn;int status;} NativePresentContext;
static int native_present_bridge(void*p){NativePresentContext*c=p;c->status=c->fn();return c->status==0;}
__declspec(dllexport) int nf_owned_native_deadline_present(NFOwnedFrameHandoff*q,uint64_t epoch,uint64_t generation,uint64_t older,uint64_t newer,uint64_t index,double alpha,uint64_t deadline,NativePresentFn fn,uint64_t*out,uint64_t*wait,uint64_t*stages,int*status){
 if(!q||!fn||!out||!wait||!stages||!status||!epoch||!generation||older>=newer||newer>UINT32_MAX||!isfinite(alpha)||alpha<0||alpha>1)return -1;
 *status=-999;int ready=nf_owned_handoff_wait_token(q,epoch,generation,deadline,wait);if(ready!=1)return ready;
 NativePresentContext c={fn,-999};int result=handoff_commit_sample(q,epoch,generation,older,newer,index,alpha,native_present_bridge,&c,out,stages);*status=c.status;return result;
}

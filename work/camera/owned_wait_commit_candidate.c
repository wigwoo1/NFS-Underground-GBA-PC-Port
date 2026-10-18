#include "owned_frame_handoff.c"
/* Keep pacing and sample publication in one native call. Caller retains all
   callback owners and publication exclusion through return. */
__declspec(dllexport) int nf_owned_handoff_wait_commit_sample(NFOwnedFrameHandoff*q,uint64_t epoch,uint64_t generation,uint64_t older,uint64_t newer,uint64_t index,double alpha,uint64_t deadline,int(*present)(void*),void*ctx,uint64_t*out,uint64_t*waitout,uint64_t*stages){
 if(!q||!present||!out||!waitout||!stages||!epoch||!generation||older>=newer||newer>UINT32_MAX||!isfinite(alpha)||alpha<0||alpha>1)return -1;
 int ready=nf_owned_handoff_wait_token(q,epoch,generation,deadline,waitout);
 if(ready!=1)return ready;
 return handoff_commit_sample(q,epoch,generation,older,newer,index,alpha,present,ctx,out,stages);
}

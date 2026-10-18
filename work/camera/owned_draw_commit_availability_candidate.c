#include "owned_frame_handoff_precise_candidate.c"
static int(*display_initialize)(void);static int(*display_poll)(unsigned);
__declspec(dllexport) int nf_owned_display_availability_configure(int(*initialize)(void),int(*poll)(unsigned)){if(!initialize||!poll)return 0;display_initialize=initialize;display_poll=poll;return 1;}
/* Draw releases lifecycle exclusion; wait and commit revalidate cancellation.
   Renderer callbacks must return zero for draw success, one for present success. */
__declspec(dllexport) int nf_owned_handoff_draw_wait_commit_sample(NFOwnedFrameHandoff*q,uint64_t epoch,uint64_t generation,uint64_t older,uint64_t newer,uint64_t index,double alpha,uint64_t deadline,int(*draw)(void*),void*drawctx,int(*present)(void*),void*presentctx,uint64_t*out,uint64_t*waitout,uint64_t*stages){
 if(!q||!draw||!present||!out||!waitout||!stages||!epoch||!generation||older>=newer||newer>UINT32_MAX||!isfinite(alpha)||alpha<0||alpha>1)return -1;
 uint64_t eligibility[4];int ready=nf_owned_handoff_wait_token(q,epoch,generation,0,eligibility);
 if(ready!=1)return ready;
 if(!display_initialize||!display_poll||display_initialize()!=0)return -1;
 /* Availability waits never hold queue/presentation exclusion. Recheck the
    generation after every bounded poll, including the successful one. */
 LARGE_INTEGER availability_frequency;QueryPerformanceFrequency(&availability_frequency);
 uint64_t availability_begin=owned_qpc_ns(availability_frequency);
 for(;;){
  if(owned_qpc_ns(availability_frequency)-availability_begin>2000000000ull)return -1;
  int available=display_poll(2);if(available<0)return -1;
  ready=nf_owned_handoff_wait_token(q,epoch,generation,0,eligibility);
  if(ready!=1)return ready;
  if(available==1)break;
 }
 if(draw(drawctx)!=0)return -1;
 ready=nf_owned_handoff_wait_token(q,epoch,generation,deadline,waitout);
 if(ready!=1)return ready;
 return handoff_commit_sample(q,epoch,generation,older,newer,index,alpha,present,presentctx,out,stages);
}


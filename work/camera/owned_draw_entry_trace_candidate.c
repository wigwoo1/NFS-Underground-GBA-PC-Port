#include "owned_frame_handoff.c"
static _Thread_local uint64_t entry_trace[9];
__declspec(dllexport) void nf_owned_entry_trace(uint64_t*out){memcpy(out,entry_trace,sizeof(entry_trace));}
/* Draw releases lifecycle exclusion; wait and commit revalidate cancellation.
   Renderer callbacks must return zero for draw success, one for present success. */
__declspec(dllexport) int nf_owned_handoff_draw_wait_commit_sample(NFOwnedFrameHandoff*q,uint64_t epoch,uint64_t generation,uint64_t older,uint64_t newer,uint64_t index,double alpha,uint64_t deadline,int(*draw)(void*),void*drawctx,int(*present)(void*),void*presentctx,uint64_t*out,uint64_t*waitout,uint64_t*stages){
 LARGE_INTEGER trace_frequency;QueryPerformanceFrequency(&trace_frequency);memset(entry_trace,0,sizeof(entry_trace));entry_trace[0]=owned_qpc_ns(trace_frequency);
 if(!q||!draw||!present||!out||!waitout||!stages||!epoch||!generation||older>=newer||newer>UINT32_MAX||!isfinite(alpha)||alpha<0||alpha>1)return -1;
 entry_trace[1]=owned_qpc_ns(trace_frequency);uint64_t eligibility[4];int ready=nf_owned_handoff_wait_token(q,epoch,generation,0,eligibility);
 entry_trace[2]=owned_qpc_ns(trace_frequency);if(ready!=1)return ready;
 entry_trace[3]=owned_qpc_ns(trace_frequency);if(draw(drawctx)!=0)return -1;
 entry_trace[4]=owned_qpc_ns(trace_frequency);entry_trace[5]=owned_qpc_ns(trace_frequency);ready=nf_owned_handoff_wait_token(q,epoch,generation,deadline,waitout);entry_trace[6]=owned_qpc_ns(trace_frequency);
 if(ready!=1)return ready;
 entry_trace[7]=owned_qpc_ns(trace_frequency);int result=handoff_commit_sample(q,epoch,generation,older,newer,index,alpha,present,presentctx,out,stages);entry_trace[8]=owned_qpc_ns(trace_frequency);return result;
}

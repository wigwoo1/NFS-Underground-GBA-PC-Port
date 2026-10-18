#include "owned_frame_handoff_precise_candidate.c"
static int(*display_initialize)(void);static int(*display_poll)(unsigned);
__declspec(dllexport) int nf_owned_display_availability_configure(int(*initialize)(void),int(*poll)(unsigned)){if(!initialize||!poll)return 0;display_initialize=initialize;display_poll=poll;return 1;}
static uint64_t availability_rows[10000][14];static unsigned availability_count,availability_dropped;
__declspec(dllexport) unsigned nf_owned_availability_count(void){return availability_count;}
__declspec(dllexport) unsigned nf_owned_availability_dropped(void){return availability_dropped;}
__declspec(dllexport) int nf_owned_availability_read(unsigned i,uint64_t*out){if(!out||i>=availability_count)return 0;memcpy(out,availability_rows[i],sizeof(availability_rows[i]));return 1;}
/* Draw releases lifecycle exclusion; wait and commit revalidate cancellation.
   Renderer callbacks must return zero for draw success, one for present success. */
__declspec(dllexport) int nf_owned_handoff_draw_wait_commit_sample(NFOwnedFrameHandoff*q,uint64_t epoch,uint64_t generation,uint64_t older,uint64_t newer,uint64_t index,double alpha,uint64_t deadline,int(*draw)(void*),void*drawctx,int(*present)(void*),void*presentctx,uint64_t*out,uint64_t*waitout,uint64_t*stages){
 if(!q||!draw||!present||!out||!waitout||!stages||!epoch||!generation||older>=newer||newer>UINT32_MAX||!isfinite(alpha)||alpha<0||alpha>1)return -1;
 LARGE_INTEGER trace_frequency;QueryPerformanceFrequency(&trace_frequency);
 uint64_t trace[14]={epoch,generation,older,newer,index,deadline,owned_qpc_ns(trace_frequency),0,0,0,0,0,0,0};
 #define TRACE_RETURN(value) do{int trace_result=(value);trace[11]=owned_qpc_ns(trace_frequency);trace[12]=(int64_t)trace_result;if(availability_count<10000)memcpy(availability_rows[availability_count++],trace,sizeof(trace));else availability_dropped++;return trace_result;}while(0)
 uint64_t eligibility[4];int ready=nf_owned_handoff_wait_token(q,epoch,generation,0,eligibility);
 if(ready!=1)TRACE_RETURN(ready);
 if(!display_initialize||!display_poll||display_initialize()!=0)TRACE_RETURN(-1);
 trace[7]=owned_qpc_ns(trace_frequency);
 /* Availability waits never hold queue/presentation exclusion. Recheck the
    generation after every bounded poll, including the successful one. */
 LARGE_INTEGER availability_frequency;QueryPerformanceFrequency(&availability_frequency);
 uint64_t availability_begin=owned_qpc_ns(availability_frequency);
 for(;;){
  if(owned_qpc_ns(availability_frequency)-availability_begin>2000000000ull)TRACE_RETURN(-1);
  int available=display_poll(2);trace[13]++;if(available<0)TRACE_RETURN(-1);
  ready=nf_owned_handoff_wait_token(q,epoch,generation,0,eligibility);
  if(ready!=1)TRACE_RETURN(ready);
  if(available==1)break;
 }
 trace[8]=owned_qpc_ns(trace_frequency);
 if(draw(drawctx)!=0)TRACE_RETURN(-1);
 trace[9]=owned_qpc_ns(trace_frequency);
 ready=nf_owned_handoff_wait_token(q,epoch,generation,deadline,waitout);
 if(ready!=1)TRACE_RETURN(ready);
 trace[10]=owned_qpc_ns(trace_frequency);
 TRACE_RETURN(handoff_commit_sample(q,epoch,generation,older,newer,index,alpha,present,presentctx,out,stages));
 #undef TRACE_RETURN
}


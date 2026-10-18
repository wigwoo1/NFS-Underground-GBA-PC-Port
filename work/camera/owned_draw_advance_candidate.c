#include "owned_presentation_advance_candidate.c"
/* Exact ceil(index*1e9/60), avoiding multiplication overflow. */
static int advance_deadline(uint64_t origin,uint64_t index,uint64_t*out){
 uint64_t seconds=index/60,tail=((index%60)*1000000000ull+59)/60;
 if(seconds>(UINT64_MAX-tail)/1000000000ull)return 0;
 uint64_t offset=seconds*1000000000ull+tail;if(origin>UINT64_MAX-offset)return 0;
 *out=origin+offset;return 1;
}
/* No game update API. Deadline authority is original presentation origin/grid.
   Return -2 when skipped slots are not yet obsolete; no draw/present occurs. */
__declspec(dllexport) int nf_owned_handoff_draw_wait_advance_sample(NFOwnedFrameHandoff*q,uint64_t epoch,uint64_t generation,uint64_t older,uint64_t newer,uint64_t index,double alpha,uint64_t origin,uint64_t previous,int(*draw)(void*),void*drawctx,int(*present)(void*),void*presentctx,uint64_t*out,uint64_t*waitout,uint64_t*stages,uint64_t*audit){
 if(!q||!draw||!present||!out||!waitout||!stages||!audit||!epoch||!generation||older>=newer||newer>UINT32_MAX||!isfinite(alpha)||alpha<0||alpha>1||previous>=UINT64_MAX-1||index<=previous+1)return -1;
 uint64_t skipped_deadline,deadline;if(!advance_deadline(origin,index-1,&skipped_deadline)||!advance_deadline(origin,index,&deadline))return -1;
 uint64_t eligibility[4];int ready=nf_owned_handoff_wait_token(q,epoch,generation,0,eligibility);if(ready!=1)return ready;
 EnterCriticalSection(&q->lock);int order=q->sample_valid&&q->last_sample[4]==previous;LeaveCriticalSection(&q->lock);if(!order)return -1;
 LARGE_INTEGER frequency;QueryPerformanceFrequency(&frequency);uint64_t observed=owned_qpc_ns(frequency);
 if(observed<skipped_deadline)return -2;
 if(draw(drawctx)!=0)return -1;
 ready=nf_owned_handoff_wait_token(q,epoch,generation,deadline,waitout);if(ready!=1)return ready;
 int result=nf_owned_handoff_commit_sample_advance(q,epoch,generation,older,newer,index,alpha,present,presentctx,out,stages,previous,audit);
 if(result==1){audit[2]=skipped_deadline;audit[3]=observed;}return result;
}

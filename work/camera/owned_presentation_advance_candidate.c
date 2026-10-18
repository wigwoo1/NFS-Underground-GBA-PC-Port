/* Opt-in explicit display advancement; base ABI and strict commit unchanged.
   Audit published only with successful callback; no game frame/update API. */
#include "owned_frame_handoff.c"
__declspec(dllexport) int nf_owned_handoff_commit_sample_advance(NFOwnedFrameHandoff*q,uint64_t epoch,uint64_t generation,uint64_t older,uint64_t newer,uint64_t index,double alpha,int(*fn)(void*),void*ctx,uint64_t*out,uint64_t*stages,uint64_t expected_previous,uint64_t*audit){
 if(!q||!fn||!out||!audit||!epoch||!generation||older>=newer||newer>UINT32_MAX||!isfinite(alpha)||alpha<0||alpha>1)return -1;
 LARGE_INTEGER stage_frequency;if(stages){QueryPerformanceFrequency(&stage_frequency);stages[0]=owned_qpc_ns(stage_frequency);}
 EnterCriticalSection(&q->presentation);if(stages)stages[1]=owned_qpc_ns(stage_frequency);
 EnterCriticalSection(&q->lock);if(stages)stages[2]=owned_qpc_ns(stage_frequency);
 int valid=!q->closed&&!q->paused&&q->epoch==epoch&&q->generation==generation;
 int order=q->sample_valid&&q->last_sample[4]==expected_previous&&expected_previous!=UINT64_MAX&&index>expected_previous;
 LeaveCriticalSection(&q->lock);
 if(stages)stages[3]=owned_qpc_ns(stage_frequency);
 int result=valid?(order?(fn(ctx)?1:-1):-1):0;
 if(stages)stages[4]=owned_qpc_ns(stage_frequency);
 if(result==1){
  LARGE_INTEGER frequency;QueryPerformanceFrequency(&frequency);uint64_t finished=owned_qpc_ns(frequency),bits;memcpy(&bits,&alpha,sizeof(bits));
  EnterCriticalSection(&q->lock);uint64_t serial=q->sample_valid?q->last_sample[7]+1:1;
  uint64_t sample[8]={epoch,generation,older,newer,index,bits,finished,serial};memcpy(q->last_sample,sample,sizeof(sample));q->sample_valid=1;memcpy(out,sample,sizeof(sample));audit[0]=expected_previous;audit[1]=index-expected_previous-1;LeaveCriticalSection(&q->lock);
 }
 if(stages)stages[5]=owned_qpc_ns(stage_frequency);
 LeaveCriticalSection(&q->presentation);if(stages)stages[6]=owned_qpc_ns(stage_frequency);return result;
}

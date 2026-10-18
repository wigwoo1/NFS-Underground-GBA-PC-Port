#include "owned_draw_commit_candidate.c"
typedef struct {uint64_t older,newer,index,deadline;double alpha;void*drawctx;void*presentctx;} NFBatchSample;
/* Synchronous borrowed contexts: caller retains complete frame/pose/sky owners
   until return. No thread creation or pointer retention. Successful prefix is
   published individually; uncommitted suffix remains caller-owned for replay. */
__declspec(dllexport) size_t nf_owned_batch_sample_size(void){return sizeof(NFBatchSample);}
__declspec(dllexport) int nf_owned_handoff_batch(NFOwnedFrameHandoff*q,uint64_t epoch,uint64_t generation,const NFBatchSample*items,unsigned count,int(*draw)(void*),int(*present)(void*),uint64_t*samples,uint64_t*waits,uint64_t*stages,unsigned*completed){
 if(!q||!items||!draw||!present||!samples||!waits||!stages||!completed||!epoch||!generation||!count||count>8)return -1;
 for(unsigned i=0;i<count;i++){
  const NFBatchSample*x=items+i;
  if(x->older>=x->newer||x->newer>UINT32_MAX||!isfinite(x->alpha)||x->alpha<0||x->alpha>1)return -1;
  if(i&&(items[i-1].index==UINT64_MAX||x->index!=items[i-1].index+1||x->deadline<items[i-1].deadline))return -1;
 }
 *completed=0;
 for(unsigned i=0;i<count;i++){
  const NFBatchSample*x=items+i;
  int result=nf_owned_handoff_draw_wait_commit_sample(q,epoch,generation,x->older,x->newer,x->index,x->alpha,x->deadline,draw,x->drawctx,present,x->presentctx,samples+8*i,waits+4*i,stages+7*i);
  if(result!=1)return result;
  *completed=i+1;
 }
 return 1;
}

/* Pause/last-commit snapshot under the same lifecycle exclusion. Metadata:
   generation,has_sample,ack_QPC_ns. No Python publication lock required. */
__declspec(dllexport) int nf_owned_handoff_pause_snapshot(NFOwnedFrameHandoff*q,unsigned paused,uint64_t*sample,uint64_t*metadata){
 if(!q||paused>1||!sample||!metadata)return 0;
 int ok=0;EnterCriticalSection(&q->presentation);EnterCriticalSection(&q->lock);
 if(!q->closed){
  if(q->paused!=paused){q->paused=paused;q->generation++;drain(q);}
  uint64_t copy[8]={0};int has=q->sample_valid&&q->last_sample[0]==q->epoch;
  if(has)memcpy(copy,q->last_sample,sizeof(copy));
  LARGE_INTEGER frequency;QueryPerformanceFrequency(&frequency);
  uint64_t info[3]={q->generation,has,owned_qpc_ns(frequency)};
  memcpy(sample,copy,sizeof(copy));memcpy(metadata,info,sizeof(info));ok=1;
 }
 LeaveCriticalSection(&q->lock);LeaveCriticalSection(&q->presentation);return ok;
}

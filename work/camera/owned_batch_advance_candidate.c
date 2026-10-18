#include "owned_draw_advance_candidate.c"
/* Draw releases lifecycle exclusion; wait and commit revalidate cancellation.
   Renderer callbacks must return zero for draw success, one for present success. */
__declspec(dllexport) int nf_owned_handoff_draw_wait_commit_sample(NFOwnedFrameHandoff*q,uint64_t epoch,uint64_t generation,uint64_t older,uint64_t newer,uint64_t index,double alpha,uint64_t deadline,int(*draw)(void*),void*drawctx,int(*present)(void*),void*presentctx,uint64_t*out,uint64_t*waitout,uint64_t*stages){
 if(!q||!draw||!present||!out||!waitout||!stages||!epoch||!generation||older>=newer||newer>UINT32_MAX||!isfinite(alpha)||alpha<0||alpha>1)return -1;
 uint64_t eligibility[4];int ready=nf_owned_handoff_wait_token(q,epoch,generation,0,eligibility);
 if(ready!=1)return ready;
 if(draw(drawctx)!=0)return -1;
 ready=nf_owned_handoff_wait_token(q,epoch,generation,deadline,waitout);
 if(ready!=1)return ready;
 return handoff_commit_sample(q,epoch,generation,older,newer,index,alpha,present,presentctx,out,stages);
}

typedef struct {uint64_t older,newer,index,deadline;double alpha;void*drawctx;void*presentctx;} NFBatchSample;
/* Synchronous borrowed contexts: caller retains complete frame/pose/sky owners
   until return. No thread creation or pointer retention. Successful prefix is
   published individually; uncommitted suffix remains caller-owned for replay. */
__declspec(dllexport) size_t nf_owned_batch_sample_size(void){return sizeof(NFBatchSample);}
__declspec(dllexport) int nf_owned_handoff_batch_advance(NFOwnedFrameHandoff*q,uint64_t epoch,uint64_t generation,const NFBatchSample*items,unsigned count,int(*draw)(void*),int(*present)(void*),uint64_t*samples,uint64_t*waits,uint64_t*stages,unsigned*completed,uint64_t origin,uint64_t*audits){
 if(!q||!items||!draw||!present||!samples||!waits||!stages||!completed||!audits||!epoch||!generation||!count||count>8)return -1;
 for(unsigned i=0;i<count;i++){
  const NFBatchSample*x=items+i;
  uint64_t exact;if(!advance_deadline(origin,x->index,&exact)||exact!=x->deadline)return -1;
  if(x->older>=x->newer||x->newer>UINT32_MAX||!isfinite(x->alpha)||x->alpha<0||x->alpha>1)return -1;
  if(i&&(items[i-1].index==UINT64_MAX||x->index!=items[i-1].index+1||x->deadline<items[i-1].deadline))return -1;
 }
 *completed=0;
 for(unsigned i=0;i<count;i++){
  const NFBatchSample*x=items+i;
  uint64_t previous[8];int has=nf_owned_handoff_last_sample(q,previous);int result;
  if(has&&previous[4]!=UINT64_MAX&&x->index>previous[4]+1){
   result=nf_owned_handoff_draw_wait_advance_sample(q,epoch,generation,x->older,x->newer,x->index,x->alpha,origin,previous[4],draw,x->drawctx,present,x->presentctx,samples+8*i,waits+4*i,stages+7*i,audits+4*i);
  }else{
   result=nf_owned_handoff_draw_wait_commit_sample(q,epoch,generation,x->older,x->newer,x->index,x->alpha,x->deadline,draw,x->drawctx,present,x->presentctx,samples+8*i,waits+4*i,stages+7*i);
   if(result==1){audits[4*i]=has?previous[4]:UINT64_MAX;audits[4*i+1]=0;audits[4*i+2]=0;audits[4*i+3]=0;}
  }
  if(result!=1)return result;
  *completed=i+1;
 }
 return 1;
}


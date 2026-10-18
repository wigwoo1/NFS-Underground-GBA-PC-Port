#include "owned_draw_wait_profile_candidate.c"
typedef struct {uint64_t older,newer,index,deadline;double alpha;void*drawctx;void*presentctx;} NFBatchSample;
/* Synchronous borrowed contexts: caller retains complete frame/pose/sky owners
   until return. No thread creation or pointer retention. Successful prefix is
   published individually; uncommitted suffix remains caller-owned for replay. */
__declspec(dllexport) size_t nf_owned_batch_sample_size(void){return sizeof(NFBatchSample);}
static DWORD gate_owner;
static uint64_t gate_timing[40];
static uint64_t gate_breakdown[48];
__declspec(dllexport) int nf_owned_ready_breakdown(uint64_t*out){if(!out||gate_owner!=GetCurrentThreadId())return 0;memcpy(out,gate_breakdown,sizeof(gate_breakdown));return 1;}
__declspec(dllexport) int nf_owned_ready_timing(uint64_t*out){if(!out||gate_owner!=GetCurrentThreadId())return 0;memcpy(out,gate_timing,sizeof(gate_timing));return 1;}
static int gate_noop_draw(void*ctx){(void)ctx;return 0;}
__declspec(dllexport) int nf_owned_handoff_batch_ready(NFOwnedFrameHandoff*q,uint64_t epoch,uint64_t generation,const NFBatchSample*items,unsigned count,int(*draw)(void*),int(*present)(void*),uint64_t*samples,uint64_t*waits,uint64_t*stages,unsigned*completed,int(*ready)(void*),void*readyctx){
 if(!q||!items||!draw||!present||!ready||!samples||!waits||!stages||!completed||!epoch||!generation||!count||count>8)return -1;
 for(unsigned i=0;i<count;i++){
  const NFBatchSample*x=items+i;
  if(x->older>=x->newer||x->newer>UINT32_MAX||!isfinite(x->alpha)||x->alpha<0||x->alpha>1)return -1;
  if(i&&(items[i-1].index==UINT64_MAX||x->index!=items[i-1].index+1||x->deadline<items[i-1].deadline))return -1;
 }
 *completed=0;gate_owner=GetCurrentThreadId();memset(gate_timing,0,sizeof(gate_timing));memset(gate_breakdown,0,sizeof(gate_breakdown));
 LARGE_INTEGER gate_frequency;QueryPerformanceFrequency(&gate_frequency);
 for(unsigned i=0;i<count;i++){
  const NFBatchSample*x=items+i;
  uint64_t eligibility[4];int valid=nf_owned_handoff_wait_token(q,epoch,generation,0,eligibility);
  if(valid!=1)return valid;
  uint64_t*t=gate_timing+5*i;t[0]=owned_qpc_ns(gate_frequency);
  if(draw(x->drawctx)!=0)return -1;
  t[1]=owned_qpc_ns(gate_frequency);
  uint64_t*b=gate_breakdown+6*i;
  for(;;){
   uint64_t started=owned_qpc_ns(gate_frequency);
   valid=nf_owned_handoff_wait_token(q,epoch,generation,0,eligibility);uint64_t checked=owned_qpc_ns(gate_frequency);uint64_t duration=checked-started;b[0]+=duration;if(duration>b[1])b[1]=duration;if(valid!=1)return valid;
   int status=ready(readyctx);t[3]++;t[2]=owned_qpc_ns(gate_frequency);duration=t[2]-checked;b[2]+=duration;if(duration>b[3])b[3]=duration;t[4]=(uint64_t)(int64_t)status;if(status==1)break;if(status!=0)return -1;
   started=owned_qpc_ns(gate_frequency);Sleep(1);duration=owned_qpc_ns(gate_frequency)-started;b[4]+=duration;if(duration>b[5])b[5]=duration;
  }
  int result=nf_owned_handoff_draw_wait_commit_sample(q,epoch,generation,x->older,x->newer,x->index,x->alpha,x->deadline,gate_noop_draw,NULL,present,x->presentctx,samples+8*i,waits+4*i,stages+7*i);
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

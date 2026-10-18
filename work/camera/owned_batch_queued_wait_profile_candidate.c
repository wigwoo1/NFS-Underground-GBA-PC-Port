#include "owned_batch_ready_wait_profile_candidate.c"
static uint64_t queued_wait_profiles[96];
__declspec(dllexport) int nf_owned_queued_wait_profiles(uint64_t*out);
static DWORD queued_owner;static uint64_t queued_timing[64],queued_cpu[32],queued_observations[64];
__declspec(dllexport) int nf_owned_queued_observations(uint64_t*out){if(!out||queued_owner!=GetCurrentThreadId())return 0;memcpy(out,queued_observations,sizeof(queued_observations));return 1;}
static uint64_t queued_cpu_now(void){FILETIME a,b,k,u;if(!GetThreadTimes(GetCurrentThread(),&a,&b,&k,&u))return UINT64_MAX;ULARGE_INTEGER x,y;x.LowPart=k.dwLowDateTime;x.HighPart=k.dwHighDateTime;y.LowPart=u.dwLowDateTime;y.HighPart=u.dwHighDateTime;return (x.QuadPart+y.QuadPart)*100;}
__declspec(dllexport) int nf_owned_queued_cpu(uint64_t*out){if(!out||queued_owner!=GetCurrentThreadId())return 0;memcpy(out,queued_cpu,sizeof(queued_cpu));return 1;}
static uint64_t queued_now(void){LARGE_INTEGER f;QueryPerformanceFrequency(&f);return owned_qpc_ns(f);}
__declspec(dllexport) int nf_owned_queued_timing(uint64_t*out){if(!out||queued_owner!=GetCurrentThreadId())return 0;memcpy(out,queued_timing,sizeof(queued_timing));return 1;}
static int(*queued_draw_probe)(uint64_t*);static uint64_t queued_draw_profiles[128],queued_draw_cpu[16];
__declspec(dllexport) int nf_owned_queued_set_draw_probe(int(*read)(uint64_t*)){if(queued_owner&&queued_owner!=GetCurrentThreadId())return 0;queued_draw_probe=read;return 1;}
__declspec(dllexport) int nf_owned_queued_draw_profiles(uint64_t*out){if(!out||queued_owner!=GetCurrentThreadId())return 0;memcpy(out,queued_draw_profiles,sizeof(queued_draw_profiles));return 1;}
__declspec(dllexport) int nf_owned_queued_draw_cpu(uint64_t*out){if(!out||queued_owner!=GetCurrentThreadId())return 0;memcpy(out,queued_draw_cpu,sizeof(queued_draw_cpu));return 1;}
typedef int(*NFLeaseAcquire)(uint64_t*);
typedef int(*NFLeaseSelect)(uint64_t,uint64_t);
typedef int(*NFLeaseRelease)(uint64_t);
typedef int(*NFLeaseReady)(uint64_t);
static int(*queued_query)(uint64_t,uint64_t*);static uint64_t queued_queries[64];
__declspec(dllexport) int nf_owned_queued_set_query(int(*read)(uint64_t,uint64_t*)){queued_query=read;return 1;}
__declspec(dllexport) int nf_owned_queued_queries(uint64_t*out){if(!out||queued_owner!=GetCurrentThreadId())return 0;memcpy(out,queued_queries,sizeof(queued_queries));return 1;}
typedef struct {uint64_t token,epoch;uint64_t*query;NFLeaseSelect select;int(*present)(void*);void*context;} NFQueuedPresent;
static int queued_present(void*opaque){NFQueuedPresent*p=opaque;if(p->select(p->token,p->epoch)!=0)return 0;if(queued_query&&queued_query(p->token,p->query)!=0)return 0;return p->present(p->context);}
/* Complete source owners remain borrowed until return. Draw ahead is bounded
   by three retained GPU slots; every commit uses the existing atomic lifecycle
   and deadline gate. Any return releases GPU leases, never caller frame data. */
__declspec(dllexport) int nf_owned_handoff_batch_queued(NFOwnedFrameHandoff*q,uint64_t epoch,uint64_t generation,const NFBatchSample*items,unsigned count,int(*draw)(void*),int(*present)(void*),uint64_t*samples,uint64_t*waits,uint64_t*stages,unsigned*completed,NFLeaseAcquire acquire,NFLeaseSelect select,NFLeaseRelease release,NFLeaseReady ready){
 if(!q||!items||!draw||!present||!samples||!waits||!stages||!completed||!acquire||!select||!release||!ready||!epoch||!generation||!count||count>8)return -1;
 for(unsigned i=0;i<count;i++){const NFBatchSample*x=items+i;if(x->older>=x->newer||x->newer>UINT32_MAX||!isfinite(x->alpha)||x->alpha<0||x->alpha>1)return -1;if(i&&(items[i-1].index==UINT64_MAX||x->index!=items[i-1].index+1||x->deadline<items[i-1].deadline))return -1;}
 *completed=0;memset(queued_wait_profiles,0,sizeof(queued_wait_profiles));queued_owner=GetCurrentThreadId();memset(queued_timing,0,sizeof(queued_timing));memset(queued_cpu,0,sizeof(queued_cpu));memset(queued_queries,0,sizeof(queued_queries));memset(queued_observations,0,sizeof(queued_observations));memset(queued_draw_profiles,0,sizeof(queued_draw_profiles));memset(queued_draw_cpu,0,sizeof(queued_draw_cpu));uint64_t tokens[3]={0};int result=1;
 for(unsigned base=0;base<count;base+=3){unsigned n=count-base;if(n>3)n=3;
  for(unsigned j=0;j<n;j++){uint64_t eligibility[4];result=nf_owned_handoff_wait_token(q,epoch,generation,0,eligibility);if(result!=1)goto cleanup;uint64_t*t=queued_timing+8*(base+j);queued_draw_cpu[2*(base+j)]=queued_cpu_now();t[0]=queued_now();if(draw(items[base+j].drawctx)!=0){result=-1;goto cleanup;}t[1]=queued_now();queued_draw_cpu[2*(base+j)+1]=queued_cpu_now();if(queued_draw_probe&&queued_draw_probe(queued_draw_profiles+16*(base+j))!=0){result=-1;goto cleanup;}if(acquire(tokens+j)!=0||!tokens[j]){result=-1;goto cleanup;}t[2]=queued_now();}
  for(unsigned j=0;j<n;j++){const NFBatchSample*x=items+base+j;uint64_t*t=queued_timing+8*(base+j);uint64_t*c=queued_cpu+4*(base+j);uint64_t*o=queued_observations+8*(base+j);c[0]=queued_cpu_now();t[3]=queued_now();
   for(;;){uint64_t eligibility[4];result=nf_owned_handoff_wait_token(q,epoch,generation,0,eligibility);if(result!=1)goto cleanup;uint64_t poll_cpu=queued_cpu_now();uint64_t poll_begin=queued_now();int status=ready(tokens[j]);uint64_t poll_end=queued_now();if(!o[5])o[0]=poll_begin;o[5]++;if(status==0){o[1]=poll_begin;o[2]=poll_end;}if(status==1){o[3]=poll_begin;o[4]=poll_end;}uint64_t poll_end_cpu=queued_cpu_now();if(poll_cpu!=UINT64_MAX&&poll_end_cpu!=UINT64_MAX&&poll_end_cpu>=poll_cpu)c[2]+=poll_end_cpu-poll_cpu;uint64_t duration=queued_now()-poll_begin;t[5]+=duration;if(duration>t[6])t[6]=duration;if(status==1)break;if(status!=0){result=-1;goto cleanup;}uint64_t yield_cpu=queued_cpu_now();uint64_t yield_begin=queued_now();Sleep(1);uint64_t yield_elapsed=queued_now()-yield_begin;t[7]+=yield_elapsed;if(yield_elapsed>o[6])o[6]=yield_elapsed;o[7]=yield_begin;uint64_t yield_end_cpu=queued_cpu_now();if(yield_cpu!=UINT64_MAX&&yield_end_cpu!=UINT64_MAX&&yield_end_cpu>=yield_cpu)c[3]+=yield_end_cpu-yield_cpu;}t[4]=queued_now();c[1]=queued_cpu_now();
   NFQueuedPresent p={tokens[j],epoch,queued_queries+8*(base+j),select,present,x->presentctx};result=nf_owned_handoff_draw_wait_commit_sample(q,epoch,generation,x->older,x->newer,x->index,x->alpha,x->deadline,gate_noop_draw,NULL,queued_present,&p,samples+8*(base+j),waits+4*(base+j),stages+7*(base+j));nf_wait_profile_read(queued_wait_profiles+12*(base+j));if(result!=1)goto cleanup;*completed=base+j+1;if(release(tokens[j])!=0){result=-1;goto cleanup;}tokens[j]=0;
  }
 }
cleanup:
 for(unsigned j=0;j<3;j++)if(tokens[j]&&release(tokens[j])!=0)result=-1;
 return result;
}

__declspec(dllexport) int nf_owned_queued_wait_profiles(uint64_t*out){if(!out||queued_owner!=GetCurrentThreadId())return 0;memcpy(out,queued_wait_profiles,sizeof(queued_wait_profiles));return 1;}

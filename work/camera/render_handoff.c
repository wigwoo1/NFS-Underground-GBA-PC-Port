#include "render_handoff.h"
#include <windows.h>
#include <stdlib.h>
#define NF_HANDOFF_CAPACITY 3
struct NFRenderHandoff {CRITICAL_SECTION lock;uint64_t epoch,stats[4];unsigned count,closed,invalid;NFRenderSubmission*pending[NF_HANDOFF_CAPACITY];};
static void drain(NFRenderHandoff*q){for(unsigned i=0;i<q->count;i++)nf_render_submission_destroy(q->pending[i]);q->stats[2]+=q->count;q->count=0;}
NFRenderHandoff*nf_render_handoff_create(uint64_t epoch){if(!epoch)return NULL;NFRenderHandoff*q=calloc(1,sizeof(*q));if(q){InitializeCriticalSection(&q->lock);q->epoch=epoch;}return q;}
int nf_render_handoff_push(NFRenderHandoff*q,NFRenderSubmission**s){if(!q||!s||!*s)return 0;int ok=0;EnterCriticalSection(&q->lock);if(!q->closed&&!q->invalid&&q->count<NF_HANDOFF_CAPACITY&&nf_render_submission_time(*s)->epoch==q->epoch){q->pending[q->count++]=*s;*s=NULL;ok=1;q->stats[0]++;}else q->stats[3]++;LeaveCriticalSection(&q->lock);return ok;}
NFRenderSubmission*nf_render_handoff_pop(NFRenderHandoff*q){if(!q)return NULL;NFRenderSubmission*s=NULL;EnterCriticalSection(&q->lock);if(q->count){s=q->pending[0];for(unsigned i=1;i<q->count;i++)q->pending[i-1]=q->pending[i];q->count--;q->stats[1]++;}LeaveCriticalSection(&q->lock);return s;}
int nf_render_handoff_epoch(NFRenderHandoff*q,uint64_t epoch){if(!q||!epoch)return 0;int ok=0;EnterCriticalSection(&q->lock);if(!q->closed&&epoch>=q->epoch){if(epoch!=q->epoch){drain(q);q->epoch=epoch;q->invalid=0;}ok=!q->invalid;}LeaveCriticalSection(&q->lock);return ok;}
void nf_render_handoff_close(NFRenderHandoff*q){if(!q)return;EnterCriticalSection(&q->lock);q->closed=1;drain(q);LeaveCriticalSection(&q->lock);}
void nf_render_handoff_destroy(NFRenderHandoff*q){if(q){nf_render_handoff_close(q);DeleteCriticalSection(&q->lock);free(q);}}
int nf_render_handoff_commit(NFRenderHandoff*q,uint64_t epoch,int(*present)(void*),void*ctx){if(!q||!present)return -1;int result=0;EnterCriticalSection(&q->lock);if(!q->closed&&!q->invalid&&q->epoch==epoch)result=present(ctx)?1:-1;LeaveCriticalSection(&q->lock);return result;}
int nf_render_handoff_stats(NFRenderHandoff*q,uint64_t out[4]){if(!q||!out)return 0;EnterCriticalSection(&q->lock);for(unsigned i=0;i<4;i++)out[i]=q->stats[i];LeaveCriticalSection(&q->lock);return 1;}
uint64_t nf_render_handoff_current_epoch(NFRenderHandoff*q){if(!q)return 0;EnterCriticalSection(&q->lock);uint64_t epoch=q->closed||q->invalid?0:q->epoch;LeaveCriticalSection(&q->lock);return epoch;}
void nf_render_handoff_invalidate(NFRenderHandoff*q){if(!q)return;EnterCriticalSection(&q->lock);q->invalid=1;drain(q);LeaveCriticalSection(&q->lock);}
int nf_render_handoff_blank(NFRenderHandoff*q,int(*blank)(void*),void*ctx){if(!q||!blank)return -1;int result=0;EnterCriticalSection(&q->lock);if(!q->closed&&q->invalid)result=blank(ctx)?1:-1;LeaveCriticalSection(&q->lock);return result;}

#ifndef NF_MODEL_OUTCOME_H
#define NF_MODEL_OUTCOME_H
#include <stdint.h>
#include <string.h>
/* Original model completion evidence. Missing records never mean no-draw.
   The caller must independently validate the completed epoch/serial/begin/end. */
typedef enum {NF_MODEL_OUTCOME_UNKNOWN=0,NF_MODEL_OUTCOME_DRAW=1,NF_MODEL_OUTCOME_NO_DRAW=2,NF_MODEL_OUTCOME_CONFLICT=3} NFModelOutcome;
typedef struct {uint32_t identity[5],frame,result;} NFModelOutcomeRecord;
typedef struct {uint64_t epoch;uint32_t serial,begin,count,failed;NFModelOutcomeRecord records[64];} NFModelOutcomeScene;
typedef struct {NFModelOutcomeScene scenes[16];} NFModelOutcomeHistory;
static inline void nf_model_outcome_reset(NFModelOutcomeHistory*h){if(h)memset(h,0,sizeof(*h));}
static inline void nf_model_outcome_record(NFModelOutcomeHistory*h,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t frame,const uint32_t identity[5],uint32_t result){
 if(!h||!epoch)return;
 NFModelOutcomeScene*s=h->scenes+serial%16;
 if(s->epoch!=epoch||s->serial!=serial||s->begin!=begin){memset(s,0,sizeof(*s));s->epoch=epoch;s->serial=serial;s->begin=begin;}
 if(!identity||identity[0]!=3||result>1||frame<begin||s->count>=64){s->failed=1;return;}
 NFModelOutcomeRecord*r=s->records+s->count++;memcpy(r->identity,identity,20);r->frame=frame;r->result=result;
}
static inline NFModelOutcome nf_model_outcome_query(const NFModelOutcomeHistory*h,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const uint32_t identity[5]){
 if(!h||!identity||identity[0]!=3||!epoch||begin>end)return NF_MODEL_OUTCOME_UNKNOWN;
 const NFModelOutcomeScene*s=h->scenes+serial%16;if(s->epoch!=epoch||s->serial!=serial||s->begin!=begin)return NF_MODEL_OUTCOME_UNKNOWN;
 if(s->failed)return NF_MODEL_OUTCOME_CONFLICT;
 unsigned zero=0,positive=0;
 for(unsigned i=0;i<s->count;i++){const NFModelOutcomeRecord*r=s->records+i;if(r->frame>=begin&&r->frame<=end&&!memcmp(r->identity,identity,20)){zero+=r->result==0;positive+=r->result==1;}}
 return zero&&positive?NF_MODEL_OUTCOME_CONFLICT:positive?NF_MODEL_OUTCOME_DRAW:zero?NF_MODEL_OUTCOME_NO_DRAW:NF_MODEL_OUTCOME_UNKNOWN;
}
#endif

#ifndef NF_SAMPLED_COMMAND_PLAN_H
#define NF_SAMPLED_COMMAND_PLAN_H
#include "ordered_dispatch.h"
typedef struct {
 uint32_t record[4],caller,pass,begin,end,depth,object;
} NFSampledInvocation;
typedef struct {uint32_t kind,source,owner;} NFSampledDraw;
typedef struct {
 uint32_t kind,source,object,owner,queue_index,pass,record[4];
} NFSampledCommand;
typedef struct {uint32_t count;NFSampledCommand commands[256];} NFSampledCommandPlan;
/* Structural binding only. Eligibility and contexts must come from a coherent
   sampled scene producer. Never supplies geometry or captured scene templates.
   Root occurrences follow native schedule; nested intervals own direct draws.
   Output is bounded, owned and unchanged on rejection. */
__declspec(dllexport) int nf_sampled_command_plan(const void*,unsigned,
 const NFSampledInvocation*,unsigned,const NFSampledDraw*,unsigned,
 NFSampledCommandPlan*);
#endif

#include "sampled_command_plan.h"
#include <string.h>
__declspec(dllexport) int nf_sampled_command_plan(const void*queue,unsigned nq,
 const NFSampledInvocation*calls,unsigned nc,const NFSampledDraw*draws,
 unsigned nd,NFSampledCommandPlan*out){
 if(!queue||!calls||!out||!nc||nc>256||nd>256||(!draws&&nd))return 0;
 NFRootRegionSchedule roots;
 if(!nf_root_region_schedule(queue,nq,&roots))return 0;
 unsigned stack[256],root_of[256],depth=0,nroot=0,closed=0;
 for(unsigned i=0;i<nc;i++){
  const NFSampledInvocation*c=calls+i;
  if(c->begin>c->end||c->end>nd||c->pass>1||c->depth>depth)return 0;
  while(depth>c->depth){closed=calls[stack[--depth]].end;}
  if(c->begin<closed)return 0;
  if(!depth){
   if(nroot>=roots.count)return 0;
   const NFRootRegionCall*r=roots.calls+nroot;
   if(c->pass!=r->pass||memcmp(c->record,r->record,16)||c->object||
      c->caller!=(r->pass?0x03004de8u:0x03004da4u))return 0;
   root_of[i]=nroot++;
  }else{
   const NFSampledInvocation*parent=calls+stack[depth-1];
   if(c->begin<parent->begin||c->end>parent->end)return 0;
   if(c->caller==0x03002ae8u){
    if(c->pass||parent->pass||c->object||memcmp((const char*)c->record+2,(const char*)parent->record+2,14))return 0;
   }else if(c->caller==0x03002364u){
    if(c->pass||!c->object)return 0;
   }else return 0;
   root_of[i]=root_of[stack[depth-1]];
  }
  stack[depth++]=i;closed=c->begin;
 }
 if(nroot!=roots.count)return 0;
 NFSampledCommandPlan result={0};result.count=nd;
 for(unsigned j=0;j<nd;j++){
  if(draws[j].kind<1||draws[j].kind>3||!draws[j].source||draws[j].owner>=nc)return 0;
  unsigned owner=draws[j].owner,deepest=256;
  for(unsigned i=0;i<nc;i++)if(calls[i].begin<=j&&j<calls[i].end){
   if(deepest==256||calls[i].depth>calls[deepest].depth)deepest=i;
   else if(calls[i].depth==calls[deepest].depth)return 0;
  }
  if(owner!=deepest)return 0;
  const NFSampledInvocation*c=calls+owner;
  NFSampledCommand*command=result.commands+j;
  command->kind=draws[j].kind;command->source=draws[j].source;
  command->object=draws[j].kind==3?draws[j].source:c->object;
  command->owner=owner;command->queue_index=roots.calls[root_of[owner]].queue_index;
  command->pass=c->pass;memcpy(command->record,c->record,16);
 }
 memcpy(out,&result,sizeof(result));return 1;
}

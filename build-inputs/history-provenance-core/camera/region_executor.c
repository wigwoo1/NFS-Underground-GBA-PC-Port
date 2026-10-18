#include "region_executor.h"
#include "ordered_dispatch.h"
#include <stdlib.h>
#include <string.h>
int nf_region_executor_begin(NFRegionExecutor*e,NFRegionExpand expand,NFRegionEmit emit,void*user,unsigned max_depth,unsigned max_regions){
 if(!e||!expand||!emit||!max_depth||max_depth>64||!max_regions||max_regions>65536)return 0;
 NFRegionExecutor owned={expand,emit,user,0,0,0,0,max_depth,max_regions};*e=owned;return 1;
}
int nf_region_execute(NFRegionExecutor*e,const uint8_t record[16],unsigned pass){
 if(!e)return 0;
 if(e->failed)return 0;
 if(!record||pass>1||!e->expand||!e->emit||e->depth>=e->max_depth||e->regions>=e->max_regions){e->failed=1;return 0;}
 NFVisibilityRegionAction*plan=malloc(515*sizeof(*plan));if(!plan){e->failed=1;return 0;}
 unsigned count=0,invocation=e->regions++;e->depth++;
 if(!e->expand(e->user,record,pass,plan,515,&count)||count>515)e->failed=1;
 for(unsigned i=0;i<count&&!e->failed;i++){
  if(plan[i].kind<1||plan[i].kind>4||plan[i].pass>1||
     (plan[i].kind!=2&&plan[i].pass!=pass)||(plan[i].kind==2&&plan[i].pass)){e->failed=1;break;}
 }
 for(unsigned i=0;i<count&&!e->failed;i++){
  e->actions++;
  int ok=plan[i].kind==2?nf_region_execute(e,plan[i].record,plan[i].pass):e->emit(e->user,e,invocation,plan+i);
  if(!ok)e->failed=1;
 }
 e->depth--;free(plan);return !e->failed;
}
int nf_region_execute_queue(NFRegionExecutor*e,const void*queue,unsigned count){
 if(!e||e->failed||e->depth)return 0;
 NFRootRegionSchedule roots;if(!nf_root_region_schedule(queue,count,&roots)){e->failed=1;return 0;}
 for(unsigned i=0;i<roots.count;i++)if(!nf_region_execute(e,(const uint8_t*)roots.calls[i].record,roots.calls[i].pass))return 0;
 return 1;
}

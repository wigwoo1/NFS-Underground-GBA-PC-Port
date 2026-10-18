#include "sampled_root_binding.h"
#include <string.h>
__declspec(dllexport) unsigned nf_sampled_root_binding_capacity(void){return NF_VISIBILITY_QUEUE_CAPACITY;}
int nf_sampled_root_binding(const void*queue,unsigned count,const uint32_t*rows,unsigned n,
 const uint32_t*commands,unsigned command_count,const uint32_t*origins,const uint32_t*passes,NFSampledRootBinding*out){
 if(!out)return 0;
 NFSceneSegments segments;NFRootRegionSchedule schedule;
 if(!nf_scene_segments(rows,n,commands,command_count,origins,passes,&segments)||
    !nf_root_region_schedule(queue,count,&schedule))return 0;
 NFSampledRootBinding result={0};result.count=schedule.count;
 for(unsigned i=0;i<n;i++)if(segments.parents[i]==UINT32_MAX){
  unsigned pass=rows[i*9+5];
  if(pass>1||rows[i*9+4]!=(pass?0x03004de8u:0x03004da4u))return 0;
 }
 for(unsigned i=0;i<schedule.count;i++){
  NFSampledRootCall*c=&result.calls[i];c->call=schedule.calls[i];c->captured=UINT32_MAX;
  unsigned region=c->call.record[0]&65535,sampled=0,captured=0,owner=UINT32_MAX;
  for(unsigned j=0;j<schedule.count;j++)if(schedule.calls[j].pass==c->call.pass&&(schedule.calls[j].record[0]&65535)==region)sampled++;
  for(unsigned j=0;j<n;j++)if(segments.parents[j]==UINT32_MAX&&rows[j*9+5]==c->call.pass&&(rows[j*9]&65535)==region){captured++;owner=j;}
  if(sampled>1||captured>1)c->status=3;
  else if(!captured)c->status=2;
  else{
   c->captured=owner;c->status=1;
   for(unsigned j=segments.offsets[owner];j<segments.offsets[owner+1];j++)if(segments.segments[j].kind>=4)c->status=4;
  }
 }
 for(unsigned i=0;i<n;i++)if(segments.parents[i]==UINT32_MAX){
  unsigned found=0;
  for(unsigned j=0;j<schedule.count;j++)if(schedule.calls[j].pass==rows[i*9+5]&&(schedule.calls[j].record[0]&65535)==(rows[i*9]&65535))found=1;
  if(!found)result.removed[result.removed_count++]=i;
 }
 *out=result;return 1;
}

#include "ordered_dispatch.h"
#include <string.h>
int nf_root_region_schedule(const void*records,unsigned count,NFRootRegionSchedule*out){
 if(!out||count>NF_VISIBILITY_QUEUE_CAPACITY||(!records&&count))return 0;
 NFRootRegionSchedule result={0};const uint8_t*bytes=records;
 for(unsigned pass=0;pass<2;pass++)for(unsigned n=count;n;n--){
  unsigned index=n-1;uint16_t flags;memcpy(&flags,bytes+index*16+10,2);
  if(flags&(pass?0x88:8))continue; /*03004DC8 excludes linked roots on pass1. */
  NFRootRegionCall*call=&result.calls[result.count++];
  call->queue_index=index;call->pass=pass;memcpy(call->record,bytes+index*16,16);
 }
 *out=result;return 1;
}
int nf_ordered_dispatch(const NFDispatchCommand*c,unsigned n,const uint32_t*p,
 const NFDispatchSelection*s,unsigned count,NFOrderedDispatch*out){
 if(!c||!p||!out||(!s&&count)||!n||n>257||count>256)return 0;
 unsigned models=0;uint8_t selected[257]={0};NFOrderedDispatch result={0};
 for(unsigned i=0;i<n;i++){
  if(c[i].kind<1||c[i].kind>3||c[i].object_selected>1)return 0;
  if(c[i].kind==3)models++;
  if(c[i].kind==2){
   if(!((p[i*3]==0x0300297c&&!p[i*3+1])||
        (p[i*3]==0x03002b38&&p[i*3+1])))return 0;
  }else if(p[i*3]||p[i*3+1]||p[i*3+2])return 0;
 }
 if(models!=1)return 0;
 for(unsigned i=0;i<count;i++){
  unsigned k=s[i].captured_index;
  if(k>=n||selected[k]||c[k].kind!=2||s[i].source!=c[k].source||
     s[i].object_selected!=c[k].object_selected||s[i].pass!=(p[k*3+1]!=0))return 0;
  selected[k]=1;
 }
 for(unsigned i=0;i<n;i++)if(c[i].kind!=2||selected[i])result.indices[result.count++]=i;
 memcpy(out,&result,sizeof(result));return 1;
}
int nf_root_region_anchors(const uint32_t*sampled,unsigned count,
 const NFRootInterval*captured,unsigned n,NFRootAnchors*out){
 if(!sampled||!captured||!out||!count||count>NF_VISIBILITY_QUEUE_CAPACITY||!n||n>NF_VISIBILITY_QUEUE_CAPACITY)return 0;
 NFRootAnchors result={0};unsigned next=0;
 for(unsigned i=0;i<n;i++){
  if(captured[i].region>65535||captured[i].begin>captured[i].end||captured[i].end>257||
     (i&&captured[i-1].end>captured[i].begin))return 0;
  for(unsigned j=0;j<i;j++)if(captured[j].region==captured[i].region)return 0;
 }
 for(unsigned i=0;i<count;i++){
  if(sampled[i]>65535)return 0;
  for(unsigned j=0;j<i;j++)if(sampled[j]==sampled[i])return 0;
  for(unsigned j=0;j<n;j++)if(sampled[i]==captured[j].region){
   if(j!=next)return 0;
   next++;break;
  }
 }
 if(next!=n)return 0;
 for(unsigned i=0;i<count;i++){
  int found=0;
  for(unsigned j=i;j<count&&!found;j++)for(unsigned k=0;k<n;k++)if(sampled[j]==captured[k].region){
   result.slots[i]=captured[k].begin;found=1;break;
  }
  if(!found)return 0;
 }
 result.count=count;*out=result;return 1;
}
int nf_wall_insertions(const uint32_t*sampled,unsigned count,
 const NFRetainedWall*retained,unsigned n,unsigned tail,NFWallInsertions*out){
 if(!out||count>64||n>64||tail>257||(!sampled&&count)||(!retained&&n))return 0;
 NFWallInsertions result={0};unsigned next=0;
 for(unsigned i=0;i<n;i++){
  if(!retained[i].source||retained[i].command>=tail||(i&&retained[i-1].command>=retained[i].command))return 0;
  for(unsigned j=0;j<i;j++)if(retained[i].source==retained[j].source)return 0;
 }
 for(unsigned i=0;i<count;i++){
  if(!sampled[i])return 0;
  for(unsigned j=0;j<i;j++)if(sampled[i]==sampled[j])return 0;
  int known=0;
  for(unsigned j=0;j<n;j++)if(sampled[i]==retained[j].source){
   if(j!=next)return 0;
   next++;known=1;break;
  }
  if(!known){unsigned k=result.count++;result.source[k]=sampled[i];result.before[k]=next<n?retained[next].command:tail;}
 }
 if(next!=n)return 0;
 *out=result;return 1;
}

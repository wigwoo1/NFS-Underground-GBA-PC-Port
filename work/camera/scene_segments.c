#include "scene_segments.h"
#include <string.h>
static int append(NFSceneSegments*r,unsigned start,unsigned kind,unsigned begin,unsigned end,unsigned child){
 if((kind==1||kind==3)&&r->count>start){NFSceneSegment*s=&r->segments[r->count-1];if(s->kind==kind&&s->end==begin){s->end=end;return 1;}}
 if(r->count>=1024)return 0;
 r->segments[r->count++]=(NFSceneSegment){kind,begin,end,child};return 1;
}
static int direct(NFSceneSegments*r,unsigned start,const uint32_t*record,unsigned begin,unsigned end,const uint32_t*c,const uint32_t*o,const uint32_t*p){
 for(unsigned j=begin;j<end;j++){
  unsigned kind;
  if(c[j*6]==3)kind=5;
  else{
   if(memcmp(record,o+j*12+2,16))return 0;
   if(c[j*6]==1)kind=2;
   else if(c[j*6]==2)kind=p[j*3+1]?3:1;
   else return 0;
  }
  if(!append(r,start,kind,j,j+1,UINT32_MAX))return 0;
 }
 return 1;
}
int nf_scene_segments(const uint32_t*rows,unsigned n,const uint32_t*c,unsigned commands,const uint32_t*o,const uint32_t*p,NFSceneSegments*out){
 if(!out||n>256||commands>257||(!rows&&n)||(!c&&commands)||(!o&&commands)||(!p&&commands))return 0;
 NFSceneSegments result={0};unsigned stack[256],depth=0,last[256],lastroot=UINT32_MAX;
 for(unsigned i=0;i<256;i++)last[i]=UINT32_MAX;
 for(unsigned i=0;i<n;i++){
  const uint32_t*r=rows+i*9;unsigned begin=r[6],end=r[7],level=r[8];
  if(begin>end||end>commands||level>depth||level>=256)return 0;
  depth=level;unsigned parent=level?stack[level-1]:UINT32_MAX;
  if(parent!=UINT32_MAX){
   const uint32_t*pr=rows+parent*9;
   if(begin<pr[6]||end>pr[7]||(last[parent]!=UINT32_MAX&&rows[last[parent]*9+7]>begin))return 0;
   last[parent]=i;
  }else{if(lastroot!=UINT32_MAX&&rows[lastroot*9+7]>begin)return 0;lastroot=i;}
  result.parents[i]=parent;stack[depth++]=i;
 }
 for(unsigned i=0;i<n;i++){
  const uint32_t*r=rows+i*9;unsigned cursor=r[6],start=result.count;result.offsets[i]=start;
  for(unsigned j=i+1;j<n;j++)if(result.parents[j]==i){
   unsigned begin=rows[j*9+6],end=rows[j*9+7];
   if(!direct(&result,start,r,cursor,begin,c,o,p)||!append(&result,start,4,begin,end,j))return 0;
   cursor=end;
  }
  if(!direct(&result,start,r,cursor,r[7],c,o,p))return 0;
 }
 result.offsets[n]=result.count;result.calls=n;*out=result;return 1;
}
int nf_segment_wall_insertions(const uint32_t*rows,unsigned n,const uint32_t*c,
 unsigned commands,const uint32_t*o,const uint32_t*p,unsigned segment_index,
 const uint32_t*sampled,unsigned count,NFWallInsertions*out){
 NFSceneSegments segments;NFRetainedWall retained[64];
 if(!out||count>64||(!sampled&&count)||!nf_scene_segments(rows,n,c,commands,o,p,&segments)||segment_index>=segments.count)return 0;
 NFSceneSegment*s=&segments.segments[segment_index];
 if((s->kind!=1&&s->kind!=3)||s->begin>=s->end||s->end-s->begin>64)return 0;
 for(unsigned i=s->begin;i<s->end;i++)retained[i-s->begin]=(NFRetainedWall){c[i*6+2],i};
 for(unsigned i=0;i<count;i++)for(unsigned j=0;j<commands;j++){
  if(j>=s->begin&&j<s->end)continue;
  if(c[j*6]==2&&sampled[i]==c[j*6+2])return 0;
 }
 return nf_wall_insertions(sampled,count,retained,s->end-s->begin,s->end,out);
}

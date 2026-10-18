#ifndef NF_ROAD_CORRECTED_CLIP_H
#define NF_ROAD_CORRECTED_CLIP_H
#include "road_near_clip.h"
#include "road_near_attributes.h"
#include "road_source_attributes.h"
#include <math.h>
#include <string.h>
/* Owned source edge order, geometric positions and corrected source UVs.
   No projected polygon correspondence or borrowed memory. Atomic output. */
static int texture_near_clip_corrected(const RoadVertex*in,unsigned count,RoadVertex*out,int near_z,const NFRoadSourceAttributes*raw,const uint32_t*reciprocal,unsigned*out_count){
 if(!in||!out||!raw||!reciprocal||!out_count||count<3||count>32||raw->count!=count||raw->shift>10||raw->stored_height<2||(raw->stored_height&1)||raw->affine>1)return 0;
 double offset[2]={raw->offsets[0]/(256.0*(1u<<raw->shift)),raw->offsets[1]/(256.0*raw->stored_height)};
 RoadVertex result[64];unsigned n=0;
 for(unsigned i=0;i<count;i++){
  unsigned previous=(i+count-1)%count;RoadVertex a=in[previous],b=in[i];
  if(!isfinite(a.p.x)||!isfinite(a.p.y)||!isfinite(a.p.z)||!isfinite(b.p.x)||!isfinite(b.p.y)||!isfinite(b.p.z))return 0;
  int ai=a.p.z>=near_z,bi=b.p.z>=near_z;
  if(ai!=bi){
   double uv[2],t=(near_z-a.p.z)/(b.p.z-a.p.z);int32_t attributes[4]={raw->attributes[previous][0],raw->attributes[previous][1],raw->attributes[i][0],raw->attributes[i][1]};
   if(!nf_road_near_attributes(a.p.z,b.p.z,attributes,raw->shift,raw->stored_height,raw->affine,near_z,reciprocal,uv))return 0;
   result[n++]=(RoadVertex){{a.p.x+(b.p.x-a.p.x)*t,a.p.y+(b.p.y-a.p.y)*t,near_z},uv[0]+offset[0],uv[1]+offset[1]};
  }
  if(bi){double uv[2];if(!nf_road_vertex_attributes(b.p.z,raw->attributes[i],raw->shift,raw->stored_height,raw->affine,reciprocal,uv))return 0;b.u=uv[0]+offset[0];b.v=uv[1]+offset[1];result[n++]=b;}
 }
 memcpy(out,result,n*sizeof(*out));*out_count=n;return 1;
}
#endif

#ifndef NF_ROAD_UV_DIAGNOSTIC_H
#define NF_ROAD_UV_DIAGNOSTIC_H
#include "road_near_continuity.h"
/* GPU probe selection: compare original correction/geometric/continuous UVs. */
static int road_uv_diagnostic(const RoadVertex*in,unsigned count,RoadVertex*out,unsigned*out_count,const NFRoadSourceAttributes*raw,const uint32_t*table,int mode){
 if(mode==0)return 1;
 if(mode==1){*out_count=texture_near_clip(in,count,out,64);return 1;}
 if(mode!=2)return 0;
 unsigned adjusted;return road_near_front_limit(in,count,out,*out_count,raw,table,&adjusted);
}
#endif

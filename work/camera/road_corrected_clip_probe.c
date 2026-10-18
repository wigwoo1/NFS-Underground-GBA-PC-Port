#include <stdint.h>
typedef struct {double x,y,z;} NFPoint3;
#include "road_corrected_clip.h"
#include "road_near_continuity.h"
__declspec(dllexport) int nf_continuous_clip_probe(const RoadVertex*in,unsigned count,RoadVertex*out,const NFRoadSourceAttributes*raw,const uint32_t*reciprocal,unsigned*out_count,unsigned*adjusted){return texture_near_clip_continuous(in,count,out,raw,reciprocal,out_count,adjusted);}
#include "road_triangulate.h"
__declspec(dllexport) unsigned nf_road_triangulate_probe(const RoadVertex*in,unsigned count,RoadVertex*out){
 if(!in||!out||count>64)return 0;return road_triangulate(in,count,out);
}
__declspec(dllexport) int nf_corrected_clip_probe(const RoadVertex*in,unsigned count,RoadVertex*out,const NFRoadSourceAttributes*raw,const uint32_t*reciprocal,unsigned*out_count){
 return texture_near_clip_corrected(in,count,out,64,raw,reciprocal,out_count);
}
__declspec(dllexport) unsigned nf_geometric_clip_probe(const RoadVertex*in,unsigned count,RoadVertex*out){
 return texture_near_clip(in,count,out,64);
}

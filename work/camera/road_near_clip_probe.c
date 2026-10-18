typedef struct {double x,y,z;} NFPoint3;
#include "road_near_clip.h"
__declspec(dllexport) unsigned nf_road_near_clip_probe(const RoadVertex*in,unsigned count,RoadVertex*out,double near_z){if(!in||!out||count<2||count>32||near_z<=0)return 0;return texture_near_clip(in,count,out,near_z);}

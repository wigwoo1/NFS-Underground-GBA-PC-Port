/* Component-only export of the production experimental road clip policy. */
#include "rigid_motion.h"
#include "road_corrected_clip.h"
#include "road_near_continuity.h"
__declspec(dllexport) int nf_test_road_clip(const RoadVertex*in,unsigned count,const NFRoadSourceAttributes*raw,const uint32_t*table,RoadVertex*out,unsigned*n,unsigned*adjusted){return texture_near_clip_continuous(in,count,out,raw,table,n,adjusted);}

__declspec(dllexport) unsigned nf_test_generic_clip(const RoadVertex*in,unsigned count,RoadVertex*out){if(!in||!out||count<3||count>32)return 0;return texture_near_clip(in,count,out,64);}

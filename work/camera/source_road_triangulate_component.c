#include "rigid_motion.h"
typedef struct {NFPoint3 p;double u,v;} RoadVertex;
#include "road_triangulate.h"
__declspec(dllexport) unsigned nf_source_triangles(const RoadVertex*ring,unsigned count,RoadVertex*out){if(!ring||!out||count<3||count>64)return 0;return road_triangulate(ring,count,out);}

#include "road_span_core.h"
__declspec(dllexport) int nf_road_span_transition_at(const double*ring,unsigned count,double scan,const uint32_t*t,double out[8]){
 return nf_road_span_core(ring,count,scan,t,out,0);
}

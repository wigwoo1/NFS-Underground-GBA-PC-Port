#include <stdint.h>
#include <string.h>
extern int nf_road_span_transition_at(const double*,unsigned,double,const uint32_t*,double*);
extern int nf_road_pair_uv_continuous(const double*,const double*,double,double,const uint32_t*,double*);
/* Scheduler owns width/pair coordinates; output left/right X and evaluated U/V. */
__declspec(dllexport) int nf_road_span_uv_at(const double*ring,unsigned count,double scan,double width,double pair,const uint32_t*t,double out[4]){
 if(!out)return 0;
 double span[8],uv[2],result[4];
 if(!nf_road_span_transition_at(ring,count,scan,t,span)||!nf_road_pair_uv_continuous(span+1,span+5,width,pair,t,uv))return 0;
 result[0]=span[0];result[1]=span[4];result[2]=uv[0];result[3]=uv[1];memcpy(out,result,sizeof(result));return 1;
}

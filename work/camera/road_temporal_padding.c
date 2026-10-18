#include <stdint.h>
#include <math.h>
#include <string.h>
extern int nf_road_span_transition_at(const double*,unsigned,double,const uint32_t*,double*);
extern int nf_road_span_padding_segmented(const double*,unsigned,double,const uint32_t*,double*);
/* Experimental temporal residual interpolation for an interior span shared
   by two source-geometry poses and the current projected pose. Geometry must
   come from world/camera transforms. No projected-polygon correspondence.
   Endpoints dispatch exactly to the existing source padding evaluator.
   Birth/death, changing topology, original duplicate/spill winners and UV/color
   composition are separate unresolved requirements; no live adoption. */
__declspec(dllexport) int nf_road_temporal_padding(const double*a,unsigned na,const double*b,unsigned nb,const double*current,unsigned nc,double scan,double phase,const uint32_t*table,double*out){
 if(!out||!isfinite(phase)||phase<0||phase>1)return 0;
 if(phase==0)return nf_road_span_padding_segmented(a,na,scan,table,out);
 if(phase==1)return nf_road_span_padding_segmented(b,nb,scan,table,out);
 double sa[8],sb[8],sc[8],pa[2],pb[2],result[2];
 if(!nf_road_span_transition_at(a,na,scan,table,sa)||!nf_road_span_transition_at(b,nb,scan,table,sb)||!nf_road_span_transition_at(current,nc,scan,table,sc)||!nf_road_span_padding_segmented(a,na,scan,table,pa)||!nf_road_span_padding_segmented(b,nb,scan,table,pb))return 0;
 result[0]=sc[0]+(1-phase)*(pa[0]-sa[0])+phase*(pb[0]-sb[0]);
 result[1]=(1-phase)*pa[1]+phase*pb[1];
 if(!isfinite(result[0])||!isfinite(result[1])||result[1]<1||result[1]>32767)return 0;
 memcpy(out,result,sizeof(result));return 1;
}

/* Fractional interval occupancy for one source pixel footprint. Paired integer
   start/width yields exact original interval membership. Does not schedule
   duplicated rows or spill writes, and is not final geometric AA. */
__declspec(dllexport) double nf_road_interval_coverage(double start,double width,double x){
 if(!isfinite(start)||!isfinite(width)||!isfinite(x)||width<1||width>32767)return -1;
 double lo=fmax(start,x),hi=fmin(start+2*width,x+1);
 return fmax(0,fmin(1,hi-lo));
}

#include <math.h>
/* Candidate fractional horizontal query extension. Original even/odd lane
   anchors share the same UV pair. Interpolate between adjacent integer
   anchors; hold the terminal pair so UV input stays in its valid domain.
   Texture lane selection and row duplication are separate coverage policies. */
__declspec(dllexport) int nf_road_pair_query_continuous(double width,double relative,double*out){
 if(!out||!isfinite(width)||!isfinite(relative)||width<1||width>32767||relative<0||relative>=2*width)return 0;
 double base=floor(relative),fraction=relative-base;
 double pair=floor(base/2)+(floor((base+1)/2)-floor(base/2))*fraction;
 *out=fmin(pair,width-1);return 1;
}

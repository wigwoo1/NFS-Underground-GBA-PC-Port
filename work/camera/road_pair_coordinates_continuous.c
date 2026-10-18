#include <math.h>
/* Experimental integer-anchor extension, not adopted by live coverage.
   Linear interpolation of floor(value/2) at adjacent integer anchors.
   This preserves paired-column plateaus and removes jumps between anchors. */
static double paired_anchor(double value){
 double base=floor(value),fraction=value-base;
 return floor(base/2)+(floor((base+1)/2)-floor(base/2))*fraction;
}
/* Output start,width,pair; reject outside half-open padded interval atomically.
   Last pair holds its value through its final lane; no out-of-domain UV query. */
__declspec(dllexport) int nf_road_pair_coordinates_continuous(double left,double right,double x,double*out){
 if(!out||!isfinite(left)||!isfinite(right)||!isfinite(x)||right<=left||fabs(left)>1e8||fabs(right)>1e8)return 0;
 double start=2*paired_anchor(left),width=paired_anchor(right-left)+2,relative=x-start;
 if(width<1||width>32767||relative<0||relative>=2*width)return 0;
 double pair=fmin(paired_anchor(relative),width-1);
 out[0]=start;out[1]=width;out[2]=pair;return 1;
}

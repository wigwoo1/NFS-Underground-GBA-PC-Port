#include <stdint.h>
#include <math.h>
/* Bilinear extension of original edge slopes. Input order x,y,unused,q,u,v.
   Source-projected endpoints only; no polygon matching or captured spans. */
static double slope(unsigned height,int32_t difference,unsigned x,const uint32_t*table){
 if(x)return (double)(int32_t)((table[height]>>8)*(uint32_t)difference)/65536.0;
 return (double)(int32_t)(uint32_t)((uint64_t)((int64_t)difference*table[height])>>24);
}
__declspec(dllexport) int nf_road_edge_continuous(const double a[6],const double b[6],const uint32_t table[32768],double out[4]){
 if(!a||!b||!table||!out)return 0;
 for(unsigned i=0;i<6;i++)if(!isfinite(a[i])||!isfinite(b[i]))return 0;
 double height=b[1]-a[1];if(height<=0||height>=32767)return 0;
 unsigned h=(unsigned)floor(height);double th=height-h,result[4];const unsigned fields[4]={0,4,5,3};
 for(unsigned k=0;k<4;k++){
  double delta=b[fields[k]]-a[fields[k]];if(delta<INT32_MIN||delta>=INT32_MAX)return 0;
  int32_t lo=(int32_t)floor(delta);double td=delta-lo;
  double v0=slope(h,lo,k==0,table),v1=slope(h,lo+1,k==0,table);
  result[k]=v0+(v1-v0)*td;
  if(th){v0=slope(h+1,lo,k==0,table);v1=slope(h+1,lo+1,k==0,table);result[k]+=(v0+(v1-v0)*td-result[k])*th;}
  if(!isfinite(result[k]))return 0;
 }
 for(unsigned k=0;k<4;k++)out[k]=result[k];
 return 1;
}



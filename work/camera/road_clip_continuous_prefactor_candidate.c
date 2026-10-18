#include <stdint.h>
#include <math.h>
#include <string.h>
/* Isolated experiment: use bounding-box trivial accept/reject only for normal
   polygon rings. Preserve the reference's previous-vertex output rotation. */
static double adjustment(unsigned distance,int32_t travel,int32_t difference,int reverse,const uint32_t*t){
 uint32_t f=(uint32_t)travel*t[distance];if(reverse)f=0u-f;
 int64_t product=(int64_t)difference*(int32_t)f;
 return (double)(int32_t)(uint32_t)((uint64_t)product>>24);
}
static int endpoint(double a[6],const double b[6],double bound,const uint32_t*t){
 double delta=b[0]-a[0],distance=fabs(delta),travel=bound-a[0];
 if(distance>=32767||travel<INT32_MIN||travel>=INT32_MAX)return 0;
 unsigned lo=(unsigned)floor(distance);int32_t tl=(int32_t)floor(travel);double fd=distance-lo,ft=travel-tl;
 int reverse=delta<0||(delta==0&&bound<a[0]);double result[6];result[0]=bound;
 for(unsigned k=1;k<6;k++){
  double diff=b[k]-a[k];if(diff<INT32_MIN||diff>=INT32_MAX)return 0;
  int32_t dl=(int32_t)floor(diff);double ff=diff-dl,sum=0,anchor=0;int anchored=0;
  for(unsigned i=0;i<2;i++)for(unsigned j=0;j<2;j++)for(unsigned q=0;q<2;q++){
   double weight=(i?fd:1-fd)*(j?ft:1-ft)*(q?ff:1-ff);
   if(weight){double sample=adjustment(lo+i,tl+(int32_t)j,dl+(int32_t)q,reverse,t);if(!anchored){anchor=sample;anchored=1;}sum+=weight*(sample-anchor);}
  }
  result[k]=a[k]+anchor+sum;if(!isfinite(result[k])||result[k]<INT32_MIN||result[k]>INT32_MAX)return 0;
 }
 memcpy(a,result,sizeof(result));return 1;
}
__declspec(dllexport) int nf_road_clip_continuous_candidate(const double*in,unsigned count,double left,double right,const uint32_t*t,double*out,unsigned capacity,unsigned*out_count){
 if(!in||!t||!out||!out_count||count>64||!isfinite(left)||!isfinite(right))return 0;
 double minx=INFINITY,maxx=-INFINITY;
 for(unsigned i=0;i<count;i++){
  double x=in[i*6];if(!isfinite(x)||fabs(x)>100000000)return 0;if(x<minx)minx=x;if(x>maxx)maxx=x;
  for(unsigned k=1;k<6;k++)if(!isfinite(in[i*6+k])||fabs(in[i*6+k])>100000000)return 0;
 }
 if(count>=3&&minx>=left&&maxx<=right){
  if(count>capacity)return 0;
  for(unsigned i=0;i<count;i++)memcpy(out+i*6,in+((i+count-1)%count)*6,6*sizeof(double));
  *out_count=count;return 1;
 }
 if(count>=3&&(maxx<left||minx>right)){*out_count=0;return 1;}
 double result[128*6];unsigned n=0;
 for(unsigned i=0;i<count;i++){
  double a[6],b[6];memcpy(a,in+((i+count-1)%count)*6,sizeof(a));memcpy(b,in+i*6,sizeof(b));
  if(a[0]<left){if(b[0]<left)continue;if(!endpoint(a,b,left,t))return 0;}
  else if(a[0]>right){if(b[0]>right)continue;if(!endpoint(a,b,right,t))return 0;}
  unsigned extra=0;
  if(b[0]<left){if(!endpoint(b,a,left,t))return 0;extra=1;}
  else if(b[0]>right){if(!endpoint(b,a,right,t))return 0;extra=1;}
  memcpy(result+n++*6,a,sizeof(a));if(extra)memcpy(result+n++*6,b,sizeof(b));
 }
 if(n>capacity)return 0;memcpy(out,result,n*6*sizeof(double));*out_count=n;return 1;
}

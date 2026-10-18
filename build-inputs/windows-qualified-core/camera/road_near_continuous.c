#include <stdint.h>
#include <math.h>
#include <string.h>
/* x,y,z,u,v. Fixed near plane; bounded no-wrap position/UV domain. */
static int near_core(const double a[5],const double b[5],double near,const uint32_t*t,double out[5]){
 if(!a||!b||!t||!out||!isfinite(near)||near<1||near>32766)return 0;
 for(unsigned k=0;k<5;k++)if(!isfinite(a[k])||!isfinite(b[k])||fabs(a[k])>100000000||fabs(b[k])>100000000)return 0;
 int start=a[2]<near;if(start==(b[2]<near))return 0;
 const double*target=start?a:b;double distance=fabs(b[2]-a[2]),travel=near-target[2];
 if(distance<=0||distance>=32767||travel<0||travel>=32767)return 0;
 unsigned dl=(unsigned)floor(distance),tl=(unsigned)floor(travel);double fd=distance-dl,ft=travel-tl,result[5];result[2]=near;
 for(unsigned k=0;k<5;k++){
  if(k==2){continue;} double diff=b[k]-a[k];if(diff<INT32_MIN||diff>=INT32_MAX)return 0;
  int32_t base=(int32_t)floor(diff);double ff=diff-base,sum=0;
  for(unsigned i=0;i<2;i++)for(unsigned j=0;j<2;j++)for(unsigned q=0;q<2;q++){
   double w=(i?fd:1-fd)*(j?ft:1-ft)*(q?ff:1-ff);if(!w)continue;
   uint32_t factor=(tl+j)*t[dl+i];int64_t product=(int64_t)(base+(int32_t)q)*factor;
   sum+=w*(int32_t)(uint32_t)((uint64_t)product>>24);
  }
  result[k]=target[k]+(start?sum:-sum);
  if(!isfinite(result[k])||result[k]<INT32_MIN||result[k]>INT32_MAX||(k==0&&(result[k]<-32768||result[k]>32767)))return 0;
 }
 memcpy(out,result,sizeof(result));return 1;
}

__declspec(dllexport) int nf_road_near_continuous(const double a[5],const double b[5],double near,const uint32_t*t,double out[5]){
 double result[5];if(!near_core(a,b,near,t,result))return 0;
 unsigned visible=a[2]>=near?0:1;const double*v=visible?b:a;double gap=v[2]-near;
 if(gap<1){
  double aa[5],bb[5],limit[5];memcpy(aa,a,sizeof(aa));memcpy(bb,b,sizeof(bb));(visible?bb:aa)[2]=near;
  if(!near_core(aa,bb,near,t,limit))return 0;
  double weight=1-gap;
  for(unsigned k=0;k<5;k++)if(k!=2)result[k]+=weight*(v[k]-limit[k]);
 }
 double distance=fabs(b[2]-a[2]);
 if(distance<1){
  double ratio=(near-a[2])/(b[2]-a[2]);
  for(unsigned k=0;k<5;k++)if(k!=2){double linear=a[k]+ratio*(b[k]-a[k]);result[k]=linear+distance*(result[k]-linear);}
 } memcpy(out,result,sizeof(result));return 1;
}


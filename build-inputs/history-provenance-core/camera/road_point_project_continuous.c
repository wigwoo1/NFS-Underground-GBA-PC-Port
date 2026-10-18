#include <stdint.h>
#include <math.h>
/* Original source point projection with multilinear integer-cell extension.
   Output x,y,q,u*q,v*q in original attribute units; no screen correspondence. */
static double coordinate(int value,unsigned z,unsigned scale,int center,int x,const uint32_t*t){
 uint32_t factor=(uint32_t)((int32_t)(t[z]*scale)>>7);
 uint32_t result=(uint32_t)center+(uint32_t)((int32_t)((uint32_t)(value>>1)*factor)>>16);
 return x?(double)(int16_t)result:(double)(int32_t)result;
}
__declspec(dllexport) int nf_road_point_project_continuous(const double point[3],const int32_t attrs[2],unsigned shift,unsigned height,const int32_t projection[3],const uint32_t*t,double out[5]){
 if(!point||!attrs||!projection||!t||!out||shift>10||height<2||height>65535)return 0;
 for(unsigned i=0;i<3;i++)if(!isfinite(point[i]))return 0;
 if(point[0]<-32768||point[0]>32767||point[1]<-32768||point[1]>32767||point[2]<1||point[2]>32767||projection[2]<0)return 0;
 int base[3];double frac[3],result[5]={0};for(unsigned i=0;i<3;i++){base[i]=(int)floor(point[i]);frac[i]=point[i]-base[i];}
 for(unsigned k=0;k<2;k++)for(unsigned i=0;i<2;i++)for(unsigned j=0;j<2;j++){
  double w=(i?frac[k]:1-frac[k])*(j?frac[2]:1-frac[2]);if(!w)continue;
  result[k]+=w*coordinate(base[k]+(int)i,base[2]+j,(unsigned)projection[2],projection[k],k==0,t);
 }
 for(unsigned j=0;j<2;j++){
  double w=j?frac[2]:1-frac[2];if(!w)continue;uint32_t r=t[base[2]+j];result[2]+=w*r;
  for(unsigned k=0;k<2;k++){uint32_t scaled=k?(uint32_t)attrs[k]*height:(uint32_t)attrs[k]<<shift;int64_t product=(int64_t)((int32_t)scaled>>7)*(int32_t)r;result[3+k]+=w*(int32_t)(uint32_t)((uint64_t)product>>8);}
 }
 for(unsigned i=0;i<5;i++){if(!isfinite(result[i]))return 0;}
 for(unsigned i=0;i<5;i++)out[i]=result[i];
 return 1;
}
/* Fractional raw UV extension; existing integer entry point stays compatible. */
__declspec(dllexport) int nf_road_point_project_fractional(const double point[3],const double attrs[2],unsigned shift,unsigned height,const int32_t projection[3],const uint32_t*t,double out[5]){
 if(!attrs||!out)return 0;
 int32_t base[2];double frac[2],result[5]={0};
 for(unsigned k=0;k<2;k++){
  if(!isfinite(attrs[k])||attrs[k]<INT32_MIN||attrs[k]>INT32_MAX-1)return 0;
  base[k]=(int32_t)floor(attrs[k]);frac[k]=attrs[k]-base[k];
 }
 for(unsigned i=0;i<2;i++)for(unsigned j=0;j<2;j++){
  double w=(i?frac[0]:1-frac[0])*(j?frac[1]:1-frac[1]);if(!w)continue;
  int32_t a[2]={base[0]+(int32_t)i,base[1]+(int32_t)j};double value[5];
  if(!nf_road_point_project_continuous(point,a,shift,height,projection,t,value))return 0;
  for(unsigned k=0;k<5;k++)result[k]+=w*value[k];
 }
 for(unsigned k=0;k<5;k++){out[k]=result[k];} return 1;
}

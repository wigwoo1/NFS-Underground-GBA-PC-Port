#include <stdint.h>
#include <math.h>
/* Fixed original Q14 matrix, bilinear extension of original world integer cells. */
static double axis(int32_t x,int32_t z,const int32_t*m,unsigned k){
 uint32_t a=(uint32_t)x+(uint32_t)m[9],b=(uint32_t)z+(uint32_t)m[11];
 uint32_t v=a*(uint32_t)m[k]+b*(uint32_t)m[6+k];
 return (int16_t)((int32_t)v>>14);
}
__declspec(dllexport) int nf_road_camera_continuous(const double p[3],const int32_t m[12],double out[3]){
 if(!p||!m||!out)return 0;
 for(unsigned k=0;k<3;k++)if(!isfinite(p[k])||p[k]<INT32_MIN||p[k]>INT32_MAX-1)return 0;
 int32_t x=(int32_t)floor(p[0]),z=(int32_t)floor(p[2]);double fx=p[0]-x,fz=p[2]-z,r[3]={0,p[1]+m[10],0};
 for(unsigned i=0;i<2;i++)for(unsigned j=0;j<2;j++){
  double w=(i?fx:1-fx)*(j?fz:1-fz);if(!w)continue;
  r[0]+=w*axis(x+i,z+j,m,0);r[2]+=w*axis(x+i,z+j,m,2);
 }
 for(unsigned k=0;k<3;k++){out[k]=r[k];} return 1;
}


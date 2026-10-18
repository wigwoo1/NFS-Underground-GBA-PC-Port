#include <stdint.h>
#include <math.h>
#include <string.h>
static int project(const double*v,uint32_t scale,const int32_t*center,const uint32_t*table,double*out){
 if(!isfinite(v[0])||!isfinite(v[1])||!isfinite(v[2])||v[0]<-2147483648.0||v[0]>2147483646.0||v[1]<-2147483648.0||v[1]>2147483646.0||v[2]<0||v[2]>24576)return 0;
 int32_t base[3];double f[3];for(unsigned k=0;k<3;k++){base[k]=(int32_t)floor(v[k]);f[k]=v[k]-base[k];}out[0]=out[1]=0;
 for(unsigned x=0;x<2;x++)for(unsigned y=0;y<2;y++)for(unsigned z=0;z<2;z++){
  double w=(x?f[0]:1-f[0])*(y?f[1]:1-f[1])*(z?f[2]:1-f[2]);if(!w)continue;
  int32_t factor=(int32_t)(scale*table[base[2]+z])>>8;uint32_t xy[2]={(uint32_t)base[0]+x,(uint32_t)base[1]+y};
  for(unsigned k=0;k<2;k++){uint32_t product=xy[k]*(uint32_t)factor;int32_t delta=(int32_t)product>>16;int16_t value=(int16_t)((uint32_t)center[k]+(uint32_t)delta);out[k]+=w*value;}
 }return 1;
}
__declspec(dllexport) int nf_source_model_project_cells(const double*m,const int16_t*local,unsigned count,uint32_t scale,const int32_t*center,const uint32_t*table,double*out){
 if(!m||!local||!center||!table||!out||!count||count>2048)return 37;
 for(unsigned k=0;k<12;k++)if(!isfinite(m[k]))return 37;
 double result[4096];for(unsigned i=0;i<count;i++){
  double v[3];for(unsigned k=0;k<3;k++){double sum=0;for(unsigned j=0;j<3;j++)sum+=local[i*3+j]*m[j*3+k];v[k]=m[9+k]+sum;}
  if(!project(v,scale,center,table,result+i*2))return 37;
 }memcpy(out,result,count*2*sizeof(double));return 0;
}

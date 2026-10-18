#include <stddef.h>
#include <math.h>
__declspec(dllexport) int nf_owned_wall_point_batch(const double *world,const double *correction,size_t count,const double *camera,double alpha,double *out){
 if(!world||!correction||!camera||!out||count>65536||!isfinite(alpha)||alpha<0||alpha>1)return 0;
 for(size_t i=0;i<count;i++){
  double wx=world[2*i],wz=world[2*i+1];
  double x=(wx+camera[9])*camera[0]+(wz+camera[11])*camera[6];
  double z=(wx+camera[9])*camera[2]+(wz+camera[11])*camera[8];
  out[2*i]=x+(1-alpha)*correction[4*i]+alpha*correction[4*i+2];
  out[2*i+1]=z+(1-alpha)*correction[4*i+1]+alpha*correction[4*i+3];
 }
 return 1;
}

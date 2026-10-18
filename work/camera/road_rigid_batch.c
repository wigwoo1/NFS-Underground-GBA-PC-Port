/* Three-term compensated float sum, following CPython3.12 semantics.
Reference: https://github.com/python/cpython/blob/v3.12.14/Python/bltinmodule.c */
#include <math.h>
#include <stddef.h>
static double sum3(double a,double b,double c){double values[3]={a,b,c},total=0.0,correction=0.0;
 for(int i=0;i<3;i++){double v=values[i],next=total+v;double residual=fabs(total)>=fabs(v)?(total-next)+v:(v-next)+total;correction=correction+residual;total=next;}
 return correction!=0.0&&isfinite(correction)?total+correction:total;
}
__declspec(dllexport) int nf_road_rigid_batch(const double*world,size_t n,const double*pose,double*out){
 if(!world||!pose||!out||!n||n>32)return 0;
 for(size_t i=0;i<n;i++){double x=world[i*3]+pose[9],y=world[i*3+1]+pose[10],z=world[i*3+2]+pose[11];
 for(int k=0;k<3;k++)out[i*3+k]=sum3(x*pose[k],y*pose[k+3],z*pose[k+6]);}
 return 1;
}
__declspec(dllexport) double nf_compensated_sum3(double a,double b,double c){return sum3(a,b,c);}

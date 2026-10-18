#include <math.h>
#include <stdint.h>
#include <string.h>
extern int nf_road_edge_continuous(const double*,const double*,const uint32_t*,double*);
/* Return left/right X,U,V,Q at the requested source scan position.
   Empty coverage returns zero and preserves output. */
static int nf_road_span_core(const double*ring,unsigned count,double scan,const uint32_t*t,double out[8],int allow_degenerate){
 if(!ring||!t||!out||count<3||count>64||!isfinite(scan))return 0;
 double result[8]={1e30,0,0,0,-1e30,0,0,0};unsigned active=0;
 for(unsigned i=0;i<count;i++){
  const double*a=ring+i*6,*b=ring+((i+1)%count)*6;
  for(unsigned k=0;k<6;k++)if(!isfinite(a[k])||fabs(a[k])>100000000)return 0;
  if(a[1]>b[1]){const double*swap=a;a=b;b=swap;}
  if(scan<a[1]||scan>=b[1])continue;
  double slope[4];if(!nf_road_edge_continuous(a,b,t,slope))return 0;
  double dy=scan-a[1],v[4]={a[0]+slope[0]*dy,a[4]+slope[1]*dy,a[5]+slope[2]*dy,a[3]+slope[3]*dy};
  /* Original reciprocal is effectively divided by height+1. Bridge its
     endpoint residual only in the final unit interval, retaining integer rows. */
  double remaining=b[1]-scan;
  if(remaining<1){
   const unsigned fields[4]={0,4,5,3};double height=b[1]-a[1];
   double weight=height<1?dy/height:1-remaining;
   for(unsigned k=0;k<4;k++)v[k]+=weight*(b[fields[k]]-a[fields[k]]-slope[k]*(b[1]-a[1]));
  }
  for(unsigned k=0;k<4;k++)if(!isfinite(v[k]))return 0;
  if(v[0]<result[0])memcpy(result,v,sizeof(v));
  if(v[0]>result[4])memcpy(result+4,v,sizeof(v));
  active++;
 }
 if(active<2||(allow_degenerate?result[4]<result[0]:result[4]<=result[0]))return 0;
 memcpy(out,result,sizeof(result));return 1;
}

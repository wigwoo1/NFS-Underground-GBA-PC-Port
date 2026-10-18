#include <math.h>
#include <stdint.h>
#include <string.h>
extern int nf_road_edge_continuous(const double*,const double*,const uint32_t*,double*);
/* Return left/right X,U,V,Q at the requested source scan position.
   Empty coverage returns zero and preserves output. */
__declspec(dllexport) int nf_road_span_at(const double*ring,unsigned count,double scan,const uint32_t*t,double out[8]){
 if(!ring||!t||!out||count<3||count>64||!isfinite(scan))return 0;
 double result[8]={1e30,0,0,0,-1e30,0,0,0};unsigned active=0;
 for(unsigned i=0;i<count;i++){
  const double*a=ring+i*6,*b=ring+((i+1)%count)*6;
  for(unsigned k=0;k<6;k++)if(!isfinite(a[k])||fabs(a[k])>100000000)return 0;
  if(a[1]>b[1]){const double*swap=a;a=b;b=swap;}
  if(scan<a[1]||scan>=b[1])continue;
  double slope[4];if(!nf_road_edge_continuous(a,b,t,slope))return 0;
  double dy=scan-a[1],v[4]={a[0]+slope[0]*dy,a[4]+slope[1]*dy,a[5]+slope[2]*dy,a[3]+slope[3]*dy};
  for(unsigned k=0;k<4;k++)if(!isfinite(v[k]))return 0;
  if(v[0]<result[0])memcpy(result,v,sizeof(v));
  if(v[0]>result[4])memcpy(result+4,v,sizeof(v));
  active++;
 }
 if(active<2||result[4]<=result[0])return 0;
 memcpy(out,result,sizeof(result));return 1;
}

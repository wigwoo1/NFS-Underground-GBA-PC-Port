#include <math.h>
#include <stdint.h>
#include <string.h>
extern int nf_road_span_transition_at(const double*,unsigned,double,const uint32_t*,double*);
/* Experimental padding extension anchored to actual source spans.
   Fractional rows require both integer boundary spans: topology boundaries
   deliberately reject until an explicit boundary policy is verified.
   Output padded start and pair width; attributes remain queried separately. */
__declspec(dllexport) int nf_road_span_padding_at(const double*ring,unsigned count,double scan,const uint32_t*table,double*out){
 if(!out||!ring||count<3||count>64||!isfinite(scan))return 0;
 double row=floor(scan),t=scan-row,a[8],b[8],q[8],result[2];
 if(!nf_road_span_transition_at(ring,count,row,table,a))return 0;
 double startA=2*floor(a[0]/2),widthA=floor((a[4]-a[0])/2)+2;
 if(t==0){result[0]=startA;result[1]=widthA;}
 else{
  double upper=row+1;
  for(unsigned i=0;i<count;i++){
   unsigned j=(i+1)%count;double y=ring[i*6+1];
   if(y==ring[j*6+1]&&y>row&&y<=row+1){
    if(y<row+1)return 0; /* unresolved subcell topology boundary */
    upper=nextafter(row+1,row); /* approach from this interval */
   }
  }
  if(!nf_road_span_transition_at(ring,count,upper,table,b)||!nf_road_span_transition_at(ring,count,scan,table,q))return 0;
  double residualA=startA-a[0],residualB=2*floor(b[0]/2)-b[0];
  double widthB=floor((b[4]-b[0])/2)+2;
  result[0]=q[0]+residualA+(residualB-residualA)*t;
  result[1]=widthA+(widthB-widthA)*t;
 }
 if(result[1]<1||result[1]>32767)return 0;
 memcpy(out,result,sizeof(result));return 1;
}

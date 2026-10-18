#include <math.h>
#include <stdint.h>
#include <string.h>
extern int nf_road_span_transition_at(const double*,unsigned,double,const uint32_t*,double*);
extern int nf_road_span_limit_at(const double*,unsigned,double,const uint32_t*,double*);
/* Candidate: split original row cells at every source vertex. Half-open
   topology intervals use their own one-sided span anchors, never the next
   interval's padding. Exact integer rows retain original padding. */
__declspec(dllexport) int nf_road_span_padding_segmented(const double*ring,unsigned count,double scan,const uint32_t*table,double*out){
 if(!out||!ring||count<3||count>64||!isfinite(scan))return 0;
 double q[8],a[8],b[8],result[2];
 if(!nf_road_span_transition_at(ring,count,scan,table,q))return 0;
 if(scan==floor(scan)){result[0]=2*floor(q[0]/2);result[1]=floor((q[4]-q[0])/2)+2;}
 else{
  double lo=floor(scan),hi=lo+1;
  for(unsigned i=0;i<count;i++){
   double y=ring[i*6+1];if(!isfinite(y))return 0;
   if(y<=scan&&y>lo)lo=y;
   if(y>scan&&y<hi)hi=y;
  }
  int horizontal=0;
  for(unsigned i=0;i<count;i++)if(ring[i*6+1]==hi&&ring[((i+1)%count)*6+1]==hi)horizontal=1;
  if(hi<=lo||!nf_road_span_limit_at(ring,count,lo,table,a))return 0;
  if(horizontal||!nf_road_span_limit_at(ring,count,hi,table,b)){
   if(!nf_road_span_limit_at(ring,count,nextafter(hi,lo),table,b))return 0;
  }
  double t=(scan-lo)/(hi-lo),ra=2*floor(a[0]/2)-a[0],rb=2*floor(b[0]/2)-b[0];
  double wa=floor((a[4]-a[0])/2)+2,wb=floor((b[4]-b[0])/2)+2;
  result[0]=q[0]+ra+(rb-ra)*t;result[1]=wa+(wb-wa)*t;
 }
 if(result[1]<1||result[1]>32767)return 0;
 memcpy(out,result,sizeof(result));return 1;
}


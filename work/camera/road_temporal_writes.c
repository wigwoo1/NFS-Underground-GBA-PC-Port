#include <stdint.h>
#include <math.h>
#include <string.h>
extern int nf_road_span_transition_at(const double*,unsigned,double,const uint32_t*,double*);
extern int nf_road_temporal_padding(const double*,unsigned,const double*,unsigned,const double*,unsigned,double,double,const uint32_t*,double*);
extern double nf_road_interval_coverage(double,double,double);
/* Exact single-destination endpoint scheduler, independent of other pose topology. */
static int endpoint_write(const double*ring,unsigned count,const uint16_t*bounds,const uint32_t*table,unsigned destination,double*out,unsigned capacity,unsigned*out_count,unsigned*reason){
 double top=160;for(unsigned i=0;i<count;i++){
  for(unsigned k=0;k<6;k++)if(!isfinite(ring[i*6+k])||fabs(ring[i*6+k])>100000000){if(reason)*reason=10;return 0;}
  double y=ring[i*6+1];if(y!=floor(y)||y<-32768||y>32767){if(reason)*reason=10;return 0;}if(y<top)top=y;
 }
 double winner[3]={0,0,1};int found=0,doubled=0;
 for(int row=(int)fmax(bounds[2],top);row<=bounds[3];row+=doubled?2:1){
  double edge[8];if(!nf_road_span_transition_at(ring,count,row,table,edge))continue;
  if(edge[3]>49152)doubled=1;
  double start=floor(edge[0]/2)*2,width=floor((edge[4]-edge[0])/2)+2;if(start<-32768||start>32767||width>16384){if(reason)*reason=10;return 0;}
  double winning_pair=-1;
  for(int duplicate=0;duplicate<(doubled?2:1);duplicate++){
   double x=(double)destination-(row+duplicate)*240;if(x<start||x>=start+width*2)continue;
   double pair=floor((x-start)/2);if(pair>=winning_pair){winning_pair=pair;winner[0]=row;winner[1]=x;found=1;}
  }
 }
 if(found&&!capacity){if(reason)*reason=9;return 0;}
 if(found)memcpy(out,winner,sizeof(winner));
 *out_count=found?1:0;return 1;
}
/* Diagnostic temporal interval contributors: row, sourceX, visible weight.
   Anchor sourceY must be integer; current sourceY may be fractional.
   Common source-row availability and doubled schedule are required.
   Never infer correspondence from screen polygons. Output is atomic on failure. */
static int temporal_writes_impl(const double*a,unsigned na,const double*b,unsigned nb,const double*current,unsigned nc,const uint16_t*bounds,double phase,const uint32_t*table,unsigned destination,double*out,unsigned capacity,unsigned*out_count,unsigned*reason){
 if(reason)*reason=0;
 if(!a||!b||!current||!bounds||!table||!out||!out_count||destination>=38400||!isfinite(phase)||phase<0||phase>1||na<3||nb<3||nc<3||na>64||nb>64||nc>64||bounds[2]>bounds[3]||bounds[3]>160){if(reason)*reason=1;return 0;}
 if(phase==0)return endpoint_write(a,na,bounds,table,destination,out,capacity,out_count,reason);
 if(phase==1)return endpoint_write(b,nb,bounds,table,destination,out,capacity,out_count,reason);
 double top[3]={160,160,160};const double*rings[3]={a,b,current};unsigned counts[3]={na,nb,nc};
 for(unsigned k=0;k<3;k++)for(unsigned i=0;i<counts[k];i++){
  double y=rings[k][i*6+1];if(!isfinite(y)||(k<2&&y!=floor(y))||y<-32768||y>32767){if(reason)*reason=2;return 0;}
  if(y<top[k])top[k]=y;
 }
 if(top[0]!=top[1]||top[0]!=floor(top[2])){if(reason)*reason=3;return 0;}
 double result[322*3];unsigned used=0;int doubled[3]={0,0,0};
 for(int row=(int)fmax(bounds[2],top[0]);row<=bounds[3];row+=doubled[0]?2:1){
  double edges[3][8];int valid[3];for(unsigned k=0;k<3;k++)valid[k]=nf_road_span_transition_at(rings[k],counts[k],row,table,edges[k]);
  if(valid[0]!=valid[1]||valid[0]!=valid[2]){if(reason)*reason=4;return 0;}
  if(!valid[0])continue;
  for(unsigned k=0;k<3;k++)if(edges[k][3]>49152)doubled[k]=1;
  if(doubled[0]!=doubled[1]||doubled[0]!=doubled[2]){if(reason)*reason=5;return 0;}
  double padding[2];if(!nf_road_temporal_padding(a,na,b,nb,current,nc,row,phase,table,padding)){if(reason)*reason=6;return 0;}
  /* Higher source X belongs to the later pair when duplicate destinations overlap. */
  for(int duplicate=doubled[0]?1:0;duplicate>=0;duplicate--){
   double x=(double)destination-(row+duplicate)*240,weight=nf_road_interval_coverage(padding[0],padding[1],x);
   if(weight<0){if(reason)*reason=7;return 0;}
   if(weight==0)continue;
   for(unsigned i=0;i<used;i++)result[i*3+2]*=1-weight;
   if(used>=322){if(reason)*reason=8;return 0;}
   result[used*3]=row;result[used*3+1]=x;result[used*3+2]=weight;used++;
  }
 }
 unsigned visible=0;for(unsigned i=0;i<used;i++)if(result[i*3+2]>0){memmove(result+visible*3,result+i*3,3*sizeof(double));visible++;}
 if(visible>capacity){if(reason)*reason=9;return 0;}
 memcpy(out,result,visible*3*sizeof(double));*out_count=visible;return 1;
}

__declspec(dllexport) int nf_road_temporal_writes(const double*a,unsigned na,const double*b,unsigned nb,const double*current,unsigned nc,const uint16_t*bounds,double phase,const uint32_t*table,unsigned destination,double*out,unsigned capacity,unsigned*out_count){return temporal_writes_impl(a,na,b,nb,current,nc,bounds,phase,table,destination,out,capacity,out_count,0);}
__declspec(dllexport) unsigned nf_road_temporal_writes_rejection(const double*a,unsigned na,const double*b,unsigned nb,const double*current,unsigned nc,const uint16_t*bounds,double phase,const uint32_t*table,unsigned destination){
 double out[966];unsigned count=0,reason=0;temporal_writes_impl(a,na,b,nb,current,nc,bounds,phase,table,destination,out,322,&count,&reason);return reason;
}

#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
extern int nf_road_edge_continuous(const double*,const double*,const uint32_t*,double*);
extern int nf_road_pair_uv(const int32_t*,const int32_t*,unsigned,unsigned,const uint32_t*,int32_t*);
typedef struct {int32_t row,x,u,v;} NFPairSample;
/* Source-ring endpoint sampling. Retains source lane coordinates after VRAM spill. */
__declspec(dllexport) int nf_road_pair_samples(const double*ring,unsigned count,const uint16_t*bounds,const uint32_t*table,NFPairSample*out){
 if(!ring||!bounds||!table||!out||count<3||count>64||bounds[2]>bounds[3]||bounds[3]>160)return 0;
 const double *ea[64],*eb[64];double slopes[64][4],top=160;unsigned n=0;
 for(unsigned i=0;i<count;i++){
  const double*a=ring+i*6,*b=ring+((i+1)%count)*6;
  for(unsigned k=0;k<6;k++)if(!isfinite(a[k])||fabs(a[k])>100000000)return 0;
  if(a[1]!=floor(a[1])||a[1]<-32768||a[1]>32767)return 0;
  if(a[1]<top)top=a[1];
  if(a[1]>b[1]){const double*t=a;a=b;b=t;}
  if(a[1]==b[1])continue;
  ea[n]=a;eb[n]=b;if(!nf_road_edge_continuous(a,b,table,slopes[n]))return 0;n++;
 }
 NFPairSample*result=calloc(38400,sizeof(*result));if(!result)return 0;
 for(unsigned i=0;i<38400;i++)result[i].row=-1;
 int scan=(int)fmax(bounds[2],top),doubled=0;
 while(scan<=bounds[3]){
  double left[4]={1e30,0,0,0},right[4]={-1e30,0,0,0};unsigned active=0;
  for(unsigned i=0;i<n;i++){
   if(scan<ea[i][1]||scan>=eb[i][1])continue;
   double dy=scan-ea[i][1],v[4]={ea[i][0]+slopes[i][0]*dy,ea[i][4]+slopes[i][1]*dy,ea[i][5]+slopes[i][2]*dy,ea[i][3]+slopes[i][3]*dy};
   if(v[0]<left[0])memcpy(left,v,sizeof(v));
   if(v[0]>right[0])memcpy(right,v,sizeof(v));
   active++;
  }
  if(active>=2&&right[0]>left[0]){
   if(left[3]>0xc000)doubled=1;
   double first=floor(left[0]/2)*2,pairs=floor((right[0]-left[0])/2)+2;
   if(first<-32768||first>32767||pairs>=32768){free(result);return 0;}
   int32_t a[3],b[3];for(unsigned k=0;k<3;k++){
    if(left[k+1]!=floor(left[k+1])||right[k+1]!=floor(right[k+1])){free(result);return 0;}
    a[k]=(int32_t)left[k+1];b[k]=(int32_t)right[k+1];
   }
   for(unsigned pair=0;pair<(unsigned)pairs;pair++){
    int32_t uv[2];if(!nf_road_pair_uv(a,b,(unsigned)pairs,pair,table,uv)){free(result);return 0;}
    for(unsigned duplicate=0;duplicate<(doubled?2u:1u);duplicate++)for(unsigned lane=0;lane<2;lane++){
     int x=(int)first+(int)pair*2+(int)lane,dest=(scan+(int)duplicate)*240+x;
     if(dest>=0&&dest<38400)result[dest]=(NFPairSample){scan,x,uv[0],uv[1]};
    }
   }
  }
  scan+=doubled?2:1;
 }
 memcpy(out,result,38400*sizeof(*result));free(result);return 1;
}


#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
extern int nf_road_edge_continuous(const double*,const double*,const uint32_t*,double*);
typedef struct {int16_t row,x;} NFSourceWrite;
typedef struct {const double*a,*b;double slopes[4];} Edge;
/* Endpoint diagnostic scheduler. Integer source scan rows, original write order. */
__declspec(dllexport) int nf_road_write_ledger(const double*ring,unsigned count,const uint16_t bounds[4],const uint32_t*table,NFSourceWrite*out){
 if(!ring||!bounds||!table||!out||count<3||count>64||bounds[2]>bounds[3]||bounds[3]>160)return 0;
 Edge edges[64];unsigned used=0;double top=160;
 for(unsigned i=0;i<count;i++){
  const double*a=ring+i*6,*b=ring+((i+1)%count)*6;
  for(unsigned k=0;k<6;k++)if(!isfinite(a[k])||fabs(a[k])>100000000)return 0;
  if(a[1]!=floor(a[1])||a[1]<-32768||a[1]>32767)return 0;
  if(a[1]<top){top=a[1];} if(a[1]>b[1]){const double*t=a;a=b;b=t;}
  if(a[1]==b[1])continue;
  edges[used].a=a;edges[used].b=b;if(!nf_road_edge_continuous(a,b,table,edges[used].slopes))return 0;used++;
 }
 NFSourceWrite*result=malloc(38400*sizeof(*result));if(!result)return 0;
 for(unsigned i=0;i<38400;i++){result[i].row=-1;result[i].x=-1;}
 int scan=(int)fmax(bounds[2],top),doubled=0;
 while(scan<=bounds[3]){
  double left=1e30,right=-1e30,leftq=0;unsigned active=0;
  for(unsigned i=0;i<used;i++){
   Edge*e=edges+i;if(scan<e->a[1]||scan>=e->b[1])continue;double dy=scan-e->a[1],x=e->a[0]+e->slopes[0]*dy,q=e->a[3]+e->slopes[3]*dy;
   if(x<left){left=x;leftq=q;}if(x>right)right=x;active++;
  }
  if(active>=2&&right>left){
   if(leftq>0xc000)doubled=1;
   double first=floor(left/2)*2,pairs=floor((right-left)/2)+2;
   if(first<-32768||first>32767||pairs>16384){free(result);return 0;}
   for(unsigned pair=0;pair<(unsigned)pairs;pair++)for(unsigned duplicate=0;duplicate<(doubled?2u:1u);duplicate++)for(unsigned lane=0;lane<2;lane++){
    int x=(int)first+(int)pair*2+(int)lane,dest=(scan+(int)duplicate)*240+x;
    if(x>32767){free(result);return 0;}if(dest>=0&&dest<38400){result[dest].row=(int16_t)scan;result[dest].x=(int16_t)x;}
   }
  }
  scan+=doubled?2:1;
 }
 memcpy(out,result,38400*sizeof(*result));free(result);return 1;
}


#include <math.h>
#include <stdint.h>
#include <string.h>
typedef struct {int16_t row,x;} NFSourceWrite;
/* Candidate visibility extension from geometry-derived write winners.
   Output sourceRow, sourceX, coverage. Missing corners have zero coverage;
   coordinates normalize over covered corners. Not final geometric AA policy. */
__declspec(dllexport) int nf_road_source_query_coverage(const NFSourceWrite*ledger,double x,double y,double*out){
 if(!ledger||!out||!isfinite(x)||!isfinite(y)||x<=-1||x>=240||y<=-1||y>=160)return 0;
 int ix=(int)floor(x),iy=(int)floor(y);double fx=x-ix,fy=y-iy,result[3]={0,0,0},anchor[2]={0,0};int anchored=0;
 for(int dy=0;dy<2;dy++)for(int dx=0;dx<2;dx++){
  double weight=(dx?fx:1-fx)*(dy?fy:1-fy);if(weight==0||ix+dx<0||ix+dx>=240||iy+dy<0||iy+dy>=160)continue;
  NFSourceWrite v=ledger[(iy+dy)*240+ix+dx];if(v.row<0||v.x<0)continue;
  if(!anchored){anchor[0]=v.row;anchor[1]=v.x;anchored=1;}
  result[0]+=weight*(v.row-anchor[0]);result[1]+=weight*(v.x-anchor[1]);result[2]+=weight;
 }
 if(result[2]<=0)return 0;
 result[0]=anchor[0]+result[0]/result[2];result[1]=anchor[1]+result[1]/result[2];memcpy(out,result,sizeof(result));return 1;
}

#include <math.h>
#include <stdint.h>
#include <string.h>
typedef struct {int16_t row,x;} NFSourceWrite;
/* Experimental query extension of the native geometry-derived write ledger.
   Preserve integer winners exactly; fractional interpolation requires every
   weighted corner to have coverage. Zero-weight/outside corners are ignored.
   Visibility boundary treatment remains a separate renderer requirement. */
__declspec(dllexport) int nf_road_source_query_continuous(const NFSourceWrite*ledger,double x,double y,double*out){
 if(!ledger||!out||!isfinite(x)||!isfinite(y)||x<0||x>239||y<0||y>159)return 0;
 int ix=(int)floor(x),iy=(int)floor(y);double fx=x-ix,fy=y-iy,result[2]={0,0};
 for(int dy=0;dy<2;dy++)for(int dx=0;dx<2;dx++){
  double weight=(dx?fx:1-fx)*(dy?fy:1-fy);if(weight==0)continue;
  if(ix+dx>=240||iy+dy>=160)return 0;
  NFSourceWrite v=ledger[(iy+dy)*240+ix+dx];if(v.row<0||v.x<0)return 0;
  result[0]+=weight*v.row;result[1]+=weight*v.x;
 }
 memcpy(out,result,sizeof(result));return 1;
}

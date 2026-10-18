#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
typedef struct {int16_t row,x;} NFSourceWrite;
extern int nf_road_write_ledger(const double*,unsigned,const uint16_t*,const uint32_t*,NFSourceWrite*);
/* Experimental multilinear row-lattice coverage moments. Original scheduler
   is unchanged. Output triples are coverage*sourceRow, coverage*sourceX, coverage.
   Does not establish continuity for X padding, Q thresholds or texture lanes.
   Bound active dimensions to prevent exponential allocation/work in live code. */
__declspec(dllexport) int nf_road_row_lattice_coverage(const double*ring,unsigned count,const uint16_t*bounds,const uint32_t*table,double*out){
 if(!ring||!bounds||!table||!out||count<3||count>64)return 0;
 double corner[384],frac[12];unsigned active[12],n=0;
 for(unsigned i=0;i<count*6;i++){if(!isfinite(ring[i]))return 0;corner[i]=ring[i];}
 for(unsigned i=0;i<count;i++){
  double y=ring[i*6+1],base=floor(y);if(base<-32768||base>32766)return 0;
  corner[i*6+1]=base;
  if(y!=base){if(n==12)return 0;active[n]=i;frac[n++]=y-base;}
 }
 double*sum=calloc(38400*3,sizeof(double));NFSourceWrite*writes=malloc(38400*sizeof(*writes));
 if(!sum||!writes){free(sum);free(writes);return 0;}
 for(unsigned mask=0;mask<(1u<<n);mask++){
  double weight=1;
  for(unsigned k=0;k<n;k++){unsigned upper=(mask>>k)&1u;weight*=upper?frac[k]:1-frac[k];corner[active[k]*6+1]=floor(ring[active[k]*6+1])+upper;}
  if(!nf_road_write_ledger(corner,count,bounds,table,writes)){free(sum);free(writes);return 0;}
  for(unsigned i=0;i<38400;i++)if(writes[i].row>=0){sum[i*3]+=weight*writes[i].row;sum[i*3+1]+=weight*writes[i].x;sum[i*3+2]+=weight;}
 }
 memcpy(out,sum,38400*3*sizeof(double));free(sum);free(writes);return 1;
}

/* Return covered per-corner winners (mask,row,x,weight) for one destination.
   Preserve masks so callers sample each corner's attributes separately.
   Capacity failures preserve both output and output count. Diagnostic only. */
__declspec(dllexport) int nf_road_row_lattice_contributors(const double*ring,unsigned count,const uint16_t*bounds,const uint32_t*table,unsigned destination,double*out,unsigned capacity,unsigned*out_count){
 if(!ring||!bounds||!table||!out||!out_count||count<3||count>64||destination>=38400||capacity>4096)return 0;
 double corner[384],frac[12];unsigned active[12],n=0;
 for(unsigned i=0;i<count*6;i++){if(!isfinite(ring[i]))return 0;corner[i]=ring[i];}
 for(unsigned i=0;i<count;i++){
  double y=ring[i*6+1],base=floor(y);if(base<-32768||base>32766)return 0;
  corner[i*6+1]=base;
  if(y!=base){if(n==12)return 0;active[n]=i;frac[n++]=y-base;}
 }

 double*result=malloc((1u<<n)*4*sizeof(double));NFSourceWrite*writes=malloc(38400*sizeof(*writes));unsigned used=0;
 if(!result||!writes){free(result);free(writes);return 0;}
 for(unsigned mask=0;mask<(1u<<n);mask++){
  double weight=1;
  for(unsigned k=0;k<n;k++){unsigned upper=(mask>>k)&1u;weight*=upper?frac[k]:1-frac[k];corner[active[k]*6+1]=floor(ring[active[k]*6+1])+upper;}
  if(!nf_road_write_ledger(corner,count,bounds,table,writes)){free(result);free(writes);return 0;}
  if(writes[destination].row<0)continue;
  result[used*4]=mask;result[used*4+1]=writes[destination].row;result[used*4+2]=writes[destination].x;result[used*4+3]=weight;used++;
 }
 if(used>capacity){free(result);free(writes);return 0;}
 memcpy(out,result,used*4*sizeof(double));*out_count=used;free(result);free(writes);return 1;
}

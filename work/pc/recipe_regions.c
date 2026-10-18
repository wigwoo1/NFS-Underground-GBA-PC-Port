#include "recipe_regions.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
struct NFPCRecipeRegions{uint64_t info[9];uint64_t rectangles[];};
NFPCRecipeRegions*nf_pc_recipe_regions_create(const NFPCRecipeCoverage*c,size_t maximum){
 uint64_t ci[10];const void*raw;size_t bytes;if(maximum>64u*1024*1024||!nf_pc_recipe_coverage_info(c,ci)||ci[8]>38400||!nf_pc_recipe_coverage_buffer(c,2,&raw,&bytes)||bytes!=ci[8]*48)return NULL;
 const uint64_t*records=raw;uint64_t*rect=calloc(ci[8]?ci[8]:1,64);if(!rect)return NULL;unsigned previous[240],current[240],pn=0,rn=0;size_t at=0;
 for(unsigned y=0;y<160;y++){unsigned cn=0;
  while(at<ci[8]&&records[at*6]/240==y){const uint64_t*record=records+at*6;unsigned left=(unsigned)(record[0]%240),right=left+1;uint64_t ordinal=record[3],refresh=record[4];if(record[1]!=ci[0]||record[2]!=ci[5]-1||!ordinal||refresh>ci[3])goto fail;at++;
   while(at<ci[8]&&right<240){const uint64_t*next=records+at*6;if(next[0]!=y*240u+right||next[1]!=record[1]||next[2]!=record[2]||next[3]!=ordinal||next[4]!=refresh)break;right++;at++;}
   unsigned id=rn;for(unsigned p=0;p<pn;p++){uint64_t*v=rect+previous[p]*8;if(v[2]==ordinal&&v[3]==refresh&&v[4]==left&&v[5]==right&&v[7]==y){id=previous[p];break;}}
   if(id==rn){uint64_t v[8]={ci[0],ci[5]-1,ordinal,refresh,left,right,y,y+1};memcpy(rect+rn*8,v,64);rn++;}else rect[id*8+7]=y+1;
   if(cn>=240)goto fail;
   current[cn++]=id;
  }
  memcpy(previous,current,cn*sizeof(*current));pn=cn;
 }
 if(at!=ci[8]||rn>ci[8])goto fail;
 size_t used=sizeof(NFPCRecipeRegions)+(size_t)rn*64;if(maximum<used)goto fail;NFPCRecipeRegions*r=malloc(used);if(!r)goto fail;memcpy(r->info,ci,6*8);r->info[6]=ci[8];r->info[7]=rn;r->info[8]=used;memcpy(r->rectangles,rect,(size_t)rn*64);free(rect);return r;
fail:free(rect);return NULL;
}
void nf_pc_recipe_regions_free(NFPCRecipeRegions*r){free(r);}
int nf_pc_recipe_regions_info(const NFPCRecipeRegions*r,uint64_t out[9]){if(!r||!out)return 0;memcpy(out,r->info,sizeof(r->info));return 1;}
int nf_pc_recipe_regions_buffer(const NFPCRecipeRegions*r,const void**out,size_t*n){if(!r||!out||!n)return 0;*out=r->rectangles;*n=r->info[7]*64;return 1;}
int nf_pc_recipe_regions_ring(const NFPCRecipeRegions*r,size_t index,const NFPCRecipeFootprint*f,const uint64_t a[5],const NFRigidPose*ca,const uint64_t b[5],const NFRigidPose*cb,double alpha,const double projection[3],void*out,size_t bytes,unsigned*count){
 uint64_t fi[6];if(!r||index>=r->info[7]||!nf_pc_recipe_footprint_info(f,fi)||!projection||!isfinite(projection[0])||!isfinite(projection[1])||!isfinite(projection[2])||projection[2]<=0||!out||bytes<288||!count)return 0;const uint64_t*v=r->rectangles+index*8;if(fi[0]!=v[0]||fi[1]!=v[1]||fi[2]!=v[2]||fi[4]!=v[3])return 0;
 const double xy[4][2]={{v[4],v[6]},{v[5],v[6]},{v[5],v[7]},{v[4],v[7]}};double camera[4][3],clipped[6][3],ring[6][6];unsigned n=0;
 for(unsigned i=0;i<4;i++)if(!nf_pc_recipe_footprint_sample_anchored(f,r->info,a,ca,b,cb,alpha,xy[i][0],xy[i][1],camera[i]))return 0;
 for(unsigned i=0;i<4;i++){const double*x=camera[(i+3)%4],*y=camera[i];int xi=x[2]>=64,yi=y[2]>=64;if(xi!=yi){double t=(64-x[2])/(y[2]-x[2]);for(unsigned k=0;k<3;k++)clipped[n][k]=x[k]+t*(y[k]-x[k]);clipped[n++][2]=64;}if(yi)memcpy(clipped[n++],y,24);}
 if(n>6)return 0;
 for(unsigned i=0;i<n;i++){double q=1/clipped[i][2],values[6]={projection[0]+projection[2]*clipped[i][0]*q,projection[1]+projection[2]*clipped[i][1]*q,clipped[i][2],0,0,q};for(unsigned k=0;k<6;k++)if(!isfinite(values[k]))return 0;memcpy(ring[i],values,48);}
 if(n)memcpy(out,ring,n*48);
 *count=n;return 1;
}

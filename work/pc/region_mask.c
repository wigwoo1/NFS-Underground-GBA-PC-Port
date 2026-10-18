#include "region_mask.h"
#include <string.h>
#include <math.h>
int nf_pc_recipe_region_mask_ring(const NFPCRecipeRegions*r,size_t index,const NFPCRecipeFootprint*f,const uint64_t a[5],const NFRigidPose*ca,const uint64_t b[5],const NFRigidPose*cb,double alpha,const double projection[3],void*out,size_t bytes,unsigned*count){
 uint64_t ri[9],fi[6];const void*raw;size_t rn;if(!nf_pc_recipe_regions_info(r,ri)||index>=ri[7]||!nf_pc_recipe_regions_buffer(r,&raw,&rn)||rn!=ri[7]*64||!nf_pc_recipe_footprint_info(f,fi)||!projection||!isfinite(projection[0])||!isfinite(projection[1])||!isfinite(projection[2])||projection[2]<=0||!out||bytes<288||!count)return 0;
 const uint64_t*v=(const uint64_t*)raw+index*8;if(fi[0]!=v[0]||fi[1]!=v[1]||fi[2]!=v[2]||fi[4]!=v[3]||!a||!b)return 0;const NFRigidPose*owner=!memcmp(ri,a,40)?ca:!memcmp(ri,b,40)?cb:NULL;if(!owner)return 0;
 const double xy[4][2]={{v[4],v[6]},{v[5],v[6]},{v[5],v[7]},{v[4],v[7]}};double camera[4][6],clipped[6][6],ring[6][6];unsigned n=0;
 for(unsigned i=0;i<4;i++){double lifted[4];if(!nf_pc_recipe_footprint_sample_anchored(f,ri,a,ca,b,cb,alpha,xy[i][0],xy[i][1],camera[i])||!nf_pc_recipe_footprint_lift_pose(f,owner,xy[i][0],xy[i][1],lifted))return 0;camera[i][3]=xy[i][0]*lifted[3];camera[i][4]=xy[i][1]*lifted[3];camera[i][5]=lifted[3];}
 for(unsigned i=0;i<4;i++){const double*x=camera[(i+3)%4],*y=camera[i];int xi=x[2]>=64,yi=y[2]>=64;if(xi!=yi){double t=(64-x[2])/(y[2]-x[2]);for(unsigned k=0;k<6;k++)clipped[n][k]=x[k]+t*(y[k]-x[k]);clipped[n++][2]=64;}if(yi)memcpy(clipped[n++],y,48);}
 for(unsigned i=0;i<n;i++){const double*p=clipped[i];if(p[5]<=0)return 0;double values[6]={projection[0]+projection[2]*p[0]/p[2],projection[1]+projection[2]*p[1]/p[2],p[2],p[3]/p[5],p[4]/p[5],p[5]/p[2]};for(unsigned k=0;k<6;k++)if(!isfinite(values[k]))return 0;memcpy(ring[i],values,48);}
 if(n)memcpy(out,ring,n*48);
 *count=n;return 1;
}

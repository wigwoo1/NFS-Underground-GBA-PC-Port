#include <stdint.h>
#include <string.h>
#include <math.h>
#include "road_source_attributes.h"
extern int nf_road_camera_continuous(const double*,const int32_t*,double*);
extern int nf_road_near_continuous(const double*,const double*,double,const uint32_t*,double*);
extern int nf_road_point_project_fractional(const double*,const double*,unsigned,unsigned,const int32_t*,const uint32_t*,double*);
static int source_project(const double point[5],const NFRoadSourceAttributes*raw,const int32_t*projection,const uint32_t*table,double out[5]){
 if(!nf_road_point_project_fractional(point,point+3,raw->shift,raw->stored_height,projection,table,out))return 0;
 if(raw->affine)for(unsigned k=0;k<2;k++){
  int32_t base=(int32_t)floor(point[3+k]);double frac=point[3+k]-base,value=0;
  for(unsigned j=0;j<2;j++){double weight=j?frac:1-frac;if(!weight)continue;uint32_t a=(uint32_t)(base+(int32_t)j);uint32_t scaled=k?a*raw->stored_height:a<<raw->shift;value+=weight*(int32_t)(scaled<<1);}
  out[3+k]=value;
 }
 return 1;
}
/* Source-order ring emission; output x,y,q,projectedU,projectedV. */
__declspec(dllexport) int nf_road_source_ring(const double*world,unsigned count,const NFRoadSourceAttributes*raw,const int32_t*matrix,const int32_t*projection,const uint32_t*table,double*out,unsigned capacity,unsigned*out_count){
 if(!world||!raw||!matrix||!projection||!table||!out||!out_count||count<3||count>32||raw->count!=count||raw->affine>1)return 0;
 double points[32][5],result[64][5];unsigned n=0;
 for(unsigned i=0;i<count;i++){
  if(!nf_road_camera_continuous(world+i*3,matrix,points[i]))return 0;
  points[i][3]=raw->attributes[i][0];points[i][4]=raw->attributes[i][1];
 }
 for(unsigned i=0;i<count;i++){
  unsigned j=(i+1)%count;int behind_a=points[i][2]<64,behind_b=points[j][2]<64;
  if(behind_a&&behind_b)continue;
  double clipped[5];if(behind_a!=behind_b){
   if(!nf_road_near_continuous(points[i],points[j],64,table,clipped))return 0;
   if(!source_project(clipped,raw,projection,table,result[n++]))return 0;
  }
  if(!behind_b&&(!behind_a||behind_a!=behind_b)){
   if(!source_project(points[j],raw,projection,table,result[n++]))return 0;
  }
 }
 if(n>capacity)return 0;
 memcpy(out,result,n*5*sizeof(double));*out_count=n;return 1;
}

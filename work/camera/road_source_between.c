#include "road_source_ring.c"
extern int nf_road_camera_between(const double*,const int32_t*,const int32_t*,double,double*);
__declspec(dllexport) int nf_road_source_ring_camera_points(const double*camera,unsigned count,const NFRoadSourceAttributes*raw,const int32_t*projection,const uint32_t*table,double*out,unsigned capacity,unsigned*out_count){
 if(!camera||!raw||!projection||!table||!out||!out_count||count<3||count>32||raw->count!=count||raw->affine>1)return 0;
 double points[32][5],result[64][5];unsigned n=0;
 for(unsigned i=0;i<count;i++){
  for(unsigned k=0;k<3;k++){if(!isfinite(camera[i*3+k]))return 0;points[i][k]=camera[i*3+k];}
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
__declspec(dllexport) int nf_road_source_ring_between(const double*world,unsigned count,const NFRoadSourceAttributes*raw,const int32_t*a,const int32_t*b,double phase,const int32_t*projection,const uint32_t*table,double*out,unsigned capacity,unsigned*out_count){
 if(!world||count<3||count>32)return 0;
 double camera[96];for(unsigned i=0;i<count;i++)if(!nf_road_camera_between(world+i*3,a,b,phase,camera+i*3))return 0;
 return nf_road_source_ring_camera_points(camera,count,raw,projection,table,out,capacity,out_count);
}

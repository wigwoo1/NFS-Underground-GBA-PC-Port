#include <assert.h>
#include <math.h>
typedef struct {double x,y,z;} NFPoint3;
typedef struct {NFPoint3 p;double u,v;} RoadVertex;
#include "road_view_clip.h"
int main(void){
 RoadVertex input[3]={{{-10,0,100},0,0},{{30,0,200},1,0},{{10,40,100},0,1}},out[8];
 unsigned n=road_view_clip(input,3,out,0,20,5,30);assert(n>=3&&n<=7);
 for(unsigned i=0;i<n;i++){
  assert(out[i].p.x>=0&&out[i].p.x<=20&&out[i].p.z>0&&out[i].p.y>=5&&out[i].p.y<=30);
  /* q and u*q are affine across projected triangle. */
  double q=.01-.000125*(out[i].p.x+10)+.0000625*out[i].p.y;
  double uq=.000125*(out[i].p.x+10)-.0000625*out[i].p.y;
  assert(fabs(1/out[i].p.z-q)<1e-12);assert(fabs(out[i].u/out[i].p.z-uq)<1e-12);
 }
 assert(road_view_clip(input,3,out,40,50,0,40)==0);
 assert(road_view_clip(input,3,out,20,0,0,40)==0);
 assert(road_view_clip(input,3,out,-20,40,0,40)==3);
 assert(road_view_clip(input,3,out,-20,40,50,60)==0);
 assert(road_view_clip(input,3,out,-20,40,30,20)==0);
 for(unsigned trial=0;trial<500;trial++){
  double l=-15+(trial*17%40),r=l+1+(trial*13%25),t=-5+(trial*11%40),b=t+1+(trial*7%25);
  n=road_view_clip(input,3,out,l,r,t,b);assert(n<=7);
  for(unsigned i=0;i<n;i++){
   assert(out[i].p.x>=l-1e-10&&out[i].p.x<=r+1e-10&&out[i].p.y>=t-1e-10&&out[i].p.y<=b+1e-10);
   double q=.01-.000125*(out[i].p.x+10)+.0000625*out[i].p.y;
   double uq=.000125*(out[i].p.x+10)-.0000625*out[i].p.y;
   assert(fabs(1/out[i].p.z-q)<1e-12&&fabs(out[i].u/out[i].p.z-uq)<1e-12);
   assert(fabs(out[i].v/out[i].p.z-.00025*out[i].p.y)<1e-12);
  }
  n=road_view_clip_mode(input,3,out,l,r,t,b,1);assert(n<=7);
  for(unsigned i=0;i<n;i++){
   double q=.01-.000125*(out[i].p.x+10)+.0000625*out[i].p.y;
   assert(fabs(1/out[i].p.z-q)<1e-12);
   assert(fabs(out[i].u-((out[i].p.x+10)/40-out[i].p.y/80))<1e-12);
   assert(fabs(out[i].v-out[i].p.y/40)<1e-12);
  }
 }
 return 0;
}

#define main preview_program_main
#include "model_preview.c"
#undef main
#include <assert.h>
#include <math.h>
int main(void){
 /* UVs follow an affine field over the face, including newly cut edges. */
 for(int step=-100;step<=100;step++){
  RoadVertex input[4],clipped[8];
  NFPoint3 corners[]={{-2,-1,step},{2,-1,step+100},{2,1,step+100},{-2,1,step}};
  for(unsigned i=0;i<4;i++){NFPoint3 p=corners[i];input[i]=(RoadVertex){p,2*p.x+3*p.y+5,7*p.x-p.y-2};}
  for(unsigned plane=0;plane<2;plane++){
   double z=plane?64:1;unsigned count=texture_near_clip(input,4,clipped,z);assert(count<=6);
   for(unsigned i=0;i<count;i++){
    RoadVertex v=clipped[i];assert(v.p.z>=z);
    assert(fabs(v.u-(2*v.p.x+3*v.p.y+5))<1e-12);
    assert(fabs(v.v-(7*v.p.x-v.p.y-2))<1e-12);
   }
  }
 }
 RoadVertex triangle[]={{{-2,0,0},0,0},{{2,0,2},1,0},{{0,2,2},0,1}},cut[6];
 assert(texture_near_clip(triangle,3,cut,1)==4);
 assert(cut[0].p.x==-1&&cut[0].p.y==1&&cut[0].u==0&&cut[0].v==.5);
 assert(cut[1].p.x==0&&cut[1].p.y==0&&cut[1].u==.5&&cut[1].v==0);
 NFPoint3 out[64];
 NFPoint3 inside[]={{-1,-1,100},{1,-1,100},{0,1,100}};
 assert(near_clip(inside,3,out)==3);
 for(unsigned i=0;i<3;i++)assert(out[i].x==inside[i].x&&out[i].y==inside[i].y&&out[i].z==inside[i].z);
 NFPoint3 outside[]={{-1,-1,20},{1,-1,20},{0,1,20}};
 assert(near_clip(outside,3,out)==0);
 NFPoint3 crossing[]={{-2,0,32},{2,0,96},{0,2,96}};
 assert(near_clip(crossing,3,out)==4);
 unsigned on_plane=0;for(unsigned i=0;i<4;i++){assert(out[i].z>=64);on_plane+=out[i].z==64;}
 assert(on_plane==2);
 NFPoint3 boundary[]={{0,0,64},{1,0,64},{0,1,64}};
 assert(near_clip(boundary,3,out)==3);
 for(int step=0;step<257;step++){
  NFPoint3 ring[]={{-3,-2,step},{3,-2,step+100},{3,2,step+100},{-3,2,step}};
  unsigned n=near_clip(ring,4,out);assert(n<=8);
  for(unsigned i=0;i<n;i++)assert(isfinite(out[i].x)&&isfinite(out[i].y)&&out[i].z>=64);
 }
 puts("PASS: analytical textured crossing, 402 textured moving cases, inside/outside/boundary and 257 wireframe moving cases");
 return 0;
}

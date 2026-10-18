#include "rigid_motion.h"
#include "road_corrected_clip.h"
#include "road_triangulate.h"
#include "road_near_continuity.h"
__declspec(dllexport) int nf_road_project_policy_component(const NFRigidPose*camera,const NFPoint3*world,const double*uv,unsigned count,const NFRoadSourceAttributes*raw,const uint32_t*table,const double*projection,RoadVertex*out,unsigned*vertices,unsigned policy){
 if(!camera||!world||!uv||!raw||!table||!projection||!out||!vertices||count<3||count>32||policy>6)return 0;
 NFRigidPose fixed={{0,0,0},{0,0,0,1}};NFPoint3 points[32];RoadVertex in[32],clipped[64],triangles[192];unsigned n;
 if(!nf_rigid_scene_sample(camera,camera,&fixed,&fixed,0,world,count,points))return 0;
 for(unsigned i=0;i<count;i++)in[i]=(RoadVertex){points[i],uv[i*2],uv[i*2+1]};
 if(policy==1)n=texture_near_clip(in,count,clipped,64);
 else if(policy==2){unsigned adjusted;if(!texture_near_clip_continuous(in,count,clipped,raw,table,&n,&adjusted))return 0;}
 else if(!texture_near_clip_corrected(in,count,clipped,64,raw,table,&n))return 0;
 if(policy==6){unsigned at=0;for(unsigned i=0;i<count;i++){unsigned previous=(i+count-1)%count;NFPoint3 a=in[previous].p,b=in[i].p;int ai=a.z>=64,bi=b.z>=64;if(ai!=bi){double behind=ai?b.z:a.z,front=ai?a.z:b.z,delta=front-behind;unsigned lo=(unsigned)floor(delta);if(lo>=32767)return 0;double f=delta-lo,r=table[lo]*(1-f)+table[lo+1]*f,t=(64-behind)*r/16777216.0;clipped[at].p.x=ai?b.x-(b.x-a.x)*t:a.x+(b.x-a.x)*t;clipped[at].p.y=ai?b.y-(b.y-a.y)*t:a.y+(b.y-a.y)*t;at++;}if(bi)at++;}if(at!=n)return 0;} for(unsigned i=0;i<n;i++){if(policy==3){int z=(int)floor(clipped[i].p.z);if(z<1||z>=32768)return 0;uint32_t scale=(uint32_t)(((uint64_t)table[z]*(uint32_t)projection[2])>>7);int32_t x=(int32_t)floor(clipped[i].p.x),y=(int32_t)floor(clipped[i].p.y);clipped[i].p.x=projection[0]+((int32_t)((uint32_t)(x>>1)*scale)>>16);clipped[i].p.y=projection[1]+((int32_t)((uint32_t)(y>>1)*scale)>>16);}else{clipped[i].p.x=projection[0]+projection[2]*clipped[i].p.x/clipped[i].p.z;clipped[i].p.y=projection[1]+projection[2]*clipped[i].p.y/clipped[i].p.z;if(policy==5&&clipped[i].p.z==64){double factor=(double)table[64]*64/16777216.0;clipped[i].p.x=projection[0]+(clipped[i].p.x-projection[0])*factor;clipped[i].p.y=projection[1]+(clipped[i].p.y-projection[1])*factor;}}}
 if(policy==4&&!raw->affine)for(unsigned i=0;i<n;i++){double z=clipped[i].p.z;unsigned lo=(unsigned)floor(z);double t=z-lo;if(lo<1||lo>=32767)return 0;double q=table[lo]*(1-t)+table[lo+1]*t;if(q<=0)return 0;clipped[i].p.z=16777216.0/q;}
 unsigned total=road_triangulate(clipped,n,triangles);memcpy(out,triangles,total*sizeof(*out));*vertices=total;return 1;
}
__declspec(dllexport) unsigned nf_road_generic_component(const RoadVertex*in,unsigned n,RoadVertex*out){return texture_near_clip(in,n,out,64);}

__declspec(dllexport) int nf_road_project_component(const NFRigidPose*c,const NFPoint3*w,const double*u,unsigned n,const NFRoadSourceAttributes*r,const uint32_t*t,const double*p,RoadVertex*out,unsigned*count){return nf_road_project_policy_component(c,w,u,n,r,t,p,out,count,0);}


/* Diagnostic source ring export before triangulation, same native geometry path. */
__declspec(dllexport) int nf_road_project_ring_component(const NFRigidPose*camera,const NFPoint3*world,const double*uv,unsigned count,const NFRoadSourceAttributes*raw,const uint32_t*table,const double*projection,RoadVertex*out,unsigned*vertices,unsigned policy){
 if(!camera||!world||!uv||!raw||!table||!projection||!out||!vertices||count<3||count>32||policy)return 0;
 NFRigidPose fixed={{0,0,0},{0,0,0,1}};NFPoint3 points[32];RoadVertex in[32],clipped[64];unsigned n;
 if(!nf_rigid_scene_sample(camera,camera,&fixed,&fixed,0,world,count,points))return 0;
 for(unsigned i=0;i<count;i++)in[i]=(RoadVertex){points[i],uv[i*2],uv[i*2+1]};
 if(!texture_near_clip_corrected(in,count,clipped,64,raw,table,&n))return 0;
 for(unsigned i=0;i<n;i++){clipped[i].p.x=projection[0]+projection[2]*clipped[i].p.x/clipped[i].p.z;clipped[i].p.y=projection[1]+projection[2]*clipped[i].p.y/clipped[i].p.z;}
 memcpy(out,clipped,n*sizeof(*out));*vertices=n;return 1;
}

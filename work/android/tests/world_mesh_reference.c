#include "rigid_motion.h"
#include "road_near_clip.h"
#include "road_triangulate.h"
#include <stdint.h>
#include <stddef.h>
#include <string.h>
__declspec(dllexport) int world_mesh_reference(const void*model,size_t model_bytes,const void*surface,size_t surface_bytes,unsigned affine,double*camera,float*out,unsigned capacity,unsigned*written){
 if(!model||model_bytes<160||!surface||surface_bytes<12||!camera||!out||!written||affine>1)return 0;const uint8_t*m=model,*s=surface;uint32_t h[3];memcpy(h,s,12);if(h[0]<3||h[0]>32||surface_bytes<12+(size_t)h[0]*40)return 0;
 double projection[3];NFRigidPose pose,fixed={{0,0,0},{0,0,0,1}};NFPoint3 input[32],points[32];memcpy(projection,m+24,24);memcpy(&pose,m+48,56);memcpy(input,s+12,h[0]*24);
 if(!nf_rigid_scene_sample(&pose,&pose,&fixed,&fixed,0,input,h[0],points))return 0;memcpy(camera,points,h[0]*24);RoadVertex in[32],clipped[64],triangles[192];
 for(unsigned i=0;i<h[0];i++){double uv[2];memcpy(uv,s+12+h[0]*24+i*16,16);in[i]=(RoadVertex){points[i],uv[0],uv[1]};}
 unsigned n=texture_near_clip(in,h[0],clipped,64);for(unsigned i=0;i<n;i++){clipped[i].p.x=projection[0]+projection[2]*clipped[i].p.x/clipped[i].p.z;clipped[i].p.y=projection[1]+projection[2]*clipped[i].p.y/clipped[i].p.z;}
 unsigned count=road_triangulate(clipped,n,triangles);if(count>capacity)return 0;for(unsigned i=0;i<count;i++){double q=affine?1:1/triangles[i].p.z;out[i*5]=triangles[i].p.x;out[i*5+1]=triangles[i].p.y;out[i*5+2]=triangles[i].u*q;out[i*5+3]=triangles[i].v*q;out[i*5+4]=q;}*written=count;return 1;
}

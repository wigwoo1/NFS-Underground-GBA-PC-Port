#include "rigid_motion.h"
#include "road_near_clip.h"
#include <stdint.h>
#include <stddef.h>
#include <string.h>
__declspec(dllexport) int model_reference(const void*data,size_t bytes,double*camera,unsigned camera_count,float*out,unsigned capacity,unsigned*written){
 if(!data||!camera||!out||!written||bytes<160)return 0;const uint8_t*m=data;uint32_t h[6];memcpy(h,m,24);
 if(h[0]!=0x324d464e||!h[1]||h[1]>2048||!h[2]||h[2]>512||h[3]>4096||camera_count<h[1])return 0;
 size_t texture=160+(size_t)h[1]*24+h[2]+(size_t)h[3]*18;if(texture>bytes)return 0;
 NFRigidPose poses[2];double projection[3];NFPoint3 model[2048],points[2048];memcpy(projection,m+24,24);memcpy(poses,m+48,112);memcpy(model,m+160,h[1]*24);
 if(!nf_rigid_scene_sample(poses,poses,poses+1,poses+1,0,model,h[1],points))return 0;memcpy(camera,points,h[1]*24);
 const uint8_t*sizes=m+160+h[1]*24,*ids=sizes+h[2],*uv=ids+h[3]*2;unsigned corner=0,used=0;
 for(unsigned face=0;face<h[2];face++){unsigned count=sizes[face];if(count<3||count>32||corner+count>h[3])return 0;RoadVertex in[32],clipped[64];
  for(unsigned i=0;i<count;i++){uint16_t id;double tex[2];memcpy(&id,ids+(corner+i)*2,2);memcpy(tex,uv+(corner+i)*16,16);if(id>=h[1])return 0;in[i]=(RoadVertex){points[id],tex[0],tex[1]};}corner+=count;
  unsigned n=texture_near_clip(in,count,clipped,1);double v[64][5],area=0;
  for(unsigned i=0;i<n;i++){double q=1/clipped[i].p.z;v[i][0]=projection[0]+projection[2]*clipped[i].p.x*q;v[i][1]=projection[1]+projection[2]*clipped[i].p.y*q;v[i][2]=clipped[i].u*q;v[i][3]=clipped[i].v*q;v[i][4]=q;}
  for(unsigned i=0;i<n;i++)area+=v[i][0]*v[(i+1)%n][1]-v[(i+1)%n][0]*v[i][1];
  if(n>=3&&area<0)for(unsigned i=1;i<n-1;i++){unsigned order[3]={0,i,i+1};for(unsigned j=0;j<3;j++){if(used>=capacity)return 0;for(unsigned k=0;k<5;k++)out[used*5+k]=(float)v[order[j]][k];used++;}}
 }if(corner!=h[3])return 0;*written=used;return 1;
}

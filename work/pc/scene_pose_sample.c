#include "scene_pose_sample.h"
#include "model_motion.h"
#include "world_motion_mesh.h"
#include <string.h>
#include <math.h>
static int unique(const NFPCScene*s,unsigned role,const uint32_t id[5]){uint64_t info[8];if(!nf_pc_scene_info(s,info))return 0;unsigned count=0;for(unsigned i=0;i<info[3];i++){uint64_t m[16],o[5];uint32_t other[5];if(!nf_pc_scene_command_info(s,i,m)||!nf_pc_scene_command_source(s,i,o,other))return 0;if(m[0]==role&&!memcmp(id,other,20))count++;}return count==1;}
static int inputs(const NFPCScene*a,unsigned ai,const NFPCScene*b,unsigned bi,double alpha,unsigned model,uint64_t am[16],uint64_t bm[16],uint64_t ak[5],uint64_t bk[5],uint32_t id[5]){
 uint64_t af[8],bf[8];uint32_t other[5];if(!isfinite(alpha)||alpha<0||alpha>1||!nf_pc_scene_info(a,af)||!nf_pc_scene_info(b,bf)||af[0]!=bf[0]||bf[1]<=af[1]||bf[1]-af[1]>8||!nf_pc_scene_command_info(a,ai,am)||!nf_pc_scene_command_info(b,bi,bm)||am[1]!=model||bm[1]!=model||!nf_pc_scene_command_source(a,ai,ak,id)||!nf_pc_scene_command_source(b,bi,bk,other)||memcmp(id,other,20)||ak[0]!=bk[0]||ak[0]!=af[0]||ak[3]>UINT32_MAX||bk[3]>UINT32_MAX||!unique(a,(unsigned)am[0],id)||!unique(b,(unsigned)bm[0],id))return 0;
 return !memcmp(ak,bk,40)||(bk[1]>ak[1]&&bk[3]>ak[3]&&bk[3]-ak[3]<=8);
}
NFPCModelMesh* nf_pc_scene_model_pose(const NFPCScene*a,unsigned ai,const NFPCScene*b,unsigned bi,double alpha,size_t maximum){
 uint64_t am[16],bm[16],ak[5],bk[5];uint32_t id[5];const void*x,*y;size_t xn,yn;if(!inputs(a,ai,b,bi,alpha,1,am,bm,ak,bk,id)||!nf_pc_scene_motion_model(a,ai,&x,&xn)||!nf_pc_scene_motion_model(b,bi,&y,&yn))return NULL;
 if(!memcmp(ak,bk,40))return nf_pc_model_mesh_decode(alpha==1?y:x,alpha==1?yn:xn,maximum);
 NFPCModelMotionKey ka={ak[0],(uint32_t)ak[3],{0}},kb={bk[0],(uint32_t)bk[3],{0}};memcpy(ka.identity,id,20);memcpy(kb.identity,id,20);return nf_pc_model_motion_sample(x,xn,&ka,y,yn,&kb,alpha,maximum);
}
NFPCWorldMesh* nf_pc_scene_world_pose(const NFPCScene*a,unsigned ai,const NFPCScene*b,unsigned bi,double alpha,size_t maximum){
 uint64_t am[16],bm[16],ak[5],bk[5];uint32_t id[5];const void*x,*y;size_t xn,yn;if(!inputs(a,ai,b,bi,alpha,0,am,bm,ak,bk,id)||!nf_pc_scene_motion_packet(a,(unsigned)am[0],&x,&xn)||!nf_pc_scene_motion_packet(b,(unsigned)bm[0],&y,&yn))return NULL;
 if(!memcmp(ak,bk,40)){NFPCWorld*w=nf_pc_world_decode(alpha==1?y:x,alpha==1?yn:xn,64u*1024*1024);if(!w)return NULL;NFPCWorldMesh*m=nf_pc_world_mesh(w,(unsigned)(alpha==1?bm[2]:am[2]),maximum);nf_pc_world_free(w);return m;}
 NFPCWorldMotionKey ka={ak[0],(uint32_t)ak[3],{0}},kb={bk[0],(uint32_t)bk[3],{0}};memcpy(ka.identity,id,20);memcpy(kb.identity,id,20);return nf_pc_world_motion_mesh(x,xn,(unsigned)am[2],&ka,y,yn,(unsigned)bm[2],&kb,alpha,maximum);
}

static int scene_owner(const NFPCScene*s,unsigned role,uint64_t out[5]){uint64_t info[8];if(!nf_pc_scene_info(s,info)||role>=info[2])return 0;for(unsigned i=0;i<info[3];i++){uint64_t m[16];uint32_t id[5];if(!nf_pc_scene_command_info(s,i,m))return 0;if(m[0]==role)return nf_pc_scene_command_source(s,i,out,id);}return 0;}
NFPCWorldMotionOwner* nf_pc_scene_world_pose_owner(const NFPCScene*a,unsigned ar,const NFPCScene*b,unsigned br,double alpha,size_t maximum){
 uint64_t af[8],bf[8],ak[5],bk[5];const void*x,*y;size_t xn,yn;if(!isfinite(alpha)||alpha<0||alpha>=1||!nf_pc_scene_info(a,af)||!nf_pc_scene_info(b,bf)||af[0]!=bf[0]||bf[1]<=af[1]||bf[1]-af[1]>8||!scene_owner(a,ar,ak)||!scene_owner(b,br,bk)||!nf_pc_scene_motion_packet(a,ar,&x,&xn)||!nf_pc_scene_motion_packet(b,br,&y,&yn))return NULL;
 return nf_pc_world_motion_owner_prepare(x,xn,ak,y,yn,bk,alpha,maximum);
}

int nf_pc_scene_pose_alpha(const NFPCScene*a,unsigned ar,const NFPCScene*b,unsigned br,double target,double*out){
 uint64_t af[8],bf[8],ak[5],bk[5],at[16],bt[16];const void*x,*y;size_t xn,yn;
 if(!out||!isfinite(target)||!nf_pc_scene_info(a,af)||!nf_pc_scene_info(b,bf)||af[0]!=bf[0]||bf[1]<=af[1]||bf[1]-af[1]>8||!scene_owner(a,ar,ak)||!scene_owner(b,br,bk)||bk[1]<=ak[1]||bk[3]<=ak[3]||bk[3]-ak[3]>8||!nf_pc_scene_motion_timing(a,ar,&x,&xn)||!nf_pc_scene_motion_timing(b,br,&y,&yn)||xn!=184||yn!=184)return 0;
 memcpy(at,x,128);memcpy(bt,y,128);
 if(at[0]!=af[0]||bt[0]!=af[0]||memcmp(at,ak,4*sizeof(uint64_t))||memcmp(bt,bk,4*sizeof(uint64_t))||at[12]!=ak[4]||bt[12]!=bk[4]||bt[6]<=at[6]||bt[6]-at[6]>8||target<(double)at[6]||target>(double)bt[6])return 0;
 *out=(target-(double)at[6])/(double)(bt[6]-at[6]);return 1;
}

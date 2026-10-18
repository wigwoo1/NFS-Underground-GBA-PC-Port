#include "world_camera_motion.h"
#include "source_road.h"
#include "../camera/rigid_motion.h"
#include <math.h>
#include <string.h>
int nf_visibility_view_sample(const uint32_t[12],const uint32_t[12],double,uint32_t[12]);
static uint32_t word(const void*p,unsigned at){uint32_t v;memcpy(&v,(const unsigned char*)p+at,4);return v;}
int nf_pc_world_camera_sample(const void*a,size_t an,const NFPCWorldMotionKey*ak,const void*b,size_t bn,const NFPCWorldMotionKey*bk,double alpha,void*out,size_t capacity){
 if(!a||!b||an!=56||bn!=56||!ak||!bk||!out||capacity<56||!ak->epoch||ak->epoch!=bk->epoch||!ak->identity[0]||memcmp(ak->identity,bk->identity,sizeof(ak->identity))||bk->refresh<=ak->refresh||bk->refresh-ak->refresh>8||!isfinite(alpha)||alpha<0||alpha>1||word(a,0)!=1||word(b,0)!=1||(word(a,4)&3)||(word(b,4)&3))return 0;
 uint32_t x[12],y[12],sample[14];memcpy(x,(const unsigned char*)a+8,48);memcpy(y,(const unsigned char*)b+8,48);
 if(!nf_visibility_view_sample(x,y,alpha,sample+2))return 0;
 memcpy(sample,alpha==1?b:a,8);memmove(out,sample,56);return 1;
}
int nf_pc_world_camera_points(const void*a,size_t an,const NFPCWorldMotionKey*ak,const void*b,size_t bn,const NFPCWorldMotionKey*bk,double alpha,const double*world,unsigned count,double*out){
 if(!world||!out||!count||count>32)return 0;
 uint32_t camera[14];double sampled[96];if(!nf_pc_world_camera_sample(a,an,ak,b,bn,bk,alpha,camera,sizeof(camera)))return 0;
 for(unsigned i=0;i<count;i++)if(!nf_pc_road_camera(camera,sizeof(camera),world+i*3,sampled+i*3))return 0;
 memcpy(out,sampled,count*3*sizeof(double));return 1;
}
int nf_pc_world_rigid_points(const void*a,size_t an,const NFPCWorldMotionKey*ak,const void*b,size_t bn,const NFPCWorldMotionKey*bk,double alpha,const double*world,unsigned count,double*out){
 if(!a||!b||an!=sizeof(NFRigidPose)||bn!=sizeof(NFRigidPose)||!world||!out||!count||count>32||!ak||!bk||!ak->epoch||ak->epoch!=bk->epoch||!ak->identity[0]||memcmp(ak->identity,bk->identity,sizeof(ak->identity))||bk->refresh<=ak->refresh||bk->refresh-ak->refresh>8||!isfinite(alpha)||alpha<0||alpha>1)return 0;
 NFRigidPose x,y,p;memcpy(&x,a,sizeof(x));memcpy(&y,b,sizeof(y));if(!nf_pose_sample(&x,&y,alpha,&p))return 0;
 if(alpha==0||alpha==1){p=alpha==0?x:y;double n=sqrt(p.rotation.x*p.rotation.x+p.rotation.y*p.rotation.y+p.rotation.z*p.rotation.z+p.rotation.w*p.rotation.w);p.rotation.x/=n;p.rotation.y/=n;p.rotation.z/=n;p.rotation.w/=n;}
 double sampled[96],qx=p.rotation.x,qy=p.rotation.y,qz=p.rotation.z,qw=p.rotation.w;
 for(unsigned i=0;i<count;i++){double v[3]={world[i*3]-p.position.x,world[i*3+1]-p.position.y,world[i*3+2]-p.position.z};for(unsigned k=0;k<3;k++)if(!isfinite(v[k]))return 0;double tx=2*(qy*v[2]-qz*v[1]),ty=2*(qz*v[0]-qx*v[2]),tz=2*(qx*v[1]-qy*v[0]);double r[3]={v[0]+qw*tx+qy*tz-qz*ty,v[1]+qw*ty+qz*tx-qx*tz,v[2]+qw*tz+qx*ty-qy*tx};for(unsigned k=0;k<3;k++){if(!isfinite(r[k]))return 0;sampled[i*3+k]=r[k];}}
 memcpy(out,sampled,count*3*sizeof(double));return 1;
}

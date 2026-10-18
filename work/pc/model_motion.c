#include "model_motion.h"
#include "../camera/rigid_motion.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
static void get_pose(const unsigned char*p,NFRigidPose*out){memcpy(out,p,sizeof(*out));}
static uint32_t u32(const unsigned char*p,size_t at){uint32_t v;memcpy(&v,p+at,4);return v;}
NFPCModelMesh* nf_pc_model_motion_sample(const void*a,size_t an,const NFPCModelMotionKey*ak,const void*b,size_t bn,const NFPCModelMotionKey*bk,double alpha,size_t maximum){
 if(!a||!b||!ak||!bk||!ak->epoch||ak->epoch!=bk->epoch||!ak->identity[0]||memcmp(ak->identity,bk->identity,sizeof(ak->identity))||bk->refresh<=ak->refresh||bk->refresh-ak->refresh>8||!isfinite(alpha)||alpha<0||alpha>1||an!=bn||an<160||an>32u*1024*1024)return NULL;
 const unsigned char*pa=a,*pb=b;
 size_t geometry_end=160+(size_t)u32(pa,4)*24+u32(pa,8)+(size_t)u32(pa,12)*18;
 if(geometry_end>an||memcmp(pa,pb,24)||memcmp(pa+160,pb+160,geometry_end-160))return NULL;
 NFPCModelMesh*ma=nf_pc_model_mesh_decode(a,an,maximum);if(!ma)return NULL;
 NFPCModelMesh*mb=nf_pc_model_mesh_decode(b,bn,maximum);if(!mb){nf_pc_model_mesh_free(ma);return NULL;}
 if(alpha==0){nf_pc_model_mesh_free(mb);return ma;}
 if(alpha==1){nf_pc_model_mesh_free(ma);return mb;}
 nf_pc_model_mesh_free(ma);nf_pc_model_mesh_free(mb);
 unsigned char*sample=malloc(an);if(!sample)return NULL;memcpy(sample,a,an);
 for(unsigned i=0;i<3;i++){double x,y,v;memcpy(&x,pa+24+i*8,8);memcpy(&y,pb+24+i*8,8);v=(1-alpha)*x+alpha*y;memcpy(sample+24+i*8,&v,8);}
 for(unsigned i=0;i<2;i++){NFRigidPose x,y,v;size_t at=48+i*56;get_pose(pa+at,&x);get_pose(pb+at,&y);if(!nf_pose_sample(&x,&y,alpha,&v)){free(sample);return NULL;}memcpy(sample+at,&v,sizeof(v));}
 NFPCModelMesh*result=nf_pc_model_mesh_decode(sample,an,maximum);free(sample);return result;
}

#include "world_motion_mesh.h"
#include "../camera/rigid_motion.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
static uint32_t word(const void*p,size_t at){uint32_t v;memcpy(&v,(const unsigned char*)p+at,4);return v;}
static int same_buffer(const NFPCWorld*a,unsigned ai,const NFPCWorld*b,unsigned bi,unsigned kind){const void*x,*y;size_t xn,yn;return nf_pc_world_surface_buffer(a,ai,kind,&x,&xn)&&nf_pc_world_surface_buffer(b,bi,kind,&y,&yn)&&xn==yn&&(!xn||!memcmp(x,y,xn));}
NFPCWorldMesh* nf_pc_world_motion_mesh(const void*a,size_t an,unsigned ai,const NFPCWorldMotionKey*ak,const void*b,size_t bn,unsigned bi,const NFPCWorldMotionKey*bk,double alpha,size_t maximum){
 if(!a||!b||!ak||!bk||!ak->epoch||ak->epoch!=bk->epoch||memcmp(ak->identity,bk->identity,sizeof(ak->identity))||bk->refresh<=ak->refresh||bk->refresh-ak->refresh>8||!isfinite(alpha)||alpha<0||alpha>1)return NULL;
 NFPCWorld*wa=nf_pc_world_decode(a,an,64u*1024*1024),*wb=nf_pc_world_decode(b,bn,64u*1024*1024),*sampled=NULL;NFPCWorldMesh*ma=NULL,*mb=NULL,*result=NULL;unsigned char*copy=NULL;
 if(!wa||!wb)goto done;
 uint64_t am[12],bm[12],wi[4];const void*id,*ca,*cb,*fixed;size_t n,can,cbn;
 if(!nf_pc_world_surface_info(wa,ai,am)||!nf_pc_world_surface_info(wb,bi,bm)||memcmp(am,bm,4*sizeof(uint64_t))||!same_buffer(wa,ai,wb,bi,0)||!same_buffer(wa,ai,wb,bi,1))goto done;
 if(!nf_pc_world_surface_buffer(wa,ai,9,&id,&n)||n!=20||memcmp(id,ak->identity,20)||!nf_pc_world_surface_buffer(wb,bi,9,&id,&n)||n!=20||memcmp(id,bk->identity,20))goto done;
 if(!nf_pc_world_surface_buffer(wa,ai,8,&fixed,&n)||n||!nf_pc_world_surface_buffer(wb,bi,8,&fixed,&n)||n)goto done;
 ma=nf_pc_world_mesh(wa,ai,maximum);mb=nf_pc_world_mesh(wb,bi,maximum);if(!ma||!mb)goto done;
 if(alpha==0){result=ma;ma=NULL;goto done;}if(alpha==1){result=mb;mb=NULL;goto done;}
 if(!nf_pc_world_model(wa,0,&ca,&can)||can<160||!nf_pc_world_model(wb,0,&cb,&cbn)||cbn<160||!nf_pc_world_info(wa,wi))goto done;
 NFRigidPose x,y,p;memcpy(&x,(const unsigned char*)ca+48,56);memcpy(&y,(const unsigned char*)cb+48,56);if(!nf_pose_sample(&x,&y,alpha,&p))goto done;
 double projection[3];for(unsigned i=0;i<3;i++){double v,w;memcpy(&v,(const unsigned char*)ca+24+i*8,8);memcpy(&w,(const unsigned char*)cb+24+i*8,8);projection[i]=(1-alpha)*v+alpha*w;}
 copy=malloc(an);if(!copy)goto done;memcpy(copy,a,an);size_t section=word(copy,36),bytes=word(copy,40);
 for(unsigned i=0;i<wi[1];i++){size_t offset=section,length=bytes;if(wi[1]>1){offset+=word(copy,section+8+i*8);length=word(copy,section+12+i*8);}if(offset>an||length>an-offset||length<160)goto done;memcpy(copy+offset+24,projection,24);memcpy(copy+offset+48,&p,56);}
 sampled=nf_pc_world_decode(copy,an,64u*1024*1024);if(sampled)result=nf_pc_world_mesh(sampled,ai,maximum);
done:free(copy);nf_pc_world_free(sampled);nf_pc_world_free(wa);nf_pc_world_free(wb);nf_pc_world_mesh_free(ma);nf_pc_world_mesh_free(mb);return result;
}

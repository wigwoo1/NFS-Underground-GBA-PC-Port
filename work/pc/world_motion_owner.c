#include "world_motion_owner.h"
#include "../camera/rigid_motion.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
struct NFPCWorldMotionOwner{NFPCWorld*a,*b,*sample;double alpha;uint64_t info[14],map[128][3];unsigned class_ok[128];};
static uint32_t word(const void*p,size_t at){uint32_t v;memcpy(&v,(const unsigned char*)p+at,4);return v;}
static int identity(const NFPCWorld*w,unsigned i,uint32_t out[5]){const void*p;size_t n;if(!nf_pc_world_surface_buffer(w,i,9,&p,&n)||n!=20)return 0;memcpy(out,p,20);return 1;}
static int same(const NFPCWorld*a,unsigned ai,const NFPCWorld*b,unsigned bi,unsigned kind){const void*x,*y;size_t xn,yn;return nf_pc_world_surface_buffer(a,ai,kind,&x,&xn)&&nf_pc_world_surface_buffer(b,bi,kind,&y,&yn)&&xn==yn&&(!xn||!memcmp(x,y,xn));}
static int binding(const void*p,const uint64_t k[5]){return k[1]==word(p,16)&&k[2]==word(p,20)&&k[3]==word(p,24)&&k[4]==word(p,28);}
static int camera(const NFPCWorld*w,const void**first,uint64_t info[4]){size_t n;if(!nf_pc_world_info(w,info)||!nf_pc_world_model(w,0,first,&n)||n<160)return 0;for(unsigned i=0;i<3;i++){double v;memcpy(&v,(const unsigned char*)*first+24+i*8,8);if(!isfinite(v)||(i==2&&v<=0))return 0;}for(unsigned i=1;i<info[1];i++){const void*p;if(!nf_pc_world_model(w,i,&p,&n)||n<160||memcmp((const unsigned char*)p+24,(const unsigned char*)*first+24,80))return 0;}return 1;}
static int source_class(const NFPCWorldMotionOwner*o,unsigned surface){
 uint32_t id[5],other[5];uint64_t source[12],meta[12];if(!identity(o->a,surface,id)||!nf_pc_world_surface_info(o->a,surface,source))return 0;
 const NFPCWorld*worlds[]={o->a,o->b};for(unsigned ep=0;ep<2;ep++){unsigned found=0;for(unsigned j=0;j<o->info[3+ep];j++){if(!identity(worlds[ep],j,other))return 0;if(memcmp(id,other,20))continue;found++;const void*fixed;size_t n;if(!nf_pc_world_surface_info(worlds[ep],j,meta)||memcmp(source,meta,4*sizeof(uint64_t))||!same(o->a,surface,worlds[ep],j,0)||!same(o->a,surface,worlds[ep],j,1)||!nf_pc_world_surface_buffer(worlds[ep],j,8,&fixed,&n)||n)return 0;}if(!found)return 0;}
 return 1;
}
NFPCWorldMotionOwner* nf_pc_world_motion_owner_prepare(const void*a,size_t an,const uint64_t ak[5],const void*b,size_t bn,const uint64_t bk[5],double alpha,size_t maximum){
 if(!a||!b||!ak||!bk||!ak[0]||ak[0]!=bk[0]||ak[1]>=bk[1]||ak[3]>=bk[3]||bk[3]-ak[3]>8||!isfinite(alpha)||alpha<0||alpha>1||maximum<sizeof(NFPCWorldMotionOwner)||maximum>64u*1024*1024)return NULL;
 NFPCWorldMotionOwner*o=calloc(1,sizeof(*o));if(!o)return NULL;o->alpha=alpha;o->info[0]=ak[0];o->info[1]=ak[3];o->info[2]=bk[3];o->info[5]=sizeof(*o);unsigned char*copy=NULL;uint64_t ai[4],bi[4];const void*ca,*cb;
 o->a=nf_pc_world_decode(a,an,maximum-o->info[5]);if(!o->a||!binding(a,ak)||!camera(o->a,&ca,ai))goto fail;o->info[5]+=ai[3];o->info[6]++;
 o->b=nf_pc_world_decode(b,bn,maximum-o->info[5]);if(!o->b||!binding(b,bk)||!camera(o->b,&cb,bi))goto fail;o->info[5]+=bi[3];o->info[6]++;o->info[3]=ai[0];o->info[4]=bi[0];
 NFRigidPose x,y,p;memcpy(&x,(const unsigned char*)ca+48,56);memcpy(&y,(const unsigned char*)cb+48,56);if(!nf_pose_sample(&x,&y,alpha,&p))goto fail;
 if(alpha>0&&alpha<1){
  if(an>maximum-o->info[5])goto fail;
  copy=malloc(an);if(!copy)goto fail;memcpy(copy,a,an);double projection[3];for(unsigned i=0;i<3;i++){double v,w;memcpy(&v,(const unsigned char*)ca+24+i*8,8);memcpy(&w,(const unsigned char*)cb+24+i*8,8);projection[i]=(1-alpha)*v+alpha*w;if(!isfinite(projection[i])||(i==2&&projection[i]<=0))goto fail;}
  size_t section=word(copy,36),bytes=word(copy,40);for(unsigned i=0;i<ai[1];i++){size_t offset=section,length=bytes;if(ai[1]>1){offset+=word(copy,section+8+i*8);length=word(copy,section+12+i*8);}if(offset>an||length>an-offset||length<160)goto fail;memcpy(copy+offset+24,projection,24);memcpy(copy+offset+48,&p,56);}
  o->sample=nf_pc_world_decode(copy,an,maximum-o->info[5]);free(copy);copy=NULL;if(!o->sample)goto fail;uint64_t si[4];if(!nf_pc_world_info(o->sample,si))goto fail;o->info[5]+=si[3];o->info[6]++;
 }
 unsigned used[128]={0};for(unsigned i=0;i<ai[0];i++){
  uint32_t id[5],other[5];if(!identity(o->a,i,id))goto fail;o->map[i][1]=UINT32_MAX;o->map[i][2]=id[0];unsigned duplicate=0,count=0,target=0;
  for(unsigned k=0;k<ai[0];k++)if(k!=i){if(!identity(o->a,k,other))goto fail;if(!memcmp(id,other,20))duplicate=1;}
  for(unsigned j=0;j<bi[0];j++){if(!identity(o->b,j,other))goto fail;if(!memcmp(id,other,20)){used[j]=1;target=j;count++;}}
  unsigned state=NFPC_MOTION_OLDER_ONLY;if(duplicate||count>1)state=NFPC_MOTION_AMBIGUOUS;
  else if(count==1){o->map[i][1]=target;uint64_t am[12],bm[12];const void*fixed;size_t n;if(!nf_pc_world_surface_info(o->a,i,am)||!nf_pc_world_surface_info(o->b,target,bm))goto fail;
   if(memcmp(am,bm,4*sizeof(uint64_t))||!same(o->a,i,o->b,target,0)||!same(o->a,i,o->b,target,1))state=NFPC_MOTION_CHANGED;
   else{if(!nf_pc_world_surface_buffer(o->a,i,8,&fixed,&n))goto fail;unsigned has=n!=0;if(!nf_pc_world_surface_buffer(o->b,target,8,&fixed,&n))goto fail;state=has||n?NFPC_MOTION_UNSUPPORTED:NFPC_MOTION_SHARED;}}
  o->map[i][0]=state;o->info[state==1?7:state==2?8:state==3?10:state==4?11:12]++;
 }for(unsigned j=0;j<bi[0];j++)if(!used[j])o->info[9]++;
 for(unsigned i=0;i<ai[0];i++){
  if(o->map[i][0]==NFPC_MOTION_SHARED){o->class_ok[i]=1;continue;}
  if(o->map[i][0]!=NFPC_MOTION_AMBIGUOUS)continue;
  uint32_t id[5],other[5];if(!identity(o->a,i,id))goto fail;unsigned reused=0;
  for(unsigned j=0;j<i;j++){if(!identity(o->a,j,other))goto fail;if(!memcmp(id,other,20)){o->class_ok[i]=o->class_ok[j];reused=1;break;}}
  if(!reused)o->class_ok[i]=source_class(o,i);
 }

 return o;
fail:free(copy);nf_pc_world_motion_owner_free(o);return NULL;
}
void nf_pc_world_motion_owner_free(NFPCWorldMotionOwner*o){if(o){nf_pc_world_free(o->a);nf_pc_world_free(o->b);nf_pc_world_free(o->sample);free(o);}}
int nf_pc_world_motion_owner_info(const NFPCWorldMotionOwner*o,uint64_t out[14]){if(!o||!out)return 0;memcpy(out,o->info,sizeof(o->info));return 1;}
int nf_pc_world_motion_owner_match(const NFPCWorldMotionOwner*o,unsigned i,uint64_t out[3]){if(!o||!out||i>=o->info[3])return 0;memcpy(out,o->map[i],sizeof(o->map[i]));return 1;}
NFPCWorldMesh* nf_pc_world_motion_owner_mesh(NFPCWorldMotionOwner*o,unsigned i,size_t maximum){if(!o||i>=o->info[3]||o->map[i][0]!=NFPC_MOTION_SHARED)return NULL;o->info[13]++;return nf_pc_world_mesh(o->alpha==1?o->b:o->alpha==0?o->a:o->sample,o->alpha==1?(unsigned)o->map[i][1]:i,maximum);}
int nf_pc_world_motion_owner_material(const NFPCWorldMotionOwner*o,unsigned i,const NFPCWorld**w,unsigned*surface){if(!o||!w||!surface||i>=o->info[3]||o->map[i][0]!=NFPC_MOTION_SHARED)return 0;*w=o->alpha==1?o->b:o->a;*surface=o->alpha==1?(unsigned)o->map[i][1]:i;return 1;}

NFPCWorldMesh* nf_pc_world_motion_owner_class_mesh(NFPCWorldMotionOwner*o,unsigned i,size_t maximum){if(!o||o->alpha>=1||i>=o->info[3]||!o->class_ok[i])return NULL;o->info[13]++;return nf_pc_world_mesh(o->alpha==0?o->a:o->sample,i,maximum);}
int nf_pc_world_motion_owner_class_material(const NFPCWorldMotionOwner*o,unsigned i,const NFPCWorld**w,unsigned*surface){if(!o||!w||!surface||o->alpha>=1||i>=o->info[3]||!o->class_ok[i])return 0;*w=o->a;*surface=i;return 1;}

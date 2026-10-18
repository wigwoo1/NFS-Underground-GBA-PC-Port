#include "visibility_snapshot.h"
#include "rigid_motion.h"
#include <math.h>
#include <string.h>
int nf_projection_focal_sample(const uint32_t a[2],const uint32_t b[2],double alpha,uint32_t out[2]){
 if(!a||!b||!out||!isfinite(alpha)||alpha<0||alpha>1)return 0;
 uint32_t sampled[2];for(unsigned i=0;i<2;i++){
  if(!a[i]||a[i]>32767||!b[i]||b[i]>32767)return 0;
  sampled[i]=alpha==0?a[i]:alpha==1?b[i]:(uint32_t)round((1-alpha)*(double)a[i]+alpha*(double)b[i]);
 }
 memcpy(out,sampled,sizeof(sampled));return 1;
}
__declspec(dllexport) int nf_visibility_view_sample(const uint32_t a[12],const uint32_t b[12],double alpha,uint32_t out[12]){
 if(!a||!b||!out||!isfinite(alpha)||alpha<0||alpha>1)return 0;
 NFPoint3 origin={0};NFRigidPose poses[2];
 if(!nf_pose_decode((const int32_t*)a,&origin,poses)||!nf_pose_decode((const int32_t*)b,&origin,poses+1))return 0;
 if(alpha==0){memmove(out,a,48);return 1;}if(alpha==1){memmove(out,b,48);return 1;}
 uint8_t dummy[164]={0},record[164];int32_t matrix[12];
 if(!nf_object_pose_sample(dummy,poses,poses+1,alpha,record,matrix))return 0;
 if(!memcmp(a,b,36))memcpy(matrix,a,36);
 for(unsigned i=9;i<12;i++)matrix[i]=(int32_t)round((1-alpha)*(double)(int32_t)a[i]+alpha*(double)(int32_t)b[i]);
 memcpy(out,matrix,48);return 1;
}
/* Research adapter for the measured planar camera contract. */
static int decode(const NFVisibilityPoseInputs*p,NFRigidPose*out){
 if(!p)return 0;
 const int32_t*v=(const int32_t*)p->view;
 for(unsigned i=0;i<3;i++)for(unsigned j=0;j<3;j++)if(p->query[i*3+j]!=p->view[j*3+i])return 0;
 if(p->query[9]||p->query[10]||p->query[11]||v[1]||v[3]||v[5]||v[7]||v[4]!=16384)return 0;
 if(-(double)v[9]!=floor((double)(int32_t)p->base[0]/256.)||-(double)v[11]!=floor((double)(int32_t)p->base[1]/256.))return 0;
 NFPoint3 pos={-(double)v[9],-(double)v[10],-(double)v[11]};
 return nf_pose_decode(v,&pos,out);
}
__declspec(dllexport) int nf_visibility_pose_sample(const NFVisibilityPoseInputs*a,const NFVisibilityPoseInputs*b,double alpha,NFVisibilityPoseInputs*out){
 NFRigidPose pa,pb,p;
 if(!out||!isfinite(alpha)||alpha<0||alpha>1||!decode(a,&pa)||!decode(b,&pb))return 0;
 if(alpha==0){memmove(out,a,sizeof(*out));return 1;}if(alpha==1){memmove(out,b,sizeof(*out));return 1;}
 if(!nf_pose_sample(&pa,&pb,alpha,&p))return 0;
 double x=p.rotation.x,y=p.rotation.y,z=p.rotation.z,w=p.rotation.w;
 double r[9]={1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)};
 NFVisibilityPoseInputs result={0};
 for(unsigned i=0;i<3;i++)for(unsigned j=0;j<3;j++){int32_t q=(int32_t)round(r[i*3+j]*16384.);result.query[i*3+j]=(uint32_t)q;result.view[j*3+i]=(uint32_t)q;}
 for(unsigned i=0;i<2;i++){double value=(1-alpha)*(double)(int32_t)a->base[i]+alpha*(double)(int32_t)b->base[i];result.base[i]=(uint32_t)(int32_t)round(value);}
 result.view[9]=(uint32_t)(int32_t)-floor((double)(int32_t)result.base[0]/256.);
 result.view[11]=(uint32_t)(int32_t)-floor((double)(int32_t)result.base[1]/256.);
 result.view[10]=(uint32_t)(int32_t)round((1-alpha)*(double)(int32_t)a->view[10]+alpha*(double)(int32_t)b->view[10]);
 memcpy(out,&result,sizeof(result));return 1;
}

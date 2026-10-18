#include "rigid_motion.h"
#include <math.h>
#include <string.h>
static NFPoint3 add(NFPoint3 a,NFPoint3 b){return (NFPoint3){a.x+b.x,a.y+b.y,a.z+b.z};}
static NFPoint3 sub(NFPoint3 a,NFPoint3 b){return (NFPoint3){a.x-b.x,a.y-b.y,a.z-b.z};}
static NFPoint3 mul(NFPoint3 a,double s){return (NFPoint3){a.x*s,a.y*s,a.z*s};}
static double dot(NFPoint3 a,NFPoint3 b){return a.x*b.x+a.y*b.y+a.z*b.z;}
static NFPoint3 cross(NFPoint3 a,NFPoint3 b){return (NFPoint3){a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
static int finite_point(NFPoint3 a){return isfinite(a.x)&&isfinite(a.y)&&isfinite(a.z);}
static int unit(NFPoint3*v){double n=sqrt(dot(*v,*v));if(!isfinite(n)||n<1e-10)return 0;*v=mul(*v,1/n);return 1;}
static int unitq(NFQuaternion*q){double n=sqrt(q->x*q->x+q->y*q->y+q->z*q->z+q->w*q->w);if(!isfinite(n)||n<1e-10)return 0;q->x/=n;q->y/=n;q->z/=n;q->w/=n;return 1;}
static NFPoint3 rotate(NFQuaternion q,NFPoint3 p){NFPoint3 v={q.x,q.y,q.z};NFPoint3 t=mul(cross(v,p),2);return add(p,add(mul(t,q.w),cross(v,t)));}
int nf_pose_decode(const int32_t m[12],const NFPoint3*position,NFRigidPose*out){
 if(!m||!position||!out||!finite_point(*position))return 0;
 NFPoint3 x={m[0]/16384.,m[1]/16384.,m[2]/16384.},y={m[3]/16384.,m[4]/16384.,m[5]/16384.},z0={m[6]/16384.,m[7]/16384.,m[8]/16384.};
 if(!unit(&x))return 0;
 y=sub(y,mul(x,dot(x,y)));if(!unit(&y))return 0;
 NFPoint3 z=cross(x,y);if(dot(z,z0)<=1e-10)return 0;
 NFQuaternion q;double trace=x.x+y.y+z.z,s;
 if(trace>0){s=sqrt(trace+1)*2;q=(NFQuaternion){(y.z-z.y)/s,(z.x-x.z)/s,(x.y-y.x)/s,s/4};}
 else if(x.x>y.y&&x.x>z.z){s=sqrt(1+x.x-y.y-z.z)*2;q=(NFQuaternion){s/4,(y.x+x.y)/s,(z.x+x.z)/s,(y.z-z.y)/s};}
 else if(y.y>z.z){s=sqrt(1+y.y-x.x-z.z)*2;q=(NFQuaternion){(y.x+x.y)/s,s/4,(z.y+y.z)/s,(z.x-x.z)/s};}
 else{s=sqrt(1+z.z-x.x-y.y)*2;q=(NFQuaternion){(z.x+x.z)/s,(z.y+y.z)/s,s/4,(x.y-y.x)/s};}
 if(!unitq(&q))return 0;
 *out=(NFRigidPose){*position,q};return 1;
}
int nf_pose_sample(const NFRigidPose*a,const NFRigidPose*b,double alpha,NFRigidPose*out){
 if(!a||!b||!out||!isfinite(alpha)||!finite_point(a->position)||!finite_point(b->position))return 0;
 NFQuaternion qa=a->rotation,qb=b->rotation;if(!unitq(&qa)||!unitq(&qb))return 0;
 if(alpha<0)alpha=0;
 if(alpha>1)alpha=1;
 double d=qa.x*qb.x+qa.y*qb.y+qa.z*qb.z+qa.w*qb.w;
 if(d<0){qb=(NFQuaternion){-qb.x,-qb.y,-qb.z,-qb.w};d=-d;}
 if(d>1)d=1;
 double wa=1-alpha,wb=alpha;
 if(d<0.9995){double angle=acos(d),denom=sin(angle);wa=sin((1-alpha)*angle)/denom;wb=sin(alpha*angle)/denom;}
 NFQuaternion q={qa.x*wa+qb.x*wb,qa.y*wa+qb.y*wb,qa.z*wa+qb.z*wb,qa.w*wa+qb.w*wb};
 if(!unitq(&q))return 0;
 NFPoint3 p=add(mul(a->position,1-alpha),mul(b->position,alpha));
 if(!finite_point(p))return 0;
 *out=(NFRigidPose){p,q};return 1;
}
int nf_rigid_scene_sample(const NFRigidPose*ca,const NFRigidPose*cb,const NFRigidPose*oa,const NFRigidPose*ob,double alpha,const NFPoint3*model,unsigned count,NFPoint3*out){
 NFRigidPose camera,object;
 if((count&&(!model||!out))||!nf_pose_sample(ca,cb,alpha,&camera)||!nf_pose_sample(oa,ob,alpha,&object))return 0;
 for(unsigned i=0;i<count;i++)if(!finite_point(model[i]))return 0;
 for(unsigned i=0;i<count;i++)out[i]=rotate(camera.rotation,sub(add(rotate(object.rotation,model[i]),object.position),camera.position));
 return 1;
}
static uint16_t motion_half(const uint8_t*p){uint16_t v;memcpy(&v,p,2);return v;}
static uint32_t motion_word(const uint8_t*p){uint32_t v;memcpy(&v,p,4);return v;}
static uint32_t motion_phase(uint32_t a,uint32_t b,unsigned mask,double alpha){
 int32_t delta=(int32_t)((b-a)&mask);if((unsigned)delta>(mask+1)/2)delta-=(int32_t)(mask+1);
 return (a+(uint32_t)(int32_t)round(alpha*delta))&mask;
}
static uint32_t pool_sample_detail[4];
void nf_object_pool_sample_detail(uint32_t out[4]){if(out)memcpy(out,pool_sample_detail,16);}
static int pool_mismatch(unsigned index,unsigned offset,uint32_t a,uint32_t b){pool_sample_detail[0]=index;pool_sample_detail[1]=offset;pool_sample_detail[2]=a;pool_sample_detail[3]=b;return 0;}
int nf_object_pool_sample_masked(const uint8_t*a,const uint8_t*b,unsigned count,const uint8_t mask[32],double alpha,uint8_t*out){
 memset(pool_sample_detail,0,16);
 if(!a||!b||!out||!count||count>256||!isfinite(alpha)||alpha<0||alpha>1)return 0;
 if(alpha==0||alpha==1){memmove(out,alpha==0?a:b,count*164u);return 1;}
 uint8_t staged[256*164];memcpy(staged,a,count*164u);
 for(unsigned i=0;i<count;i++){
  if(mask&&!(mask[i/8]&(1u<<(i&7))))continue;
  const uint8_t*x=a+i*164,*y=b+i*164;uint8_t*z=staged+i*164;
  /* Activation/deactivation is discrete. Uninitialized/dead endpoint bytes
     cannot supply a continuous pose; retain the complete older record. */
  if(!motion_half(x+72)||!motion_half(y+72))continue;
  if(motion_half(x+72)!=motion_half(y+72))return pool_mismatch(i,72,motion_half(x+72),motion_half(y+72));
  if(motion_half(x+78)!=motion_half(y+78))return pool_mismatch(i,78,motion_half(x+78),motion_half(y+78));
  if((motion_half(x+8)&3)!=(motion_half(y+8)&3))return pool_mismatch(i,8,motion_half(x+8),motion_half(y+8));
  if(motion_word(x+140)!=motion_word(y+140))return pool_mismatch(i,140,motion_word(x+140),motion_word(y+140));
  if(motion_word(x+132)!=motion_word(y+132))return pool_mismatch(i,132,motion_word(x+132),motion_word(y+132));
  for(unsigned j=12;j<=20;j+=4){double v=round((1-alpha)*(int32_t)motion_word(x+j)+alpha*(int32_t)motion_word(y+j));if(v<INT32_MIN||v>INT32_MAX)return 0;int32_t value=(int32_t)v;memcpy(z+j,&value,4);}
  for(unsigned j=48;j<=52;j+=2){uint16_t angle=(uint16_t)motion_phase(motion_half(x+j),motion_half(y+j),16383,alpha);memcpy(z+j,&angle,2);}
  uint32_t heading=(motion_word(x+44)&~UINT32_C(0x3fffff))|motion_phase(motion_word(x+44),motion_word(y+44),0x3fffff,alpha);memcpy(z+44,&heading,4);
 }
 memmove(out,staged,count*164u);return 1;
}
int nf_object_pool_sample(const uint8_t*a,const uint8_t*b,unsigned count,double alpha,uint8_t*out){return nf_object_pool_sample_masked(a,b,count,NULL,alpha,out);}
int nf_object_pose_sample(const uint8_t object[164],const NFRigidPose*a,
 const NFRigidPose*b,double alpha,uint8_t out[164],int32_t rotation[12]){
 NFRigidPose pose;
 if(!object||!out||!rotation||!isfinite(alpha)||alpha<0||alpha>1||
    !nf_pose_sample(a,b,alpha,&pose))return 0;
 double coords[3]={pose.position.x,pose.position.y,pose.position.z};
 int32_t xyz[3],matrix[12]={0};
 for(unsigned i=0;i<3;i++){
  double v=round(coords[i]*256.);
  if(!isfinite(v)||v<INT32_MIN||v>INT32_MAX)return 0;
  xyz[i]=(int32_t)v;
 }
 double x=pose.rotation.x,y=pose.rotation.y,z=pose.rotation.z,w=pose.rotation.w;
 double rows[9]={1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),
  2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),
  2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)};
 for(unsigned i=0;i<3;i++)for(unsigned j=0;j<3;j++)
  matrix[j*3+i]=(int32_t)round(rows[i*3+j]*16384.);
 uint8_t record[164];memcpy(record,object,164);memcpy(record+12,xyz,12);
 memcpy(out,record,164);memcpy(rotation,matrix,48);return 1;
}

int nf_model_world_pose(const int32_t cm[12],const int32_t mm[12],NFRigidPose*camera_out,NFRigidPose*object_out){
 if(!cm||!mm||!camera_out||!object_out)return 0;
 double a[3][3],inv[3][3];
 for(unsigned r=0;r<3;r++)for(unsigned col=0;col<3;col++)a[r][col]=cm[col*3+r]/16384.;
 double det=a[0][0]*(a[1][1]*a[2][2]-a[1][2]*a[2][1])-a[0][1]*(a[1][0]*a[2][2]-a[1][2]*a[2][0])+a[0][2]*(a[1][0]*a[2][1]-a[1][1]*a[2][0]);
 if(!isfinite(det)||det<=1e-8)return 0;
 for(unsigned r=0;r<3;r++)for(unsigned col=0;col<3;col++)inv[r][col]=(a[(col+1)%3][(r+1)%3]*a[(col+2)%3][(r+2)%3]-a[(col+1)%3][(r+2)%3]*a[(col+2)%3][(r+1)%3])/det;
 int32_t world[12]={0};double wp[3];
 for(unsigned r=0;r<3;r++){
  wp[r]=-((double)cm[9+r]);for(unsigned k=0;k<3;k++)wp[r]+=inv[r][k]*mm[9+k];
  for(unsigned col=0;col<3;col++){
   double value=0;for(unsigned k=0;k<3;k++)value+=inv[r][k]*mm[col*3+k];
   value=round(value);if(!isfinite(value)||value<INT32_MIN||value>INT32_MAX)return 0;world[col*3+r]=(int32_t)value;
  }
 }
 NFRigidPose camera,object;NFPoint3 cp={-((double)cm[9]),-((double)cm[10]),-((double)cm[11])},op={wp[0],wp[1],wp[2]};
 if(!nf_pose_decode(cm,&cp,&camera)||!nf_pose_decode(world,&op,&object))return 0;
 *camera_out=camera;*object_out=object;return 1;
}

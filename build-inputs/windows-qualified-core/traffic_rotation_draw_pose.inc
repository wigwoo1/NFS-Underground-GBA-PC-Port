/* Recover independent world rotation only after exact original Q14 products. */
#include "camera/rigid_motion.h"
static void nf_traffic_mul9(const int32_t a[12],const int32_t b[12],int32_t out[12]){
 for(unsigned r=0;r<3;r++)for(unsigned col=0;col<3;col++){
  uint32_t sum=0;for(unsigned k=0;k<3;k++)sum+=(uint32_t)a[r*3+k]*(uint32_t)b[k*3+col];
  int32_t signed_sum;memcpy(&signed_sum,&sum,4);out[r*3+col]=signed_sum>>14;
 }
}
static int nf_traffic_rotation_for_camera(const int32_t camera[12],const int32_t actual[12],int32_t out[12]){
 if(!camera||!actual||!out)return 0;
 int32_t cm[12]={0},mm[12]={0},rotation[12];
 memcpy(cm,camera,36);memcpy(mm,actual,36);NFRigidPose cp,op;uint8_t object[164]={0},sampled[164];
 if(!nf_model_world_pose(cm,mm,&cp,&op)||!nf_object_pose_sample(object,&op,&op,0,sampled,rotation))return 0;
 memcpy(out,rotation,48);return 1;
}
static int nf_traffic_rotation_pose(const int32_t camera[12],const int32_t first[12],const int32_t second[12],const int32_t actual[12],int32_t out[12]){
 if(!camera||!first||!second||!actual||!out)return 0;
 int32_t intermediate[12]={0},expected[12]={0},cm[12]={0},mm[12]={0},rotation[12];
 nf_traffic_mul9(first,camera,intermediate);nf_traffic_mul9(intermediate,second,expected);
 if(memcmp(expected,actual,36))return 0;
 memcpy(cm,camera,36);memcpy(mm,actual,36);NFRigidPose cp,op;uint8_t object[164]={0},sampled[164];
 if(!nf_model_world_pose(cm,mm,&cp,&op)||!nf_object_pose_sample(object,&op,&op,0,sampled,rotation))return 0;
 memcpy(out,rotation,48);return 1;
}

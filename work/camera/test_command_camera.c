#include "command_camera.h"
#include <assert.h>
#include <string.h>
int main(void){
 NFRigidPose cameras[2]={{{1,2,3},{0,0,0,1}},{{4,5,6},{0,1,0,0}}},poses[4],original[4];
 for(unsigned i=0;i<4;i++)poses[i]=(NFRigidPose){{10+i,20+i,30+i},{0,0,0,1}};
 memcpy(original,poses,sizeof(poses));assert(nf_command_camera_apply(NULL,0,0,poses)&&!memcmp(original,poses,sizeof(poses)));
 assert(!nf_command_camera_apply(cameras,2,2,poses)&&!memcmp(original,poses,sizeof(poses)));
 for(unsigned i=0;i<2;i++){assert(nf_command_camera_apply(cameras,2,i,poses));assert(!memcmp(poses,cameras+i,56)&&!memcmp(poses+1,cameras+i,56));assert(!memcmp(poses+2,original+2,112));}
 assert(!nf_command_camera_apply(NULL,2,0,poses));return 0;
}

#ifndef NF_COMMAND_CAMERA_H
#define NF_COMMAND_CAMERA_H
#include "rigid_motion.h"
/* Final sampled camera replaces camera endpoints only; object motion stays intact. */
static int nf_command_camera_apply(const NFRigidPose*cameras,unsigned count,unsigned command,NFRigidPose poses[4]){
 if(!poses)return 0;if(!cameras)return count==0;if(command>=count)return 0;
 poses[0]=poses[1]=cameras[command];return 1;
}
#endif

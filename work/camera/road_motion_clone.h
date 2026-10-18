#ifndef NF_ROAD_MOTION_CLONE_H
#define NF_ROAD_MOTION_CLONE_H
#include <stdlib.h>
#include "road_bundle.h"
#include "ordered_motion_identity.h"
/* Diagnostic motion preparation. Original older command/material/2D basis is
   retained for interior alpha; unmatched commands retain their original pose.
   Exact endpoints copy exact complete source bytes. No emulator writes. */
static int nf_road_motion_clone(const void*older,size_t older_size,const void*newer,size_t newer_size,double alpha,void**out,size_t*size){
 if(!out||!size||!isfinite(alpha)||alpha<0||alpha>1)return 0;NFRoadBundle a,b;if(!nf_road_bundle_view(older,older_size,&a)||!nf_road_bundle_view(newer,newer_size,&b)||a.ordered.epoch!=b.ordered.epoch||a.ordered.packet.serial>=b.ordered.packet.serial)return 0;
 const void*basis=alpha==1?newer:older;size_t bytes=alpha==1?newer_size:older_size;NFOrderedCameraSample samples;if(alpha>0&&alpha<1&&!nf_ordered_camera_sample(&a.ordered,&b.ordered,alpha,&samples))return 0;
 void*copy=malloc(bytes);if(!copy)return 0;memcpy(copy,basis,bytes);if(alpha>0&&alpha<1){NFRoadBundle owned;if(!nf_road_bundle_view(copy,bytes,&owned)){free(copy);return 0;}
  for(unsigned i=0;i<samples.identity.older_count;i++){if(!samples.present[i])continue;memcpy((void*)(owned.ordered.cameras+i*56),samples.cameras+i,56);unsigned j=samples.identity.newer_for_older[i];unsigned x=nf_bundle_word(a.ordered.packet.section[2].data+8+i*4),y=nf_bundle_word(b.ordered.packet.section[2].data+8+j*4);
   if(x>=UINT32_MAX-15){NFSceneSection ma,mb,mo;NFRigidPose pa,pb,pose;if(!nf_scene_packet_model(&a.ordered.packet,UINT32_MAX-x,&ma)||!nf_scene_packet_model(&b.ordered.packet,UINT32_MAX-y,&mb)||!nf_scene_packet_model(&owned.ordered.packet,UINT32_MAX-x,&mo)){free(copy);return 0;}memcpy(&pa,ma.data+104,56);memcpy(&pb,mb.data+104,56);if(!nf_pose_sample(&pa,&pb,alpha,&pose)){free(copy);return 0;}memcpy((void*)(mo.data+104),&pose,56);memcpy((void*)(mo.data+48),samples.cameras+i,56);}
  }NFRoadBundle checked;if(!nf_road_bundle_view(copy,bytes,&checked)){free(copy);return 0;}
 }*out=copy;*size=bytes;return 1;
}
#endif

#ifndef NF_ORDERED_MOTION_IDENTITY_H
#define NF_ORDERED_MOTION_IDENTITY_H
#include "ordered_bundle.h"
#include "rigid_motion.h"
/* Association only. Material/topology compatibility must be proved separately.
   Matches original pass/type/kind/source; never screen coordinates or ordinals. */
typedef struct {unsigned older_count,newer_count,shared,older_only,newer_only;unsigned newer_for_older[144];} NFOrderedMotionIdentity;
static int nf_motion_event_same(const NFOrderedSceneEvent*a,const NFOrderedSceneEvent*b){return a->pass==b->pass&&a->type==b->type&&a->kind==b->kind&&a->source==b->source;}
static int nf_ordered_motion_identity(const NFOrderedBundle*a,const NFOrderedBundle*b,NFOrderedMotionIdentity*out){
 if(!a||!b||!out||!a->epoch||a->epoch!=b->epoch||a->packet.serial>=b->packet.serial||a->camera_count>144||b->camera_count>144)return 0;
 NFOrderedSceneEvent older[144],newer[144];unsigned counts[2]={0};const NFOrderedBundle*views[2]={a,b};
 for(unsigned side=0;side<2;side++){NFOrderedSceneEvent*events=side?newer:older;for(unsigned i=0;i<views[side]->event_count;i++){NFOrderedSceneEvent e;memcpy(&e,views[side]->events+i*32,32);if(e.type<3)continue;if(e.type>4||counts[side]>=144)return 0;for(unsigned j=0;j<counts[side];j++)if(nf_motion_event_same(events+j,&e))return 0;events[counts[side]++]=e;}if(counts[side]!=views[side]->camera_count)return 0;}
 NFOrderedMotionIdentity result={0};result.older_count=counts[0];result.newer_count=counts[1];unsigned used[144]={0};for(unsigned i=0;i<counts[0];i++){result.newer_for_older[i]=UINT32_MAX;for(unsigned j=0;j<counts[1];j++)if(nf_motion_event_same(older+i,newer+j)){result.newer_for_older[i]=j;used[j]=1;result.shared++;break;}if(result.newer_for_older[i]==UINT32_MAX)result.older_only++;}for(unsigned j=0;j<counts[1];j++)if(!used[j])result.newer_only++;*out=result;return 1;
}
/* Shared geometry is static in world/model space. Textures and display state
   remain discrete; this does not authorize blending visibility or materials. */
static int nf_ordered_motion_compatible(const NFOrderedBundle*a,const NFOrderedBundle*b,NFOrderedMotionIdentity*out){
 NFOrderedMotionIdentity map;if(!out||!nf_ordered_motion_identity(a,b,&map))return 0;NFWorldMetadata wa[128],wb[128];unsigned na,nb;if(!nf_scene_world_metadata_all(a->packet.section[1],wa,128,&na)||!nf_scene_world_metadata_all(b->packet.section[1],wb,128,&nb))return 0;
 for(unsigned i=0;i<map.older_count;i++){unsigned j=map.newer_for_older[i];if(j==UINT32_MAX)continue;unsigned x=nf_bundle_word(a->packet.section[2].data+8+i*4),y=nf_bundle_word(b->packet.section[2].data+8+j*4);
  if(x<na&&y<nb){NFSceneSection sa,sb;if(!nf_scene_world_surface(a->packet.section[1],x,&sa)||!nf_scene_world_surface(b->packet.section[1],y,&sb)||memcmp(sa.data,sb.data,12))return 0;size_t spatial=12+(size_t)nf_bundle_word(sa.data)*40;if(sa.size<spatial||sb.size<spatial||memcmp(sa.data,sb.data,spatial)||wa[x].mode!=wb[y].mode||wa[x].size!=wb[y].size||memcmp(wa[x].data,wb[y].data,wa[x].size))return 0;}
  else if(x>=UINT32_MAX-15&&y>=UINT32_MAX-15){NFSceneSection sa,sb;if(!nf_scene_packet_model(&a->packet,UINT32_MAX-x,&sa)||!nf_scene_packet_model(&b->packet,UINT32_MAX-y,&sb)||sa.size!=sb.size||sa.size<160||memcmp(sa.data,sb.data,48)||memcmp(sa.data+160,sb.data+160,sa.size-160))return 0;}
  else return 0;
 }*out=map;return 1;
}
/* Samples only uniquely associated camera records; unmatched records are
   explicitly absent. Caller still must validate material/topology and visibility. */
typedef struct {NFOrderedMotionIdentity identity;NFRigidPose cameras[144];unsigned present[144];} NFOrderedCameraSample;
static int nf_ordered_camera_sample(const NFOrderedBundle*a,const NFOrderedBundle*b,double alpha,NFOrderedCameraSample*out){
 if(!out||!isfinite(alpha)||alpha<0||alpha>1)return 0;NFOrderedCameraSample result={0};if(!nf_ordered_motion_compatible(a,b,&result.identity))return 0;
 for(unsigned i=0;i<result.identity.older_count;i++){unsigned j=result.identity.newer_for_older[i];if(j==UINT32_MAX)continue;NFRigidPose x,y;memcpy(&x,a->cameras+i*sizeof(x),sizeof(x));memcpy(&y,b->cameras+j*sizeof(y),sizeof(y));if(!nf_pose_sample(&x,&y,alpha,result.cameras+i))return 0;result.present[i]=1;}*out=result;return 1;
}
#endif

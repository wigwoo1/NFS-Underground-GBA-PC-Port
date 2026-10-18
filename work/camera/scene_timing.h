/* Optional read-only emulated-cycle diagnostics. No publication or clock changes.
   Included after live_scene. Rows are copied before the synchronous scene sink.
   uint64 fields: epoch,serial,begin,end,flip_cycles,first_geometry_cycles,
   last_geometry_cycles,last_pc,last_lr,vcount,DISPSTAT,until_video_event,
   models,roads,walls,rotations,last_rotation_cycles,last_camera_cycles,
   last_geometry_refresh,first_geometry_refresh. until_video_event is signed. */
#define NF_SCENE_TIMING_WORDS 20
static void scene_pose_interval_reset(void),scene_pose_reset(void);
static void scene_pose_event(struct ARMCore*,unsigned);
static void scene_pose_flip(uint32_t);
static unsigned live_scene_timing_enabled;
static uint64_t live_scene_timing_history[16][NF_SCENE_TIMING_WORDS];
static uint64_t live_scene_timing_pending[NF_SCENE_TIMING_WORDS];
static void live_scene_timing_interval_reset(void){
 scene_pose_interval_reset();
 memset(live_scene_timing_pending,0,sizeof(live_scene_timing_pending));
}
static void live_scene_timing_reset(void){
 scene_pose_reset();
 memset(live_scene_timing_history,0,sizeof(live_scene_timing_history));
 live_scene_timing_interval_reset();
}
API int nf_native_scene_timing_enable(int enabled){
 if(!c||!live_scene.assembly||live_scene.started)return 0;
 live_scene_timing_enabled=enabled!=0;live_scene_timing_reset();return 1;
}
API int nf_native_scene_timing_read(uint64_t epoch,uint32_t serial,uint64_t out[NF_SCENE_TIMING_WORDS]){
 if(!out||!live_scene_timing_enabled||!live_scene.assembly||epoch!=live_scene_epoch)return 0;
 const uint64_t*row=live_scene_timing_history[serial%16];
 if(row[0]!=epoch||row[1]!=serial||!row[4])return 0;
 memcpy(out,row,sizeof(live_scene_timing_history[0]));return 1;
}
static void live_scene_timing_event(struct ARMCore*cpu,unsigned pc){
 if(!live_scene.started)return;
 scene_pose_event(cpu,pc);
 uint64_t*p=live_scene_timing_pending;
 if(pc==0x0806db14){p[15]++;p[16]=mTimingGlobalTime(&((struct GBA*)c->board)->timing);return;}
 if(pc==0x03002628){p[17]=mTimingGlobalTime(&((struct GBA*)c->board)->timing);return;}
 unsigned kind=pc==0x030032f0?13:pc==0x03000304?14:
     (pc==0x03004770&&cpu->gprs[0]==1)?12:0;
 if(!kind)return;
 uint64_t now=mTimingGlobalTime(&((struct GBA*)c->board)->timing);
 if(!p[5]){p[5]=now;p[19]=c->frameCounter(c);}
 p[6]=now;p[7]=pc;p[8]=(uint32_t)cpu->gprs[14];
 p[18]=c->frameCounter(c);p[kind]++;
}
static void live_scene_timing_flip(uint32_t frame){
 scene_pose_flip(frame);
 struct GBA*gba=c->board;
 uint64_t*p=live_scene_timing_pending;
 p[0]=live_scene_epoch;p[1]=live_scene.serial;p[2]=live_scene.begin;p[3]=frame;
 p[4]=mTimingGlobalTime(&gba->timing);
 p[9]=gba->video.vcount;p[10]=gba->memory.io[4>>1];
 p[11]=(uint64_t)(int64_t)mTimingUntil(&gba->timing,&gba->video.event);
 memcpy(live_scene_timing_history[live_scene.serial%16],p,sizeof(live_scene_timing_pending));
}

#include "pose_boundary.h"

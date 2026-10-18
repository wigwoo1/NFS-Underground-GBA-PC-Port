#define NF_SOURCE_POSE_API API
#include "source_pose_sample.h"
#undef NF_SOURCE_POSE_API
/* Source-root pose snapshot, diagnostic only. No early publication.
   Layout: 16 uint64 metadata words, camera[48], five source rows[208], sky angle/center:u32[2].
   Metadata: epoch,serial,begin,end,root_cycles,root_refresh,state,camera_address,
   pool_base,root_index,root_visits,valid_source_mask,model_entries,
   exact_camera_matches,exact_source_pose_matches,unmatched_or_invalid_entries.
   Each source row: address:u32, source[164], external_enabled:u32, matrix[36].
   The five known race slots (0..4) are explicit; unsupported objects fail matching. */
#define NF_POSE_BOUNDARY_BYTES 1224
typedef struct {uint64_t meta[16];uint8_t camera[48],source[5][208];uint32_t sky[2];} NFSourcePoseBoundary;
_Static_assert(sizeof(NFSourcePoseBoundary)==NF_POSE_BOUNDARY_BYTES,"pose boundary wire size");
static NFSourcePoseBoundary scene_pose_pending,scene_pose_history[16],scene_pose_sources[16];
static uint64_t scene_pose_source_clocks[16][3];
static uint32_t scene_pose_projection_pending[4],scene_pose_projection_history[16][4];
static uint32_t scene_pose_projection_detail[28],scene_pose_projection_details[16][28];
static uint8_t scene_pose_sine[16384];static int scene_pose_sine_valid;
API int nf_native_scene_pose_projection_read(uint64_t epoch,uint32_t serial,uint32_t out[4]){
 if(!out||!live_scene_timing_enabled||!live_scene.assembly||epoch!=live_scene_epoch)return 0;
 const NFSourcePoseBoundary*p=scene_pose_history+serial%16;
 if(p->meta[0]!=epoch||p->meta[1]!=serial||!p->meta[4])return 0;
 memcpy(out,scene_pose_projection_history[serial%16],16);return 1;
}
static void scene_pose_interval_reset(void){memset(scene_pose_projection_detail,0,sizeof(scene_pose_projection_detail));memset(scene_pose_projection_pending,0,sizeof(scene_pose_projection_pending));memset(&scene_pose_pending,0,sizeof(scene_pose_pending));}
static void scene_pose_reset(void){memset(scene_pose_projection_details,0,sizeof(scene_pose_projection_details));scene_pose_sine_valid=0;memset(scene_pose_projection_history,0,sizeof(scene_pose_projection_history));scene_pose_interval_reset();memset(scene_pose_history,0,sizeof(scene_pose_history));memset(scene_pose_sources,0,sizeof(scene_pose_sources));memset(scene_pose_source_clocks,0,sizeof(scene_pose_source_clocks));}
API int nf_native_scene_pose_boundary_read(uint64_t epoch,uint32_t serial,void*out,size_t capacity){
 if(!out||capacity<NF_POSE_BOUNDARY_BYTES||!live_scene_timing_enabled||!live_scene.assembly||epoch!=live_scene_epoch)return 0;
 const NFSourcePoseBoundary*p=scene_pose_history+serial%16;
 if(p->meta[0]!=epoch||p->meta[1]!=serial||!p->meta[4])return 0;
 memcpy(out,p,NF_POSE_BOUNDARY_BYTES);return 1;
}
/* Immutable source-only snapshot becomes readable at the observed original root.
   meta[3]==0 explicitly means no finished scene/end-refresh is being published.
   Geometry/material/visibility completion is not implied by this pose input. */
API int nf_native_scene_pose_source_read(uint64_t epoch,uint32_t serial,void*out,size_t capacity){
 if(!out||capacity<NF_POSE_BOUNDARY_BYTES||!live_scene_timing_enabled||!live_scene.assembly||epoch!=live_scene_epoch)return 0;
 const NFSourcePoseBoundary*p=scene_pose_sources+serial%16;
 if(p->meta[0]!=epoch||p->meta[1]!=serial||!p->meta[4]||p->meta[3])return 0;
 memcpy(out,p,NF_POSE_BOUNDARY_BYTES);return 1;
}
API int nf_native_scene_pose_projection_detail_read(uint64_t epoch,uint32_t serial,uint32_t out[28]){
 if(!out||!live_scene_timing_enabled||!live_scene.assembly||epoch!=live_scene_epoch)return 0;
 const NFSourcePoseBoundary*p=scene_pose_history+serial%16;
 if(p->meta[0]!=epoch||p->meta[1]!=serial||!p->meta[4]||!scene_pose_projection_details[serial%16][0])return 0;
 memcpy(out,scene_pose_projection_details[serial%16],28*sizeof(uint32_t));return 1;
}
/* Exact source clock: original global cycles, refresh, cycles since VBlank.
   Independent of the later original flip; copied atomically on valid ownership. */
API int nf_native_scene_pose_source_clock_read(uint64_t epoch,uint32_t serial,uint64_t out[3]){
 if(!out||!live_scene_timing_enabled||!live_scene.assembly||epoch!=live_scene_epoch)return 0;
 const NFSourcePoseBoundary*p=scene_pose_sources+serial%16;
 const uint64_t*t=scene_pose_source_clocks[serial%16];
 if(p->meta[0]!=epoch||p->meta[1]!=serial||!p->meta[4]||p->meta[3]||
    t[0]!=p->meta[4]||t[1]!=p->meta[5]||t[2]>=280896u)return 0;
 memcpy(out,t,3*sizeof(uint64_t));return 1;
}
static void scene_pose_event(struct ARMCore*cpu,unsigned pc){
 if(!live_scene.started)return;
 NFSourcePoseBoundary*p=&scene_pose_pending;unsigned*r=(unsigned*)cpu->gprs;
 if(pc==0x03002b74){
  uint8_t parent[16],camera[48];uint32_t state=r[0];
  if(!native_surface_read(NULL,r[3],parent,16))return;
  uint16_t depth;memcpy(&depth,parent+12,2);if(depth)return;
  p->meta[10]++;
  if(p->meta[4])return; /* Keep first exact root; never replace with a later pose. */
  uint32_t ca=rd32(state+84),base=rd32(state+60);
  if(!native_surface_read(NULL,ca,camera,48))return;
  p->sky[0]=rd32(0x03000214);p->sky[1]=rd32(0x03005abc);
  memcpy(p->camera,camera,48);p->meta[4]=mTimingGlobalTime(&((struct GBA*)c->board)->timing);
  p->meta[5]=c->frameCounter(c);p->meta[6]=state;p->meta[7]=ca;p->meta[8]=base;p->meta[9]=r[1];
  for(unsigned i=0;i<5;i++){
   uint64_t address=(uint64_t)base+i*164u;
   uint8_t*row=p->source[i];uint32_t a=(uint32_t)address;
   if(address>UINT32_MAX||!native_surface_read(NULL,a,row+4,164))continue;
   memcpy(row,&a,4);uint16_t flags;memcpy(&flags,row+14,2);
   uint32_t enabled=(flags&32)?rd32(0x03006768u):0;memcpy(row+168,&enabled,4);
   if(enabled){uint32_t external;memcpy(&external,row+144,4);
    if(external>UINT32_MAX-356u||!native_surface_read(NULL,external+320,row+172,36))continue;}
   p->meta[11]|=1u<<i;
  }
  p->meta[0]=live_scene_epoch;p->meta[1]=live_scene.serial;p->meta[2]=live_scene.begin;p->meta[3]=0;
  struct GBA*gba=c->board;
  int64_t phase=((gba->video.vcount+228-160)%228)*1232+
      ((gba->memory.io[4>>1]&2)?1232:1008)-(int64_t)mTimingUntil(&gba->timing,&gba->video.event);
  /* Out-of-range video state never becomes a usable source clock. */
  uint64_t clock[3]={p->meta[4],p->meta[5],(uint64_t)phase};
  memcpy(scene_pose_source_clocks[live_scene.serial%16],clock,sizeof(clock));
  scene_pose_sources[live_scene.serial%16]=*p;
 }else if(pc==0x03002628){
  p->meta[12]++;
  if(!scene_pose_sine_valid)scene_pose_sine_valid=native_surface_read(NULL,0x08623700u,scene_pose_sine,sizeof(scene_pose_sine));
  uint32_t predicted[12]={0},actual[12]={0};
  scene_pose_projection_pending[0]++;
  uint16_t flags=rd16(r[7]+10);scene_pose_projection_pending[(flags&32)?2:1]++;
  int predicted_ok=scene_pose_sine_valid&&nf_source_pose_model_matrix(p,sizeof(*p),r[7],scene_pose_sine,sizeof(scene_pose_sine),predicted);
  int actual_ok=native_surface_read(NULL,rd32(r[0]+60),actual,48);
  if(!predicted_ok||!actual_ok||memcmp(predicted,actual,48)){
   scene_pose_projection_pending[3]++;
   if(!scene_pose_projection_detail[0]){
    scene_pose_projection_detail[0]=r[7];scene_pose_projection_detail[1]=r[0];scene_pose_projection_detail[2]=flags;
    scene_pose_projection_detail[3]=(unsigned)predicted_ok|((unsigned)actual_ok<<1);
    memcpy(scene_pose_projection_detail+4,predicted,48);memcpy(scene_pose_projection_detail+16,actual,48);
   }
  }
  uint8_t camera[48],object[164],external[36];uint32_t ca=rd32(r[6]+84);
  if(!p->meta[4]||!native_surface_read(NULL,ca,camera,48)||!native_surface_read(NULL,r[7],object,164)){p->meta[15]++;return;}
  if(ca==p->meta[7]&&!memcmp(camera,p->camera,48))p->meta[13]++;
  for(unsigned i=0;i<5;i++)if(p->meta[11]&(1u<<i)){
   const uint8_t*row=p->source[i];uint32_t address,enabled;memcpy(&address,row,4);memcpy(&enabled,row+168,4);
   if(address!=r[7])continue;
   uint16_t a,b;memcpy(&a,row+14,2);memcpy(&b,object+10,2);
   int ok=!memcmp(row+16,object+12,12)&&!((a^b)&32);
   uint32_t current=(b&32)?rd32(0x03006768u):0;
   if(current!=enabled)ok=0;
   if(current){uint32_t ext;memcpy(&ext,object+140,4);
    if(ext>UINT32_MAX-356u||!native_surface_read(NULL,ext+320,external,36)||memcmp(row+172,external,36))ok=0;
   }else if(memcmp(row+52,object+48,4))ok=0;
   if(ok)p->meta[14]++;else p->meta[15]++;
   return;
  }
  p->meta[15]++;
 }
}
static void scene_pose_flip(uint32_t frame){
 NFSourcePoseBoundary*p=&scene_pose_pending;
 p->meta[0]=live_scene_epoch;p->meta[1]=live_scene.serial;p->meta[2]=live_scene.begin;p->meta[3]=frame;
 memcpy(scene_pose_projection_details[live_scene.serial%16],scene_pose_projection_detail,sizeof(scene_pose_projection_detail));
 memcpy(scene_pose_projection_history[live_scene.serial%16],scene_pose_projection_pending,16);
 scene_pose_history[live_scene.serial%16]=*p;
}

#include "source_pose_sample.h"
/* Owned early pose inputs for future presentation integration.
   This adapter validates/retains inputs only; it never changes rendered poses. */
typedef struct {uint64_t meta[16];uint8_t camera[48],source[5][208];uint32_t sky[2];} LiveSourcePose;
_Static_assert(sizeof(LiveSourcePose)==1224,"source pose ABI");
static struct {
 int enabled;uint64_t epoch;
 int(*read)(uint64_t,uint32_t,void*,size_t);
 int(*closed)(uint64_t,uint32_t,void*,size_t);
 int(*clock)(uint64_t,uint32_t,uint64_t*);
 int(*timing)(uint64_t,uint32_t,uint64_t*);
 int(*sky)(uint64_t,uint32_t,uint32_t,void*,size_t,size_t*);
 void(*stats)(uint32_t*);
 struct {int valid;uint32_t available;LiveSourcePose pose;uint64_t clock[3];double time;} slot[16];
 unsigned inputs,reads,scenes,models,entries,sky_matches,failures,min_lead,max_lead,clock_checks,clock_pairs;
 double phase_min,phase_max;
} live_pose;
static void live_pose_epoch(uint64_t epoch){
 if(live_pose.epoch==epoch)return;
 memset(live_pose.slot,0,sizeof(live_pose.slot));live_pose.epoch=epoch;
}
static int live_pose_enable(HMODULE bridge){
 if(!getenv("NF_LIVE_SOURCE_POSES"))return 1;
 int(*enable)(int)=(void*)GetProcAddress(bridge,"nf_native_scene_timing_enable");
 live_pose.read=(void*)GetProcAddress(bridge,"nf_native_scene_pose_source_read");
 live_pose.closed=(void*)GetProcAddress(bridge,"nf_native_scene_pose_boundary_read");
 live_pose.clock=(void*)GetProcAddress(bridge,"nf_native_scene_pose_source_clock_read");
 live_pose.timing=(void*)GetProcAddress(bridge,"nf_native_scene_timing_read");
 live_pose.stats=(void*)GetProcAddress(bridge,"nf_native_scene_stats");
 live_pose.sky=(void*)GetProcAddress(bridge,"nf_live_completed_sky_read");
 if(!enable||!live_pose.read||!live_pose.closed||!live_pose.clock||!live_pose.timing||!live_pose.stats||!live_pose.sky||!getenv("NF_LIVE_SKY_BOUNDARIES")||!enable(1))return 0;
 live_pose.enabled=1;live_pose.min_lead=UINT32_MAX;live_pose.phase_min=1;return 1;
}
static void live_pose_poll(uint64_t epoch,uint32_t refresh){
 if(!live_pose.enabled)return;live_pose_epoch(epoch);
 uint32_t stats[4];live_pose.stats(stats);LiveSourcePose p;
 if(!live_pose.read(epoch,stats[0],&p,sizeof(p)))return;
 if(p.meta[0]!=epoch||p.meta[1]!=stats[0]||p.meta[3]||!p.meta[4]||p.meta[11]!=31){live_pose.failures++;return;}
 uint64_t clock[3];
 if(!live_pose.clock(epoch,stats[0],clock)||clock[0]!=p.meta[4]||clock[1]!=p.meta[5]||clock[2]>=280896){live_pose.failures++;return;}
 double source_time=clock[1]+clock[2]/280896.0;
 unsigned index=stats[0]%16;
 if(live_pose.slot[index].valid&&live_pose.slot[index].pose.meta[0]==epoch&&live_pose.slot[index].pose.meta[1]==stats[0]){
  if(memcmp(&p,&live_pose.slot[index].pose,sizeof(p))||memcmp(clock,live_pose.slot[index].clock,sizeof(clock)))live_pose.failures++;
 }else{
  if(stats[0]){
   unsigned previous=(stats[0]-1)%16;
   if(live_pose.slot[previous].valid&&live_pose.slot[previous].pose.meta[0]==epoch&&live_pose.slot[previous].pose.meta[1]+1==stats[0]){
    double alpha;
    if(!nf_source_pose_phase(&live_pose.slot[previous].pose,sizeof(p),live_pose.slot[previous].clock,
       &p,sizeof(p),clock,(live_pose.slot[previous].time+source_time)/2,&alpha)||fabs(alpha-.5)>1e-9){live_pose.failures++;return;}
    live_pose.clock_pairs++;
   }
  }
  live_pose.slot[index].pose=p;live_pose.slot[index].available=refresh;
  memcpy(live_pose.slot[index].clock,clock,sizeof(clock));live_pose.slot[index].time=source_time;
  double phase=clock[2]/280896.0;
  if(phase<live_pose.phase_min)live_pose.phase_min=phase;if(phase>live_pose.phase_max)live_pose.phase_max=phase;
  live_pose.slot[index].valid=1;live_pose.inputs++;
 }
 live_pose.reads++;
}
static void live_pose_scene(uint64_t epoch,const NFScenePacket*packet){
 if(!live_pose.enabled)return;live_pose_epoch(epoch);
 LiveSourcePose p;unsigned index=packet->serial%16;
 if(!live_pose.closed(epoch,packet->serial,&p,sizeof(p))||!live_pose.slot[index].valid)goto failed;
 const LiveSourcePose*source=&live_pose.slot[index].pose;
 if(p.meta[0]!=epoch||p.meta[1]!=packet->serial||p.meta[2]!=packet->begin_refresh||p.meta[3]!=packet->end_refresh||
    source->meta[0]!=epoch||source->meta[1]!=packet->serial||source->meta[2]!=packet->begin_refresh||
    memcmp(p.meta+4,source->meta+4,8*sizeof(uint64_t))||memcmp(p.camera,source->camera,sizeof(p)-128)||
    p.meta[12]!=p.meta[13]||p.meta[12]!=p.meta[14]||p.meta[15])goto failed;
 if(live_pose.slot[index].available>=packet->end_refresh)goto failed;
 uint64_t timing[20];const uint64_t*clock=live_pose.slot[index].clock;
 if(!live_pose.timing(epoch,packet->serial,timing))goto failed;
 int64_t flip_phase=((timing[9]+228-160)%228)*1232+
     ((timing[10]&2)?1232:1008)-(int64_t)timing[11];
 int64_t ticks=(int64_t)((packet->end_refresh-clock[1])*280896u)+flip_phase-(int64_t)clock[2];
 if(ticks<0||(uint64_t)ticks!=timing[4]-clock[0])goto failed;
 live_pose.clock_checks++;
 uint32_t lead=packet->end_refresh-live_pose.slot[index].available;
 if(lead<live_pose.min_lead)live_pose.min_lead=lead;if(lead>live_pose.max_lead)live_pose.max_lead=lead;
 int32_t cm[12];memcpy(cm,p.camera,48);
 NFPoint3 pos={-(double)cm[9],-(double)cm[10],-(double)cm[11]};NFRigidPose expected;
 if(!nf_pose_decode(cm,&pos,&expected))goto failed;
 unsigned models=nf_scene_packet_model_count(packet),world;memcpy(&world,packet->section[1].data+4,4);
 for(unsigned i=0;i<models;i++){
  NFSceneSection model;uint32_t object;
  if(!nf_scene_packet_model(packet,i,&model)||model.size<160||memcmp(model.data+48,&expected,sizeof(expected)))goto failed;
  memcpy(&object,packet->section[4].data+8+(world+i)*20+8,4);
  int matched=0;
  for(unsigned s=0;s<5;s++){
   uint32_t address;memcpy(&address,p.source[s],4);if(address!=object)continue;
   int32_t xyz[3];double actual[3];memcpy(xyz,p.source[s]+16,12);memcpy(actual,model.data+104,24);
   for(unsigned a=0;a<3;a++)if(actual[a]!=(double)xyz[a]/256.0)goto failed;
   matched=1;break;
  }
  if(!matched)goto failed;
 }
 uint8_t sky[15192];size_t bytes=0;uint32_t angle;int32_t center;
 if(!live_pose.sky(epoch,packet->serial,0,sky,sizeof(sky),&bytes)||bytes!=sizeof(sky))goto failed;
 memcpy(&angle,sky+20,4);memcpy(&center,sky+48,4);
 if(angle!=p.sky[0]||center!=(int16_t)(p.sky[1]&65535u))goto failed;
 live_pose.scenes++;live_pose.models+=models;live_pose.entries+=(unsigned)p.meta[12];live_pose.sky_matches++;return;
 failed:live_pose.failures++;
}
static void live_pose_write(FILE*file){
 fprintf(file,",\"source_pose_enabled\":%s,\"source_pose_inputs\":%u,\"source_pose_reads\":%u,\"source_pose_scenes\":%u,\"source_pose_models\":%u,\"source_pose_entries\":%u,\"source_pose_sky_matches\":%u,\"source_pose_failures\":%u,\"source_pose_min_lead_frames\":%u,\"source_pose_max_lead_frames\":%u",
 live_pose.enabled?"true":"false",live_pose.inputs,live_pose.reads,live_pose.scenes,live_pose.models,live_pose.entries,live_pose.sky_matches,live_pose.failures,live_pose.scenes?live_pose.min_lead:0,live_pose.max_lead);
 fprintf(file,",\"source_clock_checks\":%u,\"source_clock_pairs\":%u,\"source_clock_phase_min\":%.12f,\"source_clock_phase_max\":%.12f",
 live_pose.clock_checks,live_pose.clock_pairs,live_pose.inputs?live_pose.phase_min:0,live_pose.phase_max);
}

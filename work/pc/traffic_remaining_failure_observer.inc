/* Read-only first remaining rejection plus the last producer rejection. */
static uint32_t nf_traffic_last_failure[128],nf_traffic_remaining_failure[640];
static unsigned nf_traffic_failure_sequence,nf_traffic_remaining_ready;
void nf_traffic_failure_reset(void){memset(nf_traffic_last_failure,0,sizeof(nf_traffic_last_failure));memset(nf_traffic_remaining_failure,0,sizeof(nf_traffic_remaining_failure));nf_traffic_failure_sequence=nf_traffic_remaining_ready=0;}
static void nf_traffic_failure_snapshot(struct ARMCore*cpu,unsigned pc,unsigned reason,uint32_t w[128]){
 memset(w,0,512);uint64_t epoch=live_scene_epoch;
 uint32_t h[22]={0x3150544e,1,128,reason,pc,c->frameCounter(c),(uint32_t)epoch,(uint32_t)(epoch>>32),live_scene.serial,live_scene.begin,nf_traffic_pending.active,nf_traffic_pending.phase,nf_traffic_pending.camera,nf_traffic_pending.object,nf_traffic_pending.slot,nf_traffic_pending.temp,nf_traffic_pending.frame,nf_traffic_pending.serial,(uint32_t)nf_traffic_pending.epoch,(uint32_t)(nf_traffic_pending.epoch>>32),nf_traffic_pending.index,(!nf_traffic_pending.active?1u:0u)|(nf_traffic_pending.epoch!=epoch?2u:0u)|(nf_traffic_pending.serial!=live_scene.serial?4u:0u)|(nf_traffic_pending.frame!=c->frameCounter(c)?8u:0u)};memcpy(w,h,sizeof(h));memcpy(w+32,cpu->gprs,64);
 w[22]=native_surface_read(NULL,nf_traffic_pending.camera,w+48,48);w[23]=native_surface_read(NULL,nf_traffic_pending.slot,w+112,36);uint8_t index=0;w[24]=native_surface_read(NULL,nf_traffic_pending.object+0x88,&index,1);w[25]=index;
 memcpy(w+64,nf_traffic_pending.cm,48);memcpy(w+80,nf_traffic_pending.first,48);memcpy(w+96,nf_traffic_pending.second,48);
}
void nf_traffic_failure_event(struct ARMCore*cpu,unsigned pc,unsigned reason){if(!nf_traffic_remaining_ready){nf_traffic_failure_snapshot(cpu,pc,reason,nf_traffic_last_failure);nf_traffic_failure_sequence++;}}
void nf_traffic_remaining_freeze(void){
 if(nf_traffic_remaining_ready||live_scene.serial<848)return;
 uint64_t epoch=live_scene_epoch;uint32_t h[16]={0x3146544e,1,640,(uint32_t)epoch,(uint32_t)(epoch>>32),live_scene.serial,c->frameCounter(c),live_scene.begin,nf_traffic_failure_sequence};memcpy(nf_traffic_remaining_failure,h,64);
 memcpy(nf_traffic_remaining_failure+16,nf_first_model_failure,1024);memcpy(nf_traffic_remaining_failure+272,nf_traffic_last_failure,512);
 nf_traffic_failure_snapshot(c->cpu,live_scene_event_detail[0],0,nf_traffic_remaining_failure+400);memcpy(nf_traffic_remaining_failure+528,nf_traffic_stats,48);nf_traffic_remaining_ready=1;
}
int nf_android_traffic_remaining_failure(uint32_t*out,size_t words){if(!c||!out||words<640||!nf_traffic_remaining_ready)return 0;memcpy(out,nf_traffic_remaining_failure,sizeof(nf_traffic_remaining_failure));return 1;}

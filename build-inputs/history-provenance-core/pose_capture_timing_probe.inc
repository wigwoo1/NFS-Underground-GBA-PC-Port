/* Timestamp-only bounded diagnostics. No new ARM hooks or game writes. */
typedef struct {uint64_t epoch,root_cycles[2],model_cycles[2];unsigned serial,root_frame[2],model_frame[2],roots,models;} NFPCPoseCaptureTiming;
static NFPCPoseCaptureTiming nf_pc_pose_capture_ring[16];
static NFPCPoseCaptureTiming*nf_pc_pose_record(void){
 unsigned serial=live_scene.serial;NFPCPoseCaptureTiming*p=nf_pc_pose_capture_ring+serial%16;
 if(p->epoch!=live_scene_epoch||p->serial!=serial){memset(p,0,sizeof(*p));p->epoch=live_scene_epoch;p->serial=serial;}return p;
}
static void nf_pc_pose_render_note(void){
 NFPCPoseCaptureTiming*p=nf_pc_pose_record();unsigned frame=c->frameCounter(c);uint64_t cycles=mTimingGlobalTime(c->timing);
 if(!p->roots){p->root_frame[0]=frame;p->root_cycles[0]=cycles;}p->root_frame[1]=frame;p->root_cycles[1]=cycles;p->roots++;
}
static void nf_pc_pose_model_note(void){
 NFPCPoseCaptureTiming*p=nf_pc_pose_record();unsigned frame=c->frameCounter(c);uint64_t cycles=mTimingGlobalTime(c->timing);
 if(!p->models){p->model_frame[0]=frame;p->model_cycles[0]=cycles;}p->model_frame[1]=frame;p->model_cycles[1]=cycles;p->models++;
}

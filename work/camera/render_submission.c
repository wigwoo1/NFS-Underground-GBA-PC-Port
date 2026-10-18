#include "render_submission.h"
#include <stdlib.h>
#include <math.h>
struct NFRenderSubmission {unsigned kind;NFTimelineSample time;NFSubmissionSchedule ordered_schedule;union {NFPreparedMotionSubmission*motion;NFStableSceneSubmission*stable;NFOrderedSceneSubmission*ordered;NFPresentationSubmission*native;NFHardwareSubmission*hardware;struct {NFPresentationSubmission*older,*newer;unsigned row;} split;} payload;};
int nf_render_submission_native(NFPresentationSubmission**source,NFRenderSubmission**out){if(!source||!*source||!out)return 0;const NFTimelineSample*t=nf_submission_time(*source);if(!t||!t->epoch)return 0;NFRenderSubmission*s=malloc(sizeof(*s));if(!s)return 0;s->kind=NF_RENDER_NATIVE;s->time=*t;s->payload.native=*source;*source=NULL;*out=s;return 1;}
int nf_render_submission_hardware(NFHardwareSubmission**source,NFRenderSubmission**out){if(!source||!*source||!out)return 0;NFTimelineSample t;NFSubmissionSchedule timing;if(!nf_hardware_submission_metadata(*source,&t,&timing)||!t.epoch)return 0;NFRenderSubmission*s=malloc(sizeof(*s));if(!s)return 0;s->kind=NF_RENDER_HARDWARE;s->time=t;s->payload.hardware=*source;*source=NULL;*out=s;return 1;}
unsigned nf_render_submission_kind(const NFRenderSubmission*s){return s?s->kind:0;}
const NFTimelineSample*nf_render_submission_time(const NFRenderSubmission*s){return s?&s->time:NULL;}
NFPresentationSubmission*nf_render_submission_native_view(const NFRenderSubmission*s){return s&&s->kind==NF_RENDER_NATIVE?s->payload.native:NULL;}
NFHardwareSubmission*nf_render_submission_hardware_view(const NFRenderSubmission*s){return s&&s->kind==NF_RENDER_HARDWARE?s->payload.hardware:NULL;}
void nf_render_submission_destroy(NFRenderSubmission*s){if(s){if(s->kind==NF_RENDER_PREPARED_MOTION)nf_prepared_motion_destroy(s->payload.motion);else if(s->kind==NF_RENDER_NATIVE)nf_submission_destroy(s->payload.native);else if(s->kind==NF_RENDER_HARDWARE)nf_hardware_submission_destroy(s->payload.hardware);else if(s->kind==NF_RENDER_STABLE)nf_stable_scene_destroy(s->payload.stable);else if(s->kind==NF_RENDER_ORDERED)nf_ordered_scene_submission_destroy(s->payload.ordered);else if(s->kind==NF_RENDER_SPLIT){nf_submission_destroy(s->payload.split.older);nf_submission_destroy(s->payload.split.newer);}free(s);}}

int nf_render_submission_split(NFPresentationSubmission**older,NFPresentationSubmission**newer,unsigned row,NFRenderSubmission**out){
 if(!older||!newer||older==newer||!*older||!*newer||*older==*newer||!out||!row||row>=160)return 0;
 const NFTimelineSample*a=nf_submission_time(*older),*b=nf_submission_time(*newer);
 if(!a||!b||a->epoch!=b->epoch||a->target!=b->target)return 0;
 NFSubmissionSchedule x,y;if(!nf_submission_schedule_get(*older,&x)||!nf_submission_schedule_get(*newer,&y)||x.origin_ns!=y.origin_ns||x.lag_ns!=y.lag_ns||x.source_base!=y.source_base||x.delay_refreshes!=y.delay_refreshes)return 0;
 if(nf_submission_difference(*older,*newer)&(2|32|256))return 0;
 const void*ap,*bp;size_t an,bn;NFScenePacket av,bv;
 if(!nf_submission_packet(*older,&ap,&an)||!nf_submission_packet(*newer,&bp,&bn)||!nf_scene_packet_view(ap,an,&av)||!nf_scene_packet_view(bp,bn,&bv)||av.page>1||bv.page>1||av.page==bv.page||av.end_refresh>=bv.end_refresh||floor(b->target)!=bv.end_refresh)return 0;
 const NFRigidPose*poses;unsigned count;
 if(!nf_submission_command_cameras(*older,&poses,&count)||!count||!nf_submission_command_cameras(*newer,&poses,&count)||!count)return 0;
 NFRenderSubmission*s=malloc(sizeof(*s));if(!s)return 0;s->kind=NF_RENDER_SPLIT;s->time=*b;s->payload.split.older=*older;s->payload.split.newer=*newer;s->payload.split.row=row;*older=*newer=NULL;*out=s;return 1;
}
int nf_render_submission_split_view(const NFRenderSubmission*s,NFPresentationSubmission**older,NFPresentationSubmission**newer,unsigned*row){if(!s||s->kind!=NF_RENDER_SPLIT||!older||!newer||!row)return 0;*older=s->payload.split.older;*newer=s->payload.split.newer;*row=s->payload.split.row;return 1;}

int nf_render_submission_ordered(NFOrderedSceneSubmission**source,const NFTimelineSample*t,const NFSubmissionSchedule*schedule,NFRenderSubmission**out){
 if(!source||!*source||!t||!schedule||!out||!isfinite(schedule->delay_refreshes)||schedule->delay_refreshes<0)return 0;
 const NFOrderedSceneSubmission*p=*source;NFRoadBundle a,b;NFHudSubmissionView v;
 if(!nf_road_bundle_view(p->older,p->older_size,&a)||!nf_road_bundle_view(p->newer,p->newer_size,&b)||!nf_hud_submission_view(&a,&b,p->hud,p->hud_size,p->text,p->text_size,p->cut,&v))return 0;
 if(t->epoch!=v.epoch||p->epoch!=v.epoch||p->refresh!=v.refresh||!isfinite(t->target)||floor(t->target)!=v.refresh||t->alpha!=1.0||t->older!=a.ordered.packet.serial||t->newer!=b.ordered.packet.serial)return 0;
 NFRenderSubmission*s=malloc(sizeof(*s));if(!s)return 0;s->kind=NF_RENDER_ORDERED;s->time=*t;s->ordered_schedule=*schedule;s->payload.ordered=*source;*source=NULL;*out=s;return 1;
}
const NFOrderedSceneSubmission*nf_render_submission_ordered_view(const NFRenderSubmission*s){return s&&s->kind==NF_RENDER_ORDERED?s->payload.ordered:NULL;}

int nf_render_submission_ordered_schedule(const NFRenderSubmission*s,NFSubmissionSchedule*out){if(!s||(s->kind!=NF_RENDER_ORDERED&&s->kind!=NF_RENDER_STABLE&&s->kind!=NF_RENDER_PREPARED_MOTION)||!out)return 0;*out=s->ordered_schedule;return 1;}

int nf_render_submission_stable(NFStableSceneSubmission**source,const NFTimelineSample*t,const NFSubmissionSchedule*schedule,NFRenderSubmission**out){
 if(!source||!*source||!t||!schedule||!out||!isfinite(schedule->delay_refreshes)||schedule->delay_refreshes<0)return 0;const NFStableSceneSubmission*p=*source;NFHudSubmissionView view;
 if(!nf_stable_scene_view(p->bundle,p->bundle_size,p->hud,p->hud_size,p->text,p->text_size,&p->proof,&view)||t->epoch!=p->proof.epoch||!isfinite(t->target)||floor(t->target)!=p->proof.display_refresh||t->older!=p->proof.serial||t->newer!=p->proof.serial||t->alpha!=0)return 0;
 NFRenderSubmission*s=malloc(sizeof(*s));if(!s)return 0;s->kind=NF_RENDER_STABLE;s->time=*t;s->ordered_schedule=*schedule;s->payload.stable=*source;*source=NULL;*out=s;return 1;
}
const NFStableSceneSubmission*nf_render_submission_stable_view(const NFRenderSubmission*s){return s&&s->kind==NF_RENDER_STABLE?s->payload.stable:NULL;}

static int nf_render_submission_prepared_motion_checked(NFPreparedMotionSubmission**source,const NFTimelineSample*t,const NFSubmissionSchedule*schedule,NFRenderSubmission**out,int live){
 if(!source||!*source||!t||!schedule||!out||!isfinite(schedule->delay_refreshes)||schedule->delay_refreshes<0)return 0;NFPreparedMotionSubmission*p=*source;NFRoadBundle a,b;NFScenePacket packet;NFHudSubmissionView hud;
 if(!nf_prepared_motion_source_views(p,&a,&b)||!nf_scene_packet_view(p->packet,p->packet_size,&packet)||!(p->hud_pool?(p->hud_stable&&nf_stable_scene_pool_view_validated(&a,p->hud_pool,p->hud_pool->bytes,p->text,p->text_size,&p->hud_proof,&hud)):(p->hud_stable?nf_stable_scene_view_validated(&a,p->hud,p->hud_size,p->text,p->text_size,&p->hud_proof,&hud):nf_hud_submission_view(&a,&b,p->hud,p->hud_size,p->text,p->text_size,p->hud_cut,&hud)))||p->hud_refresh!=hud.refresh||t->epoch!=hud.epoch||!isfinite(t->target)||floor(t->target)!=hud.refresh||!isfinite(t->alpha)||t->alpha!=p->alpha||t->older!=a.ordered.packet.serial||t->newer!=b.ordered.packet.serial)return 0;
 if(live&&!nf_prepared_motion_clock_views(p,t,&a,&b))return 0;
 NFRenderSubmission*s=malloc(sizeof(*s));if(!s)return 0;s->kind=NF_RENDER_PREPARED_MOTION;s->time=*t;s->ordered_schedule=*schedule;s->payload.motion=p;*source=NULL;*out=s;return 1;
}
int nf_render_submission_prepared_motion(NFPreparedMotionSubmission**source,const NFTimelineSample*t,const NFSubmissionSchedule*schedule,NFRenderSubmission**out){return nf_render_submission_prepared_motion_checked(source,t,schedule,out,0);}
const NFPreparedMotionSubmission*nf_render_submission_prepared_motion_view(const NFRenderSubmission*s){return s&&s->kind==NF_RENDER_PREPARED_MOTION?s->payload.motion:NULL;}

int nf_render_submission_prepared_motion_live(NFPreparedMotionSubmission**source,const NFTimelineSample*t,const NFSubmissionSchedule*schedule,NFRenderSubmission**out){
 return nf_render_submission_prepared_motion_checked(source,t,schedule,out,1);
}


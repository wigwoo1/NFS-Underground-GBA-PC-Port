#include "presentation_submission.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>
struct NFPresentationSubmission {NFTimelineSample time;uint32_t source[2],refresh;unsigned has_cameras,has_schedule,has_text;uint8_t text[38400],text_coverage[38400];NFSubmissionSchedule schedule;NFRigidPose cameras[2],command_cameras[144];unsigned command_camera_count;uint16_t zero[160];size_t bytes;NFHudLayerRow rows[160];unsigned char*packet_data;void(*packet_release)(void*);unsigned char packet[];};
int nf_submission_bg_palettes(const NFPresentationSubmission*s,uint64_t epoch,uint32_t refresh,uint16_t out[160][256]){
 if(!s||!out||s->time.epoch!=epoch||s->refresh!=refresh)return 0;
 for(unsigned y=0;y<160;y++)memcpy(out[y],s->rows[y].palette,512);
 return 1;
}
static unsigned last_error;unsigned nf_submission_last_error(void){return last_error;}
static int submission_create(const void*packet,size_t bytes,const NFTimelineSample*time,uint32_t older,uint32_t newer,const NFRigidPose*cameras,const uint16_t zero[160],NFSubmissionRead read,void*ctx,NFPresentationSubmission**out,void(*release)(void*)){
 NFScenePacket view;
 last_error=1;
 if(!out||!time||!zero||!read||!time->epoch||!isfinite(time->alpha)||time->alpha<0||time->alpha>1||!isfinite(time->target)||time->target<0||time->target>UINT32_MAX||older>newer||bytes>64*1024*1024||!nf_scene_packet_view(packet,bytes,&view))return 0;
 last_error=3;if(cameras){NFRigidPose check;for(unsigned i=0;i<2;i++)if(!nf_pose_sample(cameras+i,cameras+i,0,&check))return 0;}
 last_error=4;
 NFPresentationSubmission*s=malloc(sizeof(*s)+(release?0:bytes));if(!s)return 0;
 s->has_text=0;memset(s->text,0,sizeof(s->text));memset(s->text_coverage,0,sizeof(s->text_coverage));s->command_camera_count=0;memset(s->command_cameras,0,sizeof(s->command_cameras));s->has_schedule=0;memset(&s->schedule,0,sizeof(s->schedule));
 s->time=*time;s->source[0]=older;s->source[1]=newer;s->refresh=(uint32_t)floor(time->target);s->has_cameras=cameras!=NULL;if(cameras)memcpy(s->cameras,cameras,sizeof(s->cameras));else memset(s->cameras,0,sizeof(s->cameras));s->bytes=bytes;s->packet_release=release;s->packet_data=release?(unsigned char*)packet:s->packet;if(!release)memcpy(s->packet,packet,bytes);memcpy(s->zero,zero,sizeof(s->zero));
 for(unsigned y=0;y<160;y++){uint16_t color;last_error=5;if(!read(ctx,time->epoch,s->refresh,y,s->rows+y)||s->rows[y].row!=y||s->rows[y].refresh!=s->refresh){free(s);return 0;}memcpy(&color,s->rows[y].palette,2);last_error=6;if(color!=zero[y]){free(s);return 0;}}
 *out=s;last_error=0;return 1;
}
int nf_submission_create(const void*p,size_t n,const NFTimelineSample*t,uint32_t a,uint32_t b,const NFRigidPose*c,const uint16_t z[160],NFSubmissionRead r,void*ctx,NFPresentationSubmission**out){return submission_create(p,n,t,a,b,c,z,r,ctx,out,NULL);}
int nf_submission_take(void**p,size_t n,const NFTimelineSample*t,uint32_t a,uint32_t b,const NFRigidPose*c,const uint16_t z[160],NFSubmissionRead r,void*ctx,void(*release)(void*),NFPresentationSubmission**out){if(!p||!*p||!release)return 0;if(!submission_create(*p,n,t,a,b,c,z,r,ctx,out,release))return 0;*p=NULL;return 1;}
void nf_submission_destroy(NFPresentationSubmission*s){if(s&&s->packet_release)s->packet_release(s->packet_data);free(s);}
int nf_submission_schedule_set(NFPresentationSubmission*s,const NFSubmissionSchedule*t){if(!s||!t||s->has_schedule||!isfinite(t->delay_refreshes)||t->delay_refreshes<0||t->lag_ns>1000000000ull||t->origin_ns>UINT64_MAX-t->lag_ns)return 0;s->schedule=*t;s->has_schedule=1;return 1;}
int nf_submission_schedule_get(const NFPresentationSubmission*s,NFSubmissionSchedule*out){if(!s||!out||!s->has_schedule)return 0;*out=s->schedule;return 1;}
NFPresentationSubmission*nf_submission_clone(const NFPresentationSubmission*s){if(!s)return NULL;NFPresentationSubmission*copy=malloc(sizeof(*s)+s->bytes);if(copy){memcpy(copy,s,sizeof(*s));copy->packet_data=copy->packet;copy->packet_release=NULL;memcpy(copy->packet,s->packet_data,s->bytes);}return copy;}
void nf_submission_poison_retired(NFPresentationSubmission*s){if(!s)return;volatile unsigned char*rows=(volatile unsigned char*)s->rows;for(size_t i=0;i<sizeof(s->rows);i++)rows[i]=0xa5;volatile unsigned char*packet=s->packet_data;for(size_t i=0;i<s->bytes;i++)packet[i]=0xa5;}
int nf_submission_packet(const NFPresentationSubmission*s,const void**out,size_t*bytes){if(!s||!out||!bytes)return 0;*out=s->packet_data;*bytes=s->bytes;return 1;}
int nf_submission_row(const NFPresentationSubmission*s,uint64_t epoch,uint32_t refresh,unsigned y,NFHudLayerRow*out){if(!s||!out||epoch!=s->time.epoch||refresh!=s->refresh||y>=160)return 0;memcpy(out,s->rows+y,sizeof(*out));return 1;}
const NFTimelineSample*nf_submission_time(const NFPresentationSubmission*s){return s?&s->time:NULL;}
const NFRigidPose*nf_submission_cameras(const NFPresentationSubmission*s){return s&&s->has_cameras?s->cameras:NULL;}
const uint16_t*nf_submission_zero_colors(const NFPresentationSubmission*s){return s?s->zero:NULL;}
int nf_submission_sources(const NFPresentationSubmission*s,uint32_t out[2]){if(!s||!out)return 0;memcpy(out,s->source,sizeof(s->source));return 1;}
unsigned nf_submission_difference(const NFPresentationSubmission*a,const NFPresentationSubmission*b){if(!a||!b)return 255;unsigned diff=0;if(a->bytes!=b->bytes||memcmp(a->packet_data,b->packet_data,a->bytes))diff|=1;if(memcmp(a->rows,b->rows,sizeof(a->rows)))diff|=2;if(a->time.epoch!=b->time.epoch||a->time.older!=b->time.older||a->time.newer!=b->time.newer||a->time.alpha!=b->time.alpha||a->time.target!=b->time.target)diff|=4;if(a->has_cameras!=b->has_cameras||(a->has_cameras&&memcmp(a->cameras,b->cameras,sizeof(a->cameras))))diff|=8;if(memcmp(a->source,b->source,sizeof(a->source)))diff|=16;if(memcmp(a->zero,b->zero,sizeof(a->zero)))diff|=32;if(a->has_schedule!=b->has_schedule||(a->has_schedule&&(a->schedule.origin_ns!=b->schedule.origin_ns||a->schedule.lag_ns!=b->schedule.lag_ns||a->schedule.source_base!=b->schedule.source_base||a->schedule.delay_refreshes!=b->schedule.delay_refreshes)))diff|=64;if(a->command_camera_count!=b->command_camera_count||(a->command_camera_count&&memcmp(a->command_cameras,b->command_cameras,a->command_camera_count*sizeof(NFRigidPose))))diff|=128;if(a->has_text!=b->has_text||(a->has_text&&(memcmp(a->text,b->text,38400)||memcmp(a->text_coverage,b->text_coverage,38400))))diff|=256;return diff;}


int nf_submission_command_cameras_set(NFPresentationSubmission*s,const NFRigidPose*cameras,unsigned count){
 NFScenePacket packet;if(!s||!cameras||!count||count>144||s->command_camera_count||!nf_scene_packet_view(s->packet_data,s->bytes,&packet))return 0;
 uint32_t commands;memcpy(&commands,packet.section[2].data+4,4);if(count!=commands)return 0;
 NFRigidPose checked;for(unsigned i=0;i<count;i++)if(!nf_pose_sample(cameras+i,cameras+i,0,&checked))return 0;
 memcpy(s->command_cameras,cameras,count*sizeof(*cameras));s->command_camera_count=count;return 1;
}
int nf_submission_command_cameras(const NFPresentationSubmission*s,const NFRigidPose**out,unsigned*count){if(!s||!out||!count||!s->command_camera_count)return 0;*out=s->command_cameras;*count=s->command_camera_count;return 1;}

int nf_submission_text_capture(NFPresentationSubmission*s,NFSubmissionTextRead read,void*ctx){
 if(!s||!read||s->has_text)return 0;
 uint8_t*owned=malloc(76800);if(!owned)return 0;int ok=1;
 for(unsigned y=0;y<160&&ok;y++){if(!read(ctx,s->time.epoch,s->refresh,y,owned+y*240,owned+38400+y*240)){ok=0;break;}for(unsigned x=0;x<240;x++)if(owned[38400+y*240+x]>1){ok=0;break;}}
 if(ok){memcpy(s->text,owned,38400);memcpy(s->text_coverage,owned+38400,38400);s->has_text=1;}
 free(owned);return ok;
}
int nf_submission_text_row(const NFPresentationSubmission*s,uint64_t epoch,uint32_t refresh,unsigned y,uint8_t indices[240],uint8_t coverage[240]){
 if(!s||!s->has_text||!indices||!coverage||epoch!=s->time.epoch||refresh!=s->refresh||y>=160)return 0;
 memcpy(indices,s->text+y*240,240);memcpy(coverage,s->text_coverage+y*240,240);return 1;
}

int nf_submission_command_camera_pair_set(NFPresentationSubmission*s,const NFRigidPose*a,const NFRigidPose*b,unsigned count){
 if(!s||!a||!b||!count||count>144||s->command_camera_count)return 0;
 NFRigidPose sampled[144];for(unsigned i=0;i<count;i++)if(!nf_pose_sample(a+i,b+i,s->time.alpha,sampled+i))return 0;
 return nf_submission_command_cameras_set(s,sampled,count);
}

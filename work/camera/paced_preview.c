#define NF_PACKET_NO_MAIN
#define NF_PACKET_NO_FILES
static void renderer_stage(unsigned);
static void packet_stage(unsigned);
#define NF_DIAGNOSTIC_PACKET_STAGE packet_stage
#define NF_DIAGNOSTIC_RENDER_STAGE renderer_stage
#ifdef NF_NATIVE_ENDPOINT_RENDER
#include "scene_packet.h"
#include "presentation_timeline.h"
#include "visibility_snapshot.h"
#include "layer_snapshot.h"
#include "presentation_submission.h"
static void endpoint_capture(void);
static int paired_prepare(NFScenePacket*,NFScenePacket*,const NFTimelineSample*);
static int endpoint_hud(void);
#define NF_DIAGNOSTIC_HUD_DRAW endpoint_hud
#define NF_DIAGNOSTIC_PAIR_PREPARE paired_prepare
/* Capture belongs to accepted presentation, not render_packet_at cleanup. */
static void endpoint_select(const NFScenePacket*);
static void endpoint_clip(int);
static void endpoint_model_clip(int);
static int endpoint_road(unsigned,double*,double*,double*,double*);
#define NF_DIAGNOSTIC_PACKET_SELECT endpoint_select
#define NF_DIAGNOSTIC_SURFACE_CLIP endpoint_clip
#define NF_DIAGNOSTIC_MODEL_CLIP endpoint_model_clip
#define NF_DIAGNOSTIC_ROAD_BOUNDS endpoint_road
#define NF_DIAGNOSTIC_DEPTH
#define NF_SOURCE_COMMAND_ORDER
#endif
#include "packet_preview.c"
static uint64_t elapsed_ns(void);
#include "deadline_wait.h"
static uint64_t presentation_phase_ns;
static uint64_t renderer_marks[5];
static uint64_t packet_marks[8];static int packet_trace_enabled;
static void packet_stage(unsigned stage){if(packet_trace_enabled&&stage<8)packet_marks[stage]=elapsed_ns();}
static void renderer_stage(unsigned stage){if(stage<5)renderer_marks[stage]=elapsed_ns();if(stage==4&&getenv("NF_TEST_PAGE_STAGE_PROFILE"))printf("page_stage_ms setup=%.6f submit=%.6f hud=%.6f finish=%.6f\n",(renderer_marks[1]-renderer_marks[0])/1e6,(renderer_marks[2]-renderer_marks[1])/1e6,(renderer_marks[3]-renderer_marks[2])/1e6,(renderer_marks[4]-renderer_marks[3])/1e6);}
static uint64_t paired_prepare_ns,endpoint_prepare_ns;
static uint64_t preparation_total_ns,preparation_reported_ns;
static uint64_t early_gpu_ns,early_gpu_reported_ns;
static uint64_t original_work_ns,original_reported_work_ns,original_steps_total,original_reported_steps;
static unsigned preparation_reuse_count,preparation_reported_reuse;
#ifndef NF_NATIVE_ENDPOINT_RENDER
static int paired_packets;static unsigned paired_generated,paired_rejected;
#endif
#ifdef NF_NATIVE_ENDPOINT_RENDER
static int layer_sync;static unsigned layer_selected,layer_missing;static FILE*layer_sync_log;static int(*layer_read)(uint64_t,unsigned,unsigned,void*,unsigned);
static int(*bridge_layer_read)(uint64_t,unsigned,unsigned,void*,unsigned);
static NFPresentationSubmission*owned_submission;static unsigned submission_created,submission_failed,submission_retirement_tests;
static void submission_clear(void){nf_submission_destroy(owned_submission);owned_submission=NULL;}
static int submission_capture_row(void*ctx,uint64_t epoch,uint32_t refresh,unsigned y,NFHudLayerRow*out){(void)ctx;return bridge_layer_read(epoch,refresh,y,out,sizeof(*out));}
static int submission_layer_read(uint64_t epoch,unsigned refresh,unsigned y,void*out,unsigned bytes){if(bytes!=sizeof(NFHudLayerRow))return 0;return owned_submission?nf_submission_row(owned_submission,epoch,refresh,y,out):bridge_layer_read(epoch,refresh,y,out,bytes);}
static int(*layer_zero_read)(uint64_t,unsigned,void*,unsigned);
static int hud_preview;static uint64_t hud_epoch;static unsigned hud_refresh,hud_drawn,hud_failed;
static int indexed_multimodel,indexed_world,classified_world;
#include "live_hud_gpu.h"
static void*paired_owned;static void(*paired_free)(void*);static int paired_packets;static unsigned paired_generated,paired_rejected;static int(*paired_extract)(const NFVisibilityIdentity*,const NFVisibilityIdentity*,double,void**,size_t*,unsigned*);
/* Prepared packets own their bytes; no snapshot pin survives an original update. */
static void*early_owned;static size_t early_bytes;static NFTimelineSample early_time;
static unsigned early_generated,early_reused,early_discarded,early_verified,early_failed;
static uint64_t early_generation_ns;
static int early_gpu;static int early_frame_valid;static NFTimelineSample early_frame_time;static uint64_t early_frame_index;
static unsigned early_gpu_rendered,early_gpu_presented,early_gpu_discarded;
static unsigned early_gpu_verified,early_gpu_verification_draws,early_gpu_verify_failed,early_gpu_verified_updates;
static uint64_t early_gpu_verification_ns;
static unsigned early_gpu_min_models=1;
static unsigned early_gpu_verify_limit=12;
static unsigned owned_consumer_verified;
/* Render-only entry: all scene/HUD/camera inputs come from the submission.
   Caller owns GL and renderer globals, and retains s through completion. */
static int render_owned_submission(NFPresentationSubmission*s,char**args){
 const void*data;size_t bytes;NFScenePacket view;uint32_t sources[2];
 if(!s||!nf_submission_packet(s,&data,&bytes)||!nf_scene_packet_view(data,bytes,&view)||!nf_submission_sources(s,sources))return 24;
 NFPresentationSubmission*previous=owned_submission;owned_submission=s;
 const NFTimelineSample*time=nf_submission_time(s);const NFRigidPose*cameras=nf_submission_cameras(s);
 packet_source_older_refresh=sources[0];packet_source_newer_refresh=sources[1];packet_continuous_camera=cameras!=NULL;
 if(cameras)memcpy(packet_source_cameras,cameras,sizeof(packet_source_cameras));
 memcpy(preview_zero_colors,nf_submission_zero_colors(s),sizeof(preview_zero_colors));preview_zero_valid=1;
 hud_epoch=time->epoch;hud_refresh=(unsigned)floor(time->target);
 int previous_palette_valid=preview_display_palette_valid;uint16_t previous_palette[160][256];
 if(previous_palette_valid)memcpy(previous_palette,preview_display_palette,sizeof(previous_palette));
 preview_display_palette_valid=0;
 if(getenv("NF_TEST_DISPLAY_PALETTE")){
  if(!nf_submission_bg_palettes(s,hud_epoch,hud_refresh,preview_display_palette)){owned_submission=previous;preview_display_palette_valid=previous_palette_valid;if(previous_palette_valid)memcpy(preview_display_palette,previous_palette,sizeof(previous_palette));return 24;}
  preview_display_palette_valid=1;
 }
 const NFRigidPose*command_cameras=NULL;unsigned command_count=0;
 nf_submission_command_cameras(s,&command_cameras,&command_count);
 const NFRigidPose*previous_cameras=preview_command_cameras;unsigned previous_count=preview_command_camera_count;
 preview_command_cameras=command_cameras;preview_command_camera_count=command_count;
 int result=render_packet_views(view,view,*time,args);
 preview_display_palette_valid=previous_palette_valid;if(previous_palette_valid)memcpy(preview_display_palette,previous_palette,sizeof(previous_palette));
 preview_command_cameras=previous_cameras;preview_command_camera_count=previous_count;owned_submission=previous;return result;
}
static unsigned test_clock_restarts;
#include "owned_gl_worker.h"
static unsigned test_epoch_cuts,test_epoch_rejections;static int test_epoch_pending;
static int preview_render_available(NFSnapshotStore*,double,char**,int*,int*);
static unsigned prepared_model_count(void){NFScenePacket view;uint32_t bytes;if(!paired_owned)return 0;memcpy(&bytes,(const uint8_t*)paired_owned+8,4);return nf_scene_packet_view(paired_owned,bytes,&view)?nf_scene_packet_model_count(&view):0;}
static int verify_early_pixels(NFSnapshotStore*s,double target,char**args,unsigned updates){
 unsigned models=prepared_model_count();
 const size_t size=(size_t)3840*2160*3;uint8_t*before=malloc(size),*after=malloc(size);
 if(!before||!after){free(before);free(after);return 19;}
 uint64_t begin=elapsed_ns();glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,before);int error=glGetError()!=GL_NO_ERROR;
 if(getenv("NF_TEST_CORRUPT_EARLY_PIXELS"))before[0]^=1; /* Diagnostic comparison rejection only. */
 NFPresentationSubmission*saved_submission=owned_submission;owned_submission=NULL;
 if(saved_submission&&getenv("NF_TEST_SUBMISSION_RETIRE")){NFPresentationSubmission*copy=nf_submission_clone(saved_submission);if(!copy){owned_submission=saved_submission;free(before);free(after);return 19;}nf_submission_poison_retired(saved_submission);nf_submission_destroy(saved_submission);saved_submission=copy;submission_retirement_tests++;}
 if(saved_submission&&getenv("NF_TEST_OWNED_CONSUMER")){int worker=getenv("NF_TEST_OWNED_GL_WORKER")!=NULL;int check=worker?owned_gl_worker_draw(saved_submission,args,after):render_owned_submission(saved_submission,args);if(!check){if(!worker)glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,after);check=glGetError()!=GL_NO_ERROR||memcmp(before,after,size);}if(check){printf("owned_consumer_failed=1 target=%.12f\n",target);nf_submission_destroy(saved_submission);free(before);free(after);return 19;}owned_consumer_verified++;printf("owned_consumer_verified=%u\n",owned_consumer_verified);}
 int ready=1,incompatible=0,result=error?19:preview_render_available(s,target,args,&ready,&incompatible);
 if(saved_submission){unsigned diff=nf_submission_difference(saved_submission,owned_submission);if(diff){printf("submission_after_update_difference=%u target=%.12f\n",diff,target);result=19;}nf_submission_destroy(saved_submission);}
 if(!result&&ready){early_gpu_verification_draws++;glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,after);if(glGetError()!=GL_NO_ERROR||memcmp(before,after,size)){unsigned changed=0,x0=3840,y0=2160,x1=0,y1=0;for(unsigned y=0;y<2160;y++)for(unsigned x=0;x<3840;x++){size_t i=((size_t)y*3840+x)*3;if(memcmp(before+i,after+i,3)){changed++;if(x<x0)x0=x;if(x>x1)x1=x;if(y<y0)y0=y;if(y>y1)y1=y;}}printf("early_gpu_pixel_difference=%u bbox=%u,%u,%u,%u target=%.12f\n",changed,x0,y0,x1,y1,target);early_gpu_verify_failed++;result=19;}else{early_gpu_verified++;early_gpu_verified_updates+=updates;printf("early_gpu_pixel_models=%u target=%.12f updates=%u\n",models,target,updates);}}
 else if(!result)result=19;
 early_gpu_verification_ns+=elapsed_ns()-begin;free(before);free(after);return result;
}

static int same_sample(const NFTimelineSample*a,const NFTimelineSample*b){return a->epoch==b->epoch&&a->older==b->older&&a->newer==b->newer&&a->target==b->target&&a->alpha==b->alpha;}
static void early_frame_clear(void){submission_clear();if(early_frame_valid){early_frame_valid=0;early_gpu_discarded++;if(test_epoch_pending){test_epoch_rejections++;test_epoch_pending=0;}}if(paired_owned){paired_free(paired_owned);paired_owned=NULL;}}

static void early_clear(void){if(early_owned){paired_free(early_owned);early_owned=NULL;early_discarded++;}}
static int early_matches(const NFTimelineSample*t){return early_owned&&early_time.epoch==t->epoch&&early_time.older==t->older&&early_time.newer==t->newer&&early_time.target==t->target&&early_time.alpha==t->alpha;}
static void early_prepare(const NFSnapshotPair*p){
 early_clear();if(!paired_packets)return;
 NFScenePacket a,b;if(!nf_scene_packet_view(p->older,p->older_size,&a)||!nf_scene_packet_view(p->newer,p->newer_size,&b))return;
 NFVisibilityIdentity left={p->time.epoch,a.serial,a.begin_refresh,a.end_refresh,0,0},right={p->time.epoch,b.serial,b.begin_refresh,b.end_refresh,0,0};
 unsigned stage=0;uint64_t start=elapsed_ns();int ok=paired_extract(&left,&right,p->time.alpha,&early_owned,&early_bytes,&stage);uint64_t duration=elapsed_ns()-start;early_generation_ns+=duration;preparation_total_ns+=duration;
 if(!ok||!nf_scene_packet_view(early_owned,early_bytes,&a)){early_failed++;early_clear();return;}early_time=p->time;early_generated++;
}
static int paired_prepare(NFScenePacket*a,NFScenePacket*b,const NFTimelineSample*t){submission_clear();preview_zero_valid=0;if(paired_owned){paired_free(paired_owned);paired_owned=NULL;}if(!paired_packets)return 1;
 if(layer_sync){NFHudLayerRow first,last;double discrete=floor(t->target);int found=isfinite(discrete)&&discrete>=0&&discrete<=UINT32_MAX;unsigned selected=found?(unsigned)discrete:0;found=found&&layer_read(t->epoch,selected,0,&first,sizeof(first))&&layer_read(t->epoch,selected,159,&last,sizeof(last))&&first.refresh==selected&&last.refresh==selected&&first.row==0&&last.row==159;
 if(layer_sync_log)fprintf(layer_sync_log,"%llu,%.12f,%u,%d\n",(unsigned long long)t->epoch,t->target,selected,found);
 if(!found||!layer_zero_read(t->epoch,selected,preview_zero_colors,sizeof(preview_zero_colors))){layer_missing++;return 0;}preview_zero_valid=1;layer_selected++;hud_epoch=t->epoch;hud_refresh=selected;}
 NFVisibilityIdentity left={t->epoch,a->serial,a->begin_refresh,a->end_refresh,0,0},right={t->epoch,b->serial,b->begin_refresh,b->end_refresh,0,0};size_t bytes=0;unsigned stage=0;uint64_t started=elapsed_ns();int generated;
 if(early_matches(t)){
  if(getenv("NF_VERIFY_PREPARED_PACKET")){void*check=NULL;size_t check_bytes=0;int ok=paired_extract(&left,&right,t->alpha,&check,&check_bytes,&stage);int equal=ok&&check_bytes==early_bytes&&!memcmp(check,early_owned,early_bytes);if(check)paired_free(check);if(!equal){early_failed++;early_clear();paired_rejected++;return 0;}early_verified++;}
  paired_owned=early_owned;bytes=early_bytes;early_owned=NULL;early_reused++;preparation_reuse_count++;generated=1;
 }else{early_clear();generated=paired_extract(&left,&right,t->alpha,&paired_owned,&bytes,&stage);}
paired_prepare_ns+=elapsed_ns()-started;if(!generated){paired_rejected++;return 0;}
 if(getenv("NF_OWNED_SUBMISSION")){const void*owned_packet;size_t owned_bytes;if(!layer_sync||!nf_submission_create(paired_owned,bytes,t,packet_source_older_refresh,packet_source_newer_refresh,packet_continuous_camera?packet_source_cameras:NULL,preview_zero_colors,submission_capture_row,NULL,&owned_submission)){printf("submission_error=%u target=%.12f\n",nf_submission_last_error(),t->target);submission_failed++;return 0;}submission_created++;if(!nf_submission_packet(owned_submission,&owned_packet,&owned_bytes)||!nf_scene_packet_view(owned_packet,owned_bytes,a)){submission_failed++;submission_clear();return 0;}}
 else if(!nf_scene_packet_view(paired_owned,bytes,a)){paired_free(paired_owned);paired_owned=NULL;return 0;}
 if(owned_submission){uint32_t source[2];nf_submission_sources(owned_submission,source);packet_source_older_refresh=source[0];packet_source_newer_refresh=source[1];const NFRigidPose*cameras=nf_submission_cameras(owned_submission);if(cameras)memcpy(packet_source_cameras,cameras,sizeof(packet_source_cameras));memcpy(preview_zero_colors,nf_submission_zero_colors(owned_submission),sizeof(preview_zero_colors));}
 *b=*a;paired_generated++;return 1;}
#include "deferred_capture.h"
static void endpoint_capture(void){static int captured;static unsigned sequence_frame;uint64_t rings=0,crossings=0;
#ifdef NF_ROAD_ATTRIBUTE_CORRECTION
 if(deferred_capture_uv_trigger&&preview_road_continuous_adjustments>=deferred_capture_uv_trigger&&deferred_capture_start==216000)deferred_capture_start=sequence_frame;
#endif
 if(paired_owned){if(deferred_capture_model_trigger&&deferred_capture_start==216000){NFScenePacket capture_view;uint32_t capture_bytes;memcpy(&capture_bytes,(const uint8_t*)paired_owned+8,4);if(nf_scene_packet_view(paired_owned,capture_bytes,&capture_view)&&nf_scene_packet_model_count(&capture_view)>=deferred_capture_model_trigger)deferred_capture_start=sequence_frame;}if(getenv("NF_CAPTURE_NATIVE_PACKETS")&&getenv("NF_CAPTURE_SEQUENCE")&&sequence_frame>=deferred_capture_start&&sequence_frame<deferred_capture_start+12)deferred_capture_native_packets(paired_owned,sequence_frame-deferred_capture_start);if(getenv("NF_CAPTURE_NATIVE_PACKET")&&getenv("NF_CAPTURE_SEQUENCE")&&sequence_frame==deferred_capture_start+9)deferred_capture_native_packet(paired_owned);paired_free(paired_owned);paired_owned=NULL;}
#ifdef NF_ROAD_ATTRIBUTE_CORRECTION
 static uint64_t previous_rings,previous_crossings;rings=preview_road_corrected_rings-previous_rings;crossings=preview_road_near_crossings-previous_crossings;previous_rings=preview_road_corrected_rings;previous_crossings=preview_road_near_crossings;
 if(getenv("NF_CAPTURE_SEQUENCE")&&sequence_frame>=deferred_capture_start&&sequence_frame<deferred_capture_start+12)deferred_capture_road_edges(sequence_frame-deferred_capture_start);road_clip_edge_count=0;
#endif
 const char*sequence=getenv("NF_CAPTURE_SEQUENCE");const char*path=getenv("NF_ENDPOINT_CAPTURE");char sequence_path[1200];if(sequence){unsigned index=sequence_frame++;if(index<deferred_capture_start||index>=deferred_capture_start+12)return;deferred_capture_source(index-deferred_capture_start,elapsed_ns(),&packet_presented_time,packet_source_older_refresh,packet_source_newer_refresh,hud_refresh,rings,crossings);snprintf(sequence_path,sizeof(sequence_path),"%s-%03u.ppm",sequence,index-deferred_capture_start);path=sequence_path;if(deferred_capture_frames){glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,deferred_capture_frames+(size_t)(index-deferred_capture_start)*3840*2160*3);deferred_capture_count++;return;}}else if(captured||!path)return;uint8_t*rgb=malloc(3840*2160*3);FILE*f=rgb?fopen(path,"wb"):NULL;if(!f){free(rgb);return;}glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,rgb);fprintf(f,"P6\n3840 2160\n255\n");for(int y=2159;y>=0;y--)fwrite(rgb+y*3840*3,3,3840,f);fclose(f);free(rgb);captured=1;}
#include "endpoint_surface_bounds.h"
#endif
#include "frame_clock.h"
#ifdef NF_ROAD_ATTRIBUTE_CORRECTION
#define NF_CAPTURE_UV_ADJUSTMENTS preview_road_continuous_adjustments
#else
#define NF_CAPTURE_UV_ADJUSTMENTS 0
#endif
#include "window_present.h"
#include "preview_warmup.h"
#include "controller_input.h"
#include "window_lifecycle.h"
#include "preview_availability.h"
#include "presentation_hold.h"
typedef int (*PacedSink)(void*,uint64_t,const void*,size_t);
typedef struct {uint64_t index,epoch,start,end,profile[6];unsigned before,after,keys,batch,present,scenes_before,scenes_after;} NFRefreshTrace;
static int native_packets;static int(*native_extract)(uint64_t,uint32_t,uint32_t,uint32_t,void**,size_t*,unsigned*);
static unsigned native_rebuilt,native_failed,native_stage;
static unsigned received,retained_rebuilt,retained_failed;
static int(*retained_extract)(uint64_t,uint32_t,uint32_t,uint32_t,void**,size_t*);
static void(*retained_free)(void*);
static uint32_t latest_scene_end,max_scene_span;
static int retain_paced(void*context,uint64_t epoch,const void*data,size_t size){
 void*owned=NULL;size_t bytes=0;NFScenePacket packet;
 if(!nf_scene_packet_view(data,size,&packet))return 0;
 /* Paired mode retains original immutable metadata/poses for timeline selection;
    every displayed packet is regenerated by paired_prepare, including endpoints. */
 if(native_packets&&!paired_packets){uint64_t started=elapsed_ns();unsigned stage=0;if(!native_extract(epoch,packet.serial,packet.begin_refresh,packet.end_refresh,&owned,&bytes,&stage)){native_failed++;native_stage=stage;return 0;}endpoint_prepare_ns+=elapsed_ns()-started;data=owned;size=bytes;native_rebuilt++;}
 if(retained_extract&&!native_packets){
  if(!retained_extract(epoch,packet.serial,packet.begin_refresh,packet.end_refresh,&owned,&bytes)){retained_failed++;return 0;}
  if(bytes!=size||memcmp(owned,data,size)){retained_free(owned);retained_failed++;return 0;}
  data=owned;size=bytes;retained_rebuilt++;
 }
 int ok=nf_scene_packet_push(context,epoch,data,size);if(owned)retained_free(owned);
 if(ok){received++;latest_scene_end=packet.end_refresh;uint32_t span=packet.end_refresh-packet.begin_refresh;if(span>max_scene_span)max_scene_span=span;}return ok;
}
static LARGE_INTEGER timer_origin,timer_frequency;
static uint64_t elapsed_ns(void){LARGE_INTEGER now;QueryPerformanceCounter(&now);return (uint64_t)((long double)(now.QuadPart-timer_origin.QuadPart)*1000000000.0L/timer_frequency.QuadPart);}
static uint64_t process_cpu_ns(void){FILETIME created,exited,kernel,user;ULARGE_INTEGER k,u;if(!GetProcessTimes(GetCurrentProcess(),&created,&exited,&kernel,&user))return UINT64_MAX;k.LowPart=kernel.dwLowDateTime;k.HighPart=kernel.dwHighDateTime;u.LowPart=user.dwLowDateTime;u.HighPart=user.dwHighDateTime;return (k.QuadPart+u.QuadPart)*100;}
#ifndef NF_PACED_NO_MAIN
int main(int argc,char**argv){
 #ifdef NF_NATIVE_ENDPOINT_RENDER
 hud_preview=getenv("NF_LIVE_HUD")!=NULL;if(hud_preview)layer_sync=1;
 classified_world=getenv("NF_LIVE_WORLD_CLASSIFIED")!=NULL;indexed_world=classified_world||getenv("NF_LIVE_WORLD_INDEXED")!=NULL;
 indexed_multimodel=getenv("NF_LIVE_MULTIMODEL_INDEXED")!=NULL;if(indexed_world)indexed_multimodel=1;preview_zero_background=indexed_multimodel;
#endif
 int window_output=0,controller_input=0,interactive=0,retained=0,scripted_route=0;unsigned duration_seconds=3,presentation_delay=5;
 if(argc<5)return 1;
 for(int i=5;i<argc;i++){if(!strcmp(argv[i],"--layer-sync")){
#ifdef NF_NATIVE_ENDPOINT_RENDER
 layer_sync=1;
#else
 return 15;
#endif
 }else if(!strcmp(argv[i],"--paired-packets"))paired_packets=native_packets=1;else if(!strcmp(argv[i],"--scripted-route"))scripted_route=1;else if(!strcmp(argv[i],"--native-packets"))native_packets=1;else if(!strcmp(argv[i],"--retained"))retained=1;else if(!strcmp(argv[i],"--window-buffer"))window_output=1;else if(!strcmp(argv[i],"--controller"))controller_input=1;else if(!strcmp(argv[i],"--interactive"))interactive=controller_input=1;else if(!strcmp(argv[i],"--delay-refreshes")&&i+1<argc){char*end;const char*value=argv[++i];unsigned long n=strtoul(value,&end,10);if(!*value||*end||n<1||n>30)return 1;presentation_delay=(unsigned)n;}else if(!strcmp(argv[i],"--seconds")&&i+1<argc){char*end;const char*value=argv[++i];unsigned long n=strtoul(value,&end,10);if(!*value||*end||n<1||n>3600)return 1;duration_seconds=(unsigned)n;}else return 1;}
#ifdef NF_NATIVE_ENDPOINT_RENDER
 if(!native_packets)return 15;
 if(indexed_multimodel&&(!paired_packets||!layer_sync))return 15;
#endif
 if(controller_input)window_output=1; /* DLL, ROM, saved state, CSV */
 HMODULE bridge=LoadLibraryA(argv[1]);if(!bridge)return 2;
 int(*init)(const char*,const char*)=(void*)GetProcAddress(bridge,"nf_init");
 int(*state)(const char*,int)=(void*)GetProcAddress(bridge,"nf_state");
 int(*sink)(PacedSink,void*)=(void*)GetProcAddress(bridge,"nf_native_scene_sink");
 void(*frame)(unsigned)=(void*)GetProcAddress(bridge,"nf_frame");
 void(*profile_enable)(unsigned)=(void*)GetProcAddress(bridge,"nf_capture_profile_enable");
 int(*profile_read)(uint64_t*)=(void*)GetProcAddress(bridge,"nf_capture_profile_read");
 if(getenv("NF_CAPTURE_PROFILE")){if(!profile_enable||!profile_read)return 16;profile_enable(1);}
 void(*close_game)(void)=(void*)GetProcAddress(bridge,"nf_close");
 uint64_t(*epoch)(void)=(void*)GetProcAddress(bridge,"nf_native_scene_epoch");
 uint32_t(*refresh)(void)=(void*)GetProcAddress(bridge,"nf_native_scene_refresh");
 void(*discontinuity)(void)=(void*)GetProcAddress(bridge,"nf_native_scene_discontinuity");
 void(*scene_stats)(uint32_t*)=(void*)GetProcAddress(bridge,"nf_native_scene_stats");
 if(!init||!state||!sink||!frame||!close_game||!epoch||!refresh||!discontinuity||!scene_stats)return 3;
 NFSnapshotStore*s=nf_snapshot_create(32*1024*1024);if(!s)return 4;
 if(!init(argv[2],"")||!state(argv[3],0)||!sink(retain_paced,s))return 5;
#ifdef NF_NATIVE_ENDPOINT_RENDER
 if(indexed_multimodel){int(*enable_models)(int)=(void*)GetProcAddress(bridge,"nf_native_scene_multimodel");if(!enable_models||!enable_models(1))return 15;}
#endif
 if(native_packets){
#ifndef NF_NATIVE_ENDPOINT_RENDER
  return 15;
#endif
  if(retained)return 15;packet_endpoint_only=!paired_packets;native_extract=(void*)GetProcAddress(bridge,"nf_live_completed_native_packet_owned");if(!native_extract)return 15;
#ifdef NF_NATIVE_ENDPOINT_RENDER
  paired_extract=(void*)GetProcAddress(bridge,classified_world?"nf_live_completed_native_multimodel_world_classified_pair_packet":indexed_world?"nf_live_completed_native_multimodel_world_indexed_pair_packet":indexed_multimodel?"nf_live_completed_native_multimodel_indexed_pair_packet":"nf_live_completed_native_pair_packet");paired_free=(void*)GetProcAddress(bridge,"nf_scene_packet_free");if(paired_packets&&(!paired_extract||!paired_free))return 15;
#endif
 }
 if(retained||native_packets){
  retained_extract=(void*)GetProcAddress(bridge,"nf_live_completed_scene_extract");retained_free=(void*)GetProcAddress(bridge,"nf_scene_packet_free");
  int(*enable)(const void*,size_t,size_t)=(void*)GetProcAddress(bridge,"nf_live_visibility_enable");void(*audit)(int)=(void*)GetProcAddress(bridge,"nf_live_surface_audit_enable");
  if(!retained_extract||!retained_free||!enable||!audit)return 10;
  FILE*rom=fopen(argv[2],"rb");if(!rom)return 11;fseek(rom,0,SEEK_END);long bytes=ftell(rom);rewind(rom);
  if(bytes<=0||bytes>32*1024*1024){fclose(rom);return 11;}
  void*copy=malloc((size_t)bytes);if(!copy){fclose(rom);return 11;}
  int ok=fread(copy,1,(size_t)bytes,rom)==(size_t)bytes&&enable(copy,(size_t)bytes,16*1024*1024);free(copy);fclose(rom);if(!ok)return 12;audit(1);
 }
 #ifdef NF_NATIVE_ENDPOINT_RENDER
 if(layer_sync){if(!paired_packets||presentation_delay>12)return 15;int(*enable_layers)(unsigned)=(void*)GetProcAddress(bridge,"nf_layer_queue_enable");bridge_layer_read=(void*)GetProcAddress(bridge,"nf_layer_queue_hud_row");layer_read=submission_layer_read;layer_zero_read=(void*)GetProcAddress(bridge,"nf_layer_queue_zero_colors");if(!enable_layers||!bridge_layer_read||!layer_zero_read||!enable_layers(1))return 15;const char*layer_log=getenv("NF_LAYER_SYNC_LOG");if(layer_log){layer_sync_log=fopen(layer_log,"w");if(!layer_sync_log)return 15;fprintf(layer_sync_log,"epoch,target,selected_refresh,found\n");}}
#endif
 HMODULE input_module=NULL;NFGetPad getpad=NULL;
 if(controller_input){input_module=LoadLibraryA("xinput1_4.dll");if(!input_module)input_module=LoadLibraryA("xinput9_1_0.dll");if(input_module)getpad=(void*)GetProcAddress(input_module,"XInputGetState");}
 unsigned input_polls=0,connected_polls=0,incompatible_frames=0;
 FILE*log=fopen(argv[4],"wb");if(!log)return 6;
 const char*packet_trace_path=getenv("NF_PACKET_TRACE");uint64_t(*packet_trace)[10]=NULL;size_t packet_trace_count=0;
 if(packet_trace_path){packet_trace=calloc(4096,sizeof(*packet_trace));if(!packet_trace){fclose(log);return 16;}packet_trace_enabled=1;}
 const char*trace_path=getenv("NF_REFRESH_TRACE");NFRefreshTrace*trace=NULL;size_t trace_count=0,trace_capacity=0;
 if(trace_path){trace_capacity=interactive?4096:(size_t)duration_seconds*60+256;trace=malloc(trace_capacity*sizeof(*trace));if(!trace)return 16;}
 fprintf(log,"poll_ns,display_index,skipped,deadline_ns,render_start_ns,render_end_ns,simulated,refresh,ready,target,older,newer,alpha,swap_end_ns,timeline_status,epoch_mismatch,latest_scene_end,lighting_range,lighting_narrow,lighting_sample,repeated,camera_x,camera_y,camera_z,object_x,object_y,object_z,camera_qx,camera_qy,camera_qz,camera_qw,object_qx,object_qy,object_qz,object_qw,simulation_start_ns,simulation_end_ns,endpoint_prepare_ns,paired_prepare_ns,renderer_load_ns,renderer_draw_ns,renderer_hud_ns,renderer_finish_ns,source_older_refresh,source_newer_refresh,continuous_uv_adjustments,early_generation_since_display_ns,early_generation_total_ns,early_reused_since_display,early_gpu_since_display_ns,early_gpu_total_ns,early_gpu_reused,display_simulation_steps,simulation_since_display_ns,simulation_total_ns,original_steps_since_display,original_steps_total\n");
 preview_window_output=window_output;
 preview_keep_context=1;preview_measure_only=1;_putenv("NF_PREVIEW_PHASE=0");
 QueryPerformanceFrequency(&timer_frequency);QueryPerformanceCounter(&timer_origin);
 const char*phase=getenv("NF_PRESENT_PHASE_US");if(phase){char*end;unsigned long value=strtoul(phase,&end,10);if(!*phase||*end||value>15000)return 18;presentation_phase_ns=(uint64_t)value*1000;}
 if(!nf_deadline_wait_init())return 18;
 int setup_error=preview_context_open();if(setup_error)return setup_error;
 if(indexed_multimodel&&!model_zero_shader())return 37;
 uint32_t setup_refresh=refresh();
 if(!preview_draw_warmup()||refresh()!=setup_refresh)return 13;
#ifdef NF_NATIVE_ENDPOINT_RENDER
 if(!endpoint_hud_warmup()||refresh()!=setup_refresh)return 13;
#endif
 glClearColor(0,0,0,1);glClear(GL_COLOR_BUFFER_BIT);glFinish();
 #ifdef NF_NATIVE_ENDPOINT_RENDER
 if(!deferred_capture_init())return 17;
#endif
 uint64_t setup_ns=elapsed_ns();QueryPerformanceCounter(&timer_origin);
 uint64_t cpu_start_ns=process_cpu_ns();if(cpu_start_ns==UINT64_MAX)return 18;
 NFFrameClock clock;nf_frame_clock_start(&clock,0,refresh(),presentation_delay);unsigned rendered=0,empty=0,swaps=0;uint64_t skipped=0;int result=0;
 NFPresentationHold hold={0};unsigned repeats=0;
 uint64_t preparation_lead=0,preparation_index=UINT64_MAX,preparation_epoch=0;
 unsigned preparation_windows=0,preparation_available=0;
 const char*preparation_option=getenv("NF_PREPARATION_LEAD_US");
 if(preparation_option){char*tail;unsigned long value=strtoul(preparation_option,&tail,10);if(!*preparation_option||*tail||value>15000)return 18;preparation_lead=(uint64_t)value*1000;}
 char*args[]={argv[0],"unused","unused","unused"};
#ifdef NF_NATIVE_ENDPOINT_RENDER
 const char*minimum_models=getenv("NF_VERIFY_EARLY_GPU_MIN_MODELS");if(minimum_models){char*end;unsigned long value=strtoul(minimum_models,&end,10);if(!*minimum_models||*end||value<1||value>16)return 18;early_gpu_min_models=(unsigned)value;}
 const char*verify_limit=getenv("NF_VERIFY_EARLY_GPU_LIMIT");if(verify_limit){char*end;unsigned long value=strtoul(verify_limit,&end,10);if(!*verify_limit||*end||value<1||value>1000)return 18;early_gpu_verify_limit=(unsigned)value;}
 early_gpu=getenv("NF_PREPARE_GPU")!=NULL;if(early_gpu&&(!paired_packets||!preparation_lead))return 18;
#endif
 int was_running=1;unsigned lifecycle_generation=0;
 int lifecycle_test=getenv("NF_TEST_WINDOW_LIFECYCLE")!=NULL;unsigned lifecycle_test_phase=0,lifecycle_test_freezes=0,lifecycle_test_discards=0;int lifecycle_test_active=0,lifecycle_test_closed=0;uint64_t lifecycle_resume_ns=0,lifecycle_saved_steps=0;uint32_t lifecycle_saved_refresh=0;
 if(lifecycle_test){if(!window_output||interactive)return 18;if(!nf_window_attach(preview_window))return 14;SendMessage(preview_window,WM_SETFOCUS,0,0);}

 if(interactive){if(!nf_window_attach(preview_window))return 14;SetWindowTextA(preview_window,"NFSUG renderer diagnostic — Space: pause, Esc: close (no audio)");ShowWindow(preview_window,SW_SHOW);}

 for(;;){
  MSG message;int quit=0;while(PeekMessage(&message,NULL,0,0,PM_REMOVE)){if(message.message==WM_QUIT)quit=1;TranslateMessage(&message);DispatchMessage(&message);}
  if(quit||((interactive||lifecycle_test)&&window_lifecycle.closed))break;
  uint64_t now=elapsed_ns();if(!interactive&&now>=(uint64_t)duration_seconds*1000000000ull)break;
  if(lifecycle_test&&lifecycle_test_active&&now>=lifecycle_resume_ns){
   if(refresh()!=lifecycle_saved_refresh||original_steps_total!=lifecycle_saved_steps){result=19;break;}
   if(lifecycle_test_phase==1)SendMessage(preview_window,WM_KEYDOWN,VK_SPACE,0);
   else if(lifecycle_test_phase==2)SendMessage(preview_window,WM_SIZE,SIZE_RESTORED,MAKELPARAM(1280,720));
   else if(lifecycle_test_phase==3)SendMessage(preview_window,WM_EXITSIZEMOVE,0,0);
   else SendMessage(preview_window,WM_SETFOCUS,0,0);
   lifecycle_test_active=0;lifecycle_test_freezes++;printf("test_window_resume=%u total_steps=%llu refresh=%u\n",lifecycle_test_phase,(unsigned long long)original_steps_total,refresh());
  }
  if(interactive||lifecycle_test){
   int running=nf_window_running();
   int changed=lifecycle_generation!=window_lifecycle.generation;lifecycle_generation=window_lifecycle.generation;
   if(!running){
#ifdef NF_NATIVE_ENDPOINT_RENDER
    if(lifecycle_test&&lifecycle_test_active&&early_frame_valid)lifecycle_test_discards++;
    early_clear();early_frame_clear();
#endif
    hold.valid=0;
    if(was_running&&!window_lifecycle.minimized){if(!preview_window_stage(0)||!preview_window_finish()){result=12;break;}}
    was_running=0;Sleep(10);continue;
   }
   if(!was_running||changed){
#ifdef NF_NATIVE_ENDPOINT_RENDER
    early_clear();early_frame_clear();
#endif
    hold.valid=0;discontinuity();if(!nf_frame_clock_start(&clock,now,refresh(),presentation_delay)){result=7;break;}}
   was_running=1;
  }
  NFPreparationPlan preparation={0};
  if(preparation_lead){
   if(!nf_frame_clock_prepare(&clock,now,preparation_lead,&preparation)){result=7;break;}
   if(preparation.eligible&&(preparation_index!=preparation.display_index||preparation_epoch!=epoch())){
    preparation_index=preparation.display_index;preparation_epoch=epoch();preparation_windows++;
#ifdef NF_NATIVE_ENDPOINT_RENDER
    if(early_gpu)early_frame_clear();
#endif
    NFSnapshotPair candidate;int status=nf_snapshot_acquire(s,preparation.source_target,0,&candidate);
    if(status==NF_TIME_READY&&candidate.time.epoch==preparation_epoch){preparation_available++;
#ifdef NF_NATIVE_ENDPOINT_RENDER
    early_prepare(&candidate);
#endif
   }
    nf_snapshot_release(s);
#ifdef NF_NATIVE_ENDPOINT_RENDER
    if(early_gpu&&status==NF_TIME_READY&&candidate.time.epoch==preparation_epoch&&(interactive||preparation.deadline_ns<(uint64_t)duration_seconds*1000000000ull)){
     uint64_t begin=elapsed_ns();int available=1,incompatible=0;
     result=preview_render_available(s,preparation.source_target,args,&available,&incompatible);early_gpu_ns+=elapsed_ns()-begin;
     if(result)break;
     if(available){early_frame_time=candidate.time;early_frame_index=preparation.display_index;early_frame_valid=1;early_gpu_rendered++;
      /* Exercise the real capture epoch reset while a rendered frame is pending. */
      if(getenv("NF_TEST_EPOCH_CUT")&&test_epoch_cuts<3&&preparation.display_index>=(uint64_t)(test_epoch_cuts+1)*180){uint64_t before=epoch();discontinuity();if(epoch()<=before){result=19;break;}printf("test_epoch_cut_index=%llu old_epoch=%llu new_epoch=%llu\n",(unsigned long long)preparation.display_index,(unsigned long long)before,(unsigned long long)epoch());test_epoch_cuts++;test_epoch_pending=1;}
     }
     else if(paired_owned){paired_free(paired_owned);paired_owned=NULL;}
    }
#endif
   }
  }
  #ifdef NF_NATIVE_ENDPOINT_RENDER
  if(getenv("NF_TEST_CLOCK_RESTART")&&early_frame_valid&&test_clock_restarts<3&&original_steps_total>=(uint64_t)(test_clock_restarts+1)*180){
   uint32_t before=refresh();uint64_t steps_before=original_steps_total;hold.valid=0;early_clear();early_frame_clear();Sleep(200);
   if(refresh()!=before||original_steps_total!=steps_before){result=19;break;}
   discontinuity();now=elapsed_ns();if(!nf_frame_clock_start(&clock,now,refresh(),presentation_delay)){result=7;break;}
   test_clock_restarts++;preparation_index=UINT64_MAX;
   printf("test_clock_restart=%u total_steps=%llu refresh=%u origin_ns=%llu\n",test_clock_restarts,(unsigned long long)original_steps_total,refresh(),(unsigned long long)now);continue;
  }
#endif
  #ifdef NF_NATIVE_ENDPOINT_RENDER
  if(lifecycle_test&&early_frame_valid&&!lifecycle_test_active){
   if(lifecycle_test_phase<4&&original_steps_total>=(uint64_t)(lifecycle_test_phase+1)*180){
    lifecycle_test_phase++;lifecycle_test_active=1;lifecycle_saved_refresh=refresh();lifecycle_saved_steps=original_steps_total;lifecycle_resume_ns=elapsed_ns()+200000000;
    if(lifecycle_test_phase==1)SendMessage(preview_window,WM_KEYDOWN,VK_SPACE,0);
    else if(lifecycle_test_phase==2)SendMessage(preview_window,WM_SIZE,SIZE_MINIMIZED,0);
    else if(lifecycle_test_phase==3)SendMessage(preview_window,WM_ENTERSIZEMOVE,0,0);
    else SendMessage(preview_window,WM_KILLFOCUS,0,0);
    if(nf_window_running()){result=19;break;}printf("test_window_suspend=%u total_steps=%llu refresh=%u\n",lifecycle_test_phase,(unsigned long long)original_steps_total,refresh());continue;
   }
   if(lifecycle_test_phase==4&&lifecycle_test_freezes==4&&original_steps_total>=800){SendMessage(preview_window,WM_CLOSE,0,0);lifecycle_test_closed=window_lifecycle.closed;continue;}
  }
#endif
  now=elapsed_ns(); /* Early generation consumes real time: poll current time. */
  NFFramePlan plan;if(!nf_frame_clock_poll(&clock,now,&plan)){result=7;break;}
  uint64_t endpoint_before=endpoint_prepare_ns;paired_prepare_ns=0;uint64_t simulation_start=elapsed_ns();
  for(unsigned i=0;i<plan.simulation_steps;i++){
   unsigned keys=1;
   if(scripted_route){uint64_t index=original_steps_total+i;keys|=index>=180&&index<500?32:index>=500&&index<720?16:0;}
   if(controller_input){int connected=0,focused=GetForegroundWindow()==preview_window;keys=nf_input_sample(focused,focused?nf_input_keyboard():0,getpad,&connected);input_polls++;connected_polls+=connected;}
   if(trace){
    if(trace_count==trace_capacity){size_t next=trace_capacity*2;if(next<=trace_capacity||next>SIZE_MAX/sizeof(*trace)){result=16;break;}NFRefreshTrace*grown=realloc(trace,next*sizeof(*trace));if(!grown){result=16;break;}trace=grown;trace_capacity=next;}
    NFRefreshTrace*r=trace+trace_count;r->index=original_steps_total+i;r->epoch=epoch();r->before=refresh();r->keys=keys;r->batch=plan.simulation_steps;r->present=plan.present;r->scenes_before=received;r->start=elapsed_ns();frame(keys);r->end=elapsed_ns();memset(r->profile,0,sizeof(r->profile));if(getenv("NF_CAPTURE_PROFILE")&&!profile_read(r->profile)){result=16;break;}r->after=refresh();r->scenes_after=received;trace_count++;
   }else frame(keys);
  }
  if(result)break;
  uint64_t simulation_end=elapsed_ns();
  if(plan.simulation_steps){original_work_ns+=simulation_end-simulation_start;original_steps_total+=plan.simulation_steps;}
  if(plan.present){
   NFSnapshotPair pair;int timeline_status=nf_snapshot_acquire(s,plan.source_target,0,&pair),ready=timeline_status==NF_TIME_READY;
   int epoch_mismatch=timeline_status!=NF_TIME_EMPTY&&pair.time.epoch!=epoch();if(epoch_mismatch)ready=0;
   nf_snapshot_release(s);
   uint64_t start=elapsed_ns();
   memset(renderer_marks,0,sizeof(renderer_marks));int incompatible=0,gpu_reused=0;
   memset(packet_marks,0,sizeof(packet_marks));
   #ifdef NF_NATIVE_ENDPOINT_RENDER
   /* Diagnostic rejection exercises due-time fallback without touching original logic. */
   if(early_gpu&&early_frame_valid&&getenv("NF_TEST_DISCARD_GPU")&&plan.display_index%60==0){hold.valid=0;early_frame_clear();}
   int reuse_gpu=early_gpu&&early_frame_valid&&ready&&early_frame_index==plan.display_index&&same_sample(&early_frame_time,&pair.time)&&early_frame_time.epoch==epoch();
   if(reuse_gpu){gpu_reused=1;early_frame_valid=0;
    if(getenv("NF_VERIFY_EARLY_GPU_PIXELS")&&plan.simulation_steps&&early_gpu_verified<early_gpu_verify_limit&&prepared_model_count()>=early_gpu_min_models)result=verify_early_pixels(s,plan.source_target,args,plan.simulation_steps);
    if(result){early_gpu_discarded++;gpu_reused=0;}else early_gpu_presented++;
   }
   else{if(early_gpu){if(early_frame_valid)hold.valid=0;early_frame_clear();}result=preview_render_available(s,plan.source_target,args,&ready,&incompatible);}
#else
   result=preview_render_available(s,plan.source_target,args,&ready,&incompatible);
#endif
   if(result)break;
#ifdef NF_NATIVE_ENDPOINT_RENDER
   if(ready)endpoint_capture();
#endif
   if(packet_trace&&ready){if(packet_trace_count>=4096){result=16;break;}uint64_t*r=packet_trace[packet_trace_count++];r[0]=plan.display_index;r[1]=paired_prepare_ns;memcpy(r+2,packet_marks,sizeof(packet_marks));}
   incompatible_frames+=incompatible;
   int repeated=nf_presentation_hold(&hold,epoch(),plan.source_target,ready,epoch_mismatch?NF_TIME_EMPTY:timeline_status);
   repeats+=repeated;
   if(ready)rendered++;else empty++;
   uint64_t end=elapsed_ns();skipped+=plan.skipped_displays;
   if(window_output&&presentation_phase_ns&&!nf_deadline_wait_until(plan.deadline_ns+presentation_phase_ns)){result=18;break;}
   if(window_output){if(!preview_window_stage(ready||repeated)||!preview_window_finish()){result=12;break;}swaps++;}
   uint64_t swap_end=elapsed_ns();
   fprintf(log,"%llu,%llu,%llu,%llu,%llu,%llu,%llu,%u,%d,%.12f,%llu,%llu,%.12f,%llu,%d,%d,%u,%u,%u,%u,%d,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.12f,%.12f,%.12f,%.12f,%.12f,%.12f,%.12f,%.12f,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%u,%u,%llu,",(unsigned long long)now,(unsigned long long)plan.display_index,(unsigned long long)plan.skipped_displays,(unsigned long long)plan.deadline_ns,(unsigned long long)start,(unsigned long long)end,(unsigned long long)original_steps_total,refresh(),ready,plan.source_target,ready?(unsigned long long)packet_presented_time.older:0,ready?(unsigned long long)packet_presented_time.newer:0,ready?packet_presented_time.alpha:0,(unsigned long long)swap_end,timeline_status,epoch_mismatch,latest_scene_end,lighting_range_fallback,lighting_narrow_fallback,lighting_sample_fallback,repeated,packet_presented_camera.position.x,packet_presented_camera.position.y,packet_presented_camera.position.z,packet_presented_object.position.x,packet_presented_object.position.y,packet_presented_object.position.z,packet_presented_camera.rotation.x,packet_presented_camera.rotation.y,packet_presented_camera.rotation.z,packet_presented_camera.rotation.w,packet_presented_object.rotation.x,packet_presented_object.rotation.y,packet_presented_object.rotation.z,packet_presented_object.rotation.w,(unsigned long long)simulation_start,(unsigned long long)simulation_end,(unsigned long long)(endpoint_prepare_ns-endpoint_before),(unsigned long long)paired_prepare_ns,(unsigned long long)(renderer_marks[1]-renderer_marks[0]),(unsigned long long)(renderer_marks[2]-renderer_marks[1]),(unsigned long long)(renderer_marks[3]-renderer_marks[2]),(unsigned long long)(renderer_marks[4]-renderer_marks[3]),ready?packet_source_older_refresh:0,ready?packet_source_newer_refresh:0,(unsigned long long)NF_CAPTURE_UV_ADJUSTMENTS);
   /* Include every early attempt since the preceding display, including discarded work. */
   fprintf(log,"%llu,%llu,%u,%llu,%llu,%d,%u,%llu,%llu,%llu,%llu\n",(unsigned long long)(preparation_total_ns-preparation_reported_ns),(unsigned long long)preparation_total_ns,preparation_reuse_count-preparation_reported_reuse,(unsigned long long)(early_gpu_ns-early_gpu_reported_ns),(unsigned long long)early_gpu_ns,gpu_reused,plan.simulation_steps,(unsigned long long)(original_work_ns-original_reported_work_ns),(unsigned long long)original_work_ns,(unsigned long long)(original_steps_total-original_reported_steps),(unsigned long long)original_steps_total);original_reported_work_ns=original_work_ns;original_reported_steps=original_steps_total;early_gpu_reported_ns=early_gpu_ns;
   preparation_reported_ns=preparation_total_ns;preparation_reported_reuse=preparation_reuse_count;
  }
  if(preparation_lead&&preparation.next_wake_ns>now&&preparation.next_wake_ns<plan.next_wake_ns)plan.next_wake_ns=preparation.next_wake_ns;
  if(!nf_deadline_wait_until(plan.next_wake_ns)){result=18;break;}
 }
 if((retained_failed||native_failed)&&!result)result=27;
 printf("submission_created=%u submission_failed=%u submission_retirement_tests=%u\n",submission_created,submission_failed,submission_retirement_tests);if(submission_failed)result=16;
 if(getenv("NF_LAYER_DIRTY")){void(*stats)(uint64_t*)=(void*)GetProcAddress(bridge,"nf_layer_snapshot_dirty_stats");if(!stats)result=16;else{uint64_t v[3];stats(v);printf("layer_clean_reused=%llu layer_clean_verified=%llu layer_clean_failed=%llu\n",(unsigned long long)v[0],(unsigned long long)v[1],(unsigned long long)v[2]);if(v[2])result=16;}}
 if(getenv("NF_CAPTURE_PROFILE")){int(*events)(unsigned,uint64_t*)=(void*)GetProcAddress(bridge,"nf_capture_event_profile_read");if(!events)result=16;else for(unsigned i=0;i<64;i++){uint64_t values[3];if(!events(i,values))break;printf("capture_event_pc=%08x calls=%llu ns=%llu\n",(unsigned)values[0],(unsigned long long)values[1],(unsigned long long)values[2]);}}
 void(*scratch_stats)(uint64_t*)=(void*)GetProcAddress(bridge,"nf_live_surface_scratch_stats");if(scratch_stats){uint64_t values[3];scratch_stats(values);printf("surface_audit_reads=%llu scratch_growths=%llu scratch_bytes=%llu\n",(unsigned long long)values[0],(unsigned long long)values[1],(unsigned long long)values[2]);}
 if(getenv("NF_CAPTURE_PROFILE")){int(*surface_profile)(uint64_t*)=(void*)GetProcAddress(bridge,"nf_live_surface_capture_profile_read");if(surface_profile){uint64_t v[4];if(!surface_profile(v))result=16;else printf("surface_capture_extract_ns=%llu surface_capture_defer_ns=%llu surface_capture_hash_ns=%llu surface_capture_calls=%llu\n",(unsigned long long)v[0],(unsigned long long)v[1],(unsigned long long)v[2],(unsigned long long)v[3]);}}
 void(*validation_stats)(uint64_t*)=(void*)GetProcAddress(bridge,"nf_live_surface_validation_stats");if(validation_stats){uint64_t v[2];validation_stats(v);printf("surface_input_exact=%llu surface_differential_fallback=%llu\n",(unsigned long long)v[0],(unsigned long long)v[1]);}
 void(*model_validation)(uint64_t*)=(void*)GetProcAddress(bridge,"nf_live_model_validation_stats");if(model_validation){uint64_t v[2];model_validation(v);printf("model_input_exact=%llu model_differential_fallback=%llu\n",(unsigned long long)v[0],(unsigned long long)v[1]);}
 printf("native_endpoint_packets=%u native_failed=%u native_failure_stage=%u endpoint_only=%d\n",native_rebuilt,native_failed,native_stage,packet_endpoint_only);
 printf("paired_generated=%u paired_rejected=%u\n",paired_generated,paired_rejected);
 void (*asset_stats)(uint64_t*)=(void*)GetProcAddress(bridge,"nf_assembly_asset_stats");
 if(asset_stats){uint64_t counts[2];asset_stats(counts);printf("assembly_reused_assets=%llu assembly_extractions=%llu\n",(unsigned long long)counts[0],(unsigned long long)counts[1]);}
 void (*palette_stats)(uint64_t*)=(void*)GetProcAddress(bridge,"nf_scene_command_palette_stats");
 if(palette_stats){uint64_t ps[6];palette_stats(ps);printf("palette_calls=%llu palette_matches=%llu palette_duplicates=%llu palette_extractions=%llu palette_consensus_calls=%llu palette_consensus_extractions=%llu\n",(unsigned long long)ps[0],(unsigned long long)ps[1],(unsigned long long)ps[2],(unsigned long long)ps[3],(unsigned long long)ps[4],(unsigned long long)ps[5]);}
#ifdef NF_NATIVE_ENDPOINT_RENDER
 printf("classified_world=%d wall_zero_draws=%u\n",classified_world,wall_zero_draws);
 printf("texture_uploads=%u texture_hits=%u texture_evictions=%u texture_uploaded_bytes=%llu texture_hint_hits=%u texture_hash_bytes_saved=%llu\n",preview_uploads,preview_hits,preview_evictions,(unsigned long long)preview_uploaded_bytes,preview_texture_hint_hits,(unsigned long long)preview_texture_hash_bytes_saved);
 printf("indexed_world=%d world_zero_draws=%u\n",indexed_world,world_zero_draws);
 printf("indexed_multimodel=%d model_zero_draws=%u\n",indexed_multimodel,model_zero_draws);
 printf("hud_drawn=%u hud_failed=%u\n",hud_drawn,hud_failed);printf("hud_prepare_ms=%.6f hud_candidate_builds=%u hud_effect_batches=%u\n",hud_prepare_ms,hud_candidate_builds,hud_effect_batches);printf("layer_selected=%u layer_missing=%u\n",layer_selected,layer_missing);if(layer_sync_log)fclose(layer_sync_log);
#endif
 printf("presentation_delay_refreshes=%u\n",presentation_delay);
 printf("retained_rebuilt=%u retained_failed=%u\n",retained_rebuilt,retained_failed);
 if(packet_trace){FILE*f=fopen(packet_trace_path,"wb");if(!f)result=16;else{fprintf(f,"display,native_generation_ns,begin_ns,validated_ns,prepared_ns,metadata_ns,assembled_ns,selected_ns,rendered_ns,released_ns\n");for(size_t i=0;i<packet_trace_count;i++){for(unsigned j=0;j<10;j++)fprintf(f,j?",%llu":"%llu",(unsigned long long)packet_trace[i][j]);fputc('\n',f);}int failed=ferror(f);if(fclose(f))failed=1;if(failed)result=16;}free(packet_trace);packet_trace_enabled=0;printf("packet_trace_records=%llu\n",(unsigned long long)packet_trace_count);}
 fclose(log);printf("result=%d live_packets=%u rendered=%u unavailable=%u skipped=%llu simulated=%llu contexts=%u lighting_fallbacks=%u elapsed_ns=%llu setup_ns=%llu swaps=%u window_buffer=%d\n",result,received,rendered,empty,(unsigned long long)skipped,(unsigned long long)original_steps_total,preview_contexts,lighting_fallback,(unsigned long long)elapsed_ns(),(unsigned long long)setup_ns,swaps,window_output);
 if(trace){FILE*f=fopen(trace_path,"wb");if(!f)result=16;else{fprintf(f,"index,epoch,before,after,keys,batch,present,scenes_before,scenes_after,start_ns,end_ns,live_capture_ns,live_capture_calls,layer_capture_ns,layer_capture_calls,original_scanline_ns,original_scanline_calls\n");for(size_t i=0;i<trace_count;i++){NFRefreshTrace*r=trace+i;fprintf(f,"%llu,%llu,%u,%u,%u,%u,%u,%u,%u,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu\n",(unsigned long long)r->index,(unsigned long long)r->epoch,r->before,r->after,r->keys,r->batch,r->present,r->scenes_before,r->scenes_after,(unsigned long long)r->start,(unsigned long long)r->end,(unsigned long long)r->profile[0],(unsigned long long)r->profile[1],(unsigned long long)r->profile[2],(unsigned long long)r->profile[3],(unsigned long long)r->profile[4],(unsigned long long)r->profile[5]);}int trace_error=ferror(f);if(fclose(f))trace_error=1;if(trace_error)result=16;}free(trace);printf("refresh_trace_records=%llu\n",(unsigned long long)trace_count);}
 #ifdef NF_ROAD_ATTRIBUTE_CORRECTION
 printf("road_attribute_corrected_rings=%llu\n",(unsigned long long)preview_road_corrected_rings);
 printf("continuous_camera_frames=%llu\n",(unsigned long long)packet_continuous_camera_frames);
 printf("continuous_road_uv_adjustments=%llu\n",(unsigned long long)preview_road_continuous_adjustments);
#endif
 printf("controller_mode=%d input_polls=%u connected_polls=%u xinput_available=%d\n",controller_input,input_polls,connected_polls,getpad!=NULL);
 printf("incompatible_scene_frames=%u repeated_frames=%u blank_frames=%u\n",incompatible_frames,repeats,empty-repeats);
 printf("max_scene_span=%u lighting_range=%u lighting_narrow=%u lighting_sample=%u native_narrow_shading=%u\n",max_scene_span,lighting_range_fallback,lighting_narrow_fallback,lighting_sample_fallback,lighting_native_narrow);
 uint32_t stats[4];scene_stats(stats);
 printf("closed_scenes=%u published_scenes=%u rejected_scenes=%u sink_failures=%u duration_seconds=%u\n",stats[0],stats[1],stats[2],stats[3],duration_seconds);
 if(input_module)FreeLibrary(input_module);
 const char*ram_prefix=getenv("NF_ENDPOINT_RAM_PREFIX");if(ram_prefix){void(*dump)(const char*,unsigned,unsigned)=(void*)GetProcAddress(bridge,"nf_dump");if(dump){char path[1200];snprintf(path,sizeof(path),"%s-ewram.bin",ram_prefix);dump(path,0x02000000,0x40000);snprintf(path,sizeof(path),"%s-iwram.bin",ram_prefix);dump(path,0x03000000,0x8000);}}
 #ifdef NF_NATIVE_ENDPOINT_RENDER
 if(!deferred_capture_flush())result=17;
#endif
 printf("presentation_phase_us=%llu\n",(unsigned long long)(presentation_phase_ns/1000));
 printf("preparation_lead_us=%llu preparation_windows=%u preparation_available=%u\n",(unsigned long long)(preparation_lead/1000),preparation_windows,preparation_available);
 printf("precise_wait=%d deadline_waits=%u\n",nf_deadline_timer!=NULL,nf_deadline_waits);if(nf_deadline_timer)CloseHandle(nf_deadline_timer);
 #ifdef NF_NATIVE_ENDPOINT_RENDER
 printf("early_generated=%u early_reused=%u early_discarded=%u early_verified=%u early_failed=%u early_generation_ns=%llu\n",early_generated,early_reused,early_discarded,early_verified,early_failed,(unsigned long long)early_generation_ns);
 printf("early_gpu_rendered=%u early_gpu_presented=%u early_gpu_discarded=%u early_gpu_pending=%d early_gpu_ns=%llu\n",early_gpu_rendered,early_gpu_presented,early_gpu_discarded,early_frame_valid,(unsigned long long)early_gpu_ns);
 printf("test_epoch_cuts=%u test_epoch_rejections=%u\n",test_epoch_cuts,test_epoch_rejections);
 printf("early_gpu_verified=%u early_gpu_verification_draws=%u early_gpu_verify_failed=%u early_gpu_verified_updates=%u early_gpu_verification_ns=%llu\n",early_gpu_verified,early_gpu_verification_draws,early_gpu_verify_failed,early_gpu_verified_updates,(unsigned long long)early_gpu_verification_ns);early_frame_clear();early_clear();if(paired_owned){paired_free(paired_owned);paired_owned=NULL;}
#endif
 printf("early_gpu_unreported_ns=%llu\n",(unsigned long long)(early_gpu_ns-early_gpu_reported_ns));
 printf("test_window_freezes=%u test_window_pending_discards=%u test_window_closed=%d\n",lifecycle_test_freezes,lifecycle_test_discards,lifecycle_test_closed);
 printf("original_steps_total=%llu original_work_ns=%llu original_steps_unreported=%llu original_work_unreported_ns=%llu\n",(unsigned long long)original_steps_total,(unsigned long long)original_work_ns,(unsigned long long)(original_steps_total-original_reported_steps),(unsigned long long)(original_work_ns-original_reported_work_ns));
 uint64_t cpu_end_ns=process_cpu_ns();if(cpu_end_ns==UINT64_MAX||cpu_end_ns<cpu_start_ns)result=18;else printf("host_cpu_ns=%llu\n",(unsigned long long)(cpu_end_ns-cpu_start_ns));
 printf("preparation_unreported_ns=%llu\n",(unsigned long long)(preparation_total_ns-preparation_reported_ns));
 #ifdef NF_NATIVE_ENDPOINT_RENDER
 if(!owned_gl_worker_stop())result=19;
 #endif
 preview_shutdown();close_game();nf_snapshot_release(s);nf_snapshot_destroy(s);FreeLibrary(bridge);return result;
}
#endif







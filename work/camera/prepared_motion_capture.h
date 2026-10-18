#ifndef NF_PREPARED_MOTION_CAPTURE_H
#define NF_PREPARED_MOTION_CAPTURE_H
#include "ordered_capture.h"
#include "prepared_motion_submission.h"
#include "scene_command_plan.h"
/* Producer-only cache references; returned references must be released by caller.
   Eviction never invalidates a retained queued frame. */
static struct {HMODULE bridge;uint64_t epoch,version,hits,misses,clears;unsigned cursor;NFOwnedRoadSource*slots[4];} nf_shared_road_cache;
static void nf_shared_road_cache_clear(void){for(unsigned i=0;i<4;i++){nf_owned_road_source_release(nf_shared_road_cache.slots[i]);nf_shared_road_cache.slots[i]=NULL;}nf_shared_road_cache.bridge=NULL;nf_shared_road_cache.cursor=0;nf_shared_road_cache.clears++;}
static int nf_shared_road_acquire(HMODULE bridge,uint64_t epoch,unsigned serial,NFOwnedRoadSource**out){
 uint64_t(*version_read)(void)=(void*)GetProcAddress(bridge,"nf_page_write_audit_version");if(!out||!version_read)return 0;uint64_t version=version_read();if(!version)return 0;
 if(nf_shared_road_cache.bridge!=bridge||nf_shared_road_cache.epoch!=epoch||nf_shared_road_cache.version!=version){nf_shared_road_cache_clear();nf_shared_road_cache.bridge=bridge;nf_shared_road_cache.epoch=epoch;nf_shared_road_cache.version=version;}
 for(unsigned i=0;i<4;i++){NFOwnedRoadSource*s=nf_shared_road_cache.slots[i];if(s&&nf_owned_road_source_view(s,epoch,version,serial)&&nf_owned_road_source_retain(s)){*out=s;nf_shared_road_cache.hits++;return 1;}}
 int source_profile=getenv("NF_TEST_MOTION_CAPTURE_PROFILE")!=NULL;double acquire_start=source_profile?nf_capture_mark():0;uint64_t bridge_hits_before=nf_complete_road_cache.hits;
 void*data=NULL;size_t size=0;int cached=0;NFOwnedRoadSource*s=NULL;if(!nf_complete_road_acquire(bridge,epoch,serial,&data,&size,&cached))return 0;
 double acquire_end=source_profile?nf_capture_mark():0;
 int ok=nf_owned_road_source_create(data,size,epoch,version,serial,&s);double copy_end=source_profile?nf_capture_mark():0;
 if(source_profile)printf("shared_source_miss_profile epoch=%llu serial=%u bytes=%zu bridge_retained=%d bridge_hit=%d accepted=%d acquire_ms=%.6f canonical_copy_ms=%.6f total_ms=%.6f\n",(unsigned long long)epoch,serial,size,cached,nf_complete_road_cache.hits>bridge_hits_before,ok,acquire_end-acquire_start,copy_end-acquire_end,copy_end-acquire_start);if(!cached){void(*release)(void*)=(void*)GetProcAddress(bridge,"nf_live_ordered_bundle_free");if(release)release(data);}if(!ok)return 0;
 if(version_read()!=version||!nf_owned_road_source_retain(s)){nf_owned_road_source_release(s);return 0;}unsigned slot=nf_shared_road_cache.cursor++%4;nf_owned_road_source_release(nf_shared_road_cache.slots[slot]);nf_shared_road_cache.slots[slot]=s;nf_shared_road_cache.misses++;*out=s;return 1;
}
/* Producer-only capture. Every required primary-road asset must be owned;
   zero-span roads are accepted only with an explicit successful span-plan proof. */
static int nf_prepared_motion_capture(HMODULE bridge,const NFTimelineSample*time,const NFPagePersistenceProof*proof,NFPreparedMotionSubmission**out){
 if(!time||!proof||!out||time->older>=time->newer||proof->serial!=time->older||proof->epoch!=time->epoch)return 0;
 int(*scene)(uint64_t,unsigned,unsigned,double,void**,size_t*,NFRigidPose*,unsigned,unsigned*)=(void*)GetProcAddress(bridge,"nf_live_completed_draw_scene_packet_transition");
 int(*root)(uint64_t,unsigned,unsigned,uint32_t*,void*)=(void*)GetProcAddress(bridge,"nf_live_completed_draw_root");
 int(*sample)(const uint32_t*,const uint32_t*,double,uint32_t*)=(void*)GetProcAddress(bridge,"nf_visibility_view_sample");
 int(*query_sample)(uint64_t,unsigned,unsigned,unsigned,double,uint32_t*)=(void*)GetProcAddress(bridge,"nf_live_completed_builder_query_sample");
 int(*focals)(uint64_t,unsigned,unsigned,unsigned,double,uint32_t*)=(void*)GetProcAddress(bridge,"nf_live_completed_draw_sample_focals");
 int(*commands)(uint64_t,unsigned,unsigned,const uint32_t*,unsigned,unsigned,NFNativeSceneCommand*,unsigned,unsigned*)=(void*)GetProcAddress(bridge,"nf_live_completed_draw_root_commands_focal");
 int(*road)(uint64_t,unsigned,unsigned,unsigned,const uint32_t*,unsigned,unsigned,void**,size_t*)=(void*)GetProcAddress(bridge,"nf_live_completed_draw_road_asset_view");
 void(*detail)(uint32_t*)=(void*)GetProcAddress(bridge,"nf_live_completed_draw_road_asset_view_detail");
 void(*road_free)(void*)=(void*)GetProcAddress(bridge,"nf_live_road_asset_free");void(*packet_free)(void*)=(void*)GetProcAddress(bridge,"nf_scene_packet_free");void(*bundle_free)(void*)=(void*)GetProcAddress(bridge,"nf_live_ordered_bundle_free");
 if(!scene||!root||!sample||!focals||!commands||!road||!detail||!road_free||!packet_free||!bundle_free)return 0;
 int profile=getenv("NF_TEST_MOTION_CAPTURE_PROFILE")!=NULL;double marks[7]={0},scene_end=0;if(profile)marks[0]=nf_capture_mark();
 NFOwnedRoadSource*shared_old=NULL,*shared_new=NULL;int shared=getenv("NF_TEST_SHARED_MOTION_CAPTURE")!=NULL;NFPreparedMotionSubmission*owner=NULL;void*older=NULL,*newer=NULL,*packet=NULL,*assets[144]={0};size_t older_size=0,newer_size=0,packet_size=0;int stage=1,old_cached=0,cached=0,ok=0;NFRigidPose cameras[144];unsigned count=0,n=0,roads=0;NFPreparedRoadAttachment attachments[144];uint32_t a[12],b[12],view[12],focal[2];uint8_t*h=malloc(160*sizeof(NFHudLayerRow)),*text=malloc(76832);uint64_t generation_before=0,generation_after=0;
 int(*generation)(uint64_t,unsigned,unsigned,uint64_t*)=(void*)GetProcAddress(bridge,"nf_layer_queue_page_generation");int(*hud_row)(uint64_t,unsigned,unsigned,void*,unsigned)=(void*)GetProcAddress(bridge,"nf_layer_queue_hud_row");int(*text_row)(uint64_t,unsigned,unsigned,void*,void*,unsigned)=(void*)GetProcAddress(bridge,"nf_layer_queue_text_row");
 uint8_t*state=malloc(65536);NFNativeSceneCommand*cmd=malloc(144*sizeof(*cmd));
 if(!state||!cmd||!h||!text||!generation||!hud_row||!text_row||!generation(proof->epoch,proof->display_refresh,proof->page,&generation_before)||generation_before!=proof->display_generation)goto done;
 stage=2;
 if(shared){if(!nf_shared_road_acquire(bridge,time->epoch,time->older,&shared_old)||!nf_shared_road_acquire(bridge,time->epoch,time->newer,&shared_new))goto done;older=shared_old->bytes;older_size=shared_old->size;newer=shared_new->bytes;newer_size=shared_new->size;}else if(!nf_complete_road_acquire(bridge,time->epoch,time->older,&older,&older_size,&old_cached)||!nf_complete_road_acquire(bridge,time->epoch,time->newer,&newer,&newer_size,&cached))goto done;
 stage=3;
 uint32_t text_header[8]={0x5854464e,1,(uint32_t)time->epoch,(uint32_t)(time->epoch>>32),proof->display_refresh,240,160,38400};memcpy(text,text_header,32);
 for(unsigned y=0;y<160;y++)if(!hud_row(time->epoch,proof->display_refresh,y,h+y*sizeof(NFHudLayerRow),sizeof(NFHudLayerRow))||!text_row(time->epoch,proof->display_refresh,y,text+32+y*240,text+38432+y*240,240))goto done;
 if(!generation(proof->epoch,proof->display_refresh,proof->page,&generation_after)||generation_after!=generation_before)goto done;
 if(profile)marks[1]=nf_capture_mark();
 stage=4;
 if(!scene(time->epoch,time->older,time->newer,time->alpha,&packet,&packet_size,cameras,144,&count)){if(profile){uint32_t why[8]={0};void(*read_detail)(uint32_t*)=(void*)GetProcAddress(bridge,"nf_live_completed_draw_sample_detail");if(read_detail)read_detail(why);printf("motion_scene_rejection older=%u newer=%u stage=%u pass=%u command=%u kind=%u source=%u reason=%u\n",why[0],why[1],why[2],why[3],why[4],why[5],why[6],why[7]);}goto done;}
 if(profile)scene_end=nf_capture_mark();
 /* Geometry validation and copying are deferred to the final complete owner. */
 if(profile)marks[2]=nf_capture_mark();
 stage=5;
 if(!root(time->epoch,time->older,0,a,state)||!root(time->epoch,time->newer,0,b,state)||!focals(time->epoch,time->older,time->newer,0,time->alpha,focal))goto done;
 if(getenv("NF_TEST_EXACT_QUERY_SAMPLE")){uint32_t pose[26];if(!query_sample||!query_sample(time->epoch,time->older,time->newer,0,time->alpha,pose))goto done;memcpy(view,pose+14,sizeof(view));}else if(!sample(a,b,time->alpha,view))goto done;
 unsigned serial=time->alpha==1?time->newer:time->older;
 stage=6;
 if(!commands(time->epoch,serial,0,view,focal[0],focal[1],cmd,144,&n)||n!=count)goto done;
 if(profile)marks[3]=nf_capture_mark();
 stage=7;
 for(unsigned i=0;i<n;i++)if(cmd[i].kind==1&&!cmd[i].xyz[2]){size_t bytes=0;if(!road(time->epoch,serial,0,i,view,focal[0],focal[1],assets+i,&bytes)){uint32_t reason[4];detail(reason);if(reason[0]!=6||reason[3]!=0)goto done;}else attachments[roads++]=(NFPreparedRoadAttachment){i,assets[i],bytes};}
 if(profile)marks[4]=nf_capture_mark();
 /* Roads and display now share one atomic replacement copy. */
 if(profile)marks[5]=nf_capture_mark();
 stage=8;
 uint32_t geometry_rows[144*13];const uint32_t*geometry_occurrences=NULL;
 if(getenv("NF_TEST_DISTINCT_OCCURRENCE_GEOMETRY")){if(!getenv("NF_TEST_EXACT_QUERY_SAMPLE")||n!=count||n>144)goto done;for(unsigned i=0;i<n;i++){uint32_t*r=geometry_rows+i*13;r[0]=cmd[i].kind;r[1]=cmd[i].source;r[2]=cmd[i].owner;r[3]=cmd[i].pass;r[4]=cmd[i].mask;memcpy(r+5,cmd[i].record,16);for(unsigned k=0;k<4;k++)r[9+k]=cmd[i].bounds[k];}geometry_occurrences=geometry_rows;}
 if(!nf_prepared_motion_create_complete_internal(older,older_size,newer,newer_size,packet,packet_size,cameras,count,time->alpha,attachments,roads,h,160*sizeof(NFHudLayerRow),text,76832,proof,&owner,shared?shared_old:NULL,shared?shared_new:NULL,geometry_occurrences)||!nf_prepared_motion_clock_valid(owner,time))goto done;
 if(getenv("NF_TEST_EXACT_QUERY_SAMPLE")){uint32_t rows[144*13];for(unsigned i=0;i<n;i++){uint32_t*r=rows+i*13;r[0]=cmd[i].kind;r[1]=cmd[i].source;r[2]=cmd[i].owner;r[3]=cmd[i].pass;r[4]=cmd[i].mask;memcpy(r+5,cmd[i].record,16);for(unsigned j=0;j<4;j++)r[9+j]=cmd[i].bounds[j];}if(getenv("NF_TEST_OCCURRENCE_NEGATIVE")){uint32_t saved_clip=rows[9];rows[9]^=1;if(nf_prepared_motion_attach_occurrences(owner,rows,n)||owner->occurrence_count)goto done;rows[9]=saved_clip;uint32_t saved_source=rows[1];rows[1]^=0xffffffffu;if(nf_prepared_motion_attach_occurrences(owner,rows,n)||owner->occurrence_count)goto done;rows[1]=saved_source;{uint32_t forged[13];memcpy(forged,rows,sizeof(forged));forged[2]^=0xffffffffu;forged[4]^=0xffffffffu;if(!nf_prepared_motion_occurrence_same_draw(rows,forged))goto done;forged[3]^=1;if(nf_prepared_motion_occurrence_same_draw(rows,forged))goto done;}if(n>1){uint32_t saved[13];memcpy(saved,rows+13,sizeof(saved));memcpy(rows+13,rows,sizeof(saved));if(nf_prepared_motion_attach_occurrences(owner,rows,n)||owner->occurrence_count)goto done;rows[15]^=0xffffffffu;rows[17]^=0xffffffffu;if(nf_prepared_motion_attach_occurrences(owner,rows,n)||owner->occurrence_count)goto done;memcpy(rows+13,saved,sizeof(saved));}}if(!nf_prepared_motion_attach_occurrences(owner,rows,n))goto done;if(getenv("NF_TEST_OCCURRENCE_NEGATIVE")){uint32_t saved=rows[0];rows[0]^=0xffffffffu;if(owner->occurrences[0][0]!=saved||nf_prepared_motion_attach_occurrences(owner,rows,n))goto done;if(profile)printf("motion_occurrence_negatives source=1 copied=1 forged_owner_mask=1 same_draw_key=1 overwrite=1 reattach=1 count=%u\n",n);}if(profile)printf("motion_owned_occurrences count=%u older=%u newer=%u\n",owner->occurrence_count,time->older,time->newer);}
 if(shared&&getenv("NF_TEST_SHARED_SOURCE_RETIRE_EACH_CAPTURE"))nf_shared_road_cache_clear();
 *out=owner;owner=NULL;ok=1;
 done:if(profile)printf("motion_capture_stage older=%u newer=%u target=%.12f accepted=%d stage=%d cameras=%u commands=%u roads=%u\n",time->older,time->newer,time->target,ok,stage,count,n,roads);if(profile){marks[6]=nf_capture_mark();printf("motion_capture_profile target=%.12f accepted=%d acquire=%.6f geometry_owner=%.6f scene_rebuild=%.6f initial_owner=%.6f root_commands=%.6f road_assets=%.6f reserved=%.6f complete_clone=%.6f total=%.6f\n",time->target,ok,marks[1]?marks[1]-marks[0]:0,marks[2]?marks[2]-marks[1]:0,scene_end?scene_end-marks[1]:0,marks[2]?marks[2]-scene_end:0,marks[3]?marks[3]-marks[2]:0,marks[4]?marks[4]-marks[3]:0,marks[5]?marks[5]-marks[4]:0,marks[5]?marks[6]-marks[5]:0,marks[6]-marks[0]);}
 for(unsigned i=0;i<144;i++)if(assets[i])road_free(assets[i]);if(packet)packet_free(packet);if(!shared){if(newer&&!cached)bundle_free(newer);if(older&&!old_cached)bundle_free(older);}nf_owned_road_source_release(shared_old);nf_owned_road_source_release(shared_new);free(h);free(text);nf_prepared_motion_destroy(owner);free(state);free(cmd);return ok;
}
#endif



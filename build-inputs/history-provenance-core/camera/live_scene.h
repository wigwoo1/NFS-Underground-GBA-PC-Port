#ifdef NF_VISIBILITY_CAPTURE
static void indexed_copies_scene_flip(uint32_t,uint32_t,uint32_t,int);
#endif
/* Opt-in live research stream. Included after bridge memory readers. */
#include "scene_assembly.h"
#include "live_scene_api.h"
#ifdef NF_VISIBILITY_CAPTURE
static void live_model_inputs_reset(void);
static void draw_world_palette_capture(unsigned,unsigned);
#endif
#include "model_outcome.h"
static NFModelOutcomeHistory live_model_outcomes;
static unsigned live_model_outcomes_enabled=1,live_model_outcome_no_draw_queries;
static uint64_t live_scene_epoch;
static uint32_t live_scene_rejection_detail[9],live_model_detail[8],live_model_rejection_detail[8];
/* Metadata only: diagnose scenes that reach more than one model draw. */
static uint32_t live_scene_model_visits[1+16*7],live_rejected_model_visits[1+16*7];
API void nf_native_scene_model_rejection_visits(uint32_t out[1+16*7]){if(out)memcpy(out,live_rejected_model_visits,sizeof(live_rejected_model_visits));}
API void nf_native_model_rejection_detail(uint32_t out[8]){if(out)memcpy(out,live_model_rejection_detail,sizeof(live_model_rejection_detail));}
API void nf_native_scene_rejection_detail(uint32_t out[9]){if(out)memcpy(out,live_scene_rejection_detail,sizeof(live_scene_rejection_detail));}
static struct {
 NFLiveSceneSink sink;void*sink_context;unsigned mode;
 FILE*file;NFSceneAssembly*assembly;unsigned started,begin,serial,world_state,world_descriptor;
 uint32_t published,rejected,write_failed;
 unsigned context,camera,object,state,slot;void*model;size_t model_size;uint32_t identity[5];
 struct {unsigned address,frame;int32_t matrix[12];unsigned traffic,traffic_object,traffic_camera,traffic_serial;uint64_t traffic_epoch;int32_t traffic_cm[12],traffic_actual[9],traffic_draw_cm[12];unsigned traffic_draw_frame,traffic_draw_bound;} rotations[16];
 uint32_t reciprocals[32768];
} live_scene;
#include "scene_timing.h"
/* First rejected capture event, metadata only; never repairs or omits geometry. */
static uint32_t live_scene_event_detail[9],live_scene_first_bad[9],live_scene_rejected_bad[9];
API void nf_native_scene_first_bad(uint32_t out[9]){if(out)memcpy(out,live_scene_rejected_bad,sizeof(live_scene_rejected_bad));}
static uint8_t live_scene_bad_road_ewram[262144];
API void nf_native_scene_bad_road_ewram(uint8_t out[262144]){if(out)memcpy(out,live_scene_bad_road_ewram,262144);}
static uint8_t live_scene_bad_road_code[32768];static unsigned live_scene_road_code_captured;static uint32_t live_scene_current_registers[16],live_scene_road_registers[16];
API void nf_native_scene_road_registers(uint32_t out[16]){if(out)memcpy(out,live_scene_road_registers,64);}
API void nf_native_scene_bad_road_code(uint8_t out[32768]){if(out)memcpy(out,live_scene_bad_road_code,32768);}
static uint8_t live_scene_bad_road_bytes[360];static uint32_t live_scene_bad_road_reads[4];
API void nf_native_scene_bad_road(uint8_t out[360],uint32_t reads[4]){if(out)memcpy(out,live_scene_bad_road_bytes,360);if(reads)memcpy(reads,live_scene_bad_road_reads,16);}
static void live_scene_bad(void){if(!live_scene_first_bad[0]){memcpy(live_scene_first_bad,live_scene_event_detail,sizeof(live_scene_first_bad));if(live_scene_event_detail[0]==0x030032f0){uint32_t addresses[4]={live_scene_event_detail[2],live_scene_event_detail[8],live_scene_event_detail[1],live_scene_event_detail[3]};unsigned offsets[4]={0,256,304,352},sizes[4]={256,48,48,8};memcpy(live_scene_road_registers,live_scene_current_registers,64);native_surface_read(NULL,0x03000000,live_scene_bad_road_code,32768);native_surface_read(NULL,0x02000000,live_scene_bad_road_ewram,262144);memset(live_scene_bad_road_bytes,0,360);for(unsigned i=0;i<4;i++)live_scene_bad_road_reads[i]=native_surface_read(NULL,addresses[i],live_scene_bad_road_bytes+offsets[i],sizes[i]);}}nf_assembly_model(live_scene.assembly,NULL,NULL,0);}
API int nf_native_scene_multimodel(int enabled){if(!live_scene.assembly||live_scene.started)return 0;return nf_assembly_multimodel(live_scene.assembly,enabled);}
#include "../traffic_rotation_refresh2_capture.inc"
static void native_scene_event(struct ARMCore*cpu,unsigned pc){
 if(!live_scene.assembly)return;
 if(nf_traffic_event(cpu,pc))return;
 /* Only these addresses consume registers or mutate scene assembly. */
 switch(pc){case 0x03002b74:case 0x0806db14:case 0x03001800:case 0x03002628:case 0x030045e0:case 0x03004770:case 0x030032f0:case 0x03000304:break;default:return;}
 unsigned*r=(unsigned*)cpu->gprs;
 if(live_scene_timing_enabled)live_scene_timing_event(cpu,pc);
 memcpy(live_scene_current_registers,r,64);live_scene_event_detail[0]=pc;for(unsigned i=0;i<8;i++)live_scene_event_detail[i+1]=r[i];
 if(pc==0x0806db14){
  unsigned i=0;for(;i<16;i++)if(live_scene.rotations[i].address==r[2])break;
  if(i==16)i=live_scene.slot++%16;
  if(native_surface_read(NULL,r[0],live_scene.rotations[i].matrix,48)){live_scene.rotations[i].address=r[2];live_scene.rotations[i].frame=c->frameCounter(c);live_scene.rotations[i].traffic=0;}return;
 }
 if(pc==0x03001800){live_scene.world_state=r[0];live_scene.world_descriptor=r[3];return;}
 if(pc==0x03002628){live_scene.context=r[0];live_scene.state=r[6];live_scene.camera=rd32(r[6]+84);live_scene.object=r[7];return;}
 if(pc==0x030045e0){
  nf_surface_free(live_scene.model);live_scene.model=NULL;live_scene.model_size=0;
  if(r[0]!=live_scene.context){live_scene_bad();return;}
  unsigned address=rd32(r[0]+60),frame=c->frameCounter(c);
  live_model_detail[0]=live_scene.serial;live_model_detail[1]=frame;live_model_detail[2]=address;live_model_detail[3]=UINT32_MAX;live_model_detail[4]=0;live_model_detail[5]=r[0];live_model_detail[6]=live_scene.context;live_model_detail[7]=0;
  for(unsigned i=0;i<16;i++)if(live_scene.rotations[i].address==address)live_model_detail[3]=frame-live_scene.rotations[i].frame;
  for(unsigned i=0;i<16;i++)if(live_scene.rotations[i].address==address&&live_scene.rotations[i].frame>=live_scene.begin&&live_scene.rotations[i].frame<=frame&&nf_traffic_rotation_valid(i,live_scene.camera,live_scene.object)){
#ifdef NF_VISIBILITY_CAPTURE
   live_native_model_assemble(r[0],live_scene.camera,live_scene.object,live_scene.rotations[i].matrix,&live_scene.model,&live_scene.model_size);
#else
   nf_extract_model(native_surface_read,NULL,r[0],live_scene.camera,live_scene.object,live_scene.rotations[i].matrix,&live_scene.model,&live_scene.model_size);
#endif
   live_model_detail[4]=1;live_model_detail[7]=live_scene.model!=NULL;live_scene.rotations[i].address=0;break;
  }
  uint32_t id[5]={3,live_scene.state,live_scene.object,rd32(r[0]+12),0};memcpy(live_scene.identity,id,20);return;
 }
 if(pc==0x03004770){
#ifdef NF_VISIBILITY_CAPTURE
  if(live_model_outcomes_enabled&&r[4]==live_scene.context)nf_model_outcome_record(&live_model_outcomes,live_scene_epoch,live_scene.serial,live_scene.begin,c->frameCounter(c),live_scene.identity,live_scene.identity[2]==live_scene.object?r[0]:UINT32_MAX);
#endif
  if(r[0]==1){unsigned n=live_scene_model_visits[0]++;if(n<16){uint32_t visit[7]={c->frameCounter(c),r[4],live_scene.object,live_scene.state,live_scene.identity[3],live_scene.model!=NULL,r[4]==live_scene.context};memcpy(live_scene_model_visits+1+n*7,visit,sizeof(visit));}}
  if(r[0]==1){if(r[4]!=live_scene.context||!live_scene.model)live_scene_bad();else nf_assembly_model(live_scene.assembly,live_scene.identity,live_scene.model,live_scene.model_size);}
  nf_surface_free(live_scene.model);live_scene.model=NULL;live_scene.model_size=0;return;
 }
#ifdef NF_VISIBILITY_CAPTURE
 if(pc==0x030032f0||pc==0x03000304)draw_world_palette_capture(pc==0x030032f0?1:2,pc==0x030032f0?r[7]:r[6]);
#endif
 if(pc==0x030032f0){if(!live_scene_road_code_captured){memcpy(live_scene_road_registers,live_scene_current_registers,64);native_surface_read(NULL,0x03000000,live_scene_bad_road_code,32768);live_scene_road_code_captured=1;}
  unsigned layer=rd32(r[13]+4);void*surface=NULL;size_t size=0;uint32_t light=0,id[5]={1,r[1],r[7],layer?4u:8u,0};
  if(layer>1||(layer? r[14]!=0x03002abc:r[14]!=0x03002a10)||!nf_extract_road_layer(native_surface_read,NULL,r[1],r[7],r[0],r[2],layer,&surface,&size))live_scene_bad();
  else nf_assembly_surface(live_scene.assembly,id,surface,size,&light,4);
  nf_pc_history_surface_note(id,surface,size);nf_surface_free(surface);return;
 }
 if(pc==0x03000304){
  void*surface=NULL,*light=NULL;size_t size=0,light_size=0;uint32_t id[5]={2,r[1],r[6],rd16(r[6]+44),0};
  if(r[1]!=live_scene.world_state||!live_scene.world_descriptor||!nf_extract_wall(native_surface_read,NULL,r[1],live_scene.world_descriptor,r[6],r[0],r[3],r[2],&surface,&size,&light,&light_size))live_scene_bad();
  else nf_assembly_surface(live_scene.assembly,id,surface,size,light,light_size);
  nf_pc_history_surface_note(id,surface,size);nf_surface_free(surface);nf_surface_free(light);
 }
}
static void native_scene_flip(unsigned value){
 if(!live_scene.assembly)return;
 unsigned frame=c->frameCounter(c);
#ifdef NF_VISIBILITY_CAPTURE
 indexed_copies_scene_flip(live_scene.serial,live_scene.begin,frame,live_scene.started);
#endif
 if(live_scene.started){
  if(live_scene_timing_enabled)live_scene_timing_flip(frame);
  void*packet=NULL;size_t size=0;
  if(nf_assembly_finish(live_scene.assembly,live_scene.serial,live_scene.begin,frame,(value&16)?1:0,live_scene.reciprocals,sizeof(live_scene.reciprocals),&packet,&size)){
#ifdef NF_VISIBILITY_CAPTURE
   live_visibility_packet(packet,size);
#endif
   int ok=live_scene.sink?live_scene.sink(live_scene.sink_context,live_scene_epoch,packet,size):(fwrite(packet,1,size,live_scene.file)==size);
   if(ok)live_scene.published++;else live_scene.write_failed++;
   nf_scene_packet_free(packet);
  }else {memcpy(live_scene_rejected_bad,live_scene_first_bad,sizeof(live_scene_rejected_bad));memcpy(live_rejected_model_visits,live_scene_model_visits,sizeof(live_scene_model_visits));memcpy(live_model_rejection_detail,live_model_detail,sizeof(live_model_detail));live_scene.rejected++;live_scene_rejection_detail[0]=live_scene.serial;live_scene_rejection_detail[1]=live_scene.begin;live_scene_rejection_detail[2]=frame;live_scene_rejection_detail[3]=(value&16)?1:0;nf_assembly_detail(live_scene.assembly,live_scene_rejection_detail+4);}
  live_scene.serial++;
 }
 memset(live_scene_first_bad,0,sizeof(live_scene_first_bad));memset(live_scene_model_visits,0,sizeof(live_scene_model_visits));nf_assembly_reset(live_scene.assembly);nf_surface_free(live_scene.model);live_scene.model=NULL;live_scene.model_size=0;
#ifdef NF_VISIBILITY_CAPTURE
 live_model_inputs_reset();
#endif
 live_scene_timing_interval_reset();
 live_scene.started=1;live_scene.begin=frame;
}
API void nf_native_scene_stats(uint32_t out[4]){
 if(out){out[0]=live_scene.serial;out[1]=live_scene.published;out[2]=live_scene.rejected;out[3]=live_scene.write_failed;}
}
/* Synchronous borrowed packets: a sink must copy/retain before returning and
   must not reenter the emulator. Epoch changes invalidate previous presentation. */
API uint64_t nf_native_scene_epoch(void){return live_scene_epoch;}
API uint32_t nf_native_scene_refresh(void){return c?c->frameCounter(c):0;}
API void nf_native_scene_discontinuity(void){
 live_scene_timing_reset();
#ifdef NF_VISIBILITY_CAPTURE
 live_visibility_reset();live_owned_model_invalidate();
#endif
 if(!live_scene.assembly)return;
 memset(live_scene_first_bad,0,sizeof(live_scene_first_bad));memset(live_scene_rejected_bad,0,sizeof(live_scene_rejected_bad));live_scene_road_code_captured=0;memset(live_scene_road_registers,0,sizeof(live_scene_road_registers));memset(live_scene_bad_road_code,0,32768);nf_traffic_reset();live_scene_epoch++;nf_assembly_reset(live_scene.assembly);
 memset(live_scene_model_visits,0,sizeof(live_scene_model_visits));memset(live_rejected_model_visits,0,sizeof(live_rejected_model_visits));
 nf_surface_free(live_scene.model);live_scene.model=NULL;live_scene.model_size=0;
 live_scene.started=live_scene.begin=live_scene.serial=0;
 live_scene.world_state=live_scene.world_descriptor=0;
 live_scene.context=live_scene.camera=live_scene.object=live_scene.state=live_scene.slot=0;
 memset(live_scene.rotations,0,sizeof(live_scene.rotations));
 live_scene.mode=rd32(0x03005f14);
}
static void native_scene_check_mode(void){
 if(live_scene.assembly&&live_scene.mode!=rd32(0x03005f14))nf_native_scene_discontinuity();
}
API int nf_native_scenes(const char*path){
 live_scene_timing_enabled=0;live_scene_timing_reset();
#ifdef NF_VISIBILITY_CAPTURE
 live_visibility_reset();live_owned_model_invalidate();
#endif
 nf_traffic_reset();live_scene_epoch++;
 native_scene_thumb=NULL;
 if(live_scene.file)fclose(live_scene.file);
 nf_assembly_destroy(live_scene.assembly);nf_surface_free(live_scene.model);memset(&live_scene,0,sizeof(live_scene));
 if(path&&c){
  live_scene.assembly=nf_assembly_create();
  if(live_scene.assembly&&native_surface_read(NULL,0x08627700,live_scene.reciprocals,sizeof(live_scene.reciprocals)))live_scene.file=fopen(path,"wb");
  if(!live_scene.file){nf_assembly_destroy(live_scene.assembly);live_scene.assembly=NULL;}
 }
 native_scene_thumb=live_scene.file?native_scene_event:NULL;
 nfsThumbTrace=(native_scene_thumb||native_model_thumb||world_thumb||calls_file||timing_file||dt_percent!=100||normalize_steering)?thumbTrace:NULL;
 if(live_scene.file){nf_native_scene_discontinuity();nf_scene_enable(1);}
 return live_scene.file!=NULL;
}

API int nf_native_scene_sink(NFLiveSceneSink sink,void*context){
 nf_native_scenes(NULL);
 if(!sink||!c)return 0;
 live_scene.assembly=nf_assembly_create();
 if(!live_scene.assembly)return 0;
 if(!native_surface_read(NULL,0x08627700,live_scene.reciprocals,sizeof(live_scene.reciprocals))){nf_assembly_destroy(live_scene.assembly);live_scene.assembly=NULL;return 0;}
 live_scene.sink=sink;live_scene.sink_context=context;native_scene_thumb=native_scene_event;
 nfsThumbTrace=thumbTrace;nf_native_scene_discontinuity();nf_scene_enable(1);return 1;
}

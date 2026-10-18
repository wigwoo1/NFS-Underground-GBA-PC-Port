#ifdef _WIN32
#define NF_TEXT_HOST_EXPORT __declspec(dllexport)
#else
#define NF_TEXT_HOST_EXPORT
#endif
/* Optional staged extension; legacy observer/JNI unchanged. */
static unsigned android_text_enabled,android_text_begin;
static uint64_t android_text_epoch;
int nf_android_observer_text_enable(int enabled){if(!c||(enabled&&!android_layers))return 0;if(enabled&&c->frameCounter(c)==~0u)return 0;if(!nf_bitmap_text_enable(enabled!=0))return 0;android_text_enabled=enabled!=0;android_text_epoch=nf_native_scene_epoch();android_text_begin=c->frameCounter(c)+1;return 1;}
size_t nf_android_observer_text(uint64_t epoch,unsigned refresh,void*out,size_t capacity){
 if(!c||!android_layers||!android_text_enabled||!bitmap_live_layer||epoch!=android_text_epoch||epoch!=nf_native_scene_epoch()||refresh<android_text_begin||!nf_android_observer_bundle(epoch,refresh,NULL,0))return 0;
 const size_t bytes=64+76800;if(out&&capacity<bytes)return 0;uint8_t*copy=malloc(bytes);if(!copy)return 0;uint64_t header[8]={0x3154464e,1,bytes,epoch,refresh,240,160,1};memcpy(copy,header,64);int ok=1;
 for(unsigned y=0;y<160;y++){if(!nf_layer_queue_text_row(epoch,refresh,y,copy+64+y*240,copy+64+38400+y*240,240)){ok=0;break;}for(unsigned x=0;x<240;x++)if(copy[64+38400+y*240+x]>1){ok=0;break;}if(!ok)break;}
 if(ok&&epoch==nf_native_scene_epoch()){if(out)memcpy(out,copy,bytes);}else ok=0;free(copy);return ok?bytes:0;
}
/* Read-only host diagnostic; no ownership decisions altered. */
NF_TEXT_HOST_EXPORT int nf_owned_text_diagnostic(uint64_t epoch,unsigned refresh,uint64_t out[12]){
 if(!out)return 0;memset(out,0,12*sizeof(*out));out[0]=android_text_enabled;out[1]=android_text_epoch;out[2]=android_text_begin;out[3]=bitmap_live_layer!=NULL;out[4]=nf_native_scene_epoch();out[5]=nf_android_observer_bundle(epoch,refresh,NULL,0)!=0;out[11]=getenv("NF_TEST_RACING_OWNED_CAPTURE")!=NULL;
 for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==epoch&&layer_queue[i].refresh==refresh){out[6]=1;out[7]=layer_queue[i].text_valid;out[8]=layer_queue[i].kind;out[9]=layer_queue[i].mode;out[10]=layer_queue[i].frontend;break;}return 1;
}

NF_TEXT_HOST_EXPORT unsigned nf_owned_text_glyph_count(void){return bitmap_glyph_count;}
NF_TEXT_HOST_EXPORT int nf_owned_text_trace(const char*path){char calls_path[1500];if(path){snprintf(calls_path,sizeof(calls_path),"%s.calls.csv",path);nf_calls(calls_path);}else nf_calls(NULL);return nf_bitmap_blit_trace(path);}


/* Separate verified 2D context; never substitutes a 3D bundle owner. */
size_t nf_android_observer_menu_text(uint64_t epoch,unsigned refresh,void*out,size_t capacity){
 if(!c||!android_layers||!android_text_enabled||!bitmap_live_layer||epoch!=android_text_epoch||epoch!=nf_native_scene_epoch()||refresh<android_text_begin)return 0;
 const size_t bytes=80+76800;if(out&&capacity<bytes)return 0;
 for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==epoch&&layer_queue[i].refresh==refresh&&layer_queue[i].text_valid&&layer_queue[i].kind==2&&layer_queue[i].mode==1){
  for(unsigned x=0;x<38400;x++)if(layer_queue[i].text_coverage[x]>1)return 0;
  if(out){uint64_t header[10]={0x31544d4e,1,bytes,epoch,refresh,240,160,layer_queue[i].mode,layer_queue[i].frontend,2};memcpy(out,header,80);memcpy((uint8_t*)out+80,layer_queue[i].text,38400);memcpy((uint8_t*)out+38480,layer_queue[i].text_coverage,38400);}return bytes;
 }return 0;
}
size_t nf_android_observer_menu_text_bundle(uint64_t epoch,unsigned refresh,void*out,size_t capacity){
 const size_t textbytes=76880,palettebytes=81960,bytes=64+76880+81960;
 if(!nf_android_observer_menu_text(epoch,refresh,NULL,0)||(out&&capacity<bytes))return 0;
 uint8_t*copy=malloc(bytes);if(!copy)return 0;int ok=0;
 if(nf_android_observer_menu_text(epoch,refresh,copy+64,textbytes)!=textbytes)goto done;
 for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==epoch&&layer_queue[i].refresh==refresh){
  uint64_t palette[5]={0x31504d4e,1,palettebytes,epoch,refresh};memcpy(copy+64+textbytes,palette,40);
  if(!nf_layer_snapshot_bg_palettes(layer_queue[i].snapshot,refresh,(uint16_t(*)[256])(copy+64+textbytes+40)))goto done;
  ok=epoch==nf_native_scene_epoch();break;
 }
 if(ok){uint64_t header[8]={0x31424d4e,1,bytes,epoch,refresh,textbytes,palettebytes,0};memcpy(copy,header,64);if(out)memcpy(out,copy,bytes);}
 done:free(copy);return ok?bytes:0;
}
/* Host-only diagnostic of the existing source-owned classified packet path. */
NF_TEXT_HOST_EXPORT int nf_owned_source_world_enable(const void*rom,size_t bytes){if(!c||!rom||bytes<0x637700)return 0;int ok=nf_live_visibility_enable(rom,bytes,64*1024*1024);if(ok)nf_live_surface_audit_enable(1);return ok;}
NF_TEXT_HOST_EXPORT void nf_owned_source_world_disable(void){nf_live_surface_audit_enable(0);live_visibility_close();}
NF_TEXT_HOST_EXPORT size_t nf_owned_source_world_packet(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void*out,size_t capacity,unsigned*stage){void*packet=NULL;size_t bytes=0;if(!c||!nf_live_completed_native_multimodel_world_classified_owned(epoch,serial,begin,end,&packet,&bytes,stage))return 0;if(out&&capacity<bytes){nf_scene_packet_free(packet);return 0;}if(out)memcpy(out,packet,bytes);nf_scene_packet_free(packet);return bytes;}
NF_TEXT_HOST_EXPORT int nf_owned_source_world_state(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,uint64_t out[24]){
 if(!c||!out)return 0;memset(out,0,24*sizeof(*out));unsigned count=0;out[0]=nf_live_completed_models_count(epoch,serial,begin,end,&count);out[1]=count;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){NFCompletedSurfaceAudit*e=completed_surface_audit[i];if(e&&e->id.epoch==epoch&&e->id.serial==serial&&e->id.begin_refresh==begin&&e->id.end_refresh==end){out[2]=1;out[3]=e->render_snapshot!=NULL;uint32_t view[12];out[4]=nf_visibility_snapshot_prepared_view(e->render_snapshot,view);}}
 NFVisibilityPoseInputs pose;out[5]=nf_live_completed_visibility_pose(epoch,serial,begin,end,&pose);for(unsigned i=0;i<4;i++)out[6+i]=live_visibility.stats[i];out[10]=live_visibility.stage;out[11]=live_palettes.count;out[12]=pending_model_inputs.count;out[13]=pending_model_inputs.failed;out[14]=completed_model_inputs[serial%NF_COMPLETED_SURFACE_HISTORY].valid;out[15]=getenv("NF_CAPTURE_MODEL_VIEWS")!=NULL;uint32_t detail[6];out[22]=nf_live_model_publish_detail(serial,detail);if(out[22])for(unsigned i=0;i<6;i++)out[16+i]=detail[i];out[23]=live_visibility.history!=NULL;return 1;
}
/* Host diagnostic of existing original initial-page replay; no raster VRAM sampling. */
static uint64_t android_background_diagnostic_epoch;
NF_TEXT_HOST_EXPORT int nf_owned_background_enable(const void*table,unsigned bytes){if(!c||!nf_native_background_capture_only(1)||!nf_native_model_plan_trace("",table,bytes)||!nf_world_trace(""))return 0;android_background_diagnostic_epoch=nf_native_scene_epoch();return 1;}
NF_TEXT_HOST_EXPORT void nf_owned_background_disable(void){nf_world_trace(NULL);nf_native_model_plan_trace(NULL,NULL,0);nf_native_background_capture_only(0);android_background_diagnostic_epoch=0;}
NF_TEXT_HOST_EXPORT size_t nf_owned_background_read(uint64_t epoch,unsigned refresh,unsigned page,void*out,size_t capacity){if(!c||!epoch||epoch!=android_background_diagnostic_epoch||epoch!=nf_native_scene_epoch()||page>1)return 0;unsigned slot=refresh%16;if(!native_background_frames[slot].valid||native_background_frames[slot].refresh!=refresh)return 0;if(!out)return 76800;if(capacity<76800)return 0;uint8_t copy[76800];unsigned base=page*0xa000;for(unsigned i=0;i<38400;i++){copy[i]=native_background_frames[slot].vram[base+i];copy[38400+i]=native_background_frames[slot].coverage[base+i];}memcpy(out,copy,sizeof(copy));return sizeof(copy);}
/* Host-only original road capture, retaining exact scene identity and root order. */
static int android_road_owner(uint64_t epoch,unsigned serial,unsigned begin,unsigned end){if(!c||epoch!=nf_native_scene_epoch())return 0;for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){NFCompletedSurfaceAudit*e=completed_surface_audit[i];if(e&&e->id.epoch==epoch&&e->id.serial==serial&&e->id.begin_refresh==begin&&e->id.end_refresh==end)return 1;}return 0;}
NF_TEXT_HOST_EXPORT unsigned nf_owned_road_commands(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,unsigned pass,uint32_t*out,unsigned capacity){if(!android_road_owner(epoch,serial,begin,end)||pass>=4)return 0;NFNativeSceneCommand*cmd=malloc(144*sizeof(*cmd));unsigned n=0;if(!cmd)return 0;int ok=nf_live_completed_draw_root_commands(epoch,serial,pass,cmd,144,&n);if(!ok||!out||capacity<n){free(cmd);return 0;}for(unsigned i=0;i<n;i++){out[i*3]=i;out[i*3+1]=cmd[i].kind;out[i*3+2]=cmd[i].xyz[2];}free(cmd);return n;}
NF_TEXT_HOST_EXPORT size_t nf_owned_road_asset(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,unsigned pass,unsigned ordinal,void*out,size_t capacity){if(!android_road_owner(epoch,serial,begin,end))return 0;void*asset=NULL;size_t bytes=0;if(!nf_live_completed_draw_road_asset(epoch,serial,pass,ordinal,&asset,&bytes))return 0;if(out&&capacity<bytes){nf_live_road_asset_free(asset);return 0;}if(out)memcpy(out,asset,bytes);nf_live_road_asset_free(asset);return bytes;}
NF_TEXT_HOST_EXPORT unsigned nf_owned_road_command_identity(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,unsigned pass,uint32_t*out,unsigned capacity){if(!android_road_owner(epoch,serial,begin,end)||pass>=4)return 0;NFNativeSceneCommand*cmd=malloc(144*sizeof(*cmd));unsigned n=0;if(!cmd)return 0;int ok=nf_live_completed_draw_root_commands(epoch,serial,pass,cmd,144,&n);if(!ok||!out||capacity<n){free(cmd);return 0;}for(unsigned i=0;i<n;i++){NFNativeSceneCommand*d=cmd+i;uint32_t id[5]={d->kind==5?3:d->kind,completed_draw_views[serial%16].states[pass],d->source,0,0};if(d->kind==5)memcpy(id+3,d->model+12,4);else if(d->kind==1)id[3]=d->xyz[2]?4:8;else if(d->kind==2){uint32_t base;memcpy(&base,d->state+32,4);id[3]=(d->material[0]-base)/32;}memcpy(out+i*5,id,20);}free(cmd);return n;}
/* Read-only stage evidence for unavailable primary road assets. */
NF_TEXT_HOST_EXPORT int nf_owned_road_asset_diagnostic(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,unsigned pass,unsigned ordinal,uint32_t out[16]){
 if(!out)return 0;memset(out,0,64);if(!android_road_owner(epoch,serial,begin,end)||pass>=4)return 0;
 NFNativeSceneCommand*commands=malloc(144*sizeof(*commands));if(!commands)return 0;unsigned n=0,amount=0;uint32_t address,framebuffer[4],seed[16],spans[512*20];uint16_t inherited[4];uint8_t descriptor[48];out[0]=1;
 if(!nf_live_completed_draw_root_commands(epoch,serial,pass,commands,144,&n)||ordinal>=n)goto done;
 NFNativeSceneCommand*cmd=commands+ordinal;out[1]=cmd->kind;out[2]=cmd->xyz[2];out[3]=cmd->vertex_count;out[0]=2;if(cmd->kind!=1||cmd->xyz[2])goto done;
 NFVisibilitySnapshot*root=completed_draw_views[serial%16].roots[pass];memcpy(&address,cmd->state+80,4);memcpy(inherited,cmd->record+2,8);for(unsigned i=0;i<4;i++)out[8+i]=inherited[i];
 if(!owned_span_read(root,address,framebuffer,16))goto done;out[0]=3;if(!owned_span_read(root,cmd->source,descriptor,48))goto done;out[0]=4;
 if(!nf_road_material_seed(cmd->state,descriptor,owned_span_read,root,seed))goto done;out[0]=5;
 out[4]=nf_road_span_contexts(cmd->vertices,cmd->vertex_count,inherited[2],inherited[3],cmd->xyz[0],cmd->xyz[1],live_visibility.reciprocal,framebuffer,seed,spans,512,&amount);out[5]=amount;if(!out[4])goto done;out[0]=6;
 void*asset=NULL;size_t bytes=0;out[6]=completed_road_asset_from_contexts(serial,pass,ordinal,spans,amount,&asset,&bytes);out[7]=(uint32_t)bytes;if(out[6])out[0]=7;free(asset);
 done:free(commands);return 1;
}
/* Full original indexed fill/copy diagnostic; keeps sky metadata in same journal. */
NF_TEXT_HOST_EXPORT int nf_owned_all_2d_enable(void){if(!c||!live_scene.assembly)return 0;indexed_sky_only_capture=0;indexed_copy_capture_enabled=1;return 1;}
NF_TEXT_HOST_EXPORT size_t nf_owned_2d_operation(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,unsigned ordinal,void*out,size_t capacity,uint64_t meta[8]){
 if(!meta)return 0;memset(meta,0,64);if(!android_road_owner(epoch,serial,begin,end))return 0;unsigned slot=serial%16;if(completed_indexed_copies[slot].epoch!=epoch||completed_indexed_copies[slot].serial!=serial||completed_indexed_copies[slot].begin!=begin||completed_indexed_copies[slot].end!=end)return 0;
 meta[0]=completed_indexed_copies[slot].count;meta[1]=completed_indexed_copies[slot].failed;if(meta[1]||ordinal>=meta[0])return 0;NFOwnedCopyEvent*event=completed_indexed_copies[slot].events+ordinal;meta[2]=event->kind;meta[3]=event->refresh;meta[4]=event->caller;meta[5]=event->cycles;meta[6]=event->size;if(out&&capacity<event->size)return 0;if(out)memcpy(out,event->asset,event->size);return event->size;
}
/* Complete original source-command replay oracle; diagnostic only. */
NF_TEXT_HOST_EXPORT int nf_owned_full_replay_enable(void){if(!c||!native_plan_enabled||!android_background_diagnostic_epoch)return 0;native_background_capture_only=0;return 1;}
NF_TEXT_HOST_EXPORT size_t nf_owned_full_replay_read(uint64_t epoch,unsigned refresh,unsigned page,void*out,size_t capacity){if(!c||(native_original_wall_spans&&native_original_wall_failed)||epoch!=nf_native_scene_epoch()||epoch!=android_background_diagnostic_epoch||page>1)return 0;unsigned slot=refresh%16;if(!native_live_frames[slot].valid||native_live_frames[slot].refresh!=refresh)return 0;if(!out)return 38400;if(capacity<38400)return 0;memcpy(out,native_live_frames[slot].vram+page*0xa000,38400);return 38400;}
/* Compact original dispatch evidence for one exact object-pool slot. */
NF_TEXT_HOST_EXPORT int nf_owned_object_dispatch_detail(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,unsigned source,uint32_t out[64]){
 if(!out||!android_road_owner(epoch,serial,begin,end))return 0;memset(out,0,256);NFCompletedSurfaceAudit*entry=NULL;for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){NFCompletedSurfaceAudit*e=completed_surface_audit[i];if(e&&e->id.epoch==epoch&&e->id.serial==serial&&e->id.begin_refresh==begin&&e->id.end_refresh==end)entry=e;}if(!entry)return 0;
 unsigned slot=serial%NF_COMPLETED_SURFACE_HISTORY;if(!completed_model_inputs[slot].valid||!completed_model_inputs[slot].count)return 0;uint8_t state[256],object[164];uint32_t address=completed_model_inputs[slot].models[0].identity[1];if(!nf_visibility_snapshot_read(entry->render_snapshot,address,state,256))return 0;memcpy(out,state+60,4);if(source<out[0]||(source-out[0])%164)return 0;out[1]=(source-out[0])/164;out[2]=entry->visits[0];out[4]=entry->callback_count;out[5]=entry->callback_failed;out[6]=entry->object_count;out[7]=entry->object_failed;out[8]=completed_model_inputs[slot].count;
 for(unsigned i=0;i<entry->visits[0];i++)if(entry->visits[3+i*3]==out[1]){unsigned n=out[3]++;if(n<8){out[16+n*2]=entry->visits[1+i*3];out[17+n*2]=entry->visits[2+i*3];}}
 for(unsigned i=0;i<entry->object_count;i++)if(entry->objects[i].address==source)out[9]++;
 for(unsigned i=0;i<entry->callback_count;i++)if(entry->callbacks[i].index==out[1]){out[10]++;out[11]=entry->callbacks[i].selector;out[12]=entry->callbacks[i].function;out[13]=entry->callbacks[i].count;}
 out[14]=nf_visibility_snapshot_read(entry->render_snapshot,source,object,164);if(out[14])memcpy(out+32,object,128);return 1;
}

NF_TEXT_HOST_EXPORT int nf_owned_exact_wall_spans(int enabled){return nf_native_original_wall_spans(enabled);}
NF_TEXT_HOST_EXPORT void nf_owned_exact_wall_stats(uint32_t out[4]){nf_native_original_wall_span_stats(out);}

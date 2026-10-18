/* Freeze the FIRST bad event in each scene, before later models overwrite
 * ordinary diagnostics. Source-owned metadata only; never repairs a scene. */
static uint32_t nf_first_model_failure[256]={0x31424d4e,1,256};
void nf_first_model_failure_reset(void){memset(nf_first_model_failure,0,sizeof(nf_first_model_failure));nf_first_model_failure[0]=0x31424d4e;nf_first_model_failure[1]=1;nf_first_model_failure[2]=256;}
void nf_first_model_failure_capture(void){
 uint32_t w[256]={0x31424d4e,1,256};uint64_t epoch=nf_native_scene_epoch();
 w[3]=(uint32_t)epoch;w[4]=(uint32_t)(epoch>>32);w[5]=live_scene.serial;w[6]=c->frameCounter(c);w[7]=live_scene.begin;
 memcpy(w+8,live_scene_event_detail,36);
 memcpy(w+20,live_model_detail,32);
 w[28]=live_scene.context;w[29]=live_scene.camera;w[30]=live_scene.object;w[31]=live_scene.state;
 if(live_scene_event_detail[0]==0x03004770){
  w[32]=live_object_model_context.address;w[33]=live_object_model_context.object;w[34]=live_object_model_context.frame;w[35]=live_object_model_context.serial;
  w[36]=(uint32_t)live_object_model_context.epoch;w[37]=(uint32_t)(live_object_model_context.epoch>>32);w[38]=live_object_model_context.verified;w[39]=live_object_model_context.expected;
  memcpy(w+40,live_object_model_context.context,68);
  w[57]=live_owned_model.ready;w[58]=(uint32_t)live_owned_model.epoch;w[59]=(uint32_t)(live_owned_model.epoch>>32);w[60]=live_owned_model.count;w[61]=live_owned_model.used;
  memcpy(w+62,live_owned_model.args,12);w[65]=(uint32_t)live_owned_model.size;memcpy(w+66,live_owned_model.stats,16);memcpy(w+70,live_owned_model.rotation,48);
  for(unsigned i=0;i<16;i++){w[84+i*2]=live_scene.rotations[i].address;w[85+i*2]=live_scene.rotations[i].frame;}
  nf_live_native_context_extract_stats(w+116);nf_live_native_model_assembly_stats(w+120);nf_live_owned_model_assembly_stats(w+123);nf_live_native_context_guard_stats(w+125);
  memcpy(w+128,nf_context_rejection_detail,64);memcpy(w+144,nf_context_refresh_stats,16);
  w[165]=native_surface_read(NULL,live_scene.context,w+148,68);w[166]=w[165]&&!memcmp(w+148,live_object_model_context.context,68);
 }
 memcpy(nf_first_model_failure,w,sizeof(w));
}
int nf_android_first_model_failure_info(uint32_t*out,size_t words){if(!c||!out||words<256)return 0;memcpy(out,nf_first_model_failure,sizeof(nf_first_model_failure));return 1;}

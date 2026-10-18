/* Source-context handoff across ONE refresh within the same owned scene.
 * This never weakens live_native_context_matches: assembly still consumes an
 * exact current-frame token. Commit only after full model byte parity and a
 * fresh full-context comparison, with epoch/serial/object/address unchanged. */
static uint32_t nf_context_rejection_detail[16],nf_context_refresh_stats[4];
static void nf_context_rejection_capture(unsigned context,unsigned object,uint64_t epoch,unsigned serial,unsigned frame){
 uint8_t actual[68];uint32_t d[16]={context,object,(uint32_t)epoch,(uint32_t)(epoch>>32),serial,frame,
 live_object_model_context.address,live_object_model_context.object,(uint32_t)live_object_model_context.epoch,(uint32_t)(live_object_model_context.epoch>>32),live_object_model_context.serial,live_object_model_context.frame,live_object_model_context.verified,0,live_object_model_context.expected,live_scene.begin};
 d[13]=native_surface_read(NULL,context,actual,68)&&!memcmp(actual,live_object_model_context.context,68);
 memcpy(nf_context_rejection_detail,d,sizeof(d));
}
static int nf_context_refresh_commit(unsigned context,unsigned object,uint64_t epoch,unsigned serial,unsigned frame){
 if(live_object_model_context.frame==frame){nf_context_refresh_stats[3]++;return 1;}
 nf_context_refresh_stats[0]++;
 uint8_t actual[68];
 if(!live_object_model_context.verified||!live_object_model_context.expected||
    live_object_model_context.address!=context||live_object_model_context.object!=object||
    live_object_model_context.epoch!=epoch||live_object_model_context.serial!=serial||
    live_object_model_context.frame<live_scene.begin||live_object_model_context.frame==UINT32_MAX||live_object_model_context.frame+1!=frame||
    !native_surface_read(NULL,context,actual,68)||memcmp(actual,live_object_model_context.context,68)){
  nf_context_refresh_stats[2]++;return 0;
 }
 live_object_model_context.frame=frame;nf_context_refresh_stats[1]++;return 1;
}

from pathlib import Path
p=Path('work/camera/prepared_motion_submission.h');s=p.read_text();needle='\n#endif';fn='''
/* Explicit full-row export for diagnostic files; failure never publishes partial rows. */
static int nf_prepared_motion_export_hud(const NFPreparedMotionSubmission*s,uint64_t epoch,void*out,size_t bytes){
 NFHudSubmissionView view;if(!s||!out||bytes!=160*sizeof(NFHudLayerRow)||!nf_prepared_motion_display_view(s,&view)||view.epoch!=epoch)return 0;
 if(s->hud_pool)return nf_hud_pool_expand(s->hud_pool,s->hud_pool->bytes,epoch,out,bytes);
 if(!s->hud||s->hud_size!=bytes)return 0;memcpy(out,s->hud,bytes);return 1;
}
''';assert needle in s;s=s.replace(needle,fn+needle,1);p.write_text(s)
p=Path('work/camera/threaded_preview.c');s=p.read_text();a=s.index('  if(motion&&!r->result&&image_checks&&r->motion_verified<6){');b=s.index('\n  if((stable||ordered)',a);replacement='''  if(motion&&!r->result&&image_checks&&r->motion_verified<6){
   glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,a);int binding=preview_force_context_rebind;preview_force_context_rebind=1;
   NFPreparedMotionSubmission reference=*motion;void*full_hud=NULL;int paired=getenv("NF_VERIFY_OWNED_HUD_POOL")!=NULL;
   if(paired){
    size_t bytes=160*sizeof(NFHudLayerRow);full_hud=malloc(bytes);if(!full_hud||!motion->hud_pool||!nf_prepared_motion_export_hud(motion,time->epoch,full_hud,bytes))r->result=19;
    if(!r->result){NFHudRowPool*bad=malloc(motion->hud_pool->bytes);if(!bad)r->result=19;else{
     size_t extent=motion->hud_pool->bytes;memcpy(bad,motion->hud_pool,extent);NFPreparedMotionSubmission forged=*motion;forged.hud_pool=bad;NFHudSubmissionView rejected={0};bad->epoch++;if(nf_prepared_motion_display_view(&forged,&rejected))r->result=19;
     memcpy(bad,motion->hud_pool,extent);bad->payload[0]^=1;if(nf_prepared_motion_display_view(&forged,&rejected))r->result=19;free(bad);
    }}
    if(!r->result){reference.hud_pool=NULL;reference.hud=full_hud;}
   }
   if(!r->result)r->result=render_prepared_motion_hud_diagnostic(paired?&reference:motion,r->args);
   preview_force_context_rebind=binding;glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,b);
   if(glGetError()!=GL_NO_ERROR||memcmp(a,b,n))r->result=19;else if(!r->result){r->verified++;r->motion_verified++;if(paired)printf("owned_hud_pool_pixels_exact=8294400 pool_epoch_negative=1 pool_payload_negative=1\\n");}free(full_hud);
  }''';s=s[:a]+replacement+s[b:];p.write_text(s)
p=Path('work/camera/audit_threaded_racing_motion.py');s=p.read_text().replace("for flag in ['NF_TEST_OWNED_HUD_POOL'","for flag in ['NF_VERIFY_OWNED_HUD_POOL','NF_TEST_OWNED_HUD_POOL'");needle='rate=16777216/(280896*60)';s=s.replace(needle,"if os.environ.get('NF_VERIFY_OWNED_HUD_POOL')=='1':\n assert os.environ.get('NF_TEST_OWNED_HUD_POOL')=='1' and readback\n assert r.stdout.count('owned_hud_pool_pixels_exact=8294400 pool_epoch_negative=1 pool_payload_negative=1')==6\n"+needle,1);p.write_text(s)

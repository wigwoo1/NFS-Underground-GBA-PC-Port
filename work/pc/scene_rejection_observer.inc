/* Read-only diagnostic snapshot of already recorded rejection evidence.
 * Owner-thread only, no emulated memory reads or allocation/publication. */
int nf_android_scene_rejection_info(uint32_t*out,size_t words){
 if(!c||!out||words<192)return 0;
 uint32_t w[192]={0x314a524e,1,192,0};uint64_t epoch=nf_native_scene_epoch();
 w[4]=(uint32_t)epoch;w[5]=(uint32_t)(epoch>>32);
 nf_native_scene_stats(w+6);nf_native_scene_rejection_detail(w+16);
 nf_native_scene_first_bad(w+32);nf_native_model_rejection_detail(w+48);
 nf_native_scene_model_rejection_visits(w+64);
 nf_live_native_model_assembly_stats(w+177);nf_live_owned_model_assembly_stats(w+180);
 nf_live_owned_model_stats(w+182);nf_live_native_context_extract_stats(w+186);
 nf_live_native_context_guard_stats(w+190);
 memcpy(out,w,sizeof(w));return 1;
}

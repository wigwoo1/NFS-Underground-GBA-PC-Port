int nf_android_context_rejection_info(uint32_t*out,size_t words){
 if(!c||!out||words<20)return 0;uint32_t w[20];
 memcpy(w,nf_context_rejection_detail,64);memcpy(w+16,nf_context_refresh_stats,16);memcpy(out,w,sizeof(w));return 1;
}

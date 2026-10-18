extern int nf_android_traffic_remaining_failure(uint32_t*,size_t);
NFA_API int nfa_core_capture_traffic_remaining_failure(NFAAndroidCore*s,uint32_t*out,size_t words){return valid(s)&&s->capture&&out&&words>=640&&nf_android_traffic_remaining_failure(out,words);}

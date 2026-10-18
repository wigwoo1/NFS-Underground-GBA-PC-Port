extern int nf_android_traffic_rotation_stats(uint64_t[6]);
NFA_API int nfa_core_capture_traffic_rotation_stats(NFAAndroidCore*s,uint64_t out[6]){return valid(s)&&s->capture&&out&&nf_android_traffic_rotation_stats(out);}

extern int nf_android_traffic_guard_detail(uint32_t*,size_t);
NFA_API int nfa_core_capture_traffic_guard_detail(NFAAndroidCore*s,uint32_t*out,size_t words){return valid(s)&&s->capture&&out&&words>=128&&nf_android_traffic_guard_detail(out,words);}

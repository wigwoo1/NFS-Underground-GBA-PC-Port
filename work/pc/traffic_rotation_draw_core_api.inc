extern int nf_android_traffic_rotation_stats(uint64_t[6]);
NFA_API int nfa_core_capture_traffic_rotation_stats(NFAAndroidCore*s,uint64_t out[6]){return valid(s)&&s->capture&&out&&nf_android_traffic_rotation_stats(out);}

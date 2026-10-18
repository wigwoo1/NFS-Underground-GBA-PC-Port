extern int nf_android_geometry_cache_enable(int);
extern int nf_android_geometry_cache_info(uint64_t[12]);
NFA_API int nfa_core_geometry_cache_enable(NFAAndroidCore*s,int enabled){
 return valid(s)&&s->capture&&nf_android_geometry_cache_enable(enabled);
}
/* Owner-thread inspection. May be read after close once the owner has joined.
 * enabled,hits,misses,stores,evictions,clears,used,peak,budget,alloc_fail,bypass,entries */
NFA_API int nfa_core_geometry_cache_info(uint64_t out[12]){return nf_android_geometry_cache_info(out);}

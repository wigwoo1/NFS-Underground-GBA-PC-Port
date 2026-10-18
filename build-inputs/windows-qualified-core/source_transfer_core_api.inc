/* Maintained immutable packet transfer ABI. Provider DLL must outlive all frames. */

static uint64_t nfa_owned_background_counts[3];
extern size_t nf_android_observer_background_take(uint64_t,unsigned,void**);
NFA_API size_t nfa_core_capture_background_take(NFAAndroidCore*s,uint64_t epoch,unsigned refresh,void**owned){
 if(!valid(s)||!s->capture||!owned)return 0;
 size_t bytes=nf_android_observer_background_take(epoch,refresh,owned);
 if(bytes&&*owned){__atomic_fetch_add(nfa_owned_background_counts,1,__ATOMIC_RELAXED);__atomic_fetch_add(nfa_owned_background_counts+2,bytes,__ATOMIC_RELAXED);}return bytes;
}
NFA_API void nfa_core_capture_owned_free(void*owned){if(owned){__atomic_fetch_add(nfa_owned_background_counts+1,1,__ATOMIC_RELAXED);free(owned);}}
NFA_API int nfa_core_capture_owned_background_info(uint64_t out[3]){if(!out)return 0;for(unsigned i=0;i<3;i++)out[i]=__atomic_load_n(nfa_owned_background_counts+i,__ATOMIC_RELAXED);return 1;}

static uint64_t nfa_owned_geometry_counts[3];
extern size_t nf_android_observer_source_world_take(uint64_t,unsigned,unsigned,unsigned,void**);
extern void nf_android_observer_source_world_free(void*);
NFA_API size_t nfa_core_capture_source_world_take(NFAAndroidCore*s,uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void**owned){
 if(!valid(s)||!s->capture||!owned)return 0;
 size_t bytes=nf_android_observer_source_world_take(epoch,serial,begin,end,owned);
 if(bytes&&*owned){__atomic_fetch_add(nfa_owned_geometry_counts,1,__ATOMIC_RELAXED);__atomic_fetch_add(nfa_owned_geometry_counts+2,bytes,__ATOMIC_RELAXED);}return bytes;
}
NFA_API void nfa_core_capture_source_world_free(void*owned){if(owned){__atomic_fetch_add(nfa_owned_geometry_counts+1,1,__ATOMIC_RELAXED);nf_android_observer_source_world_free(owned);}}
NFA_API int nfa_core_capture_owned_geometry_info(uint64_t out[3]){if(!out)return 0;for(unsigned i=0;i<3;i++)out[i]=__atomic_load_n(nfa_owned_geometry_counts+i,__ATOMIC_RELAXED);return 1;}

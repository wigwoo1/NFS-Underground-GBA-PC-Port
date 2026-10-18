NFA_API int nfa_core_capture_enable(NFAAndroidCore*s,int enabled){
 if(!valid(s))return 0;
 if(enabled){if(s->capture)return 1;if(!nf_android_observer_attach(s->core,s->pixels)){nf_android_observer_detach();return 0;}s->capture=1;}
 else if(s->capture){nf_android_observer_detach();s->capture=0;}
 return 1;
}
NFA_API int nfa_core_capture_stats(NFAAndroidCore*s,uint64_t out[8]){
 if(!valid(s)||!out)return 0;if(!s->capture){memset(out,0,64);return 1;}
 nf_android_observer_stats(out);return 1;
}
NFA_API size_t nfa_core_capture_copy(NFAAndroidCore*s,void*out,size_t size){
 if(!valid(s)||!s->capture)return 0;return nf_android_observer_copy(out,size);
}

NFA_API int nfa_core_capture_layers(NFAAndroidCore*s,int enabled){
 if(!valid(s)||!s->capture)return 0;return nf_android_observer_layers(enabled);
}
NFA_API int nfa_core_capture_layer_info(NFAAndroidCore*s,uint64_t out[5]){
 if(!valid(s)||!s->capture||!out)return 0;return nf_android_observer_layer_info(out);
}
NFA_API size_t nfa_core_capture_layer_row(NFAAndroidCore*s,uint64_t epoch,unsigned refresh,unsigned row,void*out,size_t capacity){
 if(!valid(s)||!s->capture)return 0;return nf_android_observer_layer_row(epoch,refresh,row,out,capacity);
}

NFA_API int nfa_core_capture_pair(NFAAndroidCore*s,unsigned refresh,uint64_t out[8]){
 if(!valid(s)||!s->capture||!out)return 0;return nf_android_observer_pair(refresh,out);
}

NFA_API size_t nfa_core_capture_owned_packet(NFAAndroidCore*s,uint64_t epoch,unsigned serial,void*out,size_t capacity){
 if(!valid(s)||!s->capture)return 0;return nf_android_observer_owned_packet(epoch,serial,out,capacity);
}
NFA_API int nfa_core_capture_split(NFAAndroidCore*s,unsigned refresh,uint64_t out[12]){
 if(!valid(s)||!s->capture||!out)return 0;return nf_android_observer_split(refresh,out);
}

NFA_API int nfa_core_capture_display_owner(NFAAndroidCore*s,unsigned refresh,uint64_t out[8]){
 if(!valid(s)||!s->capture||!out)return 0;return nf_android_observer_display_owner(refresh,out);
}

NFA_API size_t nfa_core_capture_provenance(NFAAndroidCore*s,uint64_t epoch,unsigned refresh,void*out,size_t capacity){
 if(!valid(s)||!s->capture)return 0;return nf_android_observer_provenance(epoch,refresh,out,capacity);
}

NFA_API size_t nfa_core_capture_bundle(NFAAndroidCore*s,uint64_t epoch,unsigned refresh,void*out,size_t capacity){
 if(!valid(s)||!s->capture)return 0;return nf_android_observer_bundle(epoch,refresh,out,capacity);
}

NFA_API int nfa_core_capture_source_world_enable(NFAAndroidCore*s,int enabled){
 if(!valid(s)||!s->capture)return 0;return nf_android_observer_source_world_enable(enabled);
}
NFA_API size_t nfa_core_capture_source_world(NFAAndroidCore*s,uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void*out,size_t capacity){
 if(!valid(s)||!s->capture)return 0;return nf_android_observer_source_world(epoch,serial,begin,end,out,capacity);
}

int nf_android_observer_wall_history_enable(int);
size_t nf_android_observer_wall_history(uint64_t,unsigned,unsigned,unsigned,void*,size_t);
int nf_android_observer_wall_stats(uint64_t[8]);
NFA_API int nfa_core_capture_wall_history_enable(NFAAndroidCore*s,int enabled){if(!valid(s)||!s->capture)return 0;return nf_android_observer_wall_history_enable(enabled);}
NFA_API size_t nfa_core_capture_wall_history(NFAAndroidCore*s,uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void*out,size_t capacity){if(!valid(s)||!s->capture)return 0;return nf_android_observer_wall_history(epoch,serial,begin,end,out,capacity);}
NFA_API int nfa_core_capture_wall_history_stats(NFAAndroidCore*s,uint64_t out[8]){if(!valid(s)||!s->capture)return 0;return nf_android_observer_wall_stats(out);}

size_t nf_android_observer_write_ownership(uint64_t,unsigned,unsigned,unsigned,void*,size_t);
NFA_API size_t nfa_core_capture_write_ownership(NFAAndroidCore*s,uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void*out,size_t capacity){if(!valid(s)||!s->capture)return 0;return nf_android_observer_write_ownership(epoch,serial,begin,end,out,capacity);}

size_t nf_android_observer_road_history(uint64_t,unsigned,unsigned,unsigned,void*,size_t);
NFA_API size_t nfa_core_capture_road_history(NFAAndroidCore*s,uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void*out,size_t capacity){if(!valid(s)||!s->capture)return 0;return nf_android_observer_road_history(epoch,serial,begin,end,out,capacity);}

int nf_android_observer_sky_enable(int);
size_t nf_android_observer_sky(uint64_t,unsigned,void*,size_t);
NFA_API int nfa_core_capture_sky_enable(NFAAndroidCore*s,int enabled){if(!valid(s)||!s->capture)return 0;return nf_android_observer_sky_enable(enabled);}
NFA_API size_t nfa_core_capture_sky(NFAAndroidCore*s,uint64_t epoch,unsigned serial,void*out,size_t capacity){if(!valid(s)||!s->capture)return 0;return nf_android_observer_sky(epoch,serial,out,capacity);}
size_t nf_android_observer_sky_scene(uint64_t,unsigned,void*,size_t);
NFA_API size_t nfa_core_capture_sky_scene(NFAAndroidCore*s,uint64_t epoch,unsigned refresh,void*out,size_t capacity){if(!valid(s)||!s->capture)return 0;return nf_android_observer_sky_scene(epoch,refresh,out,capacity);}

size_t nf_android_observer_background_scene(uint64_t,unsigned,void*,size_t);
NFA_API size_t nfa_core_capture_background_scene(NFAAndroidCore*s,uint64_t epoch,unsigned refresh,void*out,size_t capacity){if(!valid(s)||!s->capture)return 0;return nf_android_observer_background_scene(epoch,refresh,out,capacity);}

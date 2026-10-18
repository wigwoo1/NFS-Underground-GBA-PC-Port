int nf_android_observer_text_enable(int);
size_t nf_android_observer_text(uint64_t,unsigned,void*,size_t);
NFA_API int nfa_core_capture_text_enable(NFAAndroidCore*s,int enabled){if(!valid(s)||!s->capture)return 0;return nf_android_observer_text_enable(enabled);}
NFA_API size_t nfa_core_capture_text(NFAAndroidCore*s,uint64_t epoch,unsigned refresh,void*out,size_t capacity){if(!valid(s)||!s->capture)return 0;return nf_android_observer_text(epoch,refresh,out,capacity);}
size_t nf_android_observer_menu_text(uint64_t,unsigned,void*,size_t);
NFA_API size_t nfa_core_capture_menu_text(NFAAndroidCore*s,uint64_t epoch,unsigned refresh,void*out,size_t capacity){if(!valid(s)||!s->capture)return 0;return nf_android_observer_menu_text(epoch,refresh,out,capacity);}
size_t nf_android_observer_menu_text_bundle(uint64_t,unsigned,void*,size_t);
NFA_API size_t nfa_core_capture_menu_text_bundle(NFAAndroidCore*s,uint64_t epoch,unsigned refresh,void*out,size_t capacity){if(!valid(s)||!s->capture)return 0;return nf_android_observer_menu_text_bundle(epoch,refresh,out,capacity);}

extern int nf_android_rotation_trace_enable(unsigned);
extern size_t nf_android_rotation_trace_copy(void*,size_t);
NFA_API int nfa_core_capture_rotation_trace_enable(NFAAndroidCore*s,unsigned target){return valid(s)&&s->capture&&nf_android_rotation_trace_enable(target);}
NFA_API size_t nfa_core_capture_rotation_trace_copy(NFAAndroidCore*s,void*out,size_t bytes){if(!valid(s)||!s->capture)return 0;return nf_android_rotation_trace_copy(out,bytes);}

extern size_t nf_android_rotation_trace_code(void*,size_t);
NFA_API size_t nfa_core_capture_rotation_trace_code(NFAAndroidCore*s,void*out,size_t bytes){if(!valid(s)||!s->capture)return 0;return nf_android_rotation_trace_code(out,bytes);}

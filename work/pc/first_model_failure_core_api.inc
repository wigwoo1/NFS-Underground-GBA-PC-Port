extern int nf_android_first_model_failure_info(uint32_t*,size_t);
NFA_API int nfa_core_capture_first_model_failure(NFAAndroidCore*s,uint32_t*out,size_t words){if(!valid(s)||!s->capture||!out||words<256)return 0;return nf_android_first_model_failure_info(out,words);}

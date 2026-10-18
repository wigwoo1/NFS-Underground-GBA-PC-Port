extern int nf_android_scene_rejection_info(uint32_t*,size_t);
NFA_API int nfa_core_capture_scene_rejection_info(NFAAndroidCore*s,uint32_t*out,size_t words){
 if(!valid(s)||!s->capture||!out||words<192)return 0;
 return nf_android_scene_rejection_info(out,words);
}

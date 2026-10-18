extern int nf_pc_source_pose_timing(uint64_t,unsigned,unsigned,unsigned,uint64_t*,size_t,void*,size_t);
NFA_API size_t nfa_core_capture_pose_timing(NFAAndroidCore*s,uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void*out,size_t bytes){
 if(!valid(s)||!s->capture||(out&&bytes<184))return 0;
 uint64_t words[16];unsigned char camera[56];
 if(!nf_pc_source_pose_timing(epoch,serial,begin,end,words,128,camera,56))return 0;
 if(out){memcpy(out,words,128);memcpy((unsigned char*)out+128,camera,56);}return 184;
}

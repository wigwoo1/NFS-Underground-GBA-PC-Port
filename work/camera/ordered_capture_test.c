#include "ordered_capture.h"
__declspec(dllexport) int nf_ordered_capture_test(HMODULE bridge,uint64_t epoch,unsigned older,unsigned newer,unsigned refresh,unsigned cut,NFOrderedSceneSubmission**out){return nf_ordered_capture(bridge,epoch,older,newer,refresh,cut,out);}
__declspec(dllexport) void nf_ordered_capture_test_free(NFOrderedSceneSubmission*p){nf_ordered_scene_submission_destroy(p);}

#include "stable_scene_submission.h"
__declspec(dllexport) int nf_stable_scene_create_test(const void*b,size_t bn,const void*h,size_t hn,const void*t,size_t tn,const NFPagePersistenceProof*p,NFStableSceneSubmission**out){return nf_stable_scene_create(b,bn,h,hn,t,tn,p,out);}
__declspec(dllexport) void nf_stable_scene_free_test(NFStableSceneSubmission*s){nf_stable_scene_destroy(s);}

__declspec(dllexport) void nf_complete_road_cache_clear_test(void){nf_complete_road_cache_clear();}
__declspec(dllexport) void nf_complete_road_cache_stats_test(uint64_t out[2]){out[0]=nf_complete_road_cache.hits;out[1]=nf_complete_road_cache.misses;}

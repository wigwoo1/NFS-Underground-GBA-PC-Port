#ifndef NF_SAMPLED_ROOT_BINDING_H
#define NF_SAMPLED_ROOT_BINDING_H
#include "scene_segments.h"
/* status1 unique captured direct root;2 uncaptured;3 repeated region/pass;
   4 unique root has child/model barriers. Binding never proves draw eligibility.
   Sampled ordering is authoritative; captured positions are metadata only. */
typedef struct {NFRootRegionCall call;uint32_t captured,status;} NFSampledRootCall;
typedef struct {uint32_t count,removed_count;NFSampledRootCall calls[2*NF_VISIBILITY_QUEUE_CAPACITY];uint32_t removed[256];} NFSampledRootBinding;
__declspec(dllexport) int nf_sampled_root_binding(const void*,unsigned,
 const uint32_t*,unsigned,const uint32_t*,unsigned,const uint32_t*,const uint32_t*,NFSampledRootBinding*);
#endif

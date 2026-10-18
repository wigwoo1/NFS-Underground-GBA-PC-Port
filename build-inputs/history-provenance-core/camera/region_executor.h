#ifndef NF_REGION_EXECUTOR_H
#define NF_REGION_EXECUTOR_H
#include "native_visibility.h"
typedef struct NFRegionExecutor NFRegionExecutor;
typedef int (*NFRegionExpand)(void*,const uint8_t[16],unsigned,NFVisibilityRegionAction*,unsigned,unsigned*);
typedef int (*NFRegionEmit)(void*,NFRegionExecutor*,unsigned,const NFVisibilityRegionAction*);
/* Expand supplies native local plans. Emit handles surfaces/objects/deferred;
   object handler may reenter region execution for native object child records.
   Failure is terminal; caller discards any partial scene assembly. */
struct NFRegionExecutor {NFRegionExpand expand;NFRegionEmit emit;void*user;unsigned depth,regions,actions,failed,max_depth,max_regions;};
__declspec(dllexport) int nf_region_executor_begin(NFRegionExecutor*,NFRegionExpand,NFRegionEmit,void*,unsigned,unsigned);
__declspec(dllexport) int nf_region_execute(NFRegionExecutor*,const uint8_t[16],unsigned);
__declspec(dllexport) int nf_region_execute_queue(NFRegionExecutor*,const void*,unsigned);
#endif

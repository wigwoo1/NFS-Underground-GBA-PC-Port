#ifndef NF_ORDERED_DISPATCH_H
#define NF_ORDERED_DISPATCH_H
#include <stdint.h>
#include "visibility_capacity.h"
typedef struct {uint32_t kind,ordinal,source,object,descriptor,object_selected;} NFDispatchCommand;
typedef struct {uint32_t captured_index,source,pass,object_selected;} NFDispatchSelection;
typedef struct {uint32_t count,indices[257];} NFOrderedDispatch;
typedef struct {uint32_t queue_index,pass,record[4];} NFRootRegionCall;
typedef struct {uint32_t count;NFRootRegionCall calls[2*NF_VISIBILITY_QUEUE_CAPACITY];} NFRootRegionSchedule;
/* Packed 16-byte queue records, at most NF_VISIBILITY_QUEUE_CAPACITY. Reverse eligible records in each
   of two passes, preserving duplicate occurrences. Does not emit nested calls
   or surfaces. Output is owned and unchanged on failure. */
__declspec(dllexport) int nf_root_region_schedule(const void*,unsigned,NFRootRegionSchedule*);
/* Scene-local occurrence selection only. Caller binds all inputs to the same
   retained scene. Pass metadata is three words per command (LR,mask,record),
   zero for nonwalls. No candidate insertion or object eligibility inference.
   Atomic output on failure; no borrowed output storage. */
__declspec(dllexport) int nf_ordered_dispatch(const NFDispatchCommand*,unsigned,
 const uint32_t*,const NFDispatchSelection*,unsigned,NFOrderedDispatch*);
typedef struct {uint32_t region,begin,end;} NFRootInterval;
typedef struct {uint32_t count,slots[NF_VISIBILITY_QUEUE_CAPACITY];} NFRootAnchors;
/* Unique region ids, captured roots preserved as a subsequence. New roots
   require a following captured root. Caller binds inputs to one scene/pass.
   Slots refer to original commands; no nested/within-block order inference.
   Bounded and atomic output on failure. */
__declspec(dllexport) int nf_root_region_anchors(const uint32_t*,unsigned,
 const NFRootInterval*,unsigned,NFRootAnchors*);
typedef struct {uint32_t source,command;} NFRetainedWall;
typedef struct {uint32_t count;uint32_t source[64],before[64];} NFWallInsertions;
/* Caller supplies one region/pass's ordered wall sources and a verified tail
   command (e.g. its road). Captured walls must remain an ordered subsequence.
   Reject duplicate sources, invalid command order, removals and reordering.
   Does not infer eligibility, nested call boundaries, or material ownership. */
__declspec(dllexport) int nf_wall_insertions(const uint32_t*,unsigned,
 const NFRetainedWall*,unsigned,unsigned,NFWallInsertions*);
#endif



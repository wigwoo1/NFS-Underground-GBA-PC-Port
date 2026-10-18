#ifndef NF_SNAPSHOT_STORE_H
#define NF_SNAPSHOT_STORE_H
#include "presentation_timeline.h"
#include <stddef.h>
typedef struct NFSnapshotStore NFSnapshotStore;
typedef struct {NFTimelineSample time;const void*older;size_t older_size;const void*newer;size_t newer_size;} NFSnapshotPair;
/* Single-owner API, not thread-safe. Retained byte budget excludes the temporary
   incoming allocation needed for failure-atomic replacement. Payload is opaque. */
__declspec(dllexport) NFSnapshotStore* nf_snapshot_create(size_t retained_budget);
/* Evicts oldest entries as needed for both count and byte limits. A payload
   larger than the entire budget fails without changing existing history. */
__declspec(dllexport) int nf_snapshot_push(NFSnapshotStore*,uint64_t epoch,uint64_t id,double time,const void*,size_t);
/* Acquire pins the returned immutable pair until release. All mutation and
   destruction are rejected while pinned. Returns the NF_TIME_* status. */
__declspec(dllexport) int nf_snapshot_acquire(NFSnapshotStore*,double now,double delay,NFSnapshotPair*);
__declspec(dllexport) void nf_snapshot_release(NFSnapshotStore*);
__declspec(dllexport) int nf_snapshot_destroy(NFSnapshotStore*);
#endif

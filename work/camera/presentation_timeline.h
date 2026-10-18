#ifndef NF_PRESENTATION_TIMELINE_H
#define NF_PRESENTATION_TIMELINE_H
#include <stdint.h>
#define NF_TIMELINE_CAPACITY 16
typedef struct {double time;uint64_t id;} NFTimelineEntry;
typedef struct {uint64_t epoch;unsigned count;NFTimelineEntry entries[NF_TIMELINE_CAPACITY];} NFTimeline;
typedef struct {uint64_t epoch,older,newer;double alpha,target;} NFTimelineSample;
enum {NF_TIME_EMPTY=0,NF_TIME_BEFORE=1,NF_TIME_READY=2,NF_TIME_AFTER=3};
__declspec(dllexport) void nf_timeline_clear(NFTimeline*);
/* Single-owner queue of immutable scene handles. A newer epoch resets history
   for scene cuts/reset/menu transitions; stale epochs/timestamps are rejected. */
__declspec(dllexport) int nf_timeline_push(NFTimeline*,uint64_t epoch,uint64_t id,double time);
/* All scene poses use this one pair/phase. Discrete materials use older.
   now, delay and entry timestamps share units. Never extrapolates or advances
   simulation. Caller observes BEFORE/AFTER to diagnose buffer starvation. */
__declspec(dllexport) int nf_timeline_sample(const NFTimeline*,double now,double delay,NFTimelineSample*);
#endif

#ifndef NF_FRAME_CLOCK_H
#define NF_FRAME_CLOCK_H
#include <stdint.h>
typedef struct {uint64_t origin,last,simulated,next_display;uint32_t base,active;double delay;} NFFrameClock;
typedef struct {uint32_t simulation_steps,present;uint64_t display_index,skipped_displays,deadline_ns,next_wake_ns;double source_target;} NFFramePlan;
typedef struct {uint32_t eligible;uint64_t display_index,deadline_ns,next_wake_ns;double source_target;} NFPreparationPlan;
/* Read-only early preparation window. Does not commit presentation or advance
   original simulation. Caller must acquire owned source data separately and
   invalidate prepared content on epoch/restart; overdue slots are ineligible. */
__declspec(dllexport) int nf_frame_clock_prepare(const NFFrameClock*,uint64_t now,uint64_t lead_ns,NFPreparationPlan*);
/* Monotonic nanoseconds, original 16777216/280896 Hz simulation and 60 Hz
   presentation. Restart after pause/load. Supports sessions up to seven days.
   poll commits a plan: caller must execute all returned original simulation
   steps before sampling presentation. At most four steps per poll; simulation
   is never discarded. Overdue display slots are skipped, never replayed. */
__declspec(dllexport) int nf_frame_clock_start(NFFrameClock*,uint64_t now,uint32_t source_refresh,double delay);
__declspec(dllexport) int nf_frame_clock_poll(NFFrameClock*,uint64_t now,NFFramePlan*);
#endif

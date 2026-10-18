#ifndef NF_LIVE_SCENE_API_H
#define NF_LIVE_SCENE_API_H
#include <stdint.h>
#include <stddef.h>
/* Synchronous borrowed packet. Copy/retain before returning nonzero.
   Do not reenter the emulator from this callback. Single-owner thread only. */
typedef int (*NFLiveSceneSink)(void*,uint64_t,const void*,size_t);
__declspec(dllexport) int nf_native_scene_sink(NFLiveSceneSink,void*);
/* Configure before the first captured scene. Requires NSP2-aware consumers;
   native paired regeneration is not yet multi-model capable. */
__declspec(dllexport) int nf_native_scene_multimodel(int enabled);
__declspec(dllexport) int nf_native_scenes(const char*path);
/* Suppress any retained pair whose epoch differs from this value, including
   the interval after a discontinuity and before the first replacement scene. */
__declspec(dllexport) uint64_t nf_native_scene_epoch(void);
__declspec(dllexport) uint32_t nf_native_scene_refresh(void);
__declspec(dllexport) void nf_native_scene_discontinuity(void);
/* Closed in current epoch, published, rejected, sink/write failures.
   The latter three counters cover the entire enabled session. */
__declspec(dllexport) void nf_native_scene_stats(uint32_t out[4]);

/* Optional original-cycle diagnostics; out has 20 uint64 words (scene_timing.h). */
__declspec(dllexport) int nf_native_scene_timing_enable(int);
__declspec(dllexport) int nf_native_scene_timing_read(uint64_t,uint32_t,uint64_t*);

__declspec(dllexport) int nf_native_scene_pose_boundary_read(uint64_t,uint32_t,void*,size_t);
/* Source-only immutable pose input; meta[3]==0, not complete geometry. */
__declspec(dllexport) int nf_native_scene_pose_source_read(uint64_t,uint32_t,void*,size_t);
__declspec(dllexport) int nf_native_scene_pose_source_clock_read(uint64_t,uint32_t,uint64_t*);
#endif

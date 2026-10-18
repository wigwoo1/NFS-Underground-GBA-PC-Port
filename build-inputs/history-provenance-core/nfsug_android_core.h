#ifndef NFSUG_ANDROID_CORE_H
#define NFSUG_ANDROID_CORE_H
#include <stddef.h>
#include <stdint.h>
#ifdef _WIN32
#define NFA_API __declspec(dllexport)
#else
#define NFA_API __attribute__((visibility("default")))
#endif
#ifdef __cplusplus
extern "C" {
#endif
/* Portable core boundary only. No Activity, scene renderer or frame scheduler.
   One owner thread and one live core. Discard the handle after close. */
typedef struct NFAAndroidCore NFAAndroidCore;
enum {NFA_STEP_ERROR=0,NFA_STEP_OK=1,NFA_STEP_PAUSED=2};
enum {NFA_KEY_A=1,NFA_KEY_B=2,NFA_KEY_SELECT=4,NFA_KEY_START=8,
 NFA_KEY_RIGHT=16,NFA_KEY_LEFT=32,NFA_KEY_UP=64,NFA_KEY_DOWN=128};
NFA_API NFAAndroidCore* nfa_core_open(const char*rom_path);
NFA_API void nfa_core_close(NFAAndroidCore*);
NFA_API int nfa_core_step(NFAAndroidCore*,uint32_t keys);
NFA_API int nfa_core_pause(NFAAndroidCore*,int paused);
NFA_API int nfa_core_timing(NFAAndroidCore*,uint64_t out[4]);
/* Borrowed original mGBA 32-bit color_t buffer (240x160), not native 4K output.
   Invalidated by step/reset/close. Android GPU conversion/upload is future work. */
NFA_API const uint32_t* nfa_core_pixels(NFAAndroidCore*);
NFA_API size_t nfa_core_state_size(NFAAndroidCore*);
NFA_API int nfa_core_load_state(NFAAndroidCore*,const void*,size_t);
NFA_API int nfa_core_save_state(NFAAndroidCore*,void*,size_t);
/* Interleaved stereo signed 16-bit PCM at 44100 Hz. Does not step the core. */
NFA_API size_t nfa_core_read_audio(NFAAndroidCore*,int16_t*,size_t capacity_frames);
/* Owned battery-memory copies; no filesystem writes. Zero size means no data.
   Restore accepts supported GBA save sizes only, matching an existing detected size. One owner thread required. */
NFA_API size_t nfa_core_battery_size(NFAAndroidCore*);
NFA_API size_t nfa_core_copy_battery(NFAAndroidCore*,void*,size_t capacity);
NFA_API int nfa_core_load_battery(NFAAndroidCore*,const void*,size_t bytes);
/* Caller hit-tests the Android overlay, then submits one bitmask per pointer.
   No Android screen layout or MotionEvent code is implemented yet. */
#define NFA_TOUCH_CAPACITY 16
typedef struct {int32_t ids[NFA_TOUCH_CAPACITY];uint32_t masks[NFA_TOUCH_CAPACITY];uint32_t used;} NFATouch;
NFA_API void nfa_touch_clear(NFATouch*);
NFA_API int nfa_touch_set(NFATouch*,int32_t pointer_id,uint32_t controls);
NFA_API uint32_t nfa_touch_keys(const NFATouch*);
#ifdef __cplusplus
}
#endif
#endif

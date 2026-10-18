#ifndef NF_ANDROID_SCENE_OWNER_H
#define NF_ANDROID_SCENE_OWNER_H
#include <stddef.h>
#include <stdint.h>
#ifdef _WIN32
#define NF_SCENE_API __declspec(dllexport)
#else
#define NF_SCENE_API __attribute__((visibility("default")))
#endif
/* Immutable native scene packet owner. No emulator pointers, clock or GPU.
   Caller owns one handle; discard after close. Copies never partially write.
   Rejects packets larger than 256 MiB rather than omitting scene data. */
NF_SCENE_API void* nf_android_scene_open(const void*,size_t);
NF_SCENE_API void nf_android_scene_close(void*);
NF_SCENE_API int nf_android_scene_info(const void*,uint64_t out[12]);
NF_SCENE_API size_t nf_android_scene_copy(const void*,void*,size_t);
NF_SCENE_API size_t nf_android_scene_section(const void*,unsigned,void*,size_t);
#endif

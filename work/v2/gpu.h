#ifndef NF_GPU_H
#define NF_GPU_H
#include <stdint.h>
int nf_gpu_init(void);
void nf_gpu_draw(int window_width,int window_height,int native_view);
int nf_gpu_capture(const char* path);
void nf_gpu_close(void);
int nf_gpu_polygon_count(void);
unsigned nf_gpu_frame_hash(void);
void nf_gpu_audit_layers(int enabled);
void nf_gpu_audit_frame_begin(void);
uint32_t nf_gpu_reference_hash(void);
uint32_t nf_gpu_source_region_hash(unsigned x,unsigned y,unsigned width,unsigned height);
uint32_t nf_gpu_overlay_hash(void);
uint32_t nf_gpu_background_hash(void);
uint32_t nf_gpu_overlay_pixel_count(void);
int nf_gpu_overlay_active(void);
void nf_gpu_motion(int);
int nf_gpu_texture_pack_available(void);
void nf_gpu_texture_pack(int enabled);
void nf_gpu_motion_profile(uint64_t* calls,uint64_t* total_ns,uint64_t* max_ns,uint64_t* candidates,uint64_t* legacy_cost_calls);
void nf_gpu_motion_verification(uint64_t* scene_pairs,uint64_t* mismatches);
int nf_gpu_motion_legacy_forced(void);
#endif

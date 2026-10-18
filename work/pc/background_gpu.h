#ifndef NF_PC_BACKGROUND_GPU_H
#define NF_PC_BACKGROUND_GPU_H
#include "source_background.h"
typedef struct NFPCBackgroundGPU NFPCBackgroundGPU;
/* Hidden Windows context, exclusively owned by its creating thread. Components
   only: this is not a full scene or a gameplay presentation scheduler. */
NFPC_API NFPCBackgroundGPU* nf_pc_background_gpu_open(void);
NFPC_API void nf_pc_background_gpu_close(NFPCBackgroundGPU*);
NFPC_API const char* nf_pc_background_gpu_error(void);
NFPC_API const char* nf_pc_background_gpu_renderer(const NFPCBackgroundGPU*);
/* Bottom-up RGBA readback of full target; origin-zero 3:2 active rectangle.
   Remaining target stays transparent. Caller discards output on any failure. */
NFPC_API int nf_pc_background_gpu_draw(NFPCBackgroundGPU*,const NFPCSourceFrame*,unsigned width,unsigned height,unsigned active_width,unsigned active_height,void*out,size_t bytes);
#endif

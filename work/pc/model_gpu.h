#ifndef NF_PC_MODEL_GPU_H
#define NF_PC_MODEL_GPU_H
#include "model_mesh.h"
typedef struct NFPCModelGPU NFPCModelGPU;
/* Hidden Windows context, exclusively owned by its creating thread. Components
   only: this is not a full scene or a gameplay presentation scheduler. */
NFPC_API NFPCModelGPU* nf_pc_model_gpu_open(void);
NFPC_API void nf_pc_model_gpu_close(NFPCModelGPU*);
NFPC_API const char* nf_pc_model_gpu_error(void);
NFPC_API const char* nf_pc_model_gpu_renderer(const NFPCModelGPU*);
/* Bottom-up RGBA readback of full target; origin-zero 3:2 active rectangle.
   Remaining target stays transparent. Caller discards output on any failure. */
/* Draws one model using original historical palettes and owner row clip.
   Palette is 256x160 RGBA (163840 bytes). Output is bottom-up RGBA. */
NFPC_API int nf_pc_model_gpu_draw(NFPCModelGPU*,const NFPCModelMesh*,const void*palette,size_t palette_bytes,unsigned width,unsigned height,unsigned active_width,unsigned active_height,unsigned owner_top,unsigned owner_bottom,void*out,size_t bytes);
#endif

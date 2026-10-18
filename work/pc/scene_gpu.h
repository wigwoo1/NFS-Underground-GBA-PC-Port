#ifndef NF_PC_SCENE_GPU_H
#define NF_PC_SCENE_GPU_H
#include "source_scene.h"
#include "world_mesh.h"
#include "model_mesh.h"
typedef struct NFPCSceneGPU NFPCSceneGPU;
NFPC_API NFPCSceneGPU* nf_pc_scene_gpu_open(void);
/* Borrow a host-created HWND; GL context belongs to calling render thread.
   Host must keep window alive until close. No game/core callbacks. */
NFPC_API NFPCSceneGPU* nf_pc_scene_gpu_open_window(void* hwnd);
NFPC_API void nf_pc_scene_gpu_close(NFPCSceneGPU*);
NFPC_API const char* nf_pc_scene_gpu_error(void);
NFPC_API const char* nf_pc_scene_gpu_renderer(const NFPCSceneGPU*);
/* Owner-thread snapshot; no GL calls. Exactly10 signed64 values:
   setter/getter available, requested,cached,driver-reported interval(-1 unknown),
   set attempts,set failures,readbacks,visible/hidden successful presents.
   These are API observations, not scanout/tearing or smooth-motion proof. */
NFPC_API int nf_pc_scene_gpu_swap_info(const NFPCSceneGPU*,int64_t*out,size_t bytes);
/* One context/FBO:background,retained road/wall,source commands,HUD effects.
   Bottom-up full target RGBA; active source rectangle at origin, other cells
   transparent. No original framebuffer or game scheduling. */
NFPC_API int nf_pc_scene_gpu_draw(NFPCSceneGPU*,NFPCScene*,unsigned width,unsigned height,unsigned active_width,unsigned active_height,void*out,size_t bytes);
/* Diagnostic masks:1background,2retained,4geometry,8HUD.
   All passes (15) is the ordinary draw above. Unknown bits reject untouched. */
NFPC_API int nf_pc_scene_gpu_draw_passes(NFPCSceneGPU*,NFPCScene*,unsigned width,unsigned height,unsigned active_width,unsigned active_height,unsigned passes,void*out,size_t bytes);
/* Native endpoint render without CPU readback. */
NFPC_API int nf_pc_scene_gpu_render(NFPCSceneGPU*,NFPCScene*,unsigned width,unsigned height,unsigned active_width,unsigned active_height);
/* Present cached native target if original_rgba=NULL, otherwise top-down
   240x160 original display. Letterboxes3:2, ignores original alpha. Calling
   host performs generation/epoch acceptance immediately before this commit. */
NFPC_API int nf_pc_scene_gpu_present(NFPCSceneGPU*,const void*original_rgba,size_t bytes,unsigned active_width,unsigned active_height);
/* Diagnostic synchronous mesh substitutions, one slot per source command.
   NULL slots retain endpoint geometry. Non-NULL slots must be world meshes
   sampled from that command's original source class; matching original surface
   metadata is checked. Materials, command order and endpoint scissor are kept.
   Borrows scene/meshes only during call; no ownership transfer or parent geometry mutation.
   As with ordinary draws, the material image cache requires exclusive access.
   Endpoint sky/HUD/retained layers do NOT move. This is not full-scene motion.
   Rejects invalid inputs before touching output/target. */
NFPC_API int nf_pc_scene_gpu_draw_world_meshes(NFPCSceneGPU*,NFPCScene*,const NFPCWorldMesh*const*,size_t mesh_count,unsigned width,unsigned height,unsigned active_width,unsigned active_height,unsigned passes,void*out,size_t bytes);
/* Diagnostic shared draw: optional world/model slots by original command;
   NULL arrays/slots keep endpoint geometry. Optional top-down background must
   have exactly153600 bytes. Parent materials/order/scissors/HUD/retention stay
   at the endpoint; caller must prove source identity/time compatibility.
   Borrows everything synchronously. Bounded16MiB temporary texture planes.
   Model meshes use original command layout, including empty triangle policy.
   Not coherent full-scene motion; alpha1 must submit the entire new scene. */
NFPC_API int nf_pc_scene_gpu_draw_pose_meshes(NFPCSceneGPU*,NFPCScene*,const NFPCWorldMesh*const*,const NFPCModelMesh*const*,size_t command_count,const void*background,size_t background_bytes,unsigned width,unsigned height,unsigned active_width,unsigned active_height,unsigned passes,void*out,size_t bytes);
#endif

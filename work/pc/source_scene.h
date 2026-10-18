#ifndef NF_PC_SOURCE_SCENE_H
#define NF_PC_SOURCE_SCENE_H
#include "source_frame.h"
typedef struct NFPCScene NFPCScene;
/* Initial background, retained road/wall and ordered source model/world commands.
   Historical HUD candidates/effects complete endpoint composition. Owns all data.
   Old epochs must still be discarded by the presentation caller on reset. */
NFPC_API NFPCScene* nf_pc_scene_prepare(const NFPCSourceFrame*,size_t maximum_retained_bytes);
/* Optional pose inputs. Retains the already decoded original source worlds
   within the SAME total scene budget. Endpoint pixels/commands are unchanged.
   Default prepare retains no source worlds. Returned views remain valid until
   scene free and are immutable; no frame/core dependency. Invalid getter
   arguments/default scenes leave outputs untouched. Not a motion renderer. */
NFPC_API NFPCScene* nf_pc_scene_prepare_motion(const NFPCSourceFrame*,size_t);
NFPC_API int nf_pc_scene_motion_packet(const NFPCScene*,unsigned owner,const void**,size_t*);
NFPC_API int nf_pc_scene_motion_model(const NFPCScene*,unsigned command,const void**,size_t*);
/* Optional immutable 30568-byte NFSK + copied indices + complete sky asset.
   Included in the SAME total scene budget; default scenes reject untouched. */
NFPC_API int nf_pc_scene_motion_sky(const NFPCScene*,unsigned owner,const void**,size_t*);
/* Optional immutable validated184-byte capture-time view. Only copied by
   prepare_motion from timed frames, charged to its total budget. */
NFPC_API int nf_pc_scene_motion_timing(const NFPCScene*,unsigned owner,const void**,size_t*);
NFPC_API void nf_pc_scene_free(NFPCScene*);
/* epoch,refresh,owners,commands,models,worlds,requested bytes,split row */
NFPC_API int nf_pc_scene_info(const NFPCScene*,uint64_t out[8]);
/* owner,model,index,width,height,vertices,indexed,wall,lit,left,right,top,bottom,
   owner top,owner bottom,original command index */
NFPC_API int nf_pc_scene_command_info(const NFPCScene*,unsigned,uint64_t out[16]);
/* Copied original owner key(epoch,serial,begin,end,page) and command source
   identity(kind + four source fields). Owned by the prepared scene; remains
   valid after frame/core destruction. Never infer identity from projected
   geometry or command index. Invalid arguments leave both outputs untouched.
   Identity alone does not prove geometry compatibility or motion visibility. */
NFPC_API int nf_pc_scene_command_source(const NFPCScene*,unsigned,uint64_t owner[5],uint32_t identity[5]);
/* initial source background RGBA, historical palette RGBA */
NFPC_API int nf_pc_scene_buffer(const NFPCScene*,unsigned,const void**,size_t*);
/* projected float5 vertices, float11 texture planes */
NFPC_API int nf_pc_scene_command_buffer(const NFPCScene*,unsigned,unsigned,const void**,size_t*);
/* Mutates the one-variant cache; exclusive caller. Unlit requires level0. */
NFPC_API int nf_pc_scene_command_image(NFPCScene*,unsigned,unsigned,const void**,size_t*);
NFPC_API int nf_pc_scene_command_columns(const NFPCScene*,unsigned,unsigned,uint32_t*,size_t);
/* Owner-bound NFPC_ROAD/NFPC_WALL; info/buffers0/1 follow source_retention.h.
   Buffer2 is owned float4 cell-quad vertices {x,y,u,v}, six per retained cell. */
NFPC_API int nf_pc_scene_retention_info(const NFPCScene*,unsigned owner,unsigned kind,uint64_t out[10]);
NFPC_API int nf_pc_scene_retention_buffer(const NFPCScene*,unsigned owner,unsigned kind,unsigned buffer,const void**,size_t*);
NFPC_API int nf_pc_scene_hud_info(const NFPCScene*,uint64_t out[5]);
NFPC_API int nf_pc_scene_hud_buffer(const NFPCScene*,unsigned,const void**,size_t*);
#endif

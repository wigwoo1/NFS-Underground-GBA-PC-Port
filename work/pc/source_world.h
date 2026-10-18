#ifndef NF_PC_SOURCE_WORLD_H
#define NF_PC_SOURCE_WORLD_H
#include "source_frame.h"
typedef struct NFPCWorld NFPCWorld;
/* Owned, validated SOURCE packet world data; no projection/rasterization yet. */
NFPC_API NFPCWorld* nf_pc_world_decode(const void*,size_t,size_t maximum_bytes);
NFPC_API NFPCWorld* nf_pc_source_world(const NFPCSourceFrame*,unsigned owner,size_t maximum_bytes);
NFPC_API void nf_pc_world_free(NFPCWorld*);
/* surfaces,models,commands,requested bytes */
NFPC_API int nf_pc_world_info(const NFPCWorld*,uint64_t out[4]);
/* corners,width,height,kind,mode,lit,planes,left,right,top,bottom,command order */
NFPC_API int nf_pc_world_surface_info(const NFPCWorld*,unsigned,uint64_t out[12]);
/* vertices,UV,RGBA,metadata,lighting,states,indices,attributes,camera,identity.
   Optional absent components return successful empty views. Lifetime = world. */
NFPC_API int nf_pc_world_surface_buffer(const NFPCWorld*,unsigned,unsigned,const void**,size_t*);
/* reciprocal table,bounds trailer,original order section */
NFPC_API int nf_pc_world_buffer(const NFPCWorld*,unsigned,const void**,size_t*);
/* Borrowed original source model packet for common camera/pose validation. */
NFPC_API int nf_pc_world_model(const NFPCWorld*,unsigned,const void**,size_t*);
/* Original validated model identity (kind/source fields), copied out. Invalid
   world/index/output rejects without touching output. No screen matching. */
NFPC_API int nf_pc_world_model_identity(const NFPCWorld*,unsigned,uint32_t out[5]);
NFPC_API int nf_pc_world_command(const NFPCWorld*,unsigned,uint64_t out[2]);
/* Original owned NSP bytes; borrowed only until world free. */
NFPC_API int nf_pc_world_packet(const NFPCWorld*,const void**,size_t*);
#endif

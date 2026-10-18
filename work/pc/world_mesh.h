#ifndef NF_PC_WORLD_MESH_H
#define NF_PC_WORLD_MESH_H
#include "source_world.h"
typedef struct NFPCWorldMesh NFPCWorldMesh;
/* Owns geometry after its source world is freed. Material stays in world. */
NFPC_API NFPCWorldMesh* nf_pc_world_mesh(const NFPCWorld*,unsigned surface,size_t maximum_bytes);
NFPC_API void nf_pc_world_mesh_free(NFPCWorldMesh*);
/* Original 12 surface metadata words, triangle vertices,affine,source camera,
   requested bytes. Does not apply pixel scissor or retained road/wall layers. */
NFPC_API int nf_pc_world_mesh_info(const NFPCWorldMesh*,uint64_t out[16]);
/* projected float5 vertices,original camera double3 points. */
NFPC_API int nf_pc_world_mesh_buffer(const NFPCWorldMesh*,unsigned,const void**,size_t*);
NFPC_API int nf_pc_world_mesh_plane(const NFPCWorldMesh*,unsigned triangle,float out[11]);
#endif

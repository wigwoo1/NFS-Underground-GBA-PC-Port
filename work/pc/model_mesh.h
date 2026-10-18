#ifndef NF_PC_MODEL_MESH_H
#define NF_PC_MODEL_MESH_H
#include "source_frame.h"
typedef struct NFPCModelMesh NFPCModelMesh;
enum {NFPC_MODEL_VERTICES=0,NFPC_MODEL_CAMERA=1,NFPC_MODEL_RGBA=2,NFPC_MODEL_INDICES=3};
NFPC_API unsigned nf_pc_source_model_count(const NFPCSourceFrame*,unsigned owner);
NFPC_API NFPCModelMesh* nf_pc_source_model_mesh(const NFPCSourceFrame*,unsigned owner,unsigned model,size_t maximum_bytes);
/* Standalone validated NFM2 reader for tools and malformed-input tests. */
NFPC_API NFPCModelMesh* nf_pc_model_mesh_decode(const void*,size_t,size_t maximum_bytes);
NFPC_API void nf_pc_model_mesh_free(NFPCModelMesh*);
/* width,height,source vertices,source faces,triangle vertices,indexed,requested
   bytes,left,right,top,bottom,original command order. Source clipping only. */
NFPC_API int nf_pc_model_mesh_info(const NFPCModelMesh*,uint64_t out[12]);
NFPC_API int nf_pc_model_mesh_buffer(const NFPCModelMesh*,unsigned,const void**,size_t*);
/* Float origin x/y plus normalized UVQ base/dx/dy (11 floats), exact triangle. */
NFPC_API int nf_pc_model_mesh_plane(const NFPCModelMesh*,unsigned triangle,float out[11]);
#endif

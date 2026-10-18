#ifndef NF_PC_RECIPE_MESH_H
#define NF_PC_RECIPE_MESH_H
#include "recipe_geometry.h"
typedef struct NFPCRecipeMesh NFPCRecipeMesh;
NFR_API NFPCRecipeMesh*nf_pc_recipe_mesh_ring(const double*ring,unsigned count,size_t maximum);
NFR_API void nf_pc_recipe_mesh_free(NFPCRecipeMesh*);
/* original ring vertices,triangle vertices,bytes. Empty/degenerate ring valid. */
NFR_API int nf_pc_recipe_mesh_info(const NFPCRecipeMesh*,uint64_t out[3]);
/* Borrowed x,y,u*q,v*q,q float vertices; lifetime mesh. */
NFR_API int nf_pc_recipe_mesh_vertices(const NFPCRecipeMesh*,const void**,size_t*);
NFR_API int nf_pc_recipe_mesh_plane(const NFPCRecipeMesh*,unsigned triangle,float out[11]);
#endif

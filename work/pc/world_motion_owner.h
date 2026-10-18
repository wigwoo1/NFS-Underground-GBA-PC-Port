#ifndef NF_PC_WORLD_MOTION_OWNER_H
#define NF_PC_WORLD_MOTION_OWNER_H
#include "world_mesh.h"
typedef struct NFPCWorldMotionOwner NFPCWorldMotionOwner;
enum {NFPC_MOTION_SHARED=1,NFPC_MOTION_OLDER_ONLY=2,NFPC_MOTION_AMBIGUOUS=3,NFPC_MOTION_CHANGED=4,NFPC_MOTION_UNSUPPORTED=5};
/* Source owners = epoch,serial,begin,end,page. Checks both packet bindings.
   Owns two endpoint worlds and one interior camera clone prepared ONCE.
   Retained budget<=64MiB; temporary packet copy is separately <=input size.
   This maps source identity only; it does not choose full-scene visibility. */
NFPC_API NFPCWorldMotionOwner* nf_pc_world_motion_owner_prepare(const void*,size_t,const uint64_t[5],const void*,size_t,const uint64_t[5],double,size_t);
NFPC_API void nf_pc_world_motion_owner_free(NFPCWorldMotionOwner*);
/* epoch,old refresh,new refresh,old count,new count,retained bytes,decodes,
   shared,old-only,new-only,ambiguous,changed,unsupported,mesh requests */
NFPC_API int nf_pc_world_motion_owner_info(const NFPCWorldMotionOwner*,uint64_t[14]);
/* status,new surface index (UINT32_MAX if absent),source kind */
NFPC_API int nf_pc_world_motion_owner_match(const NFPCWorldMotionOwner*,unsigned,uint64_t[3]);
/* Only unique compatible shared surfaces produce a mesh. Unmatched/changed
   visibility requires an explicit caller policy, never silent omission. */
NFPC_API NFPCWorldMesh* nf_pc_world_motion_owner_mesh(NFPCWorldMotionOwner*,unsigned,size_t);
/* Borrowed corresponding material world/index; older until exact alpha1.
   Valid only until owner free. Renderer palette/owner clipping is separate. */
NFPC_API int nf_pc_world_motion_owner_material(const NFPCWorldMotionOwner*,unsigned,const NFPCWorld**,unsigned*);
/* Source-class mesh path, alpha<1 only: never selects a newer duplicate.
   Every alias in BOTH worlds must have identical original identity,static3D
   vertices/UV/layout and no fixed-camera record. Common source camera was
   validated for the entire owner. Rebuilds each OLDER surface independently
   using the sampled owner camera; preserves all older commands/materials/order.
   At alpha1 caller must submit the complete newer endpoint scene. This does
   not choose visibility or solve retained road/wall/HUD/sky composition. */
NFPC_API NFPCWorldMesh* nf_pc_world_motion_owner_class_mesh(NFPCWorldMotionOwner*,unsigned older_surface,size_t);
NFPC_API int nf_pc_world_motion_owner_class_material(const NFPCWorldMotionOwner*,unsigned,const NFPCWorld**,unsigned*);
#endif

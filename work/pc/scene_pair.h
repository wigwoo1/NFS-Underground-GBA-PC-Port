#ifndef NF_PC_SCENE_PAIR_H
#define NF_PC_SCENE_PAIR_H
#include "source_scene.h"
typedef struct NFPCScenePair NFPCScenePair;
enum {NFPC_PAIR_SHARED=1,NFPC_PAIR_OLDER_ONLY=2,NFPC_PAIR_NEWER_ONLY=3,NFPC_PAIR_AMBIGUOUS=4,NFPC_PAIR_HELD_OWNER=5};
enum {NFPC_PAIR_METADATA_CHANGED=1,NFPC_PAIR_ORDER_CHANGED=2};
/* Owned identity map, not a scene/pose sampler. Same epoch, forward scene gap
   <=8, unchanged owner partition. Each owner must be held exactly, or advance
   serial and end-refresh by<=8. Page flips are retained, not used as identity.
   Matching uses owner ROLE and copied original identity only. Duplicates never
   choose a target. Every old/new command is represented, including ambiguity.
   Zero metadata flags does NOT prove local geometry/material compatibility. */
NFPC_API NFPCScenePair* nf_pc_scene_pair_prepare(const NFPCScene*,const NFPCScene*,size_t maximum_bytes);
NFPC_API void nf_pc_scene_pair_free(NFPCScenePair*);
/* epoch,old/new refresh,old/new count,rows,shared,old-only,new-only,ambiguous
   rows,held rows,metadata-changed rows,reordered rows,allocated bytes,owners,cut */
NFPC_API int nf_pc_scene_pair_info(const NFPCScenePair*,uint64_t out[16]);
/* status,old index,new index,owner role,flags,old order,new order,source kind.
   Missing indices/orders use UINT32_MAX. Identity copied into five32bit fields.
   Map owns all data and survives scene/frame/core destruction. Invalid getter
   arguments leave every output untouched. No borrowed scene pointers. */
NFPC_API int nf_pc_scene_pair_row(const NFPCScenePair*,unsigned,uint64_t out[8],uint32_t identity[5]);
NFPC_API int nf_pc_scene_pair_owner(const NFPCScenePair*,unsigned,unsigned endpoint,uint64_t out[5]);
#endif

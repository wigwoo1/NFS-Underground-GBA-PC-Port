#ifndef NF_PC_SCENE_REGION_PAIR_H
#define NF_PC_SCENE_REGION_PAIR_H
#include "scene_pair.h"
typedef struct NFPCSceneRegionPair NFPCSceneRegionPair;
enum {NFPC_REGION_HELD=1,NFPC_REGION_FORWARD=2,NFPC_REGION_DISCONTINUITY=3};
enum {NFPC_PAIR_DISCONTINUITY=6,NFPC_PAIR_TEMPORAL_BREAK=4};
/* Owned source map across full/split display transitions. Union of endpoint
   owner cuts forms1..3 nonoverlapping [top,bottom) bands covering0..160.
   Each band chooses its actual old/new owner by pixel coverage, NOT owner role.
   Then matches copied original identities within that band only. Backward or
   excessively separated source times are flagged, never interpolated silently.
   Global epoch change or non-forward/>8 scene refresh still rejects. Budget
   <=256KiB, allocation includes worst-case mapping rows. No borrowed scenes.
   This is ownership/identity mapping, not a pose, visibility or pixel sampler. */
NFPC_API NFPCSceneRegionPair* nf_pc_scene_region_pair_prepare(const NFPCScene*,const NFPCScene*,size_t);
NFPC_API void nf_pc_scene_region_pair_free(NFPCSceneRegionPair*);
/* epoch,old/new refresh,old/new commands,rows,bands,shared,held,old-only,
   new-only,ambiguous,discontinuity matches,allocated bytes,old/new owners */
NFPC_API int nf_pc_scene_region_pair_info(const NFPCSceneRegionPair*,uint64_t out[16]);
/* top,bottom,old/new owner index,first row,row count,temporal mode,
   old/new command count. Row ranges belong exclusively to that band. */
NFPC_API int nf_pc_scene_region_pair_band(const NFPCSceneRegionPair*,unsigned,uint64_t out[9]);
/* status,old/new command index,band index,metadata/order/temporal flags,
   old/new command order,source kind; missing index/order=UINT32_MAX.
   Every active command on either side appears exactlyonce PER BAND; commands
   spanning multiple bands intentionally appear in multiple clipped row ranges.
   Source IDs never resolve duplicates by projected geometry or draw order. */
NFPC_API int nf_pc_scene_region_pair_row(const NFPCSceneRegionPair*,unsigned,uint64_t out[8],uint32_t identity[5]);
NFPC_API int nf_pc_scene_region_pair_owner(const NFPCSceneRegionPair*,unsigned band,unsigned endpoint,uint64_t out[5]);
#endif

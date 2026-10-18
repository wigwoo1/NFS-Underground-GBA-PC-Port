#ifndef NF_PC_RECIPE_COVERAGE_H
#define NF_PC_RECIPE_COVERAGE_H
#include "source_frame.h"
typedef struct NFPCRecipeCoverage NFPCRecipeCoverage;
/* Original history+ownership proof. kind NFPC_ROAD/NFPC_WALL. Deep owned;
   no snapshot/core pointers. Retained budget excludes decode scratch (at most
   38400*24-byte samples plus1024 asset descriptors on Windows x64).
   No motion reprojection or world-space visibility policy inferred here. */
NFPC_API NFPCRecipeCoverage*nf_pc_recipe_coverage_decode(const void*,size_t,const void*,size_t,const uint64_t owner[5],unsigned kind,unsigned top,unsigned bottom,size_t maximum_retained);
NFPC_API NFPCRecipeCoverage*nf_pc_source_recipe_coverage(const NFPCSourceFrame*,unsigned owner,unsigned kind,size_t maximum_retained);
NFPC_API void nf_pc_recipe_coverage_free(NFPCRecipeCoverage*);
/* Same ten metadata fields as source_retention; final field counts this object. */
NFPC_API int nf_pc_recipe_coverage_info(const NFPCRecipeCoverage*,uint64_t out[10]);
/* 0: unchanged source-index RGBA;1: original four-u32 source records.
   2: six-u64 records {cell,epoch,recipe-kind1/2,accepted ordinal,refresh,index}.
   Records sorted by cell. Key(epoch,recipe-kind,ordinal) binds exact snapshot
   writer; no claim a covered cell can be frozen or whole surface drawn in motion. */
NFPC_API int nf_pc_recipe_coverage_buffer(const NFPCRecipeCoverage*,unsigned,const void**,size_t*);
#endif

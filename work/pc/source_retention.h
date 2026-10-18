#ifndef NF_PC_SOURCE_RETENTION_H
#define NF_PC_SOURCE_RETENTION_H
#include "source_frame.h"
typedef struct NFPCRetention NFPCRetention;
/* Compact NRH1/NWH1 source commands plus NRP1 ownership proof. owner is
   epoch,serial,begin,end,page. kind is NFPC_ROAD or NFPC_WALL. No screen
   polygon matching or framebuffer sampling. All returned storage is owned.
   Budget counts retained allocation only; decode scratch is at most
   38400 samples plus 1024 asset descriptors (493568 bytes on Windows x64).
   Legacy NRJ1 history streams are not this source-frame format. */
NFPC_API NFPCRetention* nf_pc_retention_decode(const void* history,size_t history_bytes,const void* proof,size_t proof_bytes,const uint64_t owner[5],unsigned kind,unsigned top,unsigned bottom,size_t maximum_retained_bytes);
NFPC_API NFPCRetention* nf_pc_source_retention(const NFPCSourceFrame*,unsigned owner,unsigned kind,size_t maximum_retained_bytes);
NFPC_API void nf_pc_retention_free(NFPCRetention*);
/* epoch,serial,begin,end,page,kind,top,bottom,cells,requested retained bytes */
NFPC_API int nf_pc_retention_info(const NFPCRetention*,uint64_t out[10]);
/* 0: source-index RGBA240x160 (red=index,alpha=255 iff owned; index0 opaque).
   1: cell-sorted uint32 records {cell,zero-based asset,offset,refresh}.
   Historical palette lookup and GPU submission are separate. */
NFPC_API int nf_pc_retention_buffer(const NFPCRetention*,unsigned,const void**,size_t*);
/* Opt-in owned event-ordinal grid: one uint64 per source cell (307200 bytes),
   zero outside this kind's proof and requested row clip. Charged to the SAME
   maximum_retained_bytes budget. Ordinary decode allocation/ABI is unchanged.
   Borrows input only during decode; result can outlive input/core. This links
   original journal events, not historical geometry or material reconstruction. */
NFPC_API NFPCRetention* nf_pc_retention_decode_ordinals(const void*,size_t,const void*,size_t,const uint64_t owner[5],unsigned kind,unsigned top,unsigned bottom,size_t maximum_retained_bytes);
/* Immutable grid until object free. Count is 38400 uint64 entries, not bytes.
   Default objects and invalid arguments reject without output writes. */
NFPC_API int nf_pc_retention_ordinals(const NFPCRetention*,const uint64_t**,size_t*);
NFPC_API NFPCRetention* nf_pc_source_retention_ordinals(const NFPCSourceFrame*,unsigned owner,unsigned kind,size_t maximum_retained_bytes);
#endif

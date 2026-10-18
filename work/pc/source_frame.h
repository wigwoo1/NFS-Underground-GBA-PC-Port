#ifndef NF_PC_SOURCE_FRAME_H
#define NF_PC_SOURCE_FRAME_H
#include <stdint.h>
#include <stddef.h>
#ifdef _WIN32
#define NFPC_API __declspec(dllexport)
#else
#define NFPC_API
#endif
/* Borrowed core functions must remain loaded. Capture is called on its owner
   thread; returned frame owns all bytes and may outlive the core. No stepping. */
typedef size_t (*NFPCOwnerRead)(void*,uint64_t,unsigned,unsigned,unsigned,void*,size_t);
typedef struct {
 size_t size;void *core;int (*layer_info)(void*,uint64_t*);
 size_t (*background)(void*,uint64_t,unsigned,void*,size_t);
 NFPCOwnerRead geometry,road,wall,proof;uint64_t owner_thread;
} NFPCSourceAPI;
typedef struct NFPCSourceFrame NFPCSourceFrame;
/* Transfers exactly reported allocated bytes. Any non-NULL failure allocation
   is also released. The release provider DLL must outlive every frame. */
typedef size_t (*NFPCBackgroundTake)(void*,uint64_t,unsigned,void**);
typedef void (*NFPCOwnedRelease)(void*);
typedef size_t (*NFPCOwnerTake)(void*,uint64_t,unsigned,unsigned,unsigned,void**);
NFPC_API NFPCSourceFrame* nf_pc_source_frame_capture_take_sources(const NFPCSourceAPI*,size_t,NFPCBackgroundTake,NFPCOwnedRelease,NFPCOwnerTake,NFPCOwnedRelease);
NFPC_API NFPCSourceFrame* nf_pc_source_frame_capture_take_background(const NFPCSourceAPI*,size_t,NFPCBackgroundTake,NFPCOwnedRelease);
enum {NFPC_BACKGROUND=0,NFPC_GEOMETRY=1,NFPC_ROAD=2,NFPC_WALL=3,NFPC_PROOF=4};
/* Bind once on the same thread that opened the core. No rebinding. */
NFPC_API int nf_pc_source_api_bind_owner(NFPCSourceAPI*);
NFPC_API NFPCSourceFrame* nf_pc_source_frame_capture(const NFPCSourceAPI*,size_t maximum_bytes);
/* Optional timing provider uses the SAME core/owner thread as source reads.
   Returns exactly184 bytes:16 uint64 words documented by the timing probe,
   followed by the exact56-byte NFM2 camera. Owned copy, same64MiB total budget.
   Rejected provider/binding never silently falls back to an untimed frame. */
NFPC_API NFPCSourceFrame* nf_pc_source_frame_capture_timed(const NFPCSourceAPI*,size_t,NFPCOwnerRead timing);
NFPC_API NFPCSourceFrame* nf_pc_source_frame_capture_take_sources_timed(const NFPCSourceAPI*,size_t,NFPCBackgroundTake,NFPCOwnedRelease,NFPCOwnerTake,NFPCOwnedRelease,NFPCOwnerRead timing);
/* Immutable owned184-byte view, valid until frame free. Default capture or
   invalid arguments reject without modifying outputs. No core callbacks. */
NFPC_API int nf_pc_source_frame_pose_timing(const NFPCSourceFrame*,unsigned owner,const void**,size_t*);
NFPC_API void nf_pc_source_frame_free(NFPCSourceFrame*);
/* Metadata epoch,refresh,kind,splitRow,ownerCount,allocatedBytes,serial0,serial1. */
NFPC_API int nf_pc_source_frame_info(const NFPCSourceFrame*,uint64_t out[8]);
/* Owner epoch,serial,begin,end,page. */
NFPC_API int nf_pc_source_frame_owner(const NFPCSourceFrame*,unsigned,uint64_t out[5]);
/* Read-only views, valid until free. Background includes original display
   provenance/layers/sky; renderer uses separate SOURCE geometry, never the
   embedded legacy geometry. Deep material decoding is a renderer dependency. */
NFPC_API int nf_pc_source_frame_component(const NFPCSourceFrame*,unsigned owner,unsigned kind,const void**bytes,size_t*size);
#endif

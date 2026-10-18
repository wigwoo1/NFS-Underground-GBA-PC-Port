#ifndef NF_PC_SOURCE_READER_H
#define NF_PC_SOURCE_READER_H
#include "source_frame.h"
typedef struct NFPCSourceReader NFPCSourceReader;
/* Owner-thread-only, borrowed core/API remains loaded. A bounded reusable
   scratch packet avoids rebuilding packets for size then copy. Scratch is
   separate from the returned frame's retained-allocation budget. */
NFPC_API NFPCSourceReader* nf_pc_source_reader_open(const NFPCSourceAPI*,size_t scratch_bytes);
/* Opt-in transfer; release provider DLL must outlive every frame. */
NFPC_API NFPCSourceReader* nf_pc_source_reader_open_owned_background(const NFPCSourceAPI*,size_t,NFPCBackgroundTake,NFPCOwnedRelease);
NFPC_API NFPCSourceReader* nf_pc_source_reader_open_owned_sources(const NFPCSourceAPI*,size_t,NFPCBackgroundTake,NFPCOwnedRelease,NFPCOwnerTake,NFPCOwnedRelease);
NFPC_API int nf_pc_source_reader_owned_geometry_info(const NFPCSourceReader*,uint64_t out[3]);
/* Core must guarantee stable cheap cached size/query writes on its owner thread.
   No scratch allocation; background/geometry still use immutable ownership transfer. */
NFPC_API NFPCSourceReader* nf_pc_source_reader_open_direct_sources(const NFPCSourceAPI*,size_t,NFPCBackgroundTake,NFPCOwnedRelease,NFPCOwnerTake,NFPCOwnedRelease);
/* cached size-query attempts, successful final writes, final write bytes. */
NFPC_API int nf_pc_source_reader_direct_cached_info(const NFPCSourceReader*,uint64_t out[3]);
/* attempts, successful transfers, bytes. */
NFPC_API int nf_pc_source_reader_owned_background_info(const NFPCSourceReader*,uint64_t out[3]);
NFPC_API NFPCSourceFrame* nf_pc_source_reader_capture(NFPCSourceReader*,size_t maximum_frame_bytes);
NFPC_API void nf_pc_source_reader_close(NFPCSourceReader*);
/* scratch bytes,raw packet builds,cached copies,failed packet builds,
   bytes copied,largest packet,completed frames,failed frames */
NFPC_API int nf_pc_source_reader_info(const NFPCSourceReader*,uint64_t out[8]);
/* out[0] is UINT64_MAX when capture failed before a raw-packet reader reported a bad packet. */
NFPC_API int nf_pc_source_reader_last_failure(const NFPCSourceReader*,uint64_t out[6]);
#endif

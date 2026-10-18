#ifndef NF_PC_WRITER_ADDRESS_MAP_H
#define NF_PC_WRITER_ADDRESS_MAP_H
#include "recipe_writer.h"
typedef struct NFPCWriterAddressMap NFPCWriterAddressMap;
/* Original command destinations -> raw SOURCE BYTE OFFSETS, not cached indices
   or framebuffer colors. Deep-owned compact rectangle; zero entry=no write,
   nonzero RGBA little-byte integer=offset+1. Retained budget excludes153600-byte
   temporary address scratch. Original integer source-cell reference only. */
NFR_API NFPCWriterAddressMap*nf_pc_writer_address_map(const NFPCRecipeWriter*,size_t maximum);
NFR_API void nf_pc_writer_address_map_free(NFPCWriterAddressMap*);
/* writer metadata first9;left,right,top,bottom,max_encoded_offset,bytes */
NFR_API int nf_pc_writer_address_map_info(const NFPCWriterAddressMap*,uint64_t out[15]);
NFR_API int nf_pc_writer_address_map_buffer(const NFPCWriterAddressMap*,const void**,size_t*);
#endif

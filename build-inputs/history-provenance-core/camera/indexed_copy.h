#ifndef NF_INDEXED_COPY_H
#define NF_INDEXED_COPY_H
#include <stddef.h>
#include <stdint.h>
typedef int (*NFIndexedCopyRead)(void*,uint32_t,void*,size_t);
/* NFCI v1 owns a contiguous indexed ROM-copy operation. Verified original
   ABI only: width240,height63,source/destination stride240. Includes the
   original unrolled16-byte tail; never reads a rendered framebuffer. */
__declspec(dllexport) int nf_indexed_copy_create(NFIndexedCopyRead,void*,uint32_t source,uint32_t destination,uint32_t width,uint32_t height,uint32_t source_stride,uint32_t destination_stride,void**out,size_t*size);
__declspec(dllexport) int nf_indexed_copy_view(const void*,size_t,uint32_t*page,uint32_t*offset,const uint8_t**indices,size_t*count);
__declspec(dllexport) void nf_indexed_copy_free(void*);
/* Owned original32-byte-block fill; bytes must be a positive multiple32. */
__declspec(dllexport) int nf_indexed_fill_create(uint32_t destination,uint32_t value,uint32_t bytes,void**out,size_t*size);
__declspec(dllexport) int nf_indexed_operation_view(const void*,size_t,uint32_t*kind,uint32_t*page,uint32_t*offset,const uint8_t**indices,size_t*count);
#endif

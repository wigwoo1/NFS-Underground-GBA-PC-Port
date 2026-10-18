#ifndef NFS_NATIVE_SPAN_H
#define NFS_NATIVE_SPAN_H
#include <stddef.h>
#include <stdint.h>
typedef struct {
 uint32_t width_shift,u_mask,v_mask;
 uint32_t u,v,du,dv,count;
 int duplicate_row;
} NfsSpan;
/* Recovered from ROM 0x080771e4, relocated at runtime to 0x030056d8.
   Output consists of packed 8-bit palette index pairs, not RGB565. */
int nfs_draw_span(uint8_t* dst,size_t dst_size,const uint8_t* tex,size_t tex_size,NfsSpan* span);
#endif

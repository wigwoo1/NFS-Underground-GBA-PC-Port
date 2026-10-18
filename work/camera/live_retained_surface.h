#ifndef NF_LIVE_RETAINED_SURFACE_H
#define NF_LIVE_RETAINED_SURFACE_H
#include <stdint.h>
#include <stddef.h>
/* Research bridge only; requires live visibility plus surface audit enabled.
   Last two completed scenes. Caller owns successful outputs; release both
   using nf_surface_free. Road lighting may be NULL with zero bytes.
   Identity/index/failure leaves all output slots unchanged. Single-threaded,
   call after nf_frame or at scene delivery; no emulator reentry. */
int nf_live_completed_surface_extract(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,unsigned ordinal,void**surface,size_t*bytes,void**lighting,size_t*lighting_bytes);
#endif

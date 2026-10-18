#ifndef NF_ROAD_POLYGON_CLIP_H
#define NF_ROAD_POLYGON_CLIP_H
#include <stdint.h>
#include <stddef.h>
/* Original horizontal clipping of owned projected six-word road vertices.
   Output and count are unchanged on failure. Capacity is vertex count.
   This helper does not generate visibility, vertical spans, or game timing. */
int nf_road_polygon_clip(const int32_t *input,unsigned count,int32_t left,int32_t right,const uint32_t *reciprocal,int32_t *out,unsigned capacity,unsigned *out_count);
/* Returns1 with edge context,0 when exhausted,-1 for invalid inputs.
   No output publication on0/-1. Does not write a framebuffer. */
int nf_road_edge_step(const uint32_t context[18],unsigned side,unsigned orientation,const int32_t *vertices,unsigned count,const uint32_t reciprocal[32768],const uint32_t framebuffer[4],uint32_t out[18]);
/* Four words per coverage span: destination,width,writer routine,doubled-row.
   Atomic output; no texture evaluation or framebuffer writes. */
int nf_road_span_plan(const int32_t *vertices,unsigned count,int32_t top,int32_t bottom,unsigned orientation,unsigned affine,const uint32_t reciprocal[32768],const uint32_t framebuffer[4],uint32_t *out,unsigned capacity,unsigned *out_count);
/*20words per span: four coverage words followed by16texture-context words.
   Material seed supplies masks,texture address and animation UV offsets. */
int nf_road_span_contexts(const int32_t *v,unsigned n,int32_t t,int32_t b,unsigned o,unsigned a,const uint32_t r[32768],const uint32_t f[4],const uint32_t material[16],uint32_t *out,unsigned cap,unsigned *count);
/* Owned reader supplies resolved16bit texture. Only colors are published;
   destination and doubled-row coverage are handled by the span scheduler. */
int nf_road_span_pixels(const uint32_t params[12],int (*read)(void*,uint32_t,void*,size_t),void *context,uint16_t *out,unsigned capacity);
/* Atomic16word contexts for perspective16sample subspans and final context.
   Capacity is subspan count. Does not write texture/framebuffer memory. */
int nf_road_perspective_plan(const uint32_t params[16],const uint32_t reciprocal[32768],uint32_t *out,unsigned capacity,unsigned *out_count,uint32_t final[16]);
/* Primary road material/animation seed from owned state tables. Atomic. */
int nf_road_material_seed(const uint8_t state[256],const uint8_t descriptor[48],int (*read)(void*,uint32_t,void*,size_t),void *context,uint32_t out[16]);
/* Derive continuous clip bottom from native20word spans. Retains other bounds.
   Fixed source framebuffer240bytes/row,160rows. Accepts native two-byte right padding and doubled final row, caps visible bottom160. Atomic publication. */
int nf_road_clip_bounds(const uint16_t inherited[4],const uint32_t framebuffer[4],const uint32_t *spans,unsigned count,uint16_t out[4],unsigned *cell_end);
int nf_road_spans_write(const uint32_t*,unsigned,int(*)(void*,uint32_t,void*,size_t),void*,uint8_t*,size_t);
int nf_road_draw_runs(const int32_t*,unsigned,const int32_t[4],unsigned,unsigned,const uint32_t*,uint32_t,const uint8_t*,const uint32_t[2],uint32_t*,unsigned,unsigned*);
#endif

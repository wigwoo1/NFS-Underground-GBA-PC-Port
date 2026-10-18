#ifndef NF_HASH_REGION_H
#define NF_HASH_REGION_H
#include <stddef.h>
#include <stdint.h>

static inline uint32_t nf_hash_u32_region(const uint32_t* pixels,unsigned frame_width,unsigned frame_height,unsigned x,unsigned y,unsigned width,unsigned height){
 if(!pixels||!frame_width||!frame_height||!width||!height||x>=frame_width||y>=frame_height||width>frame_width-x||height>frame_height-y)return 0;
 uint32_t hash=2166136261u;
 for(unsigned row=y;row<y+height;row++)for(unsigned col=x;col<x+width;col++)hash=(hash^pixels[(size_t)row*frame_width+col])*16777619u;
 return hash;
}
#endif

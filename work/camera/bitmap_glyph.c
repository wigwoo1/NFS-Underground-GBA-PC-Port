#include "bitmap_glyph.h"
#include <string.h>
int nf_bitmap_glyph_decode(const NFBitmapGlyph*g,const uint8_t*asset,size_t bytes,uint8_t*indices,uint8_t*coverage,size_t capacity){
 if(!g||!asset||!indices||!coverage||!g->width||!g->height||g->width>256||g->height>256||g->draw_width>g->width||g->stride<g->draw_width||g->stride>0x10000||g->flags>1||g->transparent>255||g->palette_offset>255)return 0;
 size_t size=(size_t)g->width*g->height;if(size>4096||bytes!=size||capacity<size)return 0;
 uint8_t decoded[4096]={0},writes[4096]={0};
 for(unsigned y=0;y<g->height;y++)for(unsigned x=0;x<g->draw_width;x++){
  unsigned i=y*g->width+x,index=asset[i];
  if((g->flags&1)&&index==g->transparent)continue;
  decoded[i]=(uint8_t)(index+g->palette_offset);writes[i]=1;
 }
 memcpy(indices,decoded,size);memcpy(coverage,writes,size);return 1;
}

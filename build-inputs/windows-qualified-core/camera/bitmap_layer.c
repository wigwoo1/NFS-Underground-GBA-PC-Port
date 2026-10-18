#include "bitmap_layer.h"
#include <stdlib.h>
#include <string.h>
struct NFBitmapLayer{uint64_t epoch;uint8_t indices[2][38400],coverage[2][38400];};
NFBitmapLayer*nf_bitmap_layer_create(uint64_t epoch){if(!epoch)return NULL;NFBitmapLayer*s=calloc(1,sizeof(*s));if(s)s->epoch=epoch;return s;}
void nf_bitmap_layer_destroy(NFBitmapLayer*s){free(s);}
int nf_bitmap_layer_reset(NFBitmapLayer*s,uint64_t epoch){if(!s||!epoch)return 0;memset(s,0,sizeof(*s));s->epoch=epoch;return 1;}
int nf_bitmap_layer_glyph(NFBitmapLayer*s,uint64_t epoch,uint32_t address,const NFBitmapGlyph*g,const uint8_t*a,size_t bytes){
 if(!s||epoch!=s->epoch||!g||address<0x06000000||address>=0x06014000)return 0;
 unsigned page=address>=0x0600a000,offset=address-(0x06000000+page*0xa000);uint8_t indices[4096],coverage[4096];
 if(!nf_bitmap_glyph_decode(g,a,bytes,indices,coverage,4096))return 0;
 uint64_t end=(uint64_t)offset+(uint64_t)(g->height-1)*g->stride+g->draw_width;if(offset>=38400||end>38400)return 0;
 for(unsigned y=0;y<g->height;y++)for(unsigned x=0;x<g->draw_width;x++){unsigned src=y*g->width+x,dst=offset+y*g->stride+x;if(coverage[src]){s->indices[page][dst]=indices[src];s->coverage[page][dst]=1;}}
 return 1;
}
int nf_bitmap_layer_invalidate(NFBitmapLayer*s,uint64_t epoch,uint32_t address,size_t bytes){
 if(!s||epoch!=s->epoch||bytes>UINT32_MAX||(uint64_t)address+bytes>0x100000000ULL)return 0;
 uint64_t end=(uint64_t)address+bytes;
 for(unsigned page=0;page<2;page++){uint64_t base=0x06000000+page*0xa000,start=address>base?address:base,limit=end<base+38400?end:base+38400;if(start<limit)memset(s->coverage[page]+start-base,0,(size_t)(limit-start));}
 return 1;
}
int nf_bitmap_layer_plane(const NFBitmapLayer*s,uint64_t epoch,unsigned page,uint8_t*indices,uint8_t*coverage,size_t capacity){
 if(!s||epoch!=s->epoch||page>1||!indices||!coverage||capacity<38400)return 0;
 memcpy(indices,s->indices[page],38400);memcpy(coverage,s->coverage[page],38400);return 1;
}

int nf_bitmap_layer_row(const NFBitmapLayer*s,uint64_t epoch,unsigned page,unsigned row,uint8_t indices[240],uint8_t coverage[240]){if(!s||epoch!=s->epoch||page>1||row>=160||!indices||!coverage)return 0;memcpy(indices,s->indices[page]+row*240,240);memcpy(coverage,s->coverage[page]+row*240,240);return 1;}

unsigned nf_bitmap_layer_changed_mask(const NFBitmapLayer*s,uint64_t epoch,uint32_t address,uint32_t value,unsigned bytes){
 if(!s||epoch!=s->epoch||!bytes||bytes>4)return 0;
 unsigned mask=0;
 for(unsigned i=0;i<bytes;i++){
  uint64_t a=(uint64_t)address+i;if(a<0x06000000||a>=0x06014000)continue;
  unsigned page=a>=0x0600a000,offset=(unsigned)a-(0x06000000+page*0xa000);
  if(offset<38400&&s->coverage[page][offset]&&s->indices[page][offset]!=(uint8_t)(value>>(i*8)))mask|=1u<<i;
 }
 return mask;
}

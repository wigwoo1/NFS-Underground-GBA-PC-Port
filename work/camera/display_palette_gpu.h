#ifndef NF_DISPLAY_PALETTE_GPU_H
#define NF_DISPLAY_PALETTE_GPU_H
/* Immutable, row-major BG palette upload. Caller owns palette during this call;
   preview_texture synchronously copies RGBA to the context-owned GPU cache. */
static GLuint display_palette_texture(const uint16_t colors[160][256]){
 if(!colors)return 0;
 static GLuint cached;static uint64_t generation;static HGLRC context;static uint16_t previous[160][256];
 if(cached&&generation==preview_generation&&context==preview_context&&!memcmp(previous,colors,sizeof(previous)))return cached;
 uint8_t*rgba=malloc(160u*256u*4u);if(!rgba)return 0;
 for(unsigned y=0;y<160;y++)for(unsigned index=0;index<256;index++){
  unsigned color=colors[y][index];size_t at=((size_t)y*256+index)*4;
  for(unsigned k=0;k<3;k++)rgba[at+k]=((color>>(k*5))&31)*255/31;
  rgba[at+3]=255;
 }
 GLuint texture=preview_texture(256,160,rgba);free(rgba);
 if(texture){cached=texture;generation=preview_generation;context=preview_context;memcpy(previous,colors,sizeof(previous));}
 return texture;
}
#endif

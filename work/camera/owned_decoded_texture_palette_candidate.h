static uint8_t owned_palette_channel(unsigned value){return (uint8_t)((value<<3)|(value>>2));}
/* Bounded exact-source cache for indexed material expansion, renderer-owned. */
#define OWNED_DECODED_BUDGET (16u*1024u*1024u)
typedef struct {unsigned width,height,stride,transparent;uint8_t*source,*rgba;uint8_t palette[512];size_t source_bytes,bytes;uint64_t last;} OwnedDecoded;
static OwnedDecoded owned_decoded[32];static size_t owned_decoded_bytes;static uint64_t owned_decoded_clock,owned_decoded_hits,owned_decoded_misses;
static void owned_decoded_drop(unsigned i){OwnedDecoded*t=owned_decoded+i;if(t->source){owned_decoded_bytes-=t->bytes;free(t->source);free(t->rgba);memset(t,0,sizeof(*t));}}
static void owned_decoded_clear(void){for(unsigned i=0;i<32;i++)owned_decoded_drop(i);}
static GLuint owned_indexed_texture(unsigned w,unsigned h,unsigned stride,const uint8_t*source,const uint8_t*palette,unsigned transparent){
 if(!w||!h||stride<w||!source||!palette||w>1024||h>1024||stride>2048)return 0;
 size_t n=(size_t)stride*h,bytes=n+(size_t)w*h*4;
 if(bytes>OWNED_DECODED_BUDGET)return 0;
 uint64_t now=++owned_decoded_clock;
 for(unsigned i=0;i<32;i++){OwnedDecoded*t=owned_decoded+i;
  if(t->source&&t->width==w&&t->height==h&&t->stride==stride&&t->transparent==transparent&&!memcmp(t->palette,palette,512)&&!memcmp(t->source,source,n)){
   t->last=now;owned_decoded_hits++;return preview_texture(w,h,t->rgba);
  }
 }
 owned_decoded_misses++;
 unsigned slot=32;
 while(slot==32||owned_decoded_bytes+bytes>OWNED_DECODED_BUDGET){
  slot=32;for(unsigned i=0;i<32;i++)if(!owned_decoded[i].source){slot=i;break;}
  if(slot<32&&owned_decoded_bytes+bytes<=OWNED_DECODED_BUDGET)break;
  unsigned oldest=32;for(unsigned i=0;i<32;i++)if(owned_decoded[i].source&&(oldest==32||owned_decoded[i].last<owned_decoded[oldest].last))oldest=i;
  if(oldest==32)return 0;owned_decoded_drop(oldest);
 }
 uint8_t*copy=malloc(n),*rgba=malloc((size_t)w*h*4);if(!copy||!rgba){free(copy);free(rgba);return 0;}
 memcpy(copy,source,n);
 for(unsigned y=0;y<h;y++)for(unsigned x=0;x<w;x++){unsigned j=y*w+x,index=source[y*stride+x];uint16_t color;memcpy(&color,palette+index*2,2);rgba[j*4]=owned_palette_channel(color&31);rgba[j*4+1]=owned_palette_channel((color>>5)&31);rgba[j*4+2]=owned_palette_channel((color>>10)&31);rgba[j*4+3]=(transparent&&!index)?0:255;}
 OwnedDecoded*t=owned_decoded+slot;t->width=w;t->height=h;t->stride=stride;t->transparent=transparent;t->source=copy;t->rgba=rgba;t->source_bytes=n;t->bytes=bytes;t->last=now;memcpy(t->palette,palette,512);owned_decoded_bytes+=bytes;
 return preview_texture(w,h,rgba);
}
__declspec(dllexport) void nf_owned_decoded_texture_stats(uint64_t out[3]){if(out){out[0]=owned_decoded_hits;out[1]=owned_decoded_misses;out[2]=owned_decoded_bytes;}}

#include "draw_palette.h"
#include <stdlib.h>
#include <string.h>
struct NFDrawPalettes {
 uint64_t epoch;uint32_t serial;unsigned sealed,count,unique;
 struct {uint32_t kind,source,material,palette;} draws[256];
 uint8_t palettes[64][512];
};
NFDrawPalettes* nf_draw_palettes_create(uint64_t epoch,uint32_t serial){
 if(!epoch)return NULL;
 NFDrawPalettes*p=calloc(1,sizeof(*p));if(p){p->epoch=epoch;p->serial=serial;}return p;
}
void nf_draw_palettes_destroy(NFDrawPalettes*p){free(p);}
int nf_draw_palettes_append(NFDrawPalettes*p,uint32_t kind,uint32_t source,uint32_t material,const void*palette,size_t size){
 if(!p||p->sealed||p->count==256||!palette||size!=512)return 0;
 unsigned i=0;for(;i<p->unique;i++)if(!memcmp(p->palettes[i],palette,512))break;
 if(i==64)return 0;
 if(i==p->unique){memcpy(p->palettes[i],palette,512);p->unique++;}
 p->draws[p->count].kind=kind;p->draws[p->count].source=source;p->draws[p->count].material=material;p->draws[p->count].palette=i;p->count++;return 1;
}
int nf_draw_palettes_seal(NFDrawPalettes*p){if(!p||p->sealed)return 0;p->sealed=1;return 1;}
int nf_draw_palettes_read(const NFDrawPalettes*p,uint64_t epoch,uint32_t serial,unsigned draw,uint32_t kind,uint32_t source,uint32_t material,void*out,size_t size){
 if(!p||!p->sealed||p->epoch!=epoch||p->serial!=serial||draw>=p->count||!out||size!=512)return 0;
 if(p->draws[draw].kind!=kind||p->draws[draw].source!=source||p->draws[draw].material!=material)return 0;
 memcpy(out,p->palettes[p->draws[draw].palette],512);return 1;
}
int nf_draw_palettes_info(const NFDrawPalettes*p,unsigned*draws,unsigned*palettes,size_t*bytes){
 if(!p||!draws||!palettes||!bytes)return 0;
 *draws=p->count;*palettes=p->unique;*bytes=sizeof(*p);return 1;
}

int nf_draw_palettes_key(const NFDrawPalettes*p,unsigned draw,uint32_t out[3]){
 if(!p||!p->sealed||draw>=p->count||!out)return 0;
 uint32_t key[3]={p->draws[draw].kind,p->draws[draw].source,p->draws[draw].material};memcpy(out,key,12);return 1;
}

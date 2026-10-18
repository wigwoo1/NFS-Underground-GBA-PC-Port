#include "source_background.h"
#include <string.h>
typedef struct {const unsigned char*p;size_t n;} View;
static uint64_t q(const void*p,size_t at){uint64_t v;memcpy(&v,(const unsigned char*)p+at,8);return v;}
static uint16_t h(const void*p,size_t at){uint16_t v;memcpy(&v,(const unsigned char*)p+at,2);return v;}
static int part(View b,unsigned i,View*v){if(b.n<128||i>3)return 0;uint64_t at=q(b.p,64+i*16),n=q(b.p,72+i*16);if(at>b.n||n>b.n-at)return 0;v->p=b.p+at;v->n=(size_t)n;return 1;}
static int inputs(const NFPCSourceFrame*f,uint64_t info[8],View*root,View*sky,View*layers){const void*p;size_t n;View nab;if(!nf_pc_source_frame_info(f,info)||!nf_pc_source_frame_component(f,0,NFPC_BACKGROUND,&p,&n))return 0;root->p=p;root->n=n;if(!part(*root,0,sky)||!part(*sky,0,&nab)||!part(nab,2,layers)||layers->n<28512)return 0;return 1;}
static void color(const unsigned char*p,unsigned char*out){uint16_t c=h(p,0);for(unsigned channel=0;channel<3;channel++){unsigned v=(c>>(channel*5))&31;out[channel]=(unsigned char)((v<<3)|(v>>2));}out[3]=255;}
static const unsigned char* palette(View layers,unsigned y){unsigned ref=h(layers.p,20512+(y*25+24)*2);return layers.p+28512+ref*4096;}
int nf_pc_source_palette_rgba(const NFPCSourceFrame*f,void*out,size_t size){View root,sky,layers;uint64_t info[8];if(!out||size<256u*160*4||!inputs(f,info,&root,&sky,&layers))return 0;unsigned char*p=out;for(unsigned y=0;y<160;y++)for(unsigned index=0;index<256;index++)color(palette(layers,y)+index*2,p+(y*256+index)*4);return 1;}
static int expand(const NFPCSourceFrame*f,void*out,size_t size,int sky_only){View root,sky,layers,bg[2],source[2];uint64_t info[8];if(!out||size<240u*160*4||!inputs(f,info,&root,&sky,&layers))return 0;for(unsigned i=0;i<info[4];i++)if(!part(root,i+1,&bg[i])||bg[i].n!=76880||!part(sky,i+1,&source[i])||source[i].n!=30568)return 0;unsigned char*p=out;memset(p,0,240u*160*4);for(unsigned y=0;y<160;y++){unsigned owner=info[2]==2&&y>=info[3]?1:0;const unsigned char*pal=palette(layers,y);for(unsigned x=0;x<240;x++){unsigned cell=y*240+x,index;if(sky_only){if(cell<10560||cell>=10560+15136)continue;index=source[owner].p[56+cell-10560];}else{if(!bg[owner].p[38480+cell])continue;index=bg[owner].p[80+cell];}color(pal+index*2,p+cell*4);}}return 1;}
int nf_pc_source_background_rgba(const NFPCSourceFrame*f,void*out,size_t size){return expand(f,out,size,0);}
int nf_pc_source_sky_rgba(const NFPCSourceFrame*f,void*out,size_t size){return expand(f,out,size,1);}

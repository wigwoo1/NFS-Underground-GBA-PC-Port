#include "source_hud.h"
#include "../camera/obj_tile.h"
#include <stdlib.h>
#include <string.h>
#define ROW_BYTES 100480u
#define LIMIT (64u*1024*1024)
struct NFPCHud {uint64_t info[5];uint32_t colors[38400],metadata[38400],parameters[160][5];};
static uint16_t h(const void*p,size_t at){uint16_t v;memcpy(&v,(const unsigned char*)p+at,2);return v;}
static uint32_t u(const void*p,size_t at){uint32_t v;memcpy(&v,(const unsigned char*)p+at,4);return v;}
static uint64_t q(const void*p,size_t at){uint64_t v;memcpy(&v,(const unsigned char*)p+at,8);return v;}
static uint32_t color(unsigned c){unsigned r=c&31,g=(c>>5)&31,b=(c>>10)&31;return 0xff000000u|((r<<3)|(r>>2))|(((g<<3)|(g>>2))<<8)|(((b<<3)|(b>>2))<<16);}
int nf_pc_hud_row(const void*input,size_t bytes,unsigned y,uint32_t out[240],uint32_t metadata[240],uint32_t parameters[5]){
 if(!input||bytes!=ROW_BYTES||y>=160||u(input,4)!=y||!out||!metadata||!parameters)return 0;
 const unsigned char*b=input,*r=b+8,*v=b+128,*p=v+98304,*o=p+1024;unsigned display=h(r,0),blend=h(r,0x50),alpha=h(r,0x52),brightness=h(r,0x54);if((display&0x8080)||(display&7)!=4)return 0;
 uint16_t window[6];for(unsigned i=0;i<6;i++)window[i]=h(r,64+i*2);uint32_t colors[240],tags[240],meta[240],params[5];uint8_t visible[240],backdrop[240];
 if(!nf_obj_window_scanline_prepared(v,98304,p,1024,o,1024,(uint16_t)display,y,window,blend,brightness,colors,tags,visible,backdrop))return 0;
 for(unsigned x=0;x<240;x++){unsigned control=visible[x];if(!(display&0x400))control&=~4u;unsigned flags=128|control|((backdrop[x]&32)?64:0);meta[x]=0xff000000u|(flags<<16)|(tags[x]&3)|(((tags[x]>>2)&3)<<8);}
 params[0]=color(h(p,0));params[1]=h(r,12)&3;params[2]=blend;params[3]=alpha;params[4]=brightness;memcpy(out,colors,sizeof(colors));memcpy(metadata,meta,sizeof(meta));memcpy(parameters,params,sizeof(params));return 1;
}
NFPCHud* nf_pc_hud_decode_layers(const void*input,size_t bytes,uint64_t epoch,uint64_t refresh,size_t maximum){
 if(!input||bytes<28512||bytes>LIMIT||!epoch||epoch>INT64_MAX||refresh>UINT32_MAX||maximum<sizeof(NFPCHud)||maximum>LIMIT)return NULL;
 const unsigned char*b=input;uint32_t pages=u(b,16);if(u(b,0)!=0x31504c4e||u(b,4)!=1||u(b,8)!=bytes||u(b,12)!=160||!pages||pages>4000||u(b,20)!=25||u(b,24)!=4096||u(b,28)!=refresh||bytes!=28512+(size_t)pages*4096)return NULL;
 /* Validate ALL references before using any page, even if its OBJ is disabled. */
 for(unsigned y=0;y<160;y++){if(u(b,32+y*128)!=refresh||u(b,36+y*128)!=y)return NULL;for(unsigned part=0;part<25;part++)if(h(b,20512+(y*25+part)*2)>=pages)return NULL;}
 NFPCHud*f=calloc(1,sizeof(*f));unsigned char*row=malloc(ROW_BYTES);if(!f||!row)goto fail;f->info[0]=epoch;f->info[1]=refresh;f->info[2]=160;f->info[4]=sizeof(*f);
 for(unsigned y=0;y<160;y++){memcpy(row,b+32+y*128,128);for(unsigned part=0;part<25;part++){unsigned ref=h(b,20512+(y*25+part)*2);memcpy(row+128+part*4096,b+28512+ref*4096,part==24?2048:4096);}if(!nf_pc_hud_row(row,ROW_BYTES,y,f->colors+y*240,f->metadata+y*240,f->parameters[y]))goto fail;for(unsigned x=0;x<240;x++)f->info[3]+=f->colors[y*240+x]!=0;}
 free(row);return f;
fail:free(row);free(f);return NULL;
}
static int part(const void*input,size_t bytes,unsigned index,const void**out,size_t*n){if(!input||bytes<128||index>3)return 0;uint64_t at=q(input,64+index*16),count=q(input,72+index*16);if(at>bytes||count>bytes-at)return 0;*out=(const unsigned char*)input+at;*n=(size_t)count;return 1;}
NFPCHud* nf_pc_source_hud(const NFPCSourceFrame*f,size_t maximum){uint64_t info[8];const void*root,*sky,*nab,*layers;size_t n,sn,nn,ln;if(!nf_pc_source_frame_info(f,info)||!nf_pc_source_frame_component(f,0,NFPC_BACKGROUND,&root,&n)||!part(root,n,0,&sky,&sn)||!part(sky,sn,0,&nab,&nn)||!part(nab,nn,2,&layers,&ln))return NULL;return nf_pc_hud_decode_layers(layers,ln,info[0],info[1],maximum);}
void nf_pc_hud_free(NFPCHud*f){free(f);}
int nf_pc_hud_info(const NFPCHud*f,uint64_t out[5]){if(!f||!out)return 0;memcpy(out,f->info,sizeof(f->info));return 1;}
int nf_pc_hud_buffer(const NFPCHud*f,unsigned kind,const void**p,size_t*n){if(!f||kind>2||!p||!n)return 0;*p=kind==0?(const void*)f->colors:kind==1?(const void*)f->metadata:f->parameters;*n=kind==2?sizeof(f->parameters):sizeof(f->colors);return 1;}

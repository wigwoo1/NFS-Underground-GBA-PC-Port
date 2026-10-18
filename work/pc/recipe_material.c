#include "recipe_material.h"
#include <stdlib.h>
#include <string.h>
struct NFPCRecipeMaterial{uint64_t info[5];unsigned char data[];};
static unsigned half(const void*p,unsigned at){uint16_t v;memcpy(&v,(const unsigned char*)p+at,2);return v;}
NFPCRecipeMaterial*nf_pc_recipe_material_decode(unsigned kind,const NFRecipeBlock*b,unsigned count,size_t maximum){
 if((kind!=1&&kind!=2)||!b||count!=15||maximum>64u*1024*1024)return NULL;
 for(unsigned i=0;i<count;i++)if(!b[i].data||!b[i].bytes)return NULL;
 unsigned mat=kind==1?3:4,tex=kind==1?7:8;if(b[mat].bytes!=48)return NULL;unsigned shift=half(b[mat].data,36),stored=half(b[mat].data,38);if(shift>10||!stored||stored>1024||(kind==1&&(stored<2||(stored&1))))return NULL;unsigned width=1u<<shift,height=kind==1?stored/2:stored,shaded=kind==2&&b[13].bytes==4081;size_t pixels=(size_t)width*height,source_bytes=kind==1?(size_t)width*stored:pixels;
 if(b[tex].bytes<source_bytes||(kind==2&&b[13].bytes!=1&&b[13].bytes!=4081)||pixels>(SIZE_MAX-sizeof(NFPCRecipeMaterial))/6)return NULL;
 size_t bytes=sizeof(NFPCRecipeMaterial)+pixels*6;if(maximum<bytes)return NULL;NFPCRecipeMaterial*m=calloc(1,bytes);if(!m)return NULL;uint64_t info[5]={kind,width,height,shaded,bytes};memcpy(m->info,info,sizeof(info));const unsigned char*texture=b[tex].data,*lookup=b[13].data;
 for(unsigned y=0;y<height;y++)for(unsigned x=0;x<width;x++){size_t at=(size_t)y*width+x;unsigned src=texture[kind==1?(size_t)y*width*2+x:at],index=src,state;if(kind==2&&!src)state=0;else{if(shaded)index=lookup[src*16];state=index?2:1;}m->data[at]=(unsigned char)index;m->data[pixels+at]=(unsigned char)state;m->data[pixels*2+at*4]=(unsigned char)index;m->data[pixels*2+at*4+3]=state?255:0;}
 return m;
}
void nf_pc_recipe_material_free(NFPCRecipeMaterial*m){free(m);}
int nf_pc_recipe_material_info(const NFPCRecipeMaterial*m,uint64_t out[5]){if(!m||!out)return 0;memcpy(out,m->info,sizeof(m->info));return 1;}
int nf_pc_recipe_material_buffer(const NFPCRecipeMaterial*m,unsigned kind,const void**out,size_t*n){if(!m||kind>2||!out||!n)return 0;size_t pixels=m->info[1]*m->info[2];*out=m->data+(kind==0?0:kind==1?pixels:pixels*2);*n=kind==2?pixels*4:pixels;return 1;}

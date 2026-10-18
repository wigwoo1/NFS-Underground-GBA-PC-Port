#include "recipe_writer.h"
#include <stdlib.h>
#include <string.h>
struct NFPCRecipeWriter{uint64_t info[10];size_t texture_bytes,shade_bytes;uint32_t texture_address;unsigned command_bytes;unsigned char command[80],material[48],data[];};
static uint32_t u32(const void*p,size_t at){uint32_t v;memcpy(&v,(const unsigned char*)p+at,4);return v;}
static uint64_t u64(const void*p,size_t at){uint64_t v;memcpy(&v,(const unsigned char*)p+at,8);return v;}
static int road_offset(const NFPCRecipeWriter*w,unsigned index,unsigned lane,uint64_t*out){
 const unsigned char*c=w->command;uint32_t u=u32(c,32),v=u32(c,36),um=u32(c,4),vm=u32(c,8),du=u32(c,40),dv=u32(c,44);
 for(unsigned k=0;k<=index;k++){u&=um;v&=vm;if(k==index)break;u+=du;v+=dv;}
 uint64_t address=(uint64_t)u32(c,20)+2*((u>>16)+((uint64_t)(v>>16)<<u32(c,0)))+lane;if(address<w->texture_address||address-w->texture_address>=w->texture_bytes)return 0;*out=address-w->texture_address;return 1;
}
static void wall_start(const NFPCRecipeWriter*w,unsigned*shift,unsigned*uvshift,uint32_t*texture,uint32_t*dest){
 const unsigned char*c=w->command;*shift=u32(c,12);*uvshift=15;*texture=u32(c,36);if(u32(c,24)&&u32(c,44)>0x1b000u){*shift-=2;*uvshift=17;*texture+=u32(c,28);}*texture=(*texture+((u32(c,52)&u32(c,64))>>*uvshift))&~1u;*dest=u32(c,68)+((u32(c,8)*(u32(c,4)>>14))<<1);
}
NFPCRecipeWriter*nf_pc_recipe_writer_decode(const uint64_t owner[5],unsigned kind,uint64_t ordinal,unsigned write,const NFRecipeBlock*b,unsigned count,size_t maximum){
 if(!owner||!owner[0]||owner[0]>INT64_MAX||!owner[1]||owner[1]>UINT32_MAX||owner[2]>owner[3]||owner[3]>UINT32_MAX||owner[4]>1||(kind!=1&&kind!=2)||!ordinal||ordinal>INT64_MAX||write>owner[3]||!b||count!=15||maximum>64u*1024*1024)return NULL;
 for(unsigned i=0;i<count;i++)if(!b[i].data||!b[i].bytes)return NULL;
 unsigned material=kind==1?3:4,texture=kind==1?7:8,palette=kind==1?8:9;if(b[material].bytes!=48||b[palette].bytes!=512||b[texture].bytes>16u*1024*1024||b[14].bytes!=(kind==1?80u:64u))return NULL;const unsigned char*header=b[14].data;uint64_t capture=u64(header,24);if(u64(header,16)!=owner[0]||capture>write)return NULL;
 const void*command;unsigned command_bytes=kind==1?68:80;
 if(kind==1){uint64_t first=u64(header,32),n=u64(header,40);if(u64(header,0)!=0x3152524e||!first||!n||n>8192||ordinal<first||ordinal-first>=n||b[13].bytes!=n*68)return NULL;command=(const unsigned char*)b[13].data+(ordinal-first)*68;}
 else{if(u64(header,0)!=2||u64(header,48)!=65536||u64(header,56)!=12||b[12].bytes!=80||(b[13].bytes!=1&&b[13].bytes!=4081)||u64(header,40)!=u32(b[material].data,40))return NULL;command=b[12].data;}
 size_t shade=kind==1?1:b[13].bytes,total=sizeof(NFPCRecipeWriter)+b[texture].bytes+shade+512;if(maximum<total)return NULL;NFPCRecipeWriter*w=calloc(1,total);if(!w)return NULL;memcpy(w->info,owner,40);w->info[5]=kind;w->info[6]=ordinal;w->info[7]=capture;w->info[8]=write;w->info[9]=total;w->texture_bytes=b[texture].bytes;w->shade_bytes=shade;w->texture_address=u32(b[material].data,40);w->command_bytes=command_bytes;memcpy(w->command,command,command_bytes);memcpy(w->material,b[material].data,48);memcpy(w->data,b[texture].data,b[texture].bytes);if(kind==2)memcpy(w->data+b[texture].bytes,b[13].data,shade);memcpy(w->data+b[texture].bytes+shade,b[palette].data,512);
 if(w->texture_address<0x08000000u||(uint64_t)w->texture_address+w->texture_bytes>0x0a000000u)goto fail;
 const unsigned char*c=w->command;
 if(kind==1){uint64_t dest=u32(c,24);unsigned width=u32(c,28),dup=u32(c,64);if(u32(c,0)>15||u32(c,4)>INT32_MAX||u32(c,8)>INT32_MAX||width>512||dup>1||dest<0x06000000u||dest+width*2+dup*240>0x06014000u)goto fail;for(unsigned k=0;k<width;k++){uint64_t offset;if(!road_offset(w,k,1,&offset))goto fail;}}
 else{if(u32(c,36)!=w->texture_address||u32(c,76)>320||u32(c,12)>10||!u32(c,16)||u32(c,16)>1024||(u32(c,24)&&u32(c,44)>0x1b000u&&u32(c,12)<2))goto fail;unsigned shift,uvshift;uint32_t tex,dest;wall_start(w,&shift,&uvshift,&tex,&dest);uint32_t vertical=u32(c,72),mask=(u32(c,16)<<15)-1;for(unsigned row=0;row<u32(c,76);row++){vertical&=mask;uint32_t address=tex+((vertical>>uvshift)<<shift);if(address<w->texture_address||(uint64_t)address-w->texture_address>=w->texture_bytes)goto fail;vertical+=u32(c,44);}}
 return w;
fail:free(w);return NULL;
}
void nf_pc_recipe_writer_free(NFPCRecipeWriter*w){free(w);}
int nf_pc_recipe_writer_info(const NFPCRecipeWriter*w,uint64_t out[10]){if(!w||!out)return 0;memcpy(out,w->info,sizeof(w->info));return 1;}
int nf_pc_recipe_writer_buffer(const NFPCRecipeWriter*w,unsigned kind,const void**out,size_t*n){if(!w||kind>4||!out||!n)return 0;const void*p[5]={w->command,w->data,w->data+w->texture_bytes,w->data+w->texture_bytes+w->shade_bytes,w->material};size_t sizes[5]={w->command_bytes,w->texture_bytes,w->shade_bytes,512,48};*out=p[kind];*n=sizes[kind];return 1;}
int nf_pc_recipe_writer_cell(const NFPCRecipeWriter*w,unsigned x,unsigned y,uint64_t out[4]){
 if(!w||x>=240||y>=160||!out)return 0;
 const unsigned char*c=w->command;uint64_t result[4]={UINT64_MAX,0,0,0};uint32_t target=0x06000000u+(uint32_t)w->info[4]*0xa000u+y*240+x;
 if(w->info[5]==1){for(unsigned d=0;d<=u32(c,64);d++){uint64_t start=(uint64_t)u32(c,24)+d*240;if(target<start||target-start>=u32(c,28)*2u)continue;unsigned k=(unsigned)(target-start)/2,lane=(unsigned)(target-start)&1;uint64_t offset;if(!road_offset(w,k,lane,&offset))return 0;unsigned index=w->data[offset];result[0]=offset;result[1]=result[2]=index;result[3]=index?2:1;}}
 else{unsigned shift,uvshift;uint32_t texture,dest;wall_start(w,&shift,&uvshift,&texture,&dest);uint32_t vertical=u32(c,72),mask=(u32(c,16)<<15)-1;for(unsigned row=0;row<u32(c,76);row++){vertical&=mask;uint32_t address=texture+((vertical>>uvshift)<<shift);uint64_t offset=(uint64_t)address-w->texture_address;unsigned index=w->data[offset];if(index&&(target==(dest&~1u)||target==(uint32_t)((dest&~1u)+1))){unsigned mapped=w->shade_bytes==4081?w->data[w->texture_bytes+index*16]:index;result[0]=offset;result[1]=index;result[2]=mapped;result[3]=mapped?2:1;}dest+=u32(c,8)<<1;vertical+=u32(c,44);}}
 memcpy(out,result,sizeof(result));return 1;
}

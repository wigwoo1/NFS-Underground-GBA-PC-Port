/* Extension of the frozen writer implementation; shares its exact private
   command arithmetic, with independent sampler/history tests as the oracle. */
#include "recipe_writer.c"
#include "writer_address_map.h"
struct NFPCWriterAddressMap{uint64_t info[15];unsigned char data[];};
static void address_assign(uint32_t*map,uint32_t destination,uint32_t base,uint64_t offset){if(destination>=base&&destination-base<38400)map[destination-base]=(uint32_t)offset+1;}
NFPCWriterAddressMap*nf_pc_writer_address_map(const NFPCRecipeWriter*w,size_t maximum){
 if(!w||maximum<sizeof(NFPCWriterAddressMap)||maximum>64u*1024*1024)return NULL;
 uint32_t*map=calloc(38400,4);if(!map)return NULL;uint32_t base=0x06000000u+(uint32_t)w->info[4]*0xa000u;const unsigned char*c=w->command;
 if(w->info[5]==1){for(unsigned d=0;d<=u32(c,64);d++)for(unsigned k=0;k<u32(c,28);k++){uint64_t offset;if(!road_offset(w,k,0,&offset)){free(map);return NULL;}for(unsigned lane=0;lane<2;lane++)address_assign(map,u32(c,24)+d*240+k*2+lane,base,offset+lane);}}
 else{unsigned shift,uvshift;uint32_t texture,dest;wall_start(w,&shift,&uvshift,&texture,&dest);uint32_t vertical=u32(c,72),mask=(u32(c,16)<<15)-1;for(unsigned row=0;row<u32(c,76);row++){vertical&=mask;uint32_t address=texture+((vertical>>uvshift)<<shift);uint64_t offset=(uint64_t)address-w->texture_address;if(w->data[offset])for(unsigned lane=0;lane<2;lane++)address_assign(map,(dest&~1u)+lane,base,offset);dest+=u32(c,8)<<1;vertical+=u32(c,44);}}
 unsigned left=240,right=0,top=160,bottom=0;uint32_t largest=0;for(unsigned i=0;i<38400;i++)if(map[i]){unsigned x=i%240,y=i/240;if(x<left)left=x;if(x+1>right)right=x+1;if(y<top)top=y;if(y+1>bottom)bottom=y+1;if(map[i]>largest)largest=map[i];}
 if(!largest)left=right=top=bottom=0;
 size_t n=(size_t)(right-left)*(bottom-top)*4,bytes=sizeof(NFPCWriterAddressMap)+n;if(maximum<bytes){free(map);return NULL;}NFPCWriterAddressMap*m=calloc(1,bytes);if(!m){free(map);return NULL;}memcpy(m->info,w->info,9*8);m->info[9]=left;m->info[10]=right;m->info[11]=top;m->info[12]=bottom;m->info[13]=largest;m->info[14]=bytes;
 for(unsigned y=top;y<bottom;y++)for(unsigned x=left;x<right;x++){uint32_t value=map[y*240+x];size_t at=((size_t)(y-top)*(right-left)+x-left)*4;for(unsigned k=0;k<4;k++)m->data[at+k]=(unsigned char)(value>>(k*8));}
 free(map);return m;
}
void nf_pc_writer_address_map_free(NFPCWriterAddressMap*m){free(m);}
int nf_pc_writer_address_map_info(const NFPCWriterAddressMap*m,uint64_t out[15]){if(!m||!out)return 0;memcpy(out,m->info,sizeof(m->info));return 1;}
int nf_pc_writer_address_map_buffer(const NFPCWriterAddressMap*m,const void**out,size_t*n){if(!m||!out||!n)return 0;*out=m->data;*n=(size_t)(m->info[10]-m->info[9])*(m->info[12]-m->info[11])*4;return 1;}

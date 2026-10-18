#include "indexed_copy.h"
#include <stdlib.h>
#include <string.h>
#define NF_COPY_MAGIC 0x4943464eu
#define NF_COPY_BYTES 15136u
int nf_indexed_copy_create(NFIndexedCopyRead read,void*user,uint32_t source,uint32_t destination,uint32_t width,uint32_t height,uint32_t ss,uint32_t ds,void**out,size_t*size){
 if(!read||!out||!size||width!=240||height!=63||ss!=240||ds!=240||source<0x08000000u||(uint64_t)source+NF_COPY_BYTES>0x0a000000ull||(source&1))return 0;
 if(destination<0x06000000u||destination>=0x06014000u||(destination&3))return 0;
 uint32_t delta=destination-0x06000000u,page=delta/0xa000u,offset=delta%0xa000u;
 if(page>1||offset>=38400u||NF_COPY_BYTES>38400u-offset)return 0;
 uint8_t*copy=malloc(40+NF_COPY_BYTES);if(!copy)return 0;
 uint32_t header[10]={NF_COPY_MAGIC,1,source,page,offset,width,height,ss,ds,NF_COPY_BYTES};memcpy(copy,header,40);
 if(!read(user,source,copy+40,NF_COPY_BYTES)){free(copy);return 0;}
 *out=copy;*size=40+NF_COPY_BYTES;return 1;
}
int nf_indexed_copy_view(const void*asset,size_t size,uint32_t*page,uint32_t*offset,const uint8_t**indices,size_t*count){
 if(!asset||!page||!offset||!indices||!count||size!=40+NF_COPY_BYTES)return 0;
 uint32_t h[10];memcpy(h,asset,40);
 if(h[0]!=NF_COPY_MAGIC||h[1]!=1||h[2]<0x08000000u||(uint64_t)h[2]+NF_COPY_BYTES>0x0a000000ull||(h[2]&1)||h[3]>1||h[4]>38400u-NF_COPY_BYTES||(h[4]&3)||h[5]!=240||h[6]!=63||h[7]!=240||h[8]!=240||h[9]!=NF_COPY_BYTES)return 0;
 *page=h[3];*offset=h[4];*indices=(const uint8_t*)asset+40;*count=NF_COPY_BYTES;return 1;
}
void nf_indexed_copy_free(void*asset){free(asset);}
int nf_indexed_fill_create(uint32_t destination,uint32_t value,uint32_t bytes,void**out,size_t*size){
 if(!out||!size||!bytes||(bytes&31)||destination<0x06000000u||destination>=0x06014000u||(destination&3))return 0;
 uint32_t delta=destination-0x06000000u,page=delta/0xa000u,offset=delta%0xa000u;
 if(page>1||offset>=38400u||bytes>38400u-offset)return 0;
 uint8_t*copy=malloc(40+bytes);if(!copy)return 0;
 uint32_t header[10]={0x4643464eu,1,value,page,offset,bytes,1,0,0,bytes};memcpy(copy,header,40);
 for(unsigned i=0;i<bytes;i++)copy[40+i]=(uint8_t)(value>>((i&3)*8));
 *out=copy;*size=40+bytes;return 1;
}
int nf_indexed_operation_view(const void*asset,size_t size,uint32_t*kind,uint32_t*page,uint32_t*offset,const uint8_t**indices,size_t*count){
 if(!asset||!kind||!page||!offset||!indices||!count||size<40)return 0;
 uint32_t h[10];memcpy(h,asset,40);
 if(h[0]==NF_COPY_MAGIC){uint32_t p,o;const uint8_t*i;size_t n;if(!nf_indexed_copy_view(asset,size,&p,&o,&i,&n))return 0;*kind=1;*page=p;*offset=o;*indices=i;*count=n;return 1;}
 if(h[0]!=0x4643464eu||h[1]!=1||h[3]>1||h[4]>=38400||(h[4]&3)||!h[9]||(h[9]&31)||h[9]>38400-h[4]||h[5]!=h[9]||h[6]!=1||h[7]||h[8]||size!=40ull+h[9])return 0;
 const uint8_t*i=(const uint8_t*)asset+40;for(unsigned n=0;n<h[9];n++)if(i[n]!=(uint8_t)(h[2]>>((n&3)*8)))return 0;
 *kind=2;*page=h[3];*offset=h[4];*indices=i;*count=h[9];return 1;
}

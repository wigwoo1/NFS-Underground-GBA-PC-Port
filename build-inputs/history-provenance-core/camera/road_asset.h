#ifndef NF_ROAD_ASSET_H
#define NF_ROAD_ASSET_H
#include <stdint.h>
#include <stddef.h>
#include <string.h>
typedef struct { uint32_t header[10];const uint8_t *spans,*texture; } NFRoadAssetView;
/* Packed UV stride is 1<<shift halfwords, not the masked U width. */
static size_t nf_road_texture_extent(uint32_t shift,uint32_t umask,uint32_t vmask){
 if(shift>15||(umask|vmask)&0x80000000u)return 0;
 uint64_t bytes=2ull*((umask>>16)+((uint64_t)(vmask>>16)<<shift)+1);
 return bytes<=1024*1024?(size_t)bytes:0;
}
static int nf_road_asset_view(const void*data,size_t size,NFRoadAssetView*out){
 if(!data||!out||size<40)return 0;NFRoadAssetView v;memcpy(v.header,data,40);uint32_t*h=v.header;
 if(h[0]!=0x4552464e||h[1]!=1||h[3]>=4||h[4]>=144||!h[5]||h[5]>512||h[6]>15||h[9]!=40+h[5]*80||h[8]>1024*1024||size!=(size_t)h[9]+h[8]||h[7]<0x08000000||h[7]>=0x0a000000||h[8]>0x0a000000-h[7])return 0;
 v.spans=(const uint8_t*)data+40;v.texture=(const uint8_t*)data+h[9];uint32_t first[20];memcpy(first,v.spans,80);
 if(nf_road_texture_extent(h[6],first[5],first[6])!=h[8])return 0;
 for(unsigned i=0;i<h[5];i++){uint32_t s[20];memcpy(s,v.spans+i*80,80);
 uint32_t page=s[0]>=0x0600a000?0x0600a000:0x06000000,offset=s[0]-page;
 if(offset>=38400||(offset%240)+s[1]*2>242||(s[2]!=0x03003190&&s[2]!=0x030056d8))return 0;
 if(s[4]!=h[6]||s[9]!=h[7]||s[5]!=first[5]||s[6]!=first[6]||s[10]!=s[0]||s[11]!=s[1]||!s[1]||s[1]>121||s[3]>1||s[0]<0x06000000||s[0]>=0x06014000||s[0]%2)return 0;
 }
 *out=v;return 1;
}
#endif

#ifndef NF_HUD_ROW_POOL_H
#define NF_HUD_ROW_POOL_H
#include "layer_snapshot.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <windows.h>
#include "hud_sha256.h"
static inline double nf_hud_pool_cost_mark(void){LARGE_INTEGER t,f;QueryPerformanceCounter(&t);QueryPerformanceFrequency(&f);return (double)t.QuadPart*1000/f.QuadPart;}
/* One exclusive allocation, full byte equality for pooling, no producer pointers. */
typedef struct {uint64_t epoch,hash;uint32_t refresh,count,layout;size_t bytes;NFHardwareLayerHeader headers[160];uint32_t indices[160];uint8_t payload[];} NFHudRowPool;
#define NF_HUD_POOL_PAYLOAD (sizeof(NFHudLayerRow)-offsetof(NFHudLayerRow,obj_vram))
static uint64_t nf_hud_pool_hash(const NFHudRowPool*p){uint64_t h=14695981039346656037ull;const uint8_t*b=(const uint8_t*)&p->refresh;size_t n=p->bytes- offsetof(NFHudRowPool,refresh);for(size_t i=0;i<n;i++){h^=b[i];h*=1099511628211ull;}h^=p->epoch;h*=1099511628211ull;return h;}
static int nf_hud_pool_extent(const NFHudRowPool*p,size_t bytes){
 if(!p||bytes<sizeof(*p)||p->bytes!=bytes)return 0;
 if(p->layout==1)return p->count&&p->count<=160&&bytes==sizeof(*p)+(size_t)p->count*NF_HUD_POOL_PAYLOAD;
 if((p->layout!=2&&p->layout!=258)||(p->count>>24))return 0;
 unsigned a=p->count&255,b=p->count>>8&255,c=p->count>>16&255;
 return a&&a<=160&&b&&b<=160&&c&&c<=160&&bytes==sizeof(*p)+(size_t)a*32768+(size_t)(b+c)*1024+(p->layout==258?32:0);
}
static int nf_hud_pool_index_valid(const NFHudRowPool*p,unsigned row){
 unsigned i=p->indices[row];if(p->layout==1)return i<p->count;
 return !(i>>24)&&(i&255)<(p->count&255)&&(i>>8&255)<(p->count>>8&255)&&(i>>16&255)<(p->count>>16&255);
}
/* Full pool integrity is validated by the enclosing synchronous consumer. */
static inline const uint8_t*nf_hud_pool_palette(const NFHudRowPool*p,size_t bytes,uint64_t epoch,unsigned row){
 if(!nf_hud_pool_extent(p,bytes)||!epoch||p->epoch!=epoch||row>=160||!nf_hud_pool_index_valid(p,row))return NULL;
 unsigned index=p->indices[row];
 if(p->layout==1)return p->payload+(size_t)index*NF_HUD_POOL_PAYLOAD+32768;
 return p->payload+(size_t)(p->count&255)*32768+(size_t)(index>>8&255)*1024;
}
static int nf_hud_pool_valid(const NFHudRowPool*p,size_t bytes,uint64_t epoch){
 if(!nf_hud_pool_extent(p,bytes)||!epoch||p->epoch!=epoch)return 0;
 for(unsigned i=0;i<160;i++)if(p->headers[i].row!=i||p->headers[i].refresh!=p->refresh||!nf_hud_pool_index_valid(p,i))return 0;
 if(p->layout==258){uint8_t digest[32];return !p->hash&&nf_hud_sha256(p->epoch,(const uint8_t*)&p->refresh,bytes-32- offsetof(NFHudRowPool,refresh),digest)&&!memcmp(digest,(const uint8_t*)p+bytes-32,32);}
 return p->hash==nf_hud_pool_hash(p);
}
/* Samples only reject unequal candidates; equality always requires full memcmp. */
static int nf_hud_plane_equal(const uint8_t*a,const uint8_t*b,size_t bytes,int filter){
 if(filter){size_t at[4]={0,bytes/3,bytes*2/3,bytes-8};for(unsigned i=0;i<4;i++){uint64_t x,y;memcpy(&x,a+at[i],8);memcpy(&y,b+at[i],8);if(x!=y)return 0;}}
 return !memcmp(a,b,bytes);
}
static NFHudRowPool*nf_hud_pool_create_planes(const void*data,size_t bytes,uint64_t epoch){
 if(!data||!epoch||bytes!=160*sizeof(NFHudLayerRow))return NULL;
 int profile=getenv("NF_TEST_HUD_POOL_COST_PROFILE")!=NULL;double begin=profile?nf_hud_pool_cost_mark():0,dedup=0,copied=0;int filter=getenv("NF_TEST_HUD_POOL_SAMPLE_FILTER")!=NULL;const uint8_t*b=data;unsigned unique[3][160],counts[3]={0},indices[160]={0};size_t offsets[3]={offsetof(NFHudLayerRow,obj_vram),offsetof(NFHudLayerRow,palette),offsetof(NFHudLayerRow,oam)},lengths[3]={32768,1024,1024};uint32_t refresh;memcpy(&refresh,b,4);
 for(unsigned row=0;row<160;row++){NFHardwareLayerHeader h;memcpy(&h,b+row*sizeof(NFHudLayerRow),sizeof(h));if(h.row!=row||h.refresh!=refresh)return NULL;
  for(unsigned plane=0;plane<3;plane++){unsigned j=counts[plane];const uint8_t*current=b+row*sizeof(NFHudLayerRow)+offsets[plane];
   if(row){unsigned previous=indices[row-1]>>(plane*8)&255;if(nf_hud_plane_equal(current,b+unique[plane][previous]*sizeof(NFHudLayerRow)+offsets[plane],lengths[plane],filter))j=previous;}
   if(j==counts[plane]){for(j=0;j<counts[plane];j++)if(nf_hud_plane_equal(current,b+unique[plane][j]*sizeof(NFHudLayerRow)+offsets[plane],lengths[plane],filter))break;}
   if(j==counts[plane])unique[plane][counts[plane]++]=row;
   indices[row]|=j<<(plane*8);
  }
 }
 if(profile)dedup=nf_hud_pool_cost_mark();
 int sha=getenv("NF_TEST_HUD_POOL_SHA256")!=NULL;size_t size=sizeof(NFHudRowPool)+(sha?32:0);for(unsigned i=0;i<3;i++)size+=(size_t)counts[i]*lengths[i];NFHudRowPool*p=calloc(1,size);if(!p)return NULL;p->epoch=epoch;p->refresh=refresh;p->layout=sha?258:2;p->count=counts[0]|counts[1]<<8|counts[2]<<16;p->bytes=size;
 for(unsigned i=0;i<160;i++){memcpy(p->headers+i,b+i*sizeof(NFHudLayerRow),sizeof(p->headers[i]));p->indices[i]=indices[i];}
 size_t at=0;for(unsigned plane=0;plane<3;plane++)for(unsigned j=0;j<counts[plane];j++){memcpy(p->payload+at,b+unique[plane][j]*sizeof(NFHudLayerRow)+offsets[plane],lengths[plane]);at+=lengths[plane];}
 if(profile){copied=nf_hud_pool_cost_mark();}
 if(sha){if(!nf_hud_sha256(epoch,(const uint8_t*)&p->refresh,size-32- offsetof(NFHudRowPool,refresh),(uint8_t*)p+size-32)){free(p);return NULL;}}else p->hash=nf_hud_pool_hash(p);if(profile)printf("hud_pool_cost epoch=%llu obj=%u palette=%u oam=%u bytes=%zu filter=%d sha256=%d dedup_ms=%.6f storage_ms=%.6f checksum_ms=%.6f\n",(unsigned long long)epoch,counts[0],counts[1],counts[2],size,filter,sha,dedup-begin,copied-dedup,nf_hud_pool_cost_mark()-copied);return p;
}
static NFHudRowPool*nf_hud_pool_create(const void*data,size_t bytes,uint64_t epoch){
 if(getenv("NF_TEST_HUD_POOL_PLANES"))return nf_hud_pool_create_planes(data,bytes,epoch);
 if(!data||!epoch||bytes!=160*sizeof(NFHudLayerRow)||sizeof(NFHardwareLayerHeader)!=offsetof(NFHudLayerRow,obj_vram))return NULL;
 int previous_hint=getenv("NF_TEST_HUD_POOL_PREVIOUS_HINT")!=NULL;
 const uint8_t*b=data;unsigned unique[160],indices[160],count=0;uint32_t refresh;memcpy(&refresh,b,4);
 for(unsigned i=0;i<160;i++){NFHardwareLayerHeader h;memcpy(&h,b+i*sizeof(NFHudLayerRow),sizeof(h));if(h.refresh!=refresh||h.row!=i)return NULL;
 unsigned j=count;
 if(previous_hint&&i&&!memcmp(b+i*sizeof(NFHudLayerRow)+sizeof(h),b+unique[indices[i-1]]*sizeof(NFHudLayerRow)+sizeof(h),NF_HUD_POOL_PAYLOAD))j=indices[i-1];
 else {for(j=0;j<count;j++)if(!memcmp(b+i*sizeof(NFHudLayerRow)+sizeof(h),b+unique[j]*sizeof(NFHudLayerRow)+sizeof(h),NF_HUD_POOL_PAYLOAD))break;}
 if(j==count){unique[count++]=i;}
 indices[i]=j;}
 size_t size=sizeof(NFHudRowPool)+(size_t)count*NF_HUD_POOL_PAYLOAD;NFHudRowPool*p=calloc(1,size);if(!p)return NULL;p->epoch=epoch;p->refresh=refresh;p->layout=1;p->count=count;p->bytes=size;
 for(unsigned i=0;i<160;i++){memcpy(p->headers+i,b+i*sizeof(NFHudLayerRow),sizeof(p->headers[i]));p->indices[i]=indices[i];}
 for(unsigned i=0;i<count;i++)memcpy(p->payload+(size_t)i*NF_HUD_POOL_PAYLOAD,b+unique[i]*sizeof(NFHudLayerRow)+sizeof(NFHardwareLayerHeader),NF_HUD_POOL_PAYLOAD);
 p->hash=nf_hud_pool_hash(p);return p;
}
/* Caller validates once before a complete row traversal. This accessor still bounds every read. */
static int nf_hud_pool_row(const NFHudRowPool*p,size_t bytes,uint64_t epoch,unsigned row,NFHudLayerRow*out){
 if(!out||row>=160||!nf_hud_pool_extent(p,bytes)||p->epoch!=epoch||!epoch||!nf_hud_pool_index_valid(p,row))return 0;
 NFHudLayerRow value;memcpy(&value,p->headers+row,sizeof(NFHardwareLayerHeader));
 if(p->layout==1)memcpy(value.obj_vram,p->payload+(size_t)p->indices[row]*NF_HUD_POOL_PAYLOAD,NF_HUD_POOL_PAYLOAD);
 else {unsigned index=p->indices[row],a=p->count&255,b=p->count>>8&255;memcpy(value.obj_vram,p->payload+(size_t)(index&255)*32768,32768);memcpy(value.palette,p->payload+(size_t)a*32768+(size_t)(index>>8&255)*1024,1024);memcpy(value.oam,p->payload+(size_t)a*32768+(size_t)b*1024+(size_t)(index>>16&255)*1024,1024);}
 *out=value;return 1;
}
static int nf_hud_pool_expand(const NFHudRowPool*p,size_t bytes,uint64_t epoch,void*out,size_t size){
 if(!out||size!=160*sizeof(NFHudLayerRow)||!nf_hud_pool_valid(p,bytes,epoch))return 0;
 for(unsigned i=0;i<160;i++){if(!nf_hud_pool_row(p,bytes,epoch,i,(NFHudLayerRow*)((uint8_t*)out+i*sizeof(NFHudLayerRow))))return 0;}
 return 1;
}
#endif








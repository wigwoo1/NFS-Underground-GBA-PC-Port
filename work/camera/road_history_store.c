#include "road_history_store.h"
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#ifdef _WIN32
#define RH_API __declspec(dllexport)
#else
#define RH_API __attribute__((visibility("default")))
#endif
#define RH_ASSETS 1024
#define RH_EVENTS 65536
#define RH_CELLS 76800
extern int nfs_wall_unshaded_addresses(const uint8_t*,uint32_t,uint32_t,unsigned,uint32_t*,uint32_t*);
typedef struct {unsigned category,address,bytes,refs;uint8_t *data;} RHAsset;
typedef struct {uint64_t ordinal;unsigned refresh,texture,shade,shift,refs,command[17];} RHEvent;
typedef struct {uint64_t epoch,ordinal;unsigned refresh;size_t budget,bytes;unsigned assets,events;int cells[RH_CELLS];RHAsset asset[RH_ASSETS];RHEvent event[RH_EVENTS];} RHStore;
static void rh_asset_drop(RHStore*s,unsigned id){RHAsset*a=&s->asset[id];if(a->data&&!a->refs){s->bytes-=a->bytes;free(a->data);memset(a,0,sizeof(*a));s->assets--;}}
static int rh_asset(RHStore*s,unsigned category,unsigned address,const uint8_t*data,unsigned bytes){
 int slot=-1;for(unsigned i=0;i<RH_ASSETS;i++){RHAsset*a=&s->asset[i];if(!a->data){if(slot<0)slot=(int)i;continue;}if(a->category==category&&a->address==address&&a->bytes==bytes&&!memcmp(a->data,data,bytes))return (int)i;}
 if(slot<0||bytes>s->budget-s->bytes)return -1;
 uint8_t*copy=malloc(bytes);if(!copy)return -1;memcpy(copy,data,bytes);RHAsset*a=&s->asset[slot];a->category=category;a->address=address;a->bytes=bytes;a->data=copy;s->bytes+=bytes;s->assets++;return slot;
}
RH_API int nf_road_history_reset(void*handle,uint64_t epoch){RHStore*s=handle;if(!s||!epoch||epoch>INT64_MAX)return 0;for(unsigned i=0;i<RH_ASSETS;i++)free(s->asset[i].data);memset(s->asset,0,sizeof(s->asset));memset(s->event,0,sizeof(s->event));for(unsigned i=0;i<RH_CELLS;i++)s->cells[i]=-1;s->epoch=epoch;s->ordinal=0;s->refresh=0;s->bytes=0;s->assets=s->events=0;return 1;}
RH_API void*nf_road_history_create(uint64_t epoch,size_t budget){if(budget<65536||budget>32u*1024u*1024u)return NULL;RHStore*s=calloc(1,sizeof(*s));if(!s)return NULL;s->budget=budget;if(!nf_road_history_reset(s,epoch)){free(s);return NULL;}return s;}
RH_API void nf_road_history_destroy(void*handle){RHStore*s=handle;if(!s)return;for(unsigned i=0;i<RH_ASSETS;i++)free(s->asset[i].data);free(s);}
/* One committed original affine run per append; caller preserves run order. */
RH_API int nf_road_history_append(void*handle,uint64_t epoch,uint64_t ordinal,unsigned refresh,const NFSceneEvent*e){
 RHStore*s=handle;if(!s||epoch!=s->epoch||!ordinal||ordinal>INT64_MAX||ordinal<=s->ordinal||refresh<s->refresh||!e||e->kind!=1||e->count!=1||e->shift>15||!e->commands||!e->texture||!e->texture_size||e->texture_size>0x1000000||e->texture_address<0x08000000u||e->texture_address>0x0a000000u-e->texture_size)return 0;
 const uint32_t*c=e->commands;if(c[0]>15||(c[1]&0x80000000u)||(c[2]&0x80000000u)||c[7]>512||c[16]>1||c[6]<0x06000000u)return 0;
 uint64_t dest=c[6]-0x06000000u,width=(uint64_t)c[7]*2;if(dest>0x14000u||width>0x14000u-dest||(c[16]&&(dest+240>0x14000u||width>0x14000u-dest-240)))return 0;
 unsigned cells[2048],count=0;uint32_t u=c[8],v=c[9];for(unsigned i=0;i<c[7];i++){u&=c[1];v&=c[2];uint64_t address=(uint64_t)c[5]+2*((u>>16)+((uint64_t)(v>>16)<<c[0]));if(address>UINT32_MAX||address<e->texture_address||address-e->texture_address+2>e->texture_size)return 0;
  for(unsigned row=0;row<=c[16];row++)for(unsigned lane=0;lane<2;lane++){unsigned at=(unsigned)dest+i*2+row*240+lane,page=at/0xa000u,cell=at%0xa000u;if(page<2&&cell<38400)cells[count++]=page*38400+cell;}
  u+=c[10];v+=c[11];
 }
 if(!count){s->ordinal=ordinal;s->refresh=refresh;return 1;}int slot=-1;for(unsigned i=0;i<RH_EVENTS;i++)if(!s->event[i].refs){slot=(int)i;break;}if(slot<0)return 0;
 int texture=rh_asset(s,1,e->texture_address,e->texture,(unsigned)e->texture_size);if(texture<0)return 0;RHEvent*next=&s->event[slot];memset(next,0,sizeof(*next));next->ordinal=ordinal;next->refresh=refresh;next->texture=(unsigned)texture;next->shade=UINT_MAX;next->shift=e->shift;memcpy(next->command,c,68);s->asset[texture].refs++;s->events++;
 for(unsigned i=0;i<count;i++){int old=s->cells[cells[i]];if(old==slot)continue;if(old>=0){RHEvent*previous=&s->event[old];if(!--previous->refs){s->asset[previous->texture].refs--;rh_asset_drop(s,previous->texture);s->events--;}}s->cells[cells[i]]=slot;next->refs++;}
 s->ordinal=ordinal;s->refresh=refresh;return 1;
}

typedef struct {uint64_t ordinal;unsigned index;} RHOrder;
static int rh_order(const void*a,const void*b){uint64_t x=((const RHOrder*)a)->ordinal,y=((const RHOrder*)b)->ordinal;return x<y?-1:x>y?1:0;}
RH_API size_t nf_road_history_snapshot(void*handle,uint64_t epoch,void*out,size_t capacity){
 RHStore*s=handle;if(!s||epoch!=s->epoch||!s->events)return 0;size_t bytes=64+s->bytes+(size_t)s->assets*64+(size_t)s->events*164;if(bytes>64u*1024u*1024u)return 0;if(!out)return bytes;if(capacity<bytes)return 0;
 uint8_t*copy=malloc(bytes);RHOrder*order=malloc(s->events*sizeof(*order));if(!copy||!order){free(copy);free(order);return 0;}unsigned remap[RH_ASSETS]={0},asset=0,n=0;size_t at=64;uint64_t header[8]={0x3148524e,1,bytes,epoch,s->assets,s->events,0,0};memcpy(copy,header,64);
 for(unsigned i=0;i<RH_ASSETS;i++){RHAsset*a=&s->asset[i];if(!a->data)continue;remap[i]=++asset;uint64_t h[8]={1,64+a->bytes,asset,a->category,a->address,a->bytes,0,0};memcpy(copy+at,h,64);memcpy(copy+at+64,a->data,a->bytes);at+=64+a->bytes;}
 for(unsigned i=0;i<RH_EVENTS;i++)if(s->event[i].refs){order[n].ordinal=s->event[i].ordinal;order[n++].index=i;}
 qsort(order,n,sizeof(*order),rh_order);
 for(unsigned i=0;i<n;i++){RHEvent*e=&s->event[order[i].index];uint64_t h[12]={2,164,e->ordinal,e->refresh,remap[e->texture],e->shade==UINT_MAX?0:remap[e->shade],s->asset[e->texture].address,1,e->shift,0,0,0};memcpy(copy+at,h,96);memcpy(copy+at+96,e->command,68);at+=164;}
 int ok=at==bytes;if(ok)memcpy(out,copy,bytes);free(copy);free(order);return ok?bytes:0;
}
RH_API int nf_road_history_stats(void*handle,uint64_t out[5]){RHStore*s=handle;if(!s||!out)return 0;uint64_t values[5]={s->events,s->assets,s->bytes,s->budget,sizeof(*s)+s->bytes};memcpy(out,values,sizeof(values));return 1;}





#include "wall_history_store.h"
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#ifdef _WIN32
#define WH_API __declspec(dllexport)
#else
#define WH_API __attribute__((visibility("default")))
#endif
#define WH_ASSETS 1024
#define WH_EVENTS 65536
#define WH_CELLS 76800
extern int nfs_wall_unshaded_addresses(const uint8_t*,uint32_t,uint32_t,unsigned,uint32_t*,uint32_t*);
typedef struct {unsigned category,address,bytes,refs;uint8_t *data;} WHAsset;
typedef struct {uint64_t ordinal;unsigned refresh,texture,shade,shift,refs,command[20];} WHEvent;
typedef struct {uint64_t epoch,ordinal;unsigned refresh;size_t budget,bytes;unsigned assets,events;int cells[WH_CELLS];WHAsset asset[WH_ASSETS];WHEvent event[WH_EVENTS];} WHStore;
static void wh_asset_drop(WHStore*s,unsigned id){WHAsset*a=&s->asset[id];if(a->data&&!a->refs){s->bytes-=a->bytes;free(a->data);memset(a,0,sizeof(*a));s->assets--;}}
static int wh_asset(WHStore*s,unsigned category,unsigned address,const uint8_t*data,unsigned bytes){
 int slot=-1;for(unsigned i=0;i<WH_ASSETS;i++){WHAsset*a=&s->asset[i];if(!a->data){if(slot<0)slot=(int)i;continue;}if(a->category==category&&a->address==address&&a->bytes==bytes&&!memcmp(a->data,data,bytes))return (int)i;}
 if(slot<0||bytes>s->budget-s->bytes)return -1;
 uint8_t*copy=malloc(bytes);if(!copy)return -1;memcpy(copy,data,bytes);WHAsset*a=&s->asset[slot];a->category=category;a->address=address;a->bytes=bytes;a->data=copy;s->bytes+=bytes;s->assets++;return slot;
}
WH_API int nf_wall_history_reset(void*handle,uint64_t epoch){WHStore*s=handle;if(!s||!epoch||epoch>INT64_MAX)return 0;for(unsigned i=0;i<WH_ASSETS;i++)free(s->asset[i].data);memset(s->asset,0,sizeof(s->asset));memset(s->event,0,sizeof(s->event));for(unsigned i=0;i<WH_CELLS;i++)s->cells[i]=-1;s->epoch=epoch;s->ordinal=0;s->refresh=0;s->bytes=0;s->assets=s->events=0;return 1;}
WH_API void*nf_wall_history_create(uint64_t epoch,size_t budget){if(budget<65536||budget>32u*1024u*1024u)return NULL;WHStore*s=calloc(1,sizeof(*s));if(!s)return NULL;s->budget=budget;if(!nf_wall_history_reset(s,epoch)){free(s);return NULL;}return s;}
WH_API void nf_wall_history_destroy(void*handle){WHStore*s=handle;if(!s)return;for(unsigned i=0;i<WH_ASSETS;i++)free(s->asset[i].data);free(s);}
WH_API int nf_wall_history_append(void*handle,uint64_t epoch,uint64_t ordinal,unsigned refresh,const NFSceneEvent*e){
 WHStore*s=handle;if(!s||epoch!=s->epoch||!ordinal||ordinal>INT64_MAX||ordinal<=s->ordinal||refresh<s->refresh||!e||e->kind!=2||e->count!=1||e->shift>1||!e->commands||!e->texture||e->texture_size!=65536+(e->shift?4081u:0))return 0;
 const unsigned*c=e->commands;if(c[9]!=e->texture_address||e->texture_address<0x08000000u||e->texture_address>0x0a000000u-65536||c[19]>320)return 0;
 uint32_t sources[320],destinations[320];if(!nfs_wall_unshaded_addresses((const uint8_t*)c,c[17],c[18],c[19],sources,destinations))return 0;
 unsigned cells[640],count=0;for(unsigned row=0;row<c[19];row++){if(sources[row]<e->texture_address||sources[row]-e->texture_address>=65536)return 0;if(!e->texture[sources[row]-e->texture_address])continue;
  for(unsigned lane=0;lane<2;lane++){uint32_t address=(destinations[row]&~1u)+lane;if(address<0x06000000u||address>=0x06018000u)return 0;if(address<0x06014000u){unsigned p=address-0x06000000u,page=p/0xa000u,cell=p%0xa000u;if(page<2&&cell<38400)cells[count++]=page*38400+cell;}}
 }
 unsigned shade_address=0;if(e->shift){int16_t offset;memcpy(&offset,(const uint8_t*)c+42,2);shade_address=c[5]+(int32_t)offset;if(shade_address<0x02000000u||shade_address>0x0a000000u-4081)return 0;}
 if(!count){s->ordinal=ordinal;s->refresh=refresh;return 1;}int slot=-1;for(unsigned i=0;i<WH_EVENTS;i++)if(!s->event[i].refs){slot=(int)i;break;}if(slot<0)return 0;
 int texture=wh_asset(s,1,e->texture_address,e->texture,65536);if(texture<0)return 0;int shade=-1;if(e->shift){shade=wh_asset(s,2,shade_address,e->texture+65536,4081);if(shade<0){wh_asset_drop(s,(unsigned)texture);return 0;}}
 WHEvent*next=&s->event[slot];memset(next,0,sizeof(*next));next->ordinal=ordinal;next->refresh=refresh;next->texture=(unsigned)texture;next->shade=shade<0?UINT_MAX:(unsigned)shade;next->shift=e->shift;memcpy(next->command,c,80);s->asset[texture].refs++;if(shade>=0)s->asset[shade].refs++;s->events++;
 for(unsigned i=0;i<count;i++){int old=s->cells[cells[i]];if(old==slot)continue;if(old>=0){WHEvent*previous=&s->event[old];previous->refs--;if(!previous->refs){WHAsset*a=&s->asset[previous->texture];a->refs--;wh_asset_drop(s,previous->texture);if(previous->shade!=UINT_MAX){s->asset[previous->shade].refs--;wh_asset_drop(s,previous->shade);}s->events--;}}s->cells[cells[i]]=slot;next->refs++;}
 s->ordinal=ordinal;s->refresh=refresh;return 1;
}
typedef struct {uint64_t ordinal;unsigned index;} WHOrder;
static int wh_order(const void*a,const void*b){uint64_t x=((const WHOrder*)a)->ordinal,y=((const WHOrder*)b)->ordinal;return x<y?-1:x>y?1:0;}
WH_API size_t nf_wall_history_snapshot(void*handle,uint64_t epoch,void*out,size_t capacity){
 WHStore*s=handle;if(!s||epoch!=s->epoch||!s->events)return 0;size_t bytes=64+s->bytes+(size_t)s->assets*64+(size_t)s->events*176;if(bytes>64u*1024u*1024u)return 0;if(!out)return bytes;if(capacity<bytes)return 0;
 uint8_t*copy=malloc(bytes);WHOrder*order=malloc(s->events*sizeof(*order));if(!copy||!order){free(copy);free(order);return 0;}unsigned remap[WH_ASSETS]={0},asset=0,n=0;size_t at=64;uint64_t header[8]={0x3148574e,1,bytes,epoch,s->assets,s->events,0,0};memcpy(copy,header,64);
 for(unsigned i=0;i<WH_ASSETS;i++){WHAsset*a=&s->asset[i];if(!a->data)continue;remap[i]=++asset;uint64_t h[8]={1,64+a->bytes,asset,a->category,a->address,a->bytes,0,0};memcpy(copy+at,h,64);memcpy(copy+at+64,a->data,a->bytes);at+=64+a->bytes;}
 for(unsigned i=0;i<WH_EVENTS;i++)if(s->event[i].refs){order[n].ordinal=s->event[i].ordinal;order[n++].index=i;}
 qsort(order,n,sizeof(*order),wh_order);
 for(unsigned i=0;i<n;i++){WHEvent*e=&s->event[order[i].index];uint64_t h[12]={2,176,e->ordinal,e->refresh,remap[e->texture],e->shade==UINT_MAX?0:remap[e->shade],s->asset[e->texture].address,1,e->shift,0,0,0};memcpy(copy+at,h,96);memcpy(copy+at+96,e->command,80);at+=176;}
 int ok=at==bytes;if(ok)memcpy(out,copy,bytes);free(copy);free(order);return ok?bytes:0;
}
WH_API int nf_wall_history_stats(void*handle,uint64_t out[5]){WHStore*s=handle;if(!s||!out)return 0;uint64_t values[5]={s->events,s->assets,s->bytes,s->budget,sizeof(*s)+s->bytes};memcpy(out,values,sizeof(values));return 1;}




/* Diagnostic original-cell event provenance; no history state changes. */
__declspec(dllexport) size_t nf_wall_history_cell_ordinals(void*handle,uint64_t epoch,unsigned page,void*out,size_t capacity){
 WHStore*s=handle;size_t bytes=38400u*sizeof(uint64_t);if(!s||s->epoch!=epoch||page>1||(out&&capacity<bytes))return 0;
 if(out){uint64_t*values=out;for(unsigned i=0;i<38400;i++){int slot=s->cells[page*38400+i];values[i]=slot>=0?s->event[slot].ordinal:0;}}return bytes;
}

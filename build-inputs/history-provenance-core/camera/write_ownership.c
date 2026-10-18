#include "write_ownership.h"
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#ifdef _WIN32
#define OW_API __declspec(dllexport)
#else
#define OW_API __attribute__((visibility("default")))
#endif
#define OW_BYTES 0x18000u
extern int nfs_wall_unshaded_addresses(const uint8_t*,uint32_t,uint32_t,unsigned,uint32_t*,uint32_t*);
typedef struct {uint64_t epoch;unsigned refresh;uint8_t kind[OW_BYTES];uint32_t written[OW_BYTES];} Ownership;
typedef void(*Range)(void*,unsigned,unsigned);
static int range(void*context,Range emit,uint64_t at,uint64_t count){if(at>OW_BYTES||count>OW_BYTES-at)return 0;if(emit&&count)emit(context,(unsigned)at,(unsigned)count);return 1;}
/* Walk twice: validate all destination/skip semantics before committing tags.
   Borrowed commands/textures must stay immutable until apply returns. */
static int walk(const NFSceneEvent*e,Range emit,void*context){
 if(!e||!e->commands)return 0;
 const uint32_t*c=e->commands;
 if(e->kind==1){if(e->count>8192)return 0;for(unsigned i=0;i<e->count;i++){const uint32_t*p=c+i*17;if(p[6]<0x06000000u||p[7]>512||p[16]>1)return 0;uint64_t at=p[6]-0x06000000u,n=(uint64_t)p[7]*2;if(at>0x14000u||n>0x14000u-at||!range(context,emit,at,n))return 0;if(p[16]&&(at+240>0x14000u||n>0x14000u-at-240||!range(context,emit,at+240,n)))return 0;}}
 else if(e->kind==2){if(!e->texture||e->count>512||e->shift>1||(e->shift==1&&(e->count!=1||e->texture_size!=65536+4081)))return 0;size_t size=e->shift?65536:e->texture_size;
  for(unsigned col=0;col<e->count;col++){const uint32_t*p=c+col*20;uint32_t source[320],dest[320];if(!nfs_wall_unshaded_addresses((const uint8_t*)p,p[17],p[18],p[19],source,dest))return 0;for(unsigned row=0;row<p[19];row++){if(source[row]<e->texture_address||source[row]-e->texture_address>=size)return 0;if(!e->texture[source[row]-e->texture_address])continue;uint32_t at=dest[row]&~1u;if(at<0x06000000u||!range(context,emit,at-0x06000000u,2))return 0;}}
 }
 else if(e->kind==3){if(e->count>65536||(e->count&&e->shift>10))return 0;for(unsigned i=0;i<e->count;i++){const uint32_t*p=c+i*7;if(!p[2])continue;if(p[1]<0x06000000u||p[2]>240||!range(context,emit,p[1]-0x06000000u,p[2]))return 0;}}
 else if(e->kind==4){if(!range(context,emit,c[0],(uint64_t)(c[2]>>5)*32))return 0;}
 else if(e->kind==6){if(!range(context,emit,c[0],(uint64_t)(c[1]>>5)*32))return 0;}
 else if(e->kind==5){if(c[1]>4096||c[2]>512||c[3]>4096||c[4]>4096)return 0;for(unsigned row=0;row<c[2];row++)if(!range(context,emit,(uint64_t)c[0]+(uint64_t)row*(c[4]&~3u),((uint64_t)(c[1]>>5)+1)*32))return 0;}
 else return 0;
 return 1;
}
OW_API int nf_write_ownership_reset(void*handle,uint64_t epoch){Ownership*s=handle;if(!s||!epoch||epoch>INT64_MAX)return 0;memset(s,0,sizeof(*s));s->epoch=epoch;return 1;}
OW_API void*nf_write_ownership_create(uint64_t epoch){Ownership*s=malloc(sizeof(*s));if(!s)return NULL;if(!nf_write_ownership_reset(s,epoch)){free(s);return NULL;}return s;}
OW_API void nf_write_ownership_destroy(void*handle){free(handle);}
typedef struct {Ownership*s;unsigned kind,refresh;} Commit;
static void commit(void*context,unsigned at,unsigned bytes){Commit*c=context;memset(c->s->kind+at,c->kind,bytes);for(unsigned i=0;i<bytes;i++)c->s->written[at+i]=c->refresh;}
OW_API int nf_write_ownership_apply(void*handle,uint64_t epoch,unsigned refresh,const NFSceneEvent*e){Ownership*s=handle;if(!s||s->epoch!=epoch||refresh<s->refresh||!walk(e,NULL,NULL))return 0;Commit context={s,e->kind,refresh};if(!walk(e,commit,&context))return 0;s->refresh=refresh;return 1;}
OW_API size_t nf_write_ownership_page(void*handle,uint64_t epoch,unsigned page,void*out,size_t capacity){Ownership*s=handle;const size_t bytes=38400*5;if(!s||s->epoch!=epoch||page>1||(out&&capacity<bytes))return 0;if(out){memcpy(out,s->kind+page*0xa000u,38400);memcpy((uint8_t*)out+38400,s->written+page*0xa000u,38400*4);}return bytes;}

OW_API size_t nf_write_ownership_size(void){return sizeof(Ownership);}

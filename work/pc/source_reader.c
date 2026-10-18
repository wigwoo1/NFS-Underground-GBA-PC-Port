#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "source_reader.h"
#include <stdlib.h>
#include <string.h>
struct NFPCSourceReader {NFPCSourceAPI raw,wrapped;DWORD owner;unsigned char*scratch;size_t bytes;uint64_t stats[8],key[6],failure[6];size_t pending;NFPCBackgroundTake take;NFPCOwnedRelease release;uint64_t owned_stats[3];NFPCOwnerTake geometry_take;NFPCOwnedRelease geometry_release;uint64_t geometry_stats[3];int direct_cached;uint64_t direct_stats[3];};
static int owns(const NFPCSourceReader*r){return r&&r->owner==GetCurrentThreadId();}
static int layer(void*context,uint64_t*out){NFPCSourceReader*r=context;return owns(r)&&r->raw.layer_info(r->raw.core,out);}
static size_t cached_error(NFPCSourceReader*r,const uint64_t key[6],size_t n){
 r->stats[3]++;uint64_t failure[6]={key[0],key[1],key[2],key[3],key[4],n};memcpy(r->failure,failure,sizeof(failure));return 0;
}
static size_t cached_packet(NFPCSourceReader*r,unsigned kind,uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void*out,size_t capacity){
 if(kind<2||kind>4)return 0;
 uint64_t key[6]={kind,epoch,serial,begin,end,0};NFPCOwnerRead read=kind==2?r->raw.road:kind==3?r->raw.wall:r->raw.proof;
 if(!out){r->pending=0;r->direct_stats[0]++;r->stats[1]++;size_t n=read(r->raw.core,epoch,serial,begin,end,NULL,0);
  if(!n||n>r->bytes)return cached_error(r,key,n);
  r->pending=n;memcpy(r->key,key,sizeof(key));if(n>r->stats[5])r->stats[5]=n;return n;
 }
 if(!r->pending||capacity<r->pending||memcmp(key,r->key,sizeof(key)))return 0;
 size_t expected=r->pending;r->pending=0;size_t n=read(r->raw.core,epoch,serial,begin,end,out,capacity);
 if(n!=expected)return cached_error(r,key,n);
 r->direct_stats[1]++;r->direct_stats[2]+=n;return n;
}
static size_t packet(NFPCSourceReader*r,unsigned kind,uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void*out,size_t capacity){
 if(!owns(r))return 0;
 if(r->direct_cached)return cached_packet(r,kind,epoch,serial,begin,end,out,capacity);
 uint64_t key[6]={kind,epoch,serial,begin,end,0};
 if(!out){r->pending=0;size_t n;if(kind==0)n=r->raw.background(r->raw.core,epoch,serial,r->scratch,r->bytes);else{NFPCOwnerRead read=kind==1?r->raw.geometry:kind==2?r->raw.road:kind==3?r->raw.wall:r->raw.proof;n=read(r->raw.core,epoch,serial,begin,end,r->scratch,r->bytes);}r->stats[1]++;if(!n||n>r->bytes){r->stats[3]++;r->failure[0]=kind;r->failure[1]=epoch;r->failure[2]=serial;r->failure[3]=begin;r->failure[4]=end;r->failure[5]=n;return 0;}r->pending=n;memcpy(r->key,key,sizeof(key));if(n>r->stats[5])r->stats[5]=n;return n;}
 if(!r->pending||capacity<r->pending||memcmp(key,r->key,sizeof(key)))return 0;
 size_t n=r->pending;memcpy(out,r->scratch,n);r->pending=0;r->stats[2]++;r->stats[4]+=n;return n;
}
static size_t background(void*c,uint64_t e,unsigned refresh,void*out,size_t n){return packet(c,0,e,refresh,0,0,out,n);}
#define OWNER(name,kind) static size_t name(void*c,uint64_t e,unsigned s,unsigned b,unsigned end,void*out,size_t n){return packet(c,kind,e,s,b,end,out,n);}
OWNER(geometry,1)
OWNER(road,2)
OWNER(wall,3)
OWNER(proof,4)
static NFPCSourceReader* reader_open(const NFPCSourceAPI*a,size_t bytes,int allocate_scratch){
 if(!a||a->size!=sizeof(*a)||a->owner_thread!=GetCurrentThreadId()||!a->core||!a->layer_info||!a->background||!a->geometry||!a->road||!a->wall||!a->proof||!bytes||bytes>64u*1024*1024)return NULL;
 NFPCSourceReader*r=calloc(1,sizeof(*r));if(!r)return NULL;if(allocate_scratch){r->scratch=malloc(bytes);if(!r->scratch){free(r);return NULL;}}r->raw=*a;r->bytes=bytes;r->stats[0]=allocate_scratch?bytes:0;r->owner=GetCurrentThreadId();r->wrapped=(NFPCSourceAPI){sizeof(NFPCSourceAPI),r,layer,background,geometry,road,wall,proof,0};if(!nf_pc_source_api_bind_owner(&r->wrapped)){free(r->scratch);free(r);return NULL;}return r;
}
NFPCSourceReader* nf_pc_source_reader_open(const NFPCSourceAPI*a,size_t bytes){return reader_open(a,bytes,1);}
static size_t take_background(void*context,uint64_t epoch,unsigned refresh,void**owned){
 NFPCSourceReader*r=context;if(!owns(r))return 0;
 size_t n=r->take(r->raw.core,epoch,refresh,owned);r->stats[1]++;r->owned_stats[0]++;
 if(!n||!*owned||n>r->bytes){r->stats[3]++;uint64_t failure[6]={0,epoch,refresh,0,0,n};memcpy(r->failure,failure,sizeof(failure));return 0;}
 if(n>r->stats[5])r->stats[5]=n;
 r->owned_stats[1]++;r->owned_stats[2]+=n;return n;
}
NFPCSourceReader* nf_pc_source_reader_open_owned_background(const NFPCSourceAPI*a,size_t bytes,NFPCBackgroundTake take,NFPCOwnedRelease release){
 if(!take||!release)return NULL;
 NFPCSourceReader*r=nf_pc_source_reader_open(a,bytes);if(r){r->take=take;r->release=release;}return r;
}
int nf_pc_source_reader_owned_background_info(const NFPCSourceReader*r,uint64_t out[3]){if(!owns(r)||!out)return 0;memcpy(out,r->owned_stats,sizeof(r->owned_stats));return 1;}
static size_t take_geometry(void*context,uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void**owned){
 NFPCSourceReader*r=context;if(!owns(r))return 0;
 size_t n=r->geometry_take(r->raw.core,epoch,serial,begin,end,owned);r->stats[1]++;r->geometry_stats[0]++;
 if(!n||!*owned||n>r->bytes){r->stats[3]++;uint64_t failure[6]={1,epoch,serial,begin,end,n};memcpy(r->failure,failure,sizeof(failure));return 0;}
 if(n>r->stats[5])r->stats[5]=n;
 r->geometry_stats[1]++;r->geometry_stats[2]+=n;return n;
}
NFPCSourceReader* nf_pc_source_reader_open_owned_sources(const NFPCSourceAPI*a,size_t bytes,NFPCBackgroundTake take,NFPCOwnedRelease release,NFPCOwnerTake geometry_take,NFPCOwnedRelease geometry_release){
 if(!geometry_take||!geometry_release)return NULL;
 NFPCSourceReader*r=nf_pc_source_reader_open_owned_background(a,bytes,take,release);if(r){r->geometry_take=geometry_take;r->geometry_release=geometry_release;}return r;
}
NFPCSourceReader* nf_pc_source_reader_open_direct_sources(const NFPCSourceAPI*a,size_t bytes,NFPCBackgroundTake take,NFPCOwnedRelease release,NFPCOwnerTake geometry_take,NFPCOwnedRelease geometry_release){
 if(!take||!release||!geometry_take||!geometry_release)return NULL;
 NFPCSourceReader*r=reader_open(a,bytes,0);if(r){r->take=take;r->release=release;r->geometry_take=geometry_take;r->geometry_release=geometry_release;r->direct_cached=1;}return r;
}
int nf_pc_source_reader_direct_cached_info(const NFPCSourceReader*r,uint64_t out[3]){if(!owns(r)||!out)return 0;memcpy(out,r->direct_stats,sizeof(r->direct_stats));return 1;}
int nf_pc_source_reader_owned_geometry_info(const NFPCSourceReader*r,uint64_t out[3]){if(!owns(r)||!out)return 0;memcpy(out,r->geometry_stats,sizeof(r->geometry_stats));return 1;}
NFPCSourceFrame* nf_pc_source_reader_capture(NFPCSourceReader*r,size_t maximum){if(!owns(r))return NULL;r->pending=0;memset(r->failure,0,sizeof(r->failure));r->failure[0]=UINT64_MAX;NFPCSourceFrame*f=r->geometry_take?nf_pc_source_frame_capture_take_sources(&r->wrapped,maximum,take_background,r->release,take_geometry,r->geometry_release):r->take?nf_pc_source_frame_capture_take_background(&r->wrapped,maximum,take_background,r->release):nf_pc_source_frame_capture(&r->wrapped,maximum);r->pending=0;r->stats[f?6:7]++;return f;}
void nf_pc_source_reader_close(NFPCSourceReader*r){if(!owns(r))return;free(r->scratch);free(r);}
int nf_pc_source_reader_info(const NFPCSourceReader*r,uint64_t out[8]){if(!owns(r)||!out)return 0;memcpy(out,r->stats,sizeof(r->stats));return 1;}
int nf_pc_source_reader_last_failure(const NFPCSourceReader*r,uint64_t out[6]){if(!owns(r)||!out)return 0;memcpy(out,r->failure,sizeof(r->failure));return 1;}

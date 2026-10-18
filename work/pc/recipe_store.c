#include "recipe_store.h"
#include <windows.h>
#include <stdlib.h>
#include <string.h>
#define BUCKETS 4096u
#define BLOCKS 16u
#define LIMIT (256u*1024*1024)
typedef struct {volatile LONG refs;volatile LONG64 used;size_t maximum;} Ledger;
typedef struct Blob {struct Blob*next;Ledger*ledger;volatile LONG refs;unsigned users;uint64_t hash;size_t bytes;unsigned char data[];} Blob;
typedef struct Writer {struct Writer*next;uint64_t ordinal,mark;unsigned kind,count;Blob*block[BLOCKS];} Writer;
struct NFRecipeStore {Ledger*ledger;DWORD owner;uint64_t epoch,stamp;size_t writers,blobs;Writer*writer[BUCKETS];Blob*blob[BUCKETS];};
typedef struct {uint64_t ordinal;unsigned kind,count;Blob*block[BLOCKS];} Entry;
struct NFRecipeSnapshot {Ledger*ledger;uint64_t epoch;size_t count,bytes;Entry entries[];};
static LONG64 used(Ledger*l){return InterlockedCompareExchange64(&l->used,0,0);}
static int reserve(Ledger*l,size_t n){LONG64 old=used(l);for(;;){if(n>l->maximum-(size_t)old)return 0;LONG64 found=InterlockedCompareExchange64(&l->used,old+(LONG64)n,old);if(found==old)return 1;old=found;}}
static void release(Ledger*l,size_t n){InterlockedAdd64(&l->used,-(LONG64)n);}
static void ledger_drop(Ledger*l){if(!InterlockedDecrement(&l->refs))free(l);}
static void blob_drop(Blob*b){if(!InterlockedDecrement(&b->refs)){Ledger*l=b->ledger;release(l,sizeof(*b)+b->bytes);free(b);ledger_drop(l);}}
static uint64_t hash(const void*data,size_t n){const unsigned char*p=data;uint64_t h=UINT64_C(14695981039346656037);for(size_t i=0;i<n;i++){h^=p[i];h*=UINT64_C(1099511628211);}return h;}
static unsigned bucket(unsigned kind,uint64_t ordinal){return (unsigned)((ordinal*UINT64_C(11400714819323198485))^(kind*809u))&(BUCKETS-1);}
static int owner(NFRecipeStore*s){return s&&s->owner==GetCurrentThreadId();}
static Writer*find(NFRecipeStore*s,unsigned kind,uint64_t ordinal){for(Writer*w=s->writer[bucket(kind,ordinal)];w;w=w->next)if(w->kind==kind&&w->ordinal==ordinal)return w;return NULL;}
static void writer_free(NFRecipeStore*s,Writer*w){for(unsigned i=0;i<w->count;i++){w->block[i]->users--;blob_drop(w->block[i]);}release(s->ledger,sizeof(*w));free(w);s->writers--;}
static void collect(NFRecipeStore*s){for(unsigned i=0;i<BUCKETS;i++){Blob**link=s->blob+i;while(*link){Blob*b=*link;if(b->users){link=&b->next;continue;}*link=b->next;s->blobs--;blob_drop(b);}}}
static void clear(NFRecipeStore*s){for(unsigned i=0;i<BUCKETS;i++){Writer*w=s->writer[i];while(w){Writer*next=w->next;writer_free(s,w);w=next;}s->writer[i]=NULL;}collect(s);}
size_t nf_recipe_store_minimum(void){return sizeof(Ledger)+sizeof(NFRecipeStore);}
NFRecipeStore*nf_recipe_store_open(uint64_t epoch,size_t maximum){if(!epoch||epoch>INT64_MAX||maximum<nf_recipe_store_minimum()||maximum>LIMIT)return NULL;Ledger*l=calloc(1,sizeof(*l));if(!l)return NULL;l->refs=1;l->used=sizeof(*l);l->maximum=maximum;if(!reserve(l,sizeof(NFRecipeStore))){free(l);return NULL;}NFRecipeStore*s=calloc(1,sizeof(*s));if(!s){free(l);return NULL;}s->ledger=l;s->owner=GetCurrentThreadId();s->epoch=epoch;return s;}
void nf_recipe_store_close(NFRecipeStore*s){if(!owner(s))return;Ledger*l=s->ledger;clear(s);release(l,sizeof(*s));free(s);ledger_drop(l);}
int nf_recipe_store_reset(NFRecipeStore*s,uint64_t epoch){if(!owner(s)||!epoch||epoch>INT64_MAX)return 0;clear(s);s->epoch=epoch;s->stamp=0;return 1;}
int nf_recipe_store_info(NFRecipeStore*s,uint64_t out[5]){if(!owner(s)||!out)return 0;uint64_t a[5]={s->epoch,s->writers,s->blobs,(uint64_t)used(s->ledger),s->ledger->maximum};memcpy(out,a,sizeof(a));return 1;}
int nf_recipe_store_put(NFRecipeStore*s,uint64_t epoch,unsigned kind,uint64_t ordinal,const NFRecipeBlock*blocks,unsigned count){
 if(!owner(s)||epoch!=s->epoch||(kind!=1&&kind!=2)||!ordinal||ordinal>INT64_MAX||!blocks||!count||count>BLOCKS)return 0;
 for(unsigned i=0;i<count;i++)if(!blocks[i].data||!blocks[i].bytes||blocks[i].bytes>0x100000)return 0;
 Writer*prior=find(s,kind,ordinal);if(prior){if(prior->count!=count)return 0;for(unsigned i=0;i<count;i++)if(prior->block[i]->bytes!=blocks[i].bytes||memcmp(prior->block[i]->data,blocks[i].data,blocks[i].bytes))return 0;return 1;}
 if(!reserve(s->ledger,sizeof(Writer)))return 0;
 Writer*w=calloc(1,sizeof(*w));if(!w){release(s->ledger,sizeof(Writer));return 0;}Blob*staged[BLOCKS];unsigned staged_count=0;
 for(unsigned i=0;i<count;i++){uint64_t h=hash(blocks[i].data,blocks[i].bytes);Blob*b=s->blob[h&(BUCKETS-1)];for(;b;b=b->next)if(b->hash==h&&b->bytes==blocks[i].bytes&&!memcmp(b->data,blocks[i].data,b->bytes))break;
  if(!b)for(unsigned j=0;j<staged_count;j++)if(staged[j]->hash==h&&staged[j]->bytes==blocks[i].bytes&&!memcmp(staged[j]->data,blocks[i].data,blocks[i].bytes)){b=staged[j];break;}
  if(!b){size_t n=sizeof(Blob)+blocks[i].bytes;if(!reserve(s->ledger,n))goto fail;b=malloc(n);if(!b){release(s->ledger,n);goto fail;}b->ledger=s->ledger;InterlockedIncrement(&s->ledger->refs);b->refs=1;b->users=0;b->hash=h;b->bytes=blocks[i].bytes;b->next=NULL;memcpy(b->data,blocks[i].data,b->bytes);staged[staged_count++]=b;}w->block[i]=b;
 }
 for(unsigned i=0;i<staged_count;i++){Blob*b=staged[i];unsigned at=(unsigned)b->hash&(BUCKETS-1);b->next=s->blob[at];s->blob[at]=b;s->blobs++;}
 w->kind=kind;w->ordinal=ordinal;w->count=count;for(unsigned i=0;i<count;i++){w->block[i]->users++;InterlockedIncrement(&w->block[i]->refs);}unsigned at=bucket(kind,ordinal);w->next=s->writer[at];s->writer[at]=w;s->writers++;return 1;
fail:for(unsigned i=0;i<staged_count;i++)blob_drop(staged[i]);release(s->ledger,sizeof(*w));free(w);return 0;
}
int nf_recipe_store_prune(NFRecipeStore*s,uint64_t epoch,const uint64_t*keys,size_t count){
 if(!owner(s)||epoch!=s->epoch||count>262144||(!keys&&count))return 0;
 for(size_t i=0;i<count;i++)if(keys[i*2]>2||!find(s,(unsigned)keys[i*2],keys[i*2+1]))return 0;
 if(++s->stamp==0){for(unsigned i=0;i<BUCKETS;i++)for(Writer*w=s->writer[i];w;w=w->next)w->mark=0;s->stamp=1;}
 for(size_t i=0;i<count;i++)find(s,(unsigned)keys[i*2],keys[i*2+1])->mark=s->stamp;
 for(unsigned i=0;i<BUCKETS;i++){Writer**link=s->writer+i;while(*link){Writer*w=*link;if(w->mark==s->stamp){link=&w->next;continue;}*link=w->next;writer_free(s,w);}}collect(s);return 1;
}
NFRecipeSnapshot*nf_recipe_store_snapshot(NFRecipeStore*s,uint64_t epoch,const uint64_t*keys,size_t count){
 if(!owner(s)||epoch!=s->epoch||count>262144||(!keys&&count))return NULL;
 for(size_t i=0;i<count;i++)if(keys[i*2]>2||!find(s,(unsigned)keys[i*2],keys[i*2+1]))return NULL;
 size_t bytes=sizeof(NFRecipeSnapshot)+count*sizeof(Entry);if(!reserve(s->ledger,bytes))return NULL;NFRecipeSnapshot*p=calloc(1,bytes);if(!p){release(s->ledger,bytes);return NULL;}p->ledger=s->ledger;InterlockedIncrement(&s->ledger->refs);p->epoch=epoch;p->count=count;p->bytes=bytes;
 for(size_t i=0;i<count;i++){Writer*w=find(s,(unsigned)keys[i*2],keys[i*2+1]);Entry*e=p->entries+i;e->kind=w->kind;e->ordinal=w->ordinal;e->count=w->count;for(unsigned j=0;j<w->count;j++){e->block[j]=w->block[j];InterlockedIncrement(&e->block[j]->refs);}}return p;
}
void nf_recipe_snapshot_free(NFRecipeSnapshot*p){if(!p)return;Ledger*l=p->ledger;for(size_t i=0;i<p->count;i++)for(unsigned j=0;j<p->entries[i].count;j++)blob_drop(p->entries[i].block[j]);release(l,p->bytes);free(p);ledger_drop(l);}
int nf_recipe_snapshot_info(const NFRecipeSnapshot*p,uint64_t out[5]){if(!p||!out)return 0;uint64_t a[5]={p->epoch,p->count,p->bytes,(uint64_t)used(p->ledger),p->ledger->maximum};memcpy(out,a,sizeof(a));return 1;}
int nf_recipe_snapshot_writer(const NFRecipeSnapshot*p,size_t index,uint64_t out[3]){if(!p||!out||index>=p->count)return 0;const Entry*e=p->entries+index;uint64_t a[3]={e->kind,e->ordinal,e->count};memcpy(out,a,sizeof(a));return 1;}
int nf_recipe_snapshot_block(const NFRecipeSnapshot*p,size_t index,unsigned block,const void**out,size_t*bytes){if(!p||!out||!bytes||index>=p->count||block>=p->entries[index].count)return 0;const Blob*b=p->entries[index].block[block];*out=b->data;*bytes=b->bytes;return 1;}

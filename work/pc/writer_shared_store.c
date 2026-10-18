#include "recipe_store.c"
#include "writer_shared.h"
typedef struct {Ledger*ledger;size_t bytes;} WriterAllocation;
void*nf_pc_writer_ledger_allocate(NFRecipeStore*s,size_t n,size_t*charged){
 if(!owner(s)||!charged||n>LIMIT-sizeof(WriterAllocation))return NULL;
 size_t bytes=sizeof(WriterAllocation)+n;if(!reserve(s->ledger,bytes))return NULL;
 WriterAllocation*a=calloc(1,bytes);if(!a){release(s->ledger,bytes);return NULL;}a->ledger=s->ledger;a->bytes=bytes;InterlockedIncrement(&a->ledger->refs);*charged=bytes;return a+1;
}
void nf_pc_writer_ledger_free(void*p){if(!p)return;WriterAllocation*a=(WriterAllocation*)p-1;Ledger*l=a->ledger;size_t bytes=a->bytes;free(a);release(l,bytes);ledger_drop(l);}

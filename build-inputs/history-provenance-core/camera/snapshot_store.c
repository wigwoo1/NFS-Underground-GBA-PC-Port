#include "snapshot_store.h"
#include <stdlib.h>
#include <string.h>
typedef struct {uint64_t id;void*data;size_t size;} Slot;
struct NFSnapshotStore {NFTimeline timeline;Slot slots[NF_TIMELINE_CAPACITY];size_t budget,used;int pinned;};
NFSnapshotStore* nf_snapshot_create(size_t budget){
 if(!budget)return NULL;
 NFSnapshotStore*s=calloc(1,sizeof(*s));if(s)s->budget=budget;return s;
}
int nf_snapshot_push(NFSnapshotStore*s,uint64_t epoch,uint64_t id,double time,const void*data,size_t size){
 if(!s||s->pinned||!data||!size||size>s->budget)return 0;
 NFTimeline next=s->timeline;unsigned count=s->timeline.count;int reset=count&&epoch>s->timeline.epoch;
 if(!reset)for(unsigned i=0;i<count;i++)if(s->slots[i].id==id)return 0;
 if(!nf_timeline_push(&next,epoch,id,time))return 0;
 size_t retained=reset?0:s->used;
 unsigned evict=0;
 if(!reset){
  if(count==NF_TIMELINE_CAPACITY)retained-=s->slots[evict++].size;
  while(size>s->budget-retained&&evict<count)retained-=s->slots[evict++].size;
  /* Timeline push already removed one entry at capacity. Trim any further
     oldest entries needed for the byte budget; commit only after allocation. */
  unsigned extra=evict-(count==NF_TIMELINE_CAPACITY?1:0);
  if(extra){memmove(next.entries,next.entries+extra,(next.count-extra)*sizeof(*next.entries));next.count-=extra;}
 }
 void*copy=malloc(size);if(!copy)return 0;memcpy(copy,data,size);
 if(reset){for(unsigned i=0;i<count;i++)free(s->slots[i].data);count=0;}
 else if(evict){for(unsigned i=0;i<evict;i++)free(s->slots[i].data);memmove(s->slots,s->slots+evict,(count-evict)*sizeof(*s->slots));count-=evict;}
 s->slots[count]=(Slot){id,copy,size};s->used=retained+size;s->timeline=next;return 1;
}
int nf_snapshot_acquire(NFSnapshotStore*s,double now,double delay,NFSnapshotPair*out){
 if(!s||!out||s->pinned)return NF_TIME_EMPTY;
 NFSnapshotPair result={0};int status=nf_timeline_sample(&s->timeline,now,delay,&result.time);if(!status)return status;
 for(unsigned i=0;i<s->timeline.count;i++){
  Slot*slot=s->slots+i;
  if(slot->id==result.time.older){result.older=slot->data;result.older_size=slot->size;}
  if(slot->id==result.time.newer){result.newer=slot->data;result.newer_size=slot->size;}
 }
 if(!result.older||!result.newer)return NF_TIME_EMPTY;
 s->pinned=1;*out=result;return status;
}
void nf_snapshot_release(NFSnapshotStore*s){if(s)s->pinned=0;}
int nf_snapshot_destroy(NFSnapshotStore*s){
 if(!s)return 1;
 if(s->pinned)return 0;
 for(unsigned i=0;i<s->timeline.count;i++)free(s->slots[i].data);
 free(s);return 1;
}

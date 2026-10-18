#ifndef NF_MODEL_CONTEXT_REFRESH_H
#define NF_MODEL_CONTEXT_REFRESH_H
#include <stdint.h>
#include <stddef.h>
#include <string.h>

/* Revalidate an unconsumed context across exactly one original refresh.
   No game memory or retained source bytes are changed by this function. */
typedef struct {
 uint64_t epoch,context_epoch,owned_epoch;
 uint32_t serial,context_serial,begin,frame,context_frame;
 uint32_t context,context_address,object,context_object,camera;
 uint32_t verified,expected,active,ready,owned_args[3],count,used;
 const uint8_t*context_bytes;
 const uint8_t*owned_bytes;
 const uint32_t(*blocks)[3];
 const int32_t*rotation;
 const int32_t*owned_rotation;
} NFModelContextRefresh;
typedef int (*NFModelContextRefreshRead)(void*,uint32_t,void*,size_t);
static int nf_model_context_refresh_checked(const NFModelContextRefresh*q,NFModelContextRefreshRead read,void*user){
 if(!q||!read||!q->verified||!q->expected||q->active||!q->ready||
    q->epoch!=q->context_epoch||q->epoch!=q->owned_epoch||q->serial!=q->context_serial||
    q->context!=q->context_address||q->object!=q->context_object||
    q->owned_args[0]!=q->context||q->owned_args[1]!=q->camera||q->owned_args[2]!=q->object||
    q->frame<=q->context_frame||q->frame-q->context_frame!=1||q->context_frame<q->begin||
    !q->context_bytes||!q->owned_bytes||!q->blocks||!q->rotation||!q->owned_rotation||
    !q->count||q->count>128||!q->used||q->used>262144||
    memcmp(q->rotation,q->owned_rotation,48))return 0;
 uint8_t actual[512];
 if((uint64_t)q->context+68>0x100000000ull||!read(user,q->context,actual,68)||memcmp(actual,q->context_bytes,68))return 0;
 uint32_t consumed=0;
 for(unsigned i=0;i<q->count;i++){
  const uint32_t*b=q->blocks[i];
  if(!b[1]||b[2]!=consumed||b[2]>q->used||b[1]>q->used-b[2]||(uint64_t)b[0]+b[1]>0x100000000ull)return 0;
  for(uint32_t at=0;at<b[1];){size_t size=b[1]-at;if(size>sizeof(actual))size=sizeof(actual);
   if(!read(user,b[0]+at,actual,size)||memcmp(actual,q->owned_bytes+b[2]+at,size))return 0;
   at+=(uint32_t)size;
  }
  consumed+=b[1];
 }
 return consumed==q->used;
}
#endif

#include "nfsug_scene_owner.h"
#include "scene_packet.h"
#include <stdlib.h>
#include <string.h>
typedef struct { NFScenePacket packet;size_t bytes;uint8_t data[]; } OwnedScene;
void* nf_android_scene_open(const void*data,size_t bytes){
 if(!data||bytes<92||bytes>256u*1024u*1024u)return NULL;
 OwnedScene*s=malloc(sizeof(*s)+bytes);if(!s)return NULL;
 memcpy(s->data,data,bytes);s->bytes=bytes;
 if(!nf_scene_packet_view(s->data,bytes,&s->packet)){free(s);return NULL;}
 return s;
}
void nf_android_scene_close(void*handle){free(handle);}
int nf_android_scene_info(const void*handle,uint64_t out[12]){
 if(!handle||!out)return 0;
 const OwnedScene*s=handle;uint32_t world=0;memcpy(&world,s->packet.section[1].data+4,4);
 uint64_t values[12]={s->packet.serial,s->packet.begin_refresh,s->packet.end_refresh,
  s->packet.page,s->bytes,nf_scene_packet_model_count(&s->packet),world};
 for(unsigned i=0;i<5;i++)values[7+i]=s->packet.section[i].size;
 memcpy(out,values,sizeof(values));return 1;
}
size_t nf_android_scene_copy(const void*handle,void*out,size_t capacity){
 if(!handle||!out)return 0;
 const OwnedScene*s=handle;if(capacity<s->bytes)return 0;
 memcpy(out,s->data,s->bytes);return s->bytes;
}
size_t nf_android_scene_section(const void*handle,unsigned section,void*out,size_t capacity){
 if(!handle||!out||section>=5)return 0;
 const OwnedScene*s=handle;NFSceneSection part=s->packet.section[section];
 if(capacity<part.size)return 0;
 memcpy(out,part.data,part.size);return part.size;
}

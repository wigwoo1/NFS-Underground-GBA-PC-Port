#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include "native_scene_executor.h"

int nf_road_spans_write(const uint32_t*,unsigned,NFSceneReader,void*,uint8_t*,size_t);
int nfs_wall_columns_write(const uint32_t*,unsigned,uint32_t,const uint8_t*,size_t,uint8_t*,size_t,unsigned*);
int nfs_wall_columns_write_shaded(const uint32_t*,unsigned,uint32_t,const uint8_t*,size_t,const uint8_t*,size_t,uint8_t*,size_t,unsigned*);
int nfs_model_rows_write(const uint32_t*,unsigned,unsigned,uint32_t,const uint8_t*,size_t,uint8_t*,size_t);
int nfs_initial_fill(uint8_t*,size_t,uint32_t,uint32_t,uint32_t);
int nfs_initial_copy(uint8_t*,size_t,uint32_t,const uint8_t*,size_t,uint32_t,uint32_t,uint32_t,uint32_t);
int nfs_initial_block_copy(uint8_t*,size_t,uint32_t,const uint8_t*,size_t,uint32_t);
/* Ordered owned events commit together. A failed event publishes no VRAM. */
__declspec(dllexport) int nf_scene_execute(const NFSceneEvent *events,unsigned count,uint8_t *vram,size_t bytes,unsigned *out_writes){
 if(!events||!vram||count>4096||bytes!=0x18000)return 0;
 uint8_t *next=malloc(bytes);if(!next)return 0;
 memcpy(next,vram,bytes);int ok=0;unsigned total=0;
 for(unsigned i=0;i<count;i++){
  const NFSceneEvent *e=events+i;unsigned writes;
  if(e->kind==1){if(!nf_road_spans_write(e->commands,e->count,e->read,e->context,next,bytes))goto done;}
  else if(e->kind==2){if(e->shift==0){if(!nfs_wall_columns_write(e->commands,e->count,e->texture_address,e->texture,e->texture_size,next,bytes,&writes))goto done;}else if(e->shift==1&&e->count==1&&e->texture_size==65536+4081){if(!nfs_wall_columns_write_shaded(e->commands,1,e->texture_address,e->texture,65536,e->texture+65536,4081,next,bytes,&writes))goto done;}else goto done;total+=writes;}
  else if(e->kind==3){if(!nfs_model_rows_write(e->commands,e->count,e->shift,e->texture_address,e->texture,e->texture_size,next,bytes))goto done;}
  else if(e->kind==4){if(!e->commands||!nfs_initial_fill(next,bytes,e->commands[0],e->commands[1],e->commands[2]))goto done;}
  else if(e->kind==5){if(!e->commands||!nfs_initial_copy(next,bytes,e->commands[0],e->texture,e->texture_size,e->commands[1],e->commands[2],e->commands[3],e->commands[4]))goto done;}
  else if(e->kind==6){if(!e->commands||!nfs_initial_block_copy(next,bytes,e->commands[0],e->texture,e->texture_size,e->commands[1]))goto done;}
  else goto done;
 }
 memcpy(vram,next,bytes);if(out_writes)*out_writes=total;ok=1;
 done:free(next);return ok;
}

/* Synchronous persistent scene ownership. Caller commands need remain valid
   only until submit returns. No emulated memory pointer is retained. */
typedef struct { uint8_t vram[0x18000]; uint64_t generation; } NFScene;
static int owned_road_read(void *context,uint32_t address,void *out,size_t bytes){
 const NFSceneEvent *e=context;
 if(address<e->texture_address||(uint64_t)address-e->texture_address>e->texture_size||bytes>e->texture_size-(address-e->texture_address))return 0;
 memcpy(out,e->texture+(address-e->texture_address),bytes);return 1;
}
__declspec(dllexport) void *nf_scene_create(const uint8_t *seed,size_t bytes){
 if(!seed||bytes!=0x18000)return NULL;
 NFScene *scene=malloc(sizeof(*scene));if(!scene)return NULL;
 memcpy(scene->vram,seed,bytes);scene->generation=0;return scene;
}
__declspec(dllexport) void nf_scene_destroy(void *handle){free(handle);}
__declspec(dllexport) int nf_scene_snapshot(void *handle,uint8_t *out,size_t bytes,uint64_t *generation){
 if(!handle||!out||bytes!=0x18000||!generation)return 0;
 NFScene *scene=handle;memcpy(out,scene->vram,bytes);*generation=scene->generation;return 1;
}
__declspec(dllexport) int nf_scene_submit_stats(void *handle,const NFSceneEvent *events,unsigned count,unsigned *out_writes){
 if(!handle||!events||count>4096)return 0;
 NFScene *scene=handle;
 if(scene->generation==UINT64_MAX)return 0;
 NFSceneEvent *owned=malloc((count?count:1)*sizeof(*owned));if(!owned)return 0;
 memcpy(owned,events,count*sizeof(*owned));int ok=0;
 for(unsigned i=0;i<count;i++)if(owned[i].kind==1){
  if(!owned[i].texture||owned[i].texture_size>0x1000000)goto done;
  owned[i].read=owned_road_read;owned[i].context=owned+i;
 }
 if(!nf_scene_execute(owned,count,scene->vram,sizeof(scene->vram),out_writes))goto done;
 scene->generation++;ok=1;
 done:free(owned);return ok;
}

__declspec(dllexport) int nf_scene_submit(void *handle,const NFSceneEvent *events,unsigned count){return nf_scene_submit_stats(handle,events,count,NULL);}

/* Independent committed-scene branch for frame-closing operations. */
__declspec(dllexport) void *nf_scene_fork(const void *handle){
 if(!handle)return NULL;
 NFScene *branch=malloc(sizeof(*branch));if(!branch)return NULL;
 memcpy(branch,handle,sizeof(*branch));return branch;
}

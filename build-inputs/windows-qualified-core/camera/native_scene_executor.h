#ifndef NF_NATIVE_SCENE_EXECUTOR_H
#define NF_NATIVE_SCENE_EXECUTOR_H
#include <stdint.h>
#include <stddef.h>
typedef int (*NFSceneReader)(void*,uint32_t,void*,size_t);
/* Wall kind2: shift0 is the existing unshaded column batch. shift1 owns one
   original shaded column: texture[65536] followed by its effective lookup[4081].
   Zero source skips before lookup; mapped zero from a nonzero source writes. */
typedef struct {
 unsigned kind,count,shift,texture_address;
 const uint32_t *commands;
 const uint8_t *texture;
 size_t texture_size;
 NFSceneReader read;
 void *context;
} NFSceneEvent;

int nf_scene_execute(const NFSceneEvent*,unsigned,uint8_t*,size_t,unsigned*);
void *nf_scene_create(const uint8_t*,size_t);
void nf_scene_destroy(void*);
void *nf_scene_fork(const void*);
int nf_scene_snapshot(void*,uint8_t*,size_t,uint64_t*);
int nf_scene_submit(void*,const NFSceneEvent*,unsigned);
int nf_scene_submit_stats(void*,const NFSceneEvent*,unsigned,unsigned*);
#endif

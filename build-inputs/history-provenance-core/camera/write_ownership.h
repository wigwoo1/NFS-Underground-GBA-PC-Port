#ifndef NF_WRITE_OWNERSHIP_H
#define NF_WRITE_OWNERSHIP_H
#include "native_scene_executor.h"
/* Owner-thread audit of SUCCESSFULLY COMMITTED source events. Source validation
   remains the executor's job. Records writes even when resulting colors agree. */
void *nf_write_ownership_create(uint64_t);
void nf_write_ownership_destroy(void*);
int nf_write_ownership_reset(void*,uint64_t);
int nf_write_ownership_apply(void*,uint64_t,unsigned,const NFSceneEvent*);
size_t nf_write_ownership_page(void*,uint64_t,unsigned,void*,size_t);
size_t nf_write_ownership_size(void);
#endif

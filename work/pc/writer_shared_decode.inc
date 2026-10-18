#include "writer_shared.h"
NFPCRecipeWriter*nf_pc_recipe_writer_decode_shared(NFRecipeStore*s,const uint64_t owner[5],unsigned kind,uint64_t ordinal,unsigned write,const NFRecipeBlock*b,unsigned count){
 NFPCRecipeWriter*temporary=nf_pc_recipe_writer_decode(owner,kind,ordinal,write,b,count,64u*1024*1024);if(!temporary)return NULL;
 size_t charged=0;NFPCRecipeWriter*w=nf_pc_writer_ledger_allocate(s,sizeof(*w),&charged);if(!w){nf_pc_recipe_writer_free(temporary);return NULL;}
 uint64_t key[2]={kind,ordinal};NFRecipeSnapshot*snapshot=NULL;
 if(!nf_recipe_store_put(s,owner[0],kind,ordinal,b,count)||(snapshot=nf_recipe_store_snapshot(s,owner[0],key,1))==NULL)goto fail;
 memcpy(w,temporary,sizeof(*w));w->shared_allocation=w;w->shared_snapshot=snapshot;uint64_t info[5];if(!nf_recipe_snapshot_info(snapshot,info))goto fail;w->info[9]=charged+info[2];
 const void*p;size_t n;if(!nf_recipe_snapshot_block(snapshot,0,kind==1?7:8,&p,&n)||n!=w->texture_bytes)goto fail;w->texture_data=p;if(kind==2){if(!nf_recipe_snapshot_block(snapshot,0,13,&p,&n)||n!=w->shade_bytes)goto fail;w->shade_data=p;}else{static const unsigned char unshaded=0;w->shade_data=&unshaded;}if(!nf_recipe_snapshot_block(snapshot,0,kind==1?8:9,&p,&n)||n!=512)goto fail;w->palette_data=p;
 nf_pc_recipe_writer_free(temporary);return w;
fail:if(snapshot)nf_recipe_snapshot_free(snapshot);nf_pc_writer_ledger_free(w);nf_pc_recipe_writer_free(temporary);return NULL;
}

int nf_pc_recipe_writer_shared_info(const NFPCRecipeWriter*w,uint64_t out[5]){return w&&w->shared_snapshot&&nf_recipe_snapshot_info(w->shared_snapshot,out);}

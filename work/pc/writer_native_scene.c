#include "writer_native_scene.h"
#include "recipe_regions.h"
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
typedef struct {uint64_t kind,ordinal;size_t index,binding;} Lookup;
typedef struct {unsigned owner,kind;uint64_t ordinal;NFPCRecipeWriter*writer;NFPCWriterAddressMap*map;} Binding;
struct NFPCWriterNativeScene {uint64_t info[10];NFPCScene*scene;NFPCSceneWriterDraw*draws;Binding*bindings;};
static int compare_lookup(const void*a,const void*b){const Lookup*x=a,*y=b;if(x->kind!=y->kind)return x->kind<y->kind?-1:1;return x->ordinal<y->ordinal?-1:x->ordinal>y->ordinal;}
void nf_pc_writer_native_scene_free(NFPCWriterNativeScene*s){if(!s)return;for(size_t i=0;i<s->info[4];i++){nf_pc_writer_address_map_free(s->bindings[i].map);nf_pc_recipe_writer_free(s->bindings[i].writer);}nf_pc_scene_free(s->scene);free(s->draws);free(s->bindings);free(s);}
int nf_pc_writer_native_scene_info(const NFPCWriterNativeScene*s,uint64_t out[10]){if(!s||!out)return 0;memcpy(out,s->info,sizeof(s->info));return 1;}
NFPCWriterNativeScene*nf_pc_writer_native_scene_prepare(const NFPCSourceFrame*f,const NFRecipeSnapshot*const views[2],size_t maximum){
 uint64_t fi[8];if(!f||!views||maximum<sizeof(NFPCWriterNativeScene)||maximum>64u*1024*1024||!nf_pc_source_frame_info(f,fi)||!fi[4]||fi[4]>2)return NULL;
 NFPCWriterNativeScene*s=calloc(1,sizeof(*s));NFRecipeStore*pool=NULL;NFPCRecipeRegions*regions[2][2]={{0}};NFPCRecipeCoverage*coverage[2][2]={{0}};Lookup*lookup[2]={0};size_t lookup_count[2]={0};uint64_t keys[2][5]={{0}},scene_info[8];size_t total=0,external=0;
 if(!s)return NULL;
 s->info[0]=fi[0];s->info[1]=fi[1];s->info[2]=fi[4];
 s->scene=nf_pc_scene_prepare(f,maximum-sizeof(*s));if(!s->scene||!nf_pc_scene_info(s->scene,scene_info))goto fail;
 for(unsigned owner=0;owner<fi[4];owner++){
  uint64_t vi[5];if(!nf_pc_source_frame_owner(f,owner,keys[owner])||!nf_recipe_snapshot_info(views[owner],vi)||vi[0]!=fi[0]||vi[1]>262144)goto fail;
  lookup_count[owner]=(size_t)vi[1];lookup[owner]=calloc(vi[1]?vi[1]:1,sizeof(Lookup));if(!lookup[owner])goto fail;
  for(size_t i=0;i<vi[1];i++){uint64_t w[3];if(!nf_recipe_snapshot_writer(views[owner],i,w)||(w[0]!=1&&w[0]!=2)||!w[1]||w[2]!=15)goto fail;lookup[owner][i]=(Lookup){w[0],w[1],i,SIZE_MAX};}
  qsort(lookup[owner],lookup_count[owner],sizeof(Lookup),compare_lookup);for(size_t i=1;i<lookup_count[owner];i++)if(!compare_lookup(lookup[owner]+i-1,lookup[owner]+i))goto fail;
  for(unsigned layer=0;layer<2;layer++){uint64_t ri[9];coverage[owner][layer]=nf_pc_source_recipe_coverage(f,owner,NFPC_ROAD+layer,64u*1024*1024);if(!coverage[owner][layer])goto fail;regions[owner][layer]=nf_pc_recipe_regions_create(coverage[owner][layer],64u*1024*1024);if(!regions[owner][layer]||!nf_pc_recipe_regions_info(regions[owner][layer],ri)||ri[7]>38400||total>153600-ri[7])goto fail;total+=(size_t)ri[7];s->info[5]+=ri[6];}
 }
 external=sizeof(*s)+(size_t)scene_info[6]+total*(sizeof(NFPCSceneWriterDraw)+sizeof(Binding));if(external>maximum)goto fail;
 s->draws=total?calloc(total,sizeof(*s->draws)):NULL;s->bindings=total?calloc(total,sizeof(*s->bindings)):NULL;if(total&&(!s->draws||!s->bindings))goto fail;
 pool=nf_recipe_store_open(fi[0],maximum-external);if(!pool)goto fail;
 for(unsigned layer=0;layer<2;layer++)for(unsigned owner=0;owner<fi[4];owner++){
  const void*data;size_t bytes;if(!nf_pc_recipe_regions_buffer(regions[owner][layer],&data,&bytes)||bytes%64)goto fail;const uint64_t*rect=data;
  for(size_t i=0;i<bytes/64;i++){
   const uint64_t*r=rect+i*8;Lookup key={r[1],r[2],0,SIZE_MAX};
   Lookup*found=bsearch(&key,lookup[owner],lookup_count[owner],sizeof(Lookup),compare_lookup);
   if(!found)goto fail;
   size_t binding=found->binding;
   if(binding==SIZE_MAX){
    if(s->info[4]>=total)goto fail;
    NFRecipeBlock blocks[15];
    for(unsigned j=0;j<15;j++)if(!nf_recipe_snapshot_block(views[owner],found->index,j,&blocks[j].data,&blocks[j].bytes))goto fail;
    binding=(size_t)s->info[4]++;found->binding=binding;
    Binding*b=s->bindings+binding;b->owner=owner;b->kind=(unsigned)r[1];b->ordinal=r[2];
    b->writer=nf_pc_recipe_writer_decode_shared(pool,keys[owner],b->kind,b->ordinal,(unsigned)r[3],blocks,15);if(!b->writer)goto fail;
    uint64_t pi[5],mi[15];if(!nf_recipe_store_info(pool,pi)||external+pi[3]>maximum)goto fail;
    b->map=nf_pc_writer_address_map(b->writer,maximum-external-(size_t)pi[3]);if(!b->map||!nf_pc_writer_address_map_info(b->map,mi))goto fail;
    external+=(size_t)mi[14];if(external>maximum||!nf_pc_writer_store_set_maximum(pool,maximum-external))goto fail;
   }
   if(binding>=s->info[4])goto fail;
   Binding*b=s->bindings+binding;if(b->owner!=owner||b->kind!=(unsigned)r[1]||b->ordinal!=r[2])goto fail;
   NFPCSceneWriterDraw*d=s->draws+s->info[3]++;d->owner=owner;d->count=4;d->endpoint=1;d->writer=b->writer;d->map=b->map;
   for(unsigned j=0;j<4;j++)d->bounds[j]=(unsigned)r[4+j];
   double left=r[4],right=r[5],top=r[6],bottom=r[7],ring[24]={left,top,128,left,top,1,right,top,128,right,top,1,right,bottom,128,right,bottom,1,left,bottom,128,left,bottom,1};memcpy(d->ring,ring,sizeof(ring));
  }
  /* Verify every covered source cell against its exact accepted writer. */
  if(!nf_pc_recipe_coverage_buffer(coverage[owner][layer],2,&data,&bytes)||bytes%48)goto fail;
  const uint64_t*records=data;
  for(size_t i=0;i<bytes/48;i++){
   const uint64_t*r=records+i*6;Lookup key={r[2],r[3],0,SIZE_MAX};
   Lookup*found=bsearch(&key,lookup[owner],lookup_count[owner],sizeof(Lookup),compare_lookup);
   if(!found||found->binding>=s->info[4])goto fail;
   Binding*b=s->bindings+found->binding;uint64_t value[4];
   if(b->owner!=owner||b->kind!=(unsigned)r[2]||b->ordinal!=r[3]||!nf_pc_recipe_writer_cell(b->writer,(unsigned)(r[0]%240),(unsigned)(r[0]/240),value)||!value[3]||value[2]!=r[5])goto fail;
  }
 }
 {uint64_t pi[5];if(!nf_recipe_store_info(pool,pi))goto fail;s->info[9]=external+pi[3];if(s->info[9]>maximum)goto fail;nf_recipe_store_close(pool);pool=NULL;s->info[6]=external;if(s->info[4]){if(!nf_pc_recipe_writer_shared_info(s->bindings[0].writer,pi))goto fail;s->info[7]=pi[3];}s->info[8]=external+s->info[7];if(s->info[8]>maximum)goto fail;}
 for(unsigned owner=0;owner<2;owner++){free(lookup[owner]);for(unsigned layer=0;layer<2;layer++){nf_pc_recipe_regions_free(regions[owner][layer]);nf_pc_recipe_coverage_free(coverage[owner][layer]);}}return s;
fail:if(pool)nf_recipe_store_close(pool);for(unsigned owner=0;owner<2;owner++){free(lookup[owner]);for(unsigned layer=0;layer<2;layer++){nf_pc_recipe_regions_free(regions[owner][layer]);nf_pc_recipe_coverage_free(coverage[owner][layer]);}}nf_pc_writer_native_scene_free(s);return NULL;
}
int nf_pc_writer_native_scene_draw(NFPCSceneGPU*g,NFPCWriterNativeScene*s,unsigned w,unsigned h,unsigned aw,unsigned ah,void*out,size_t bytes){return s&&nf_pc_scene_gpu_draw_source_writers(g,s->scene,w,h,aw,ah,s->draws,(size_t)s->info[3],out,bytes);}
int nf_pc_writer_native_scene_render(NFPCSceneGPU*g,NFPCWriterNativeScene*s,unsigned w,unsigned h,unsigned aw,unsigned ah){return s&&nf_pc_scene_gpu_render_source_writers(g,s->scene,w,h,aw,ah,s->draws,(size_t)s->info[3]);}

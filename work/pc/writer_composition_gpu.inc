#include "writer_composition_gpu.h"
static int source_writer_list_valid(const NFPCScene*s,const NFPCSceneWriterDraw*draws,size_t count){
 if(!s||count>153600||(!draws&&count))return 0;
 for(size_t i=0;i<count;i++){const NFPCSceneWriterDraw*d=draws+i;uint64_t wi[10],mi[15];
  if(d->reserved||d->owner>=s->info[2]||d->count>6||d->endpoint>1||!nf_pc_recipe_writer_info(d->writer,wi)||!nf_pc_writer_address_map_info(d->map,mi)||memcmp(wi,mi,9*sizeof(uint64_t))||memcmp(wi,s->owner[d->owner],5*sizeof(uint64_t)))return 0;
  unsigned top=d->owner?(unsigned)s->info[7]:0,bottom=(!d->owner&&s->info[2]==2)?(unsigned)s->info[7]:160;
  if(d->bounds[0]>d->bounds[1]||d->bounds[1]>240||d->bounds[2]>d->bounds[3]||d->bounds[2]<top||d->bounds[3]>bottom)return 0;
  for(unsigned j=0;j<d->count;j++){const double*v=d->ring+j*6;for(unsigned k=0;k<6;k++)if(!isfinite(v[k]))return 0;if(v[2]<64||v[5]<=0)return 0;}
 }
 return 1;
}
static int draw_scene_source_writers(NFPCSceneGPU*g,const NFPCScene*s,unsigned aw,unsigned ah){
 for(size_t i=0;i<g->scene_writer_count;i++){const NFPCSceneWriterDraw*d=g->scene_writer_draws+i;if(!nf_pc_scene_gpu_render_scene_writer_banded(g,s,d->owner,d->ring,d->count,d->bounds,d->writer,d->map,aw,ah,d->endpoint))return 0;}
 /* Leaf passes release the FBO and use their own texture programs. Restore the
    baseline scene stage's target, texture bindings and geometry program. */
 g->bind(FRAMEBUFFER,g->fbo);glViewport(0,0,aw,ah);g->active(TEXTURE0);glBindTexture(GL_TEXTURE_2D,g->input);g->use_program(g->program);return 1;
}
static int source_writers_render(NFPCSceneGPU*g,NFPCScene*s,unsigned w,unsigned h,unsigned aw,unsigned ah,const NFPCSceneWriterDraw*draws,size_t count,void*out,size_t bytes,int readback){
 if(!g||g->owner!=GetCurrentThreadId()||g->use_scene_writer_draws||!source_writer_list_valid(s,draws,count))return 0;
 g->scene_writer_draws=draws;g->scene_writer_count=count;g->use_scene_writer_draws=1;int ok=render(g,s,w,h,aw,ah,15,out,bytes,readback);g->scene_writer_draws=NULL;g->scene_writer_count=0;g->use_scene_writer_draws=0;return ok;
}

int nf_pc_scene_gpu_draw_source_writers(NFPCSceneGPU*g,NFPCScene*s,unsigned w,unsigned h,unsigned aw,unsigned ah,const NFPCSceneWriterDraw*d,size_t n,void*out,size_t bytes){return source_writers_render(g,s,w,h,aw,ah,d,n,out,bytes,1);}
int nf_pc_scene_gpu_render_source_writers(NFPCSceneGPU*g,NFPCScene*s,unsigned w,unsigned h,unsigned aw,unsigned ah,const NFPCSceneWriterDraw*d,size_t n){return source_writers_render(g,s,w,h,aw,ah,d,n,NULL,0,0);}

#include "writer_band_gpu.h"
int nf_pc_scene_gpu_render_scene_writer_banded(NFPCSceneGPU*g,const NFPCScene*s,unsigned owner,const double*ring,unsigned count,const unsigned bounds[4],const NFPCRecipeWriter*w,const NFPCWriterAddressMap*m,unsigned aw,unsigned ah,unsigned endpoint){
 uint64_t wi[10],mi[15];
 if(!s||!bounds||owner>=s->info[2]||s->info[2]>2||!nf_pc_recipe_writer_info(w,wi)||!nf_pc_writer_address_map_info(m,mi)||memcmp(wi,s->owner[owner],5*sizeof(uint64_t))||memcmp(mi,s->owner[owner],5*sizeof(uint64_t)))return 0;
 unsigned top=owner?(unsigned)s->info[7]:0,bottom=(!owner&&s->info[2]==2)?(unsigned)s->info[7]:160;
 if(top>bottom||bottom>160||bounds[2]<top||bounds[3]>bottom)return 0;
 return nf_pc_scene_gpu_render_writer_band(g,ring,count,bounds,w,m,s->palette,sizeof(s->palette),aw,ah,endpoint,0,top,bottom);
}

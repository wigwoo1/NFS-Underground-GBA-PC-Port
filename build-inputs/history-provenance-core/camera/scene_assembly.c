#include <stdio.h>
#include "scene_assembly.h"
#include "native_surface.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
#define NF_ASSEMBLY_BUDGET (32u*1024u*1024u)
typedef struct {uint32_t identity[5];uint8_t*data,*lighting,*indices;size_t size,light_size,index_size;uint16_t bounds[4];unsigned bounded,index_mode;} Item;
struct NFSceneAssembly {Item surface[128],models[16];uint32_t order[144];unsigned count,commands,failed,model_count,multimodel;size_t bytes;unsigned bounds_count;double bounds_alpha;};
static uint64_t assembly_asset_stats[2];
void nf_assembly_asset_stats(uint64_t out[2]){if(out)memcpy(out,assembly_asset_stats,sizeof(assembly_asset_stats));}
static uint32_t word(const void*p){uint32_t v;memcpy(&v,p,4);return v;}
static int fail(NFSceneAssembly*s){if(s)s->failed=1;return 0;}
void nf_assembly_detail(const NFSceneAssembly*s,uint32_t out[5]){if(!out)return;uint32_t v[5]={0};if(s){v[0]=s->failed;v[1]=s->count;v[2]=s->commands;v[3]=s->model_count;v[4]=s->bounds_count;}memcpy(out,v,sizeof(v));}
NFSceneAssembly*nf_assembly_create(void){return calloc(1,sizeof(NFSceneAssembly));}
int nf_assembly_multimodel(NFSceneAssembly*s,int enabled){if(!s||s->commands||s->failed)return 0;s->multimodel=enabled!=0;return 1;}
void nf_assembly_reset(NFSceneAssembly*s){
 if(!s)return;
 for(unsigned i=0;i<s->count;i++){free(s->surface[i].data);free(s->surface[i].lighting);free(s->surface[i].indices);}
 unsigned multimodel=s->multimodel;for(unsigned i=0;i<s->model_count;i++)free(s->models[i].data);memset(s,0,sizeof(*s));s->multimodel=multimodel;
}
void nf_assembly_destroy(NFSceneAssembly*s){nf_assembly_reset(s);free(s);}
int nf_assembly_surface(NFSceneAssembly*s,const uint32_t id[5],const void*data,size_t size,const void*lighting,size_t light_size){
 if(!s||s->failed||!id||!data||!lighting||s->count>=128||s->commands>=(s->multimodel?144u:129u)||size<12||light_size<4)return fail(s);
 if((id[0]!=1&&id[0]!=2)||id[4]||size>NF_ASSEMBLY_BUDGET||light_size>NF_ASSEMBLY_BUDGET||size+light_size>NF_ASSEMBLY_BUDGET-s->bytes)return fail(s);
 const uint8_t*p=data;unsigned n=word(p),w=word(p+4),h=word(p+8),lit=word(lighting);
 if(n<3||n>32||!w||w>1024||!h||h>1024||size!=12ull+n*40ull+w*h*4ull||lit>1||light_size!=(lit?20ull+w*h*64ull:4ull))return fail(s);
 if(lit){const uint8_t*l=lighting;if(word(l+4)>15||word(l+8)>15||word(l+12)!=w||word(l+16)!=h)return fail(s);}
 Item item={0};item.data=malloc(size);item.lighting=malloc(light_size);
 if(!item.data||!item.lighting){free(item.data);free(item.lighting);return fail(s);}
 memcpy(item.data,data,size);memcpy(item.lighting,lighting,light_size);memcpy(item.identity,id,20);item.size=size;item.light_size=light_size;
 s->surface[s->count]=item;s->order[s->commands++]=s->count++;s->bytes+=size+light_size;return 1;
}
int nf_assembly_surface_indices(NFSceneAssembly*s,unsigned index,const uint8_t*indices,size_t size){
 if(!s||s->failed||!indices||index>=s->count)return fail(s);
 Item*t=s->surface+index;if(t->identity[0]!=1||word(t->lighting)||t->indices||size!=(size_t)word(t->data+4)*word(t->data+8)||size>NF_ASSEMBLY_BUDGET-s->bytes)return fail(s);
 uint8_t*copy=malloc(size);if(!copy)return fail(s);memcpy(copy,indices,size);t->indices=copy;t->index_size=size;t->index_mode=1;s->bytes+=size;return 1;
}
int nf_assembly_wall_states(NFSceneAssembly*s,unsigned index,const uint8_t*states,size_t size,unsigned planes){
 if(!s||s->failed||!states||index>=s->count)return fail(s);
 Item*t=s->surface+index;size_t pixels=(size_t)word(t->data+4)*word(t->data+8);
 if(t->identity[0]!=2||t->indices||planes!=(word(t->lighting)?17u:1u)||size!=pixels*planes||size>NF_ASSEMBLY_BUDGET-s->bytes)return fail(s);
 for(size_t i=0;i<size;i++)if(states[i]>2)return fail(s);
 for(size_t i=0;i<pixels;i++){if(states[i]==1)return fail(s);for(unsigned level=1;level<planes;level++)if((states[i]==0)!=(states[level*pixels+i]==0))return fail(s);}
 uint8_t*copy=malloc(size);if(!copy)return fail(s);memcpy(copy,states,size);t->indices=copy;t->index_size=size;t->index_mode=planes==17?3:2;s->bytes+=size;return 1;
}
int nf_assembly_road_mapping(NFSceneAssembly*s,unsigned index,unsigned affine){
 if(!s||s->failed||index>=s->count||affine>1)return fail(s);
 Item*t=s->surface+index;if(t->identity[0]!=1||t->index_mode!=1)return fail(s);
 t->index_mode=affine?4:1;return 1;
}
int nf_assembly_wall_indices(NFSceneAssembly*s,unsigned index,const uint8_t*states,const uint8_t*indices,size_t size,unsigned planes){
 if(!s||s->failed||!states||!indices||index>=s->count)return fail(s);
 Item*t=s->surface+index;size_t pixels=(size_t)word(t->data+4)*word(t->data+8);
 if(t->identity[0]!=2||t->indices||planes!=(word(t->lighting)?17u:1u)||size!=pixels*planes||size>(NF_ASSEMBLY_BUDGET-s->bytes)/2)return fail(s);
 for(size_t i=0;i<size;i++)if(states[i]>2||(states[i]==2)!=(indices[i]!=0))return fail(s);
 for(size_t i=0;i<pixels;i++){if(states[i]==1)return fail(s);for(unsigned level=1;level<planes;level++)if((states[i]==0)!=(states[level*pixels+i]==0))return fail(s);}
 uint8_t*copy=malloc(size*2);if(!copy)return fail(s);memcpy(copy,states,size);memcpy(copy+size,indices,size);
 t->indices=copy;t->index_size=size*2;t->index_mode=planes==17?8:7;s->bytes+=size*2;return 1;
}
int nf_assembly_road_attributes(NFSceneAssembly*s,unsigned index,const NFRoadSourceAttributes*raw){
 if(!s||s->failed||!raw||index>=s->count)return fail(s);Item*t=s->surface+index;
 if(t->identity[0]!=1||!t->indices||(t->index_mode!=1&&t->index_mode!=4)||word(t->lighting)||raw->affine!=(t->index_mode==4)||288u>NF_ASSEMBLY_BUDGET-s->bytes||!nf_scene_road_attributes_match((NFSceneSection){t->data,t->size},raw)){if(getenv("NF_TEST_MOTION_CAPTURE_PROFILE"))fprintf(stderr,"road_attribute_header_rejection source=%u kind=%u indices=%u mode=%u lighting=%u bytes=%llu surface_bytes=%llu surface_count=%u width=%u height=%u raw_count=%u shift=%u stored_height=%u affine=%u material=%u animation=%u\n",t->identity[2],t->identity[0],t->indices!=NULL,t->index_mode,word(t->lighting),(unsigned long long)s->bytes,(unsigned long long)t->size,word(t->data),word(t->data+4),word(t->data+8),raw->count,raw->shift,raw->stored_height,raw->affine,raw->material,raw->animation);return fail(s);}
 uint8_t*copy=malloc(t->index_size+288);if(!copy)return fail(s);memcpy(copy,t->indices,t->index_size);memcpy(copy+t->index_size,raw,288);
 free(t->indices);t->indices=copy;t->index_size+=288;t->index_mode=raw->affine?6:5;s->bytes+=288;return 1;
}
int nf_assembly_model(NFSceneAssembly*s,const uint32_t id[5],const void*data,size_t size){
 if(!s||s->failed||!id||!data||id[0]!=3||id[4]||s->model_count>=(s->multimodel?16u:1u)||s->commands>=(s->multimodel?144u:129u)||size<160||size>NF_ASSEMBLY_BUDGET-s->bytes||word(data)!=0x324d464e)return fail(s);
 uint8_t*copy=malloc(size);if(!copy)return fail(s);
 memcpy(copy,data,size);Item*model=s->models+s->model_count;memcpy(model->identity,id,20);model->data=copy;model->size=size;s->order[s->commands++]=UINT32_MAX-s->model_count++;s->bytes+=size;return 1;
}
static uint32_t assembly_bounds_rejection[6];
__declspec(dllexport) void nf_assembly_bounds_rejection(uint32_t out[6]){if(out)memcpy(out,assembly_bounds_rejection,sizeof(assembly_bounds_rejection));}
int nf_assembly_bounds(NFSceneAssembly*s,unsigned index,double alpha,const uint16_t bounds[4]){
 assembly_bounds_rejection[0]=s?s->failed:99;assembly_bounds_rejection[1]=index;assembly_bounds_rejection[2]=s?s->count:0;assembly_bounds_rejection[3]=s&&index<s->count?s->surface[index].bounded:99;assembly_bounds_rejection[4]=s?s->bounds_count:0;assembly_bounds_rejection[5]=s&&s->bounds_count&&s->bounds_alpha!=alpha;
 if(!s||s->failed||!bounds||index>=s->count||s->surface[index].bounded||!isfinite(alpha)||alpha<0||alpha>=1||bounds[0]>bounds[1]||bounds[1]>240||bounds[2]>bounds[3]||bounds[3]>160||(s->bounds_count&&s->bounds_alpha!=alpha))return fail(s);
 memcpy(s->surface[index].bounds,bounds,8);s->surface[index].bounded=1;s->bounds_count++;s->bounds_alpha=alpha;return 1;
}
int nf_assembly_finish(NFSceneAssembly*s,uint32_t serial,uint32_t begin,uint32_t end,uint32_t page,const void*table,size_t table_size,void**out,size_t*out_size){
 if(!s||s->failed||(s->bounds_count&&s->bounds_count!=s->count)||!out||!out_size||!table||table_size!=32768*4||!s->model_count||s->commands!=s->count+s->model_count||end<=begin||page>1)return 0;
 size_t sizes[4]={8,8+s->commands*4,8+table_size,8+s->commands*20};
 unsigned indexed_surfaces=0;size_t index_bytes=0;
 for(unsigned i=0;i<s->count;i++){sizes[0]+=s->surface[i].size;sizes[2]+=s->surface[i].light_size;if(s->surface[i].indices){indexed_surfaces++;index_bytes+=s->surface[i].index_size;}}
 if(indexed_surfaces)sizes[0]+=8+s->count*8+index_bytes;
 uint8_t*sections[4]={0};for(unsigned i=0;i<4;i++){sections[i]=malloc(sizes[i]);if(!sections[i]){for(unsigned j=0;j<4;j++)free(sections[j]);return 0;}}
 uint32_t headers[4][2]={{0x31444652,s->count},{0x314f464e,s->commands},{0x314c464e,s->count},{0x3149464e,s->commands}};
 for(unsigned i=0;i<4;i++)memcpy(sections[i],headers[i],8);
 unsigned mapping[128],next=0;size_t wp=8,lp=8,ip=8;
 /* Packet storage groups roads then walls, while commands retain draw order. */
 for(unsigned kind=1;kind<=2;kind++)for(unsigned i=0;i<s->count;i++)if(s->surface[i].identity[0]==kind){
  Item*t=s->surface+i;mapping[i]=next++;memcpy(sections[0]+wp,t->data,t->size);wp+=t->size;
  memcpy(sections[2]+lp,t->lighting,t->light_size);lp+=t->light_size;memcpy(sections[3]+ip,t->identity,20);ip+=20;
 }
 memcpy(sections[2]+lp,table,table_size);for(unsigned i=0;i<s->model_count;i++)memcpy(sections[3]+ip+i*20,s->models[i].identity,20);
 for(unsigned i=0;i<s->commands;i++){uint32_t index=s->order[i]>=UINT32_MAX-15?s->order[i]:mapping[s->order[i]];memcpy(sections[1]+8+i*4,&index,4);}
 void*owned_models=NULL;const uint8_t*model_data=s->models[0].data;size_t model_size=s->models[0].size;
 if(s->model_count>1){model_size=8+s->model_count*8;for(unsigned i=0;i<s->model_count;i++)model_size=((model_size+7)&~(size_t)7)+s->models[i].size;
  uint8_t*list=calloc(1,model_size);if(!list){for(unsigned i=0;i<4;i++)free(sections[i]);return 0;}owned_models=list;uint32_t header[2]={0x314c4d4e,s->model_count};memcpy(list,header,8);size_t offset=8+s->model_count*8;
  for(unsigned i=0;i<s->model_count;i++){offset=(offset+7)&~(size_t)7;uint32_t entry[2]={(uint32_t)offset,(uint32_t)s->models[i].size};memcpy(list+8+i*8,entry,8);memcpy(list+offset,s->models[i].data,s->models[i].size);offset+=s->models[i].size;}model_data=list;
 }
 if(indexed_surfaces){
  uint32_t trailer[2]={0x3149574e,s->count};memcpy(sections[0]+wp,trailer,8);wp+=8;
  for(unsigned kind=1;kind<=2;kind++)for(unsigned i=0;i<s->count;i++)if(s->surface[i].identity[0]==kind){
   Item*t=s->surface+i;uint32_t record[2]={t->index_mode,(uint32_t)t->index_size};memcpy(sections[0]+wp,record,8);wp+=8;
   if(t->index_size){memcpy(sections[0]+wp,t->indices,t->index_size);wp+=t->index_size;}
  }
 }
 NFScenePacket packet={serial,begin,end,page,{{model_data,model_size},{sections[0],sizes[0]},{sections[1],sizes[1]},{sections[2],sizes[2]},{sections[3],sizes[3]}}};
 int ok;
 if(s->bounds_count){
  uint16_t bounds[144][4];for(unsigned i=0;i<s->count;i++)memcpy(bounds[mapping[i]],s->surface[i].bounds,8);
  unsigned bounded_models=0;for(unsigned i=0;i<s->model_count;i++)if(s->models[i].bounded){memcpy(bounds[s->count+i],s->models[i].bounds,8);bounded_models++;}
  if(bounded_models&&bounded_models!=s->model_count){for(unsigned i=0;i<4;i++)free(sections[i]);free(owned_models);return 0;}
  void*base=NULL;size_t size=0;ok=nf_scene_packet_build(&packet,&base,&size);
  if(ok){ok=nf_scene_packet_with_bounds(base,size,s->bounds_alpha,&bounds[0][0],s->count+bounded_models,out,out_size);nf_scene_packet_free(base);}
 }else ok=nf_scene_packet_build(&packet,out,out_size);for(unsigned i=0;i<4;i++)free(sections[i]);free(owned_models);return ok;
}

static int assembly_commands_impl(const NFNativeSceneCommand*commands,unsigned count,const uint32_t*identities,const uint16_t*bounds,double alpha,NFReadMemory read,void*user,const uint8_t palette[512],NFScenePalette selector,void*selector_user,const int32_t rotation[12],uint32_t serial,uint32_t begin,uint32_t end,uint32_t page,const void*table,void**out,size_t*out_size,NFSceneModelInputs model_selector,void*model_user,unsigned indexed,NFScenePaletteAssets assets){
 if(!commands||!count||count>(model_selector?144u:129u)||!identities||!read||(!palette&&!selector&&!assets)||!rotation||!out||!out_size)return 0;
 NFSceneAssembly*s=nf_assembly_create();if(!s)return 0;int ok=1;unsigned surfaces=0;if(model_selector)nf_assembly_multimodel(s,1);
 for(unsigned i=0;i<count&&ok;i++){
  const NFNativeSceneCommand*c=commands+i;const uint32_t*id=identities+i*5;unsigned kind=c->kind==5?3:c->kind;
  if((kind!=1&&kind!=2&&kind!=3)||id[0]!=kind||id[2]!=c->source){ok=0;break;}
  void*asset=NULL,*lighting=NULL;size_t size=0,light_size=0;uint32_t unlit=0;
  uint8_t selected[512];int32_t selected_rotation[12];const int32_t*model_rotation=rotation;const uint8_t*colors=palette;
  if(kind==3&&model_selector){NFSceneModelInputResult result=(NFSceneModelInputResult)model_selector(model_user,i,c,id,selected_rotation,selected);if(result==NF_MODEL_INPUT_OWNED_NO_DRAW){if(alpha==0.0)continue;ok=0;break;}ok=result==NF_MODEL_INPUT_READY;model_rotation=selected_rotation;colors=selected;}
  else if(assets){ok=assets(selector_user,i,c,read,user,rotation,selected,&asset,&size,&lighting,&light_size);colors=selected;}
  else if(selector){ok=selector(selector_user,i,c,read,user,rotation,selected);colors=selected;}
  if(ok&&assets&&kind!=3)assembly_asset_stats[0]++;
  if(ok&&(kind==3||!assets)){assembly_asset_stats[1]++;ok=nf_extract_scene_command_full(c,read,user,colors,model_rotation,&asset,&size,&lighting,&light_size,NULL);}
  if(ok&&kind==3&&indexed){
   uint8_t*indices=NULL;uint32_t width,height;void*tagged=NULL;size_t tagged_size;
   ok=nf_model_texture_indices_owned(read,user,c->model,&indices,&width,&height)&&nf_scene_model_attach_indices((NFSceneSection){asset,size},indices,(size_t)width*height,&tagged,&tagged_size);
   free(indices);if(ok){nf_surface_free(asset);asset=tagged;size=tagged_size;}
  }
  if(ok&&kind==3){ok=nf_assembly_model(s,id,asset,size);
   const uint16_t*clip=bounds?bounds+i*4:c->bounds;
   if(ok&&(clip[0]>clip[1]||clip[1]>240||clip[2]>clip[3]||clip[3]>160))ok=0;
   if(ok){memcpy(s->models[s->model_count-1].bounds,clip,8);s->models[s->model_count-1].bounded=1;}
  }
  else if(ok){ok=nf_assembly_surface(s,id,asset,size,lighting?lighting:&unlit,lighting?light_size:4);
   if(ok&&kind==1&&(indexed&2)){
    uint8_t*indices=NULL;uint32_t width,height;
    ok=nf_scene_command_road_indices_owned(c,read,user,&indices,&width,&height)&&width==word((uint8_t*)asset+4)&&height==word((uint8_t*)asset+8)&&nf_assembly_surface_indices(s,surfaces,indices,(size_t)width*height);free(indices);
    if(ok&&(indexed&4))ok=nf_assembly_road_mapping(s,surfaces,c->xyz[1]);
    if(ok&&(indexed&8)){NFRoadSourceAttributes raw;ok=nf_scene_command_road_attributes_owned(c,read,user,&raw)&&nf_assembly_road_attributes(s,surfaces,&raw);}
    if(ok&&(indexed&16)){NFRoadCameraMetadata camera;camera.version=1;memcpy(&camera.address,c->state+84,4);ok=!(camera.address&3)&&(uint64_t)camera.address+48<=0x100000000ull&&read(user,camera.address,camera.matrix,48)&&nf_assembly_road_camera(s,surfaces,&camera);}
   }
   if(ok&&kind==2&&(indexed&4)){
    uint8_t*states=NULL;uint32_t width,height,planes;
    ok=nf_scene_command_wall_states_owned(c,read,user,&states,&width,&height,&planes)&&width==word((uint8_t*)asset+4)&&height==word((uint8_t*)asset+8)&&nf_assembly_wall_states(s,surfaces,states,(size_t)width*height*planes,planes);free(states);
   }
   if(ok)ok=nf_assembly_bounds(s,surfaces++,alpha,bounds?bounds+i*4:c->bounds);
  }
  nf_surface_free(asset);nf_surface_free(lighting);
 }
 if(ok)ok=nf_assembly_finish(s,serial,begin,end,page,table,131072,out,out_size);
 nf_assembly_destroy(s);return ok;
}

int nf_assembly_commands(const NFNativeSceneCommand*c,unsigned n,const uint32_t*ids,const uint16_t*b,double alpha,NFReadMemory read,void*user,const uint8_t palette[512],const int32_t rotation[12],uint32_t serial,uint32_t begin,uint32_t end,uint32_t page,const void*table,void**out,size_t*size){return assembly_commands_impl(c,n,ids,b,alpha,read,user,palette,NULL,NULL,rotation,serial,begin,end,page,table,out,size,NULL,NULL,0,NULL);}
int nf_assembly_commands_palettes(const NFNativeSceneCommand*c,unsigned n,const uint32_t*ids,const uint16_t*b,double alpha,NFReadMemory read,void*user,NFScenePalette selector,void*selector_user,const int32_t rotation[12],uint32_t serial,uint32_t begin,uint32_t end,uint32_t page,const void*table,void**out,size_t*size){return selector&&assembly_commands_impl(c,n,ids,b,alpha,read,user,NULL,selector,selector_user,rotation,serial,begin,end,page,table,out,size,NULL,NULL,0,NULL);}

int nf_assembly_commands_model_inputs(const NFNativeSceneCommand*c,unsigned n,const uint32_t*ids,const uint16_t*b,double alpha,NFReadMemory read,void*user,NFScenePalette palette,void*palette_user,const int32_t rotation[12],NFSceneModelInputs models,void*model_user,uint32_t serial,uint32_t begin,uint32_t end,uint32_t page,const void*table,void**out,size_t*size){return palette&&models&&assembly_commands_impl(c,n,ids,b,alpha,read,user,NULL,palette,palette_user,rotation,serial,begin,end,page,table,out,size,models,model_user,0,NULL);}
int nf_assembly_commands_indexed_model_inputs(const NFNativeSceneCommand*c,unsigned n,const uint32_t*ids,const uint16_t*b,double alpha,NFReadMemory read,void*user,NFScenePalette palette,void*palette_user,const int32_t rotation[12],NFSceneModelInputs models,void*model_user,uint32_t serial,uint32_t begin,uint32_t end,uint32_t page,const void*table,void**out,size_t*size){return palette&&models&&assembly_commands_impl(c,n,ids,b,alpha,read,user,NULL,palette,palette_user,rotation,serial,begin,end,page,table,out,size,models,model_user,1,NULL);}

int nf_assembly_commands_indexed_world_model_inputs(const NFNativeSceneCommand*c,unsigned n,const uint32_t*ids,const uint16_t*b,double alpha,NFReadMemory read,void*user,NFScenePalette palette,void*palette_user,const int32_t rotation[12],NFSceneModelInputs models,void*model_user,uint32_t serial,uint32_t begin,uint32_t end,uint32_t page,const void*table,void**out,size_t*size){return palette&&models&&assembly_commands_impl(c,n,ids,b,alpha,read,user,NULL,palette,palette_user,rotation,serial,begin,end,page,table,out,size,models,model_user,3,NULL);}
int nf_assembly_commands_classified_world_model_inputs(const NFNativeSceneCommand*c,unsigned n,const uint32_t*ids,const uint16_t*b,double alpha,NFReadMemory read,void*user,NFScenePalette palette,void*palette_user,const int32_t rotation[12],NFSceneModelInputs models,void*model_user,uint32_t serial,uint32_t begin,uint32_t end,uint32_t page,const void*table,void**out,size_t*size){return palette&&models&&assembly_commands_impl(c,n,ids,b,alpha,read,user,NULL,palette,palette_user,rotation,serial,begin,end,page,table,out,size,models,model_user,7,NULL);}
int nf_assembly_commands_road_attributes_model_inputs(const NFNativeSceneCommand*c,unsigned n,const uint32_t*ids,const uint16_t*b,double alpha,NFReadMemory read,void*user,NFScenePalette palette,void*palette_user,const int32_t rotation[12],NFSceneModelInputs models,void*model_user,uint32_t serial,uint32_t begin,uint32_t end,uint32_t page,const void*table,void**out,size_t*size){return palette&&models&&assembly_commands_impl(c,n,ids,b,alpha,read,user,NULL,palette,palette_user,rotation,serial,begin,end,page,table,out,size,models,model_user,15,NULL);}
int nf_assembly_commands_classified_assets_model_inputs(const NFNativeSceneCommand*c,unsigned n,const uint32_t*ids,const uint16_t*b,double alpha,NFReadMemory read,void*user,NFScenePaletteAssets assets,void*asset_user,const int32_t rotation[12],NFSceneModelInputs models,void*model_user,uint32_t serial,uint32_t begin,uint32_t end,uint32_t page,const void*table,void**out,size_t*size){return assets&&models&&assembly_commands_impl(c,n,ids,b,alpha,read,user,NULL,NULL,asset_user,rotation,serial,begin,end,page,table,out,size,models,model_user,7,assets);}

int nf_assembly_commands_road_attributes_assets_model_inputs(const NFNativeSceneCommand*c,unsigned n,const uint32_t*ids,const uint16_t*b,double alpha,NFReadMemory read,void*user,NFScenePaletteAssets assets,void*asset_user,const int32_t rotation[12],NFSceneModelInputs models,void*model_user,uint32_t serial,uint32_t begin,uint32_t end,uint32_t page,const void*table,void**out,size_t*size){return assets&&models&&assembly_commands_impl(c,n,ids,b,alpha,read,user,NULL,NULL,asset_user,rotation,serial,begin,end,page,table,out,size,models,model_user,15,assets);}

int nf_assembly_model_bounds(NFSceneAssembly*s,unsigned index,const uint16_t bounds[4]){
 if(!s||s->failed||!bounds||index>=s->model_count||s->models[index].bounded||bounds[0]>bounds[1]||bounds[1]>240||bounds[2]>bounds[3]||bounds[3]>160)return fail(s);
 memcpy(s->models[index].bounds,bounds,8);s->models[index].bounded=1;return 1;
}
int nf_assembly_road_camera(NFSceneAssembly*s,unsigned index,const NFRoadCameraMetadata*camera){
 if(!s||s->failed||!camera||index>=s->count)return fail(s);
 Item*t=s->surface+index;
 if((t->index_mode!=5&&t->index_mode!=6)||camera->version!=1||(camera->address&3)||(uint64_t)camera->address+48>0x100000000ull||56u>NF_ASSEMBLY_BUDGET-s->bytes)return fail(s);
 size_t pixels=t->index_size-288;uint8_t*copy=malloc(t->index_size+56);if(!copy)return fail(s);
 memcpy(copy,t->indices,pixels);memcpy(copy+pixels,camera,56);memcpy(copy+pixels+56,t->indices+pixels,288);
 free(t->indices);t->indices=copy;t->index_size+=56;t->index_mode=t->index_mode==6?10:9;s->bytes+=56;return 1;
}

int nf_assembly_commands_road_camera_model_inputs(const NFNativeSceneCommand*c,unsigned n,const uint32_t*ids,const uint16_t*b,double alpha,NFReadMemory read,void*user,NFScenePalette palette,void*palette_user,const int32_t rotation[12],NFSceneModelInputs models,void*model_user,uint32_t serial,uint32_t begin,uint32_t end,uint32_t page,const void*table,void**out,size_t*size){return palette&&models&&assembly_commands_impl(c,n,ids,b,alpha,read,user,NULL,palette,palette_user,rotation,serial,begin,end,page,table,out,size,models,model_user,31,NULL);}

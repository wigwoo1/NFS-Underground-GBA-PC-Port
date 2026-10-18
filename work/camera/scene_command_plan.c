static unsigned model_dispatch_trace[8];
__declspec(dllexport) void nf_model_dispatch_trace(unsigned out[8]){for(unsigned i=0;i<8;i++)out[i]=model_dispatch_trace[i];}
static unsigned model_classification_trace[8];
__declspec(dllexport) void nf_model_classification_trace(unsigned out[8]){for(unsigned i=0;i<8;i++)out[i]=model_classification_trace[i];}
#include "scene_command_plan.h"
#include "road_polygon_clip.h"
#include <stdlib.h>
#include <string.h>
typedef struct {uint8_t state[256],current_state[256],*objects,bits[32],edges[32*52],stream[192*24];unsigned object_count,used,capacity;uint32_t matrix[12],object_address;NFVisibilityRead read;void*read_user;const uint32_t*reciprocal;NFSceneObjectCallback callback;void*callback_user;NFNativeSceneCommand*commands;uint32_t failure_line,phase,source,read_address,debug[13];} NFScenePlan;
static uint32_t command_occurrence_trace[1+144*13];
__declspec(dllexport) void nf_command_occurrence_trace(uint32_t out[1873]){if(out)memcpy(out,command_occurrence_trace,sizeof(command_occurrence_trace));}
static uint32_t command_plan_visits[1+2048*3];
static uint8_t command_plan_object_mask[32];
void nf_scene_command_plan_object_mask(uint8_t out[32]){if(out)memcpy(out,command_plan_object_mask,32);}
void nf_scene_command_plan_visits(uint32_t out[1+2048*3]){if(out)memcpy(out,command_plan_visits,sizeof(command_plan_visits));}
static uint32_t command_plan_road[12+128*6];
void nf_scene_command_plan_road(uint32_t out[12+128*6]){if(out)memcpy(out,command_plan_road,sizeof(command_plan_road));}
static uint32_t command_plan_detail[18];
void nf_scene_command_plan_detail(uint32_t out[18]){if(out)memcpy(out,command_plan_detail,sizeof(command_plan_detail));}
static int plan_failure(NFScenePlan*p,unsigned line){if(!p->failure_line)p->failure_line=line;return 0;}
static uint32_t plan_word(const uint8_t*p){uint32_t v;memcpy(&v,p,4);return v;}
static uint16_t plan_half(const uint8_t*p){uint16_t v;memcpy(&v,p,2);return v;}
static void plan_road_failure(unsigned stage,const int32_t*vertices,unsigned count,const uint8_t*state,const NFVisibilityRegionAction*a,unsigned orientation,unsigned affine,const uint32_t*framebuffer){
 command_plan_road[0]=stage;command_plan_road[1]=count;command_plan_road[2]=plan_half(state+226);command_plan_road[3]=plan_half(state+228);command_plan_road[4]=plan_half(a->record+6);command_plan_road[5]=plan_half(a->record+8);command_plan_road[6]=orientation;command_plan_road[7]=affine;if(framebuffer)memcpy(command_plan_road+8,framebuffer,16);if(count<=128)memcpy(command_plan_road+12,vertices,count*24u);
}
static int plan_read(void*user,uint32_t address,void*out,size_t bytes){
 NFScenePlan*p=user;if(!p->read(p->read_user,address,out,bytes)){p->read_address=address;return plan_failure(p,__LINE__);}
 uint64_t end=(uint64_t)address+bytes,pool_end=(uint64_t)p->object_address+p->object_count*164u;
 uint64_t lo=address>p->object_address?address:p->object_address,hi=end<pool_end?end:pool_end;
 if(lo<hi)memcpy((uint8_t*)out+(size_t)(lo-address),p->objects+(size_t)(lo-p->object_address),(size_t)(hi-lo));
 uint32_t matrix_address=plan_word(p->state+84);uint64_t matrix_end=(uint64_t)matrix_address+48;
 lo=address>matrix_address?address:matrix_address;hi=end<matrix_end?end:matrix_end;
 if(lo<hi)memcpy((uint8_t*)out+(size_t)(lo-address),(const uint8_t*)p->matrix+(size_t)(lo-matrix_address),(size_t)(hi-lo));
 return 1;
}
static int plan_expand(void*user,const uint8_t record[16],unsigned pass,NFVisibilityRegionAction*out,unsigned capacity,unsigned*count){
 NFScenePlan*p=user;uint8_t viewport[16],descriptor[48];uint32_t geometry[2];
 if(nfs_visibility_region_setup(p->current_state,record,plan_read,p,viewport,descriptor,geometry)<0)return plan_failure(p,__LINE__);
 return nfs_visibility_region_actions(p->state,record,pass,plan_read,p,p->reciprocal,out,capacity,count);
}
static NFNativeSceneCommand*plan_append(NFScenePlan*p,unsigned kind,unsigned owner,const NFVisibilityRegionAction*a,const uint8_t state[256]){
 if(p->used>=p->capacity)return NULL;
 NFNativeSceneCommand*c=p->commands+p->used++;memset(c,0,sizeof(*c));c->kind=kind;c->owner=owner;c->pass=a->pass;c->mask=a->mask;c->object=65535;memcpy(c->record,a->record,16);memcpy(c->state,state,256);memcpy(c->bounds,a->record+2,8);/* Reversed horizontal viewport owns an empty clip interval. */if(c->bounds[0]>c->bounds[1])c->bounds[1]=c->bounds[0];return c;
}
static int plan_surfaces(NFScenePlan*p,unsigned owner,const NFVisibilityRegionAction*a,uint8_t state[256]){
 p->phase=a->kind;p->source=plan_half(a->record);
 uint8_t descriptor[48],viewport[16],vertices[32*68];uint32_t geometry[2];
 if(a->kind==4){
  if(!plan_read(p,plan_word(state+20)+(uint32_t)plan_half(a->record)*48,descriptor,48))return plan_failure(p,__LINE__);
  geometry[0]=plan_word(state+16)+(uint32_t)plan_half(descriptor)*68;geometry[1]=plan_half(descriptor+2);if(geometry[1]>32)return plan_failure(p,__LINE__);
 }else if(nfs_visibility_region_setup(state,a->record,plan_read,p,viewport,descriptor,geometry)!=1||
    nfs_visibility_region_reconstruct(state,a->record,plan_read,p,p->reciprocal,p->edges,sizeof(p->edges),p->stream,64*24)!=1)return plan_failure(p,__LINE__);
 if(!plan_read(p,geometry[0],vertices,geometry[1]*68u))return plan_failure(p,__LINE__);
 NFVisibilityWallDraw walls[32];unsigned count;uint32_t deferred;
 if(!nfs_visibility_wall_draw_plan(state,vertices,geometry[1],p->edges,a->mask,plan_read,p,walls,32,&count,&deferred))return plan_failure(p,__LINE__);
 for(unsigned i=0;i<count;i++){
  NFNativeSceneCommand*c=plan_append(p,2,owner,a,state);if(!c)return plan_failure(p,__LINE__);
  c->source=geometry[0]+walls[i].edge*68;c->material[0]=walls[i].resolved_material;c->material[1]=walls[i].texture;c->material[2]=walls[i].shift;c->material[3]=walls[i].height;c->xyz[0]=walls[i].flags;memcpy(c->edge,p->edges+walls[i].edge*52,52);
 }
 if(a->kind==4)return 1;
 unsigned input_count=plan_half(state+242),clipped_count=0;int32_t clipped[128*6];
 if(plan_half(descriptor+8)||plan_half(descriptor+4)){
  if(!nf_road_polygon_clip((const int32_t*)p->stream,input_count,plan_half(state+226),plan_half(state+228),p->reciprocal,clipped,128,&clipped_count)){plan_road_failure(1,(const int32_t*)p->stream,input_count,state,a,0,0,NULL);return plan_failure(p,__LINE__);}
  memcpy(p->stream+input_count*24u,clipped,clipped_count*24u);
  uint16_t n=(uint16_t)clipped_count;memcpy(state+244,&n,2);
 }
 for(unsigned secondary=0;secondary<2;secondary++){
  unsigned index=plan_half(descriptor+(secondary?4:8));if(!index)continue;
  uint8_t material[32],animation[8];uint32_t address=plan_word(state+32)+index*32;
  if(!plan_read(p,address,material,32)||!plan_read(p,plan_word(state+72)+plan_half(material)*8u,animation,8))return plan_failure(p,__LINE__);
  address+=(uint32_t)plan_half(animation+2)*32;if(!plan_read(p,address,material,32))return plan_failure(p,__LINE__);
  NFNativeSceneCommand*c=plan_append(p,1,owner,a,state);if(!c)return plan_failure(p,__LINE__);
  c->source=plan_word(state+20)+(uint32_t)plan_half(a->record)*48;c->material[0]=address;c->material[1]=plan_word(state)+plan_word(material+4);c->material[2]=plan_half(material+26);c->material[3]=plan_half(material+10);
  c->xyz[0]=descriptor[18]&(secondary?2:1);c->xyz[1]=plan_half(a->record+10)&1;c->xyz[2]=secondary;c->vertex_count=clipped_count;memcpy(c->vertices,clipped,clipped_count*24u);
  if(secondary)for(unsigned i=0;i<clipped_count;i++){c->vertices[i*6+1]=c->vertices[i*6+2];memcpy(p->stream+(input_count+i)*24u+4,c->vertices+i*6+1,4);}
  uint32_t framebuffer[4]={0},coverage[512*4],spans[512*20]={0};unsigned span_count;
  if(!plan_read(p,plan_word(state+80),framebuffer,sizeof(framebuffer))||
     !nf_road_span_plan(c->vertices,clipped_count,c->bounds[2],c->bounds[3],c->xyz[0],c->xyz[1],p->reciprocal,framebuffer,coverage,512,&span_count)){plan_road_failure(2,c->vertices,clipped_count,state,a,c->xyz[0],c->xyz[1],framebuffer);return plan_failure(p,__LINE__);}
  for(unsigned i=0;i<span_count;i++)memcpy(spans+i*20,coverage+i*4,16);
  if(!nf_road_clip_bounds(c->bounds,framebuffer,spans,span_count,c->bounds,&c->cell_end)){for(unsigned j=0;j<4;j++)p->debug[j]=c->bounds[j];memcpy(p->debug+4,framebuffer,16);p->debug[8]=span_count;if(span_count)memcpy(p->debug+9,spans+(span_count-1)*20,16);return plan_failure(p,__LINE__);}
 }
 memcpy(p->current_state,state,256);return 1;
}
static int plan_emit(void*user,NFRegionExecutor*executor,unsigned owner,const NFVisibilityRegionAction*a){
 NFScenePlan*p=user;uint8_t state[256];memcpy(state,p->current_state,256);
 if(a->kind!=3)return plan_surfaces(p,owner,a,state);
 model_dispatch_trace[0]++;model_dispatch_trace[1]=plan_half(a->record);model_dispatch_trace[2]=a->pass;NFVisibilityObjectSource sources[512];unsigned count;NFVisibilityObjectDispatch dispatch;
 if(!nfs_visibility_object_sources(state,a->record,plan_read,p,sources,512,&count)||!nfs_visibility_object_dispatch_begin(&dispatch,sources,count,p->object_count))return plan_failure(p,__LINE__);
 model_dispatch_trace[3]+=count;uint32_t head=65535,maximum=UINT32_MAX;unsigned region;int source_status;
 while((source_status=nfs_visibility_object_dispatch_next(&dispatch,&region))==1){
  for(;;){
   if(dispatch.collector.cursor.current<256)command_plan_object_mask[dispatch.collector.cursor.current/8]|=1u<<(dispatch.collector.cursor.current&7);
   if(dispatch.collector.cursor.current!=65535){model_dispatch_trace[4]++;model_dispatch_trace[5]=dispatch.collector.cursor.current;unsigned n=command_plan_visits[0];if(n<2048){command_plan_visits[1+n*3]=plan_half(a->record);command_plan_visits[2+n*3]=a->pass;command_plan_visits[3+n*3]=dispatch.collector.cursor.current;command_plan_visits[0]++;}}
   uint32_t selector;int status=nfs_visibility_object_collect_step(&dispatch.collector,p->objects,p->bits,32,p->matrix,&head,&maximum,&selector);
   if(status<0)return plan_failure(p,__LINE__);
   if(!status)break;
   if(status==2){
    if(!p->callback||!p->callback(p->callback_user,dispatch.collector.cursor.current,selector,p->objects,p->object_count,p->bits,p->matrix,&head,&maximum))return plan_failure(p,__LINE__);
    if(nfs_visibility_object_collect_step(&dispatch.collector,p->objects,p->bits,32,p->matrix,&head,&maximum,&selector)!=1)return plan_failure(p,__LINE__);
   }
  }
 }
 if(source_status<0)return plan_failure(p,__LINE__);
 uint32_t indices[512];unsigned amount;if(!nfs_visibility_object_sorted_plan(p->objects,p->object_count,head,indices,512,&amount))return plan_failure(p,__LINE__);
 for(unsigned i=0;i<amount;i++){
  unsigned index=indices[i],branch;uint8_t child[16]={0};uint32_t xyz[3];uint8_t*object=p->objects+index*164;
  if(nfs_visibility_object_branch_prepare(state,object,a->record,p->matrix,xyz,&branch,child)!=1)return plan_failure(p,__LINE__);
  memcpy(p->current_state+226,state+226,4);
  if(branch){if(!nf_region_execute(executor,child,0))return plan_failure(p,__LINE__);continue;}
  model_classification_trace[0]++;model_classification_trace[1]=index;model_classification_trace[2]=object[0x88];uint32_t material[4];int visible=nfs_visibility_object_material_plan(state,object,xyz,plan_read,p,p->reciprocal,material);model_classification_trace[3]=(unsigned)visible;if(visible<0)return plan_failure(p,__LINE__);if(!visible)continue;
  uint8_t model[68]={0};uint32_t billboard[18];int ready;
  if(material[3]){ready=nfs_visibility_object_billboard_plan(state,object,xyz,material,plan_read,p,p->reciprocal,billboard);if(ready==-2)return plan_failure(p,__LINE__);}
  else {ready=nfs_visibility_object_model_plan(state,object,material,plan_read,p,model);if(ready<0)return plan_failure(p,__LINE__);}
  model_classification_trace[4]=(unsigned)ready;model_classification_trace[5]=material[3];if(ready!=1)continue;model_classification_trace[6]++;
  NFNativeSceneCommand*c=plan_append(p,material[3]?6:5,owner,a,state);if(!c)return plan_failure(p,__LINE__);
  c->object=index;c->source=p->object_address+index*164;memcpy(c->xyz,xyz,12);memcpy(c->material,material,16);
  if(material[3])memcpy(c->billboard,billboard,72);else memcpy(c->model,model,68);
 }
 return 1;
}
int nf_scene_command_plan(const uint8_t state[256],const void*queue,unsigned queue_count,uint8_t*objects,unsigned object_count,uint8_t bits[32],NFVisibilityRead read,void*read_user,const uint32_t reciprocal[32768],NFSceneObjectCallback callback,void*callback_user,NFNativeSceneCommand*out,unsigned capacity,unsigned*out_count){
 memset(model_dispatch_trace,0,sizeof(model_dispatch_trace));memset(model_classification_trace,0,sizeof(model_classification_trace));memset(command_plan_road,0,sizeof(command_plan_road));memset(command_plan_visits,0,sizeof(command_plan_visits));memset(command_plan_detail,0,sizeof(command_plan_detail));
 memset(command_plan_object_mask,0,32);
 if(!state||!objects||!object_count||object_count>256||!bits||!read||!reciprocal||!out||!out_count||!capacity||capacity>65536)return 0;
 NFScenePlan p={0};p.objects=malloc(object_count*164u);p.commands=malloc((size_t)capacity*sizeof(*out));if(!p.objects||!p.commands){free(p.objects);free(p.commands);return 0;}
 memcpy(p.state,state,256);memcpy(p.current_state,state,256);memcpy(p.objects,objects,object_count*164u);memcpy(p.bits,bits,32);p.object_count=object_count;p.object_address=plan_word(state+60);p.capacity=capacity;p.read=read;p.read_user=read_user;p.reciprocal=reciprocal;p.callback=callback;p.callback_user=callback_user;
 int ok=read(read_user,plan_word(state+84),p.matrix,48)&&read(read_user,plan_word(state+104),p.edges,sizeof(p.edges))&&read(read_user,plan_word(state+108),p.stream,sizeof(p.stream));NFRegionExecutor executor;
 if(ok)ok=nf_region_executor_begin(&executor,plan_expand,plan_emit,&p,32,4096)&&nf_region_execute_queue(&executor,queue,queue_count);
 if(ok){memcpy(out,p.commands,p.used*sizeof(*out));*out_count=p.used;memcpy(objects,p.objects,object_count*164u);memcpy(bits,p.bits,32);}
 memset(command_occurrence_trace,0,sizeof(command_occurrence_trace));if(ok){command_occurrence_trace[0]=p.used<144?p.used:144;for(unsigned i=0;i<command_occurrence_trace[0];i++){NFNativeSceneCommand*c=p.commands+i;uint32_t*r=command_occurrence_trace+1+i*13;r[0]=c->kind;r[1]=c->source;r[2]=c->owner;r[3]=c->pass;r[4]=c->mask;memcpy(r+5,c->record,16);for(unsigned k=0;k<4;k++)r[9+k]=c->bounds[k];}}
command_plan_detail[0]=p.failure_line;command_plan_detail[1]=p.used;command_plan_detail[2]=p.phase;command_plan_detail[3]=p.source;command_plan_detail[4]=p.read_address;memcpy(command_plan_detail+5,p.debug,sizeof(p.debug));
 free(p.objects);free(p.commands);return ok;
}

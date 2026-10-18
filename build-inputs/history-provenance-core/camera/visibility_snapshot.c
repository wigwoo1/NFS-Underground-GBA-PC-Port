#include <math.h>
#include "visibility_snapshot.h"
#include "scene_assembly.h"
#include "object_projection.h"
#include <stdlib.h>
#include <string.h>
#include <limits.h>
static unsigned snapshot_owned_callbacks;
void nf_visibility_snapshot_owned_callbacks(int enabled){snapshot_owned_callbacks=enabled!=0;}
struct NFVisibilityAssets {size_t size;unsigned refs;uint8_t rom[];};
struct NFVisibilitySnapshot {NFVisibilityAssets*assets;NFVisibilityIdentity identity;unsigned bound,palette_present,prepared,query_owned;uint32_t state_address,selected,recovery,base[2],query[12],view[12];uint8_t ram[0x48000],palette[512];};
struct NFVisibilityHistory {NFVisibilityAssets*assets;size_t budget;unsigned count,capacity;NFVisibilitySnapshot*entries[16];};
size_t nf_visibility_history_budget(NFVisibilityAssets*a,unsigned count){return !a||count>16?0:sizeof(NFVisibilityHistory)+sizeof(*a)+a->size+(size_t)count*sizeof(NFVisibilitySnapshot);}
NFVisibilityHistory* nf_visibility_history_create(NFVisibilityAssets*a,size_t budget){
 if(!a||a->refs==UINT_MAX||budget<nf_visibility_history_budget(a,1))return NULL;
 NFVisibilityHistory*h=calloc(1,sizeof(*h));if(!h)return NULL;
 h->assets=a;h->budget=budget;h->capacity=16;
 while(nf_visibility_history_budget(a,h->capacity)>budget)h->capacity--;
 a->refs++;return h;
}
size_t nf_visibility_history_bytes(const NFVisibilityHistory*h){return h?nf_visibility_history_budget(h->assets,h->count):0;}
void nf_visibility_history_destroy(NFVisibilityHistory*h){if(h){for(unsigned i=0;i<h->count;i++)nf_visibility_snapshot_destroy(h->entries[i]);nf_visibility_assets_release(h->assets);free(h);}}
int nf_visibility_history_push(NFVisibilityHistory*h,const NFVisibilitySnapshot*s){
 if(!h||!s||!s->bound||s->assets!=h->assets||h->assets->refs==UINT_MAX)return 0;
 unsigned reset=0;
 if(h->count){const NFVisibilityIdentity*last=&h->entries[h->count-1]->identity;
  if(s->identity.epoch<last->epoch)return 0;
  reset=s->identity.epoch>last->epoch;
  if(!reset&&(s->identity.serial<=last->serial||s->identity.end_refresh<last->end_refresh))return 0;
 }
 NFVisibilitySnapshot*copy=malloc(sizeof(*copy));if(!copy)return 0;
 memcpy(copy,s,sizeof(*copy));h->assets->refs++;
 if(reset){for(unsigned i=0;i<h->count;i++)nf_visibility_snapshot_destroy(h->entries[i]);h->count=0;}
 if(h->count==h->capacity){nf_visibility_snapshot_destroy(h->entries[0]);memmove(h->entries,h->entries+1,(h->count-1)*sizeof(h->entries[0]));h->count--;}
 h->entries[h->count++]=copy;return 1;
}
int nf_visibility_history_evaluate(NFVisibilityHistory*h,uint64_t epoch,uint32_t serial,uint32_t begin_refresh,uint32_t end_refresh,NFVisibilityResult*out){
 if(!h)return 0;
 for(unsigned i=0;i<h->count;i++)if(h->entries[i]->identity.epoch==epoch&&h->entries[i]->identity.serial==serial)return nf_visibility_snapshot_evaluate_for(h->entries[i],epoch,serial,begin_refresh,end_refresh,out);
 return 0;
}
NFVisibilityAssets* nf_visibility_assets_create(const void*rom,size_t size){
 if(!rom||size<0x647700||size>32u*1024u*1024u)return NULL;
 NFVisibilityAssets*a=malloc(sizeof(*a)+size);if(!a)return NULL;
 a->size=size;a->refs=1;memcpy(a->rom,rom,size);return a;
}
void nf_visibility_assets_release(NFVisibilityAssets*a){if(a&&!--a->refs)free(a);}
int nf_visibility_snapshot_read(NFVisibilitySnapshot*s,uint32_t address,void*out,size_t size){
 if(!s||(!out&&size))return 0;
 const uint8_t*data=NULL;size_t length=0;uint32_t start=0;
 if(address>=0x02000000&&address<0x02040000){start=0x02000000;data=s->ram;length=0x40000;}
 else if(address>=0x03000000&&address<0x03008000){start=0x03000000;data=s->ram+0x40000;length=0x8000;}
 else if(address>=0x08000000&&(uint64_t)address<0x08000000ull+s->assets->size){start=0x08000000;data=s->assets->rom;length=s->assets->size;}
 else if(s->palette_present&&address>=0x05000000&&address<0x05000200){start=0x05000000;data=s->palette;length=512;}
 else return 0;
 size_t offset=address-start;if(size>length-offset)return 0;
 if(size)memcpy(out,data+offset,size);
 return 1;
}
static int retained_read(void*context,uint32_t address,void*out,size_t size){return nf_visibility_snapshot_read(context,address,out,size);}
NFVisibilitySnapshot* nf_visibility_snapshot_create(NFVisibilityAssets*a,const void*ram,size_t size,uint32_t state_address,uint32_t selected,uint32_t recovery,const uint32_t base[2],const uint32_t query[12],const uint32_t view[12]){
 if(!a||a->refs==UINT_MAX||!ram||size!=0x48000||selected>=512||recovery>=512||!base||!query||!view)return NULL;
 NFVisibilitySnapshot*s=malloc(sizeof(*s));if(!s)return NULL;
 s->assets=a;s->query_owned=0;s->prepared=0;s->bound=0;s->palette_present=0;memset(s->palette,0,sizeof(s->palette));memset(&s->identity,0,sizeof(s->identity));s->state_address=state_address;s->selected=selected;s->recovery=recovery;
 memcpy(s->ram,ram,size);memcpy(s->base,base,8);memcpy(s->query,query,48);memcpy(s->view,view,48);
 uint8_t state[256];
 if(!((state_address>=0x02000000&&state_address<=0x0203ff00)||(state_address>=0x03000000&&state_address<=0x03007f00))||!nf_visibility_snapshot_read(s,state_address,state,256)){free(s);return NULL;}
 a->refs++;return s;
}
NFVisibilitySnapshot* nf_visibility_snapshot_create_prepared(NFVisibilityAssets*a,const void*ram,size_t size,uint32_t state_address,uint32_t selected){
 const uint32_t unused_base[2]={0},unused_query[12]={0},unused_view[12]={0};
 NFVisibilitySnapshot*s=nf_visibility_snapshot_create(a,ram,size,state_address,selected,0,unused_base,unused_query,unused_view);
 if(!s)return NULL;uint8_t state[256];uint32_t address;
 if(!nf_visibility_snapshot_read(s,state_address,state,256)){nf_visibility_snapshot_destroy(s);return NULL;}
 memcpy(&address,state+0x54,4);
 if(!nf_visibility_snapshot_read(s,address,s->view,48)){nf_visibility_snapshot_destroy(s);return NULL;}
 s->prepared=1;return s;
}
int nf_visibility_snapshot_attach_query(NFVisibilitySnapshot*s,const uint32_t base[2],const uint32_t query[12]){
 if(!s||!s->prepared||s->bound||s->query_owned||!base||!query)return 0;
 for(unsigned i=0;i<3;i++)for(unsigned j=0;j<3;j++)if(query[i*3+j]!=s->view[j*3+i])return 0;
 if((int64_t)(int32_t)s->view[9]!=-(int64_t)((int32_t)base[0]>>8)||(int64_t)(int32_t)s->view[11]!=-(int64_t)((int32_t)base[1]>>8))return 0;
 memcpy(s->base,base,8);memcpy(s->query,query,48);s->query_owned=1;return 1;
}
int nf_visibility_snapshot_owned_query(const NFVisibilitySnapshot*s,uint32_t out[14]){if(!s||!out||!s->query_owned)return 0;memcpy(out,s->base,8);memcpy(out+2,s->query,48);return 1;}
int nf_visibility_snapshot_prepared_view(const NFVisibilitySnapshot*s,uint32_t out[12]){if(!s||!s->prepared||!out)return 0;memcpy(out,s->view,48);return 1;}
NFVisibilitySnapshot* nf_visibility_snapshot_clone_focal(const NFVisibilitySnapshot*source,uint32_t focal){
 if(!source||!source->prepared||!source->assets||source->assets->refs==UINT_MAX||!focal||focal>32767)return NULL;
 uint8_t state[256],projection[32];uint32_t address;
 if(!nf_visibility_snapshot_read((NFVisibilitySnapshot*)source,source->state_address,state,256))return NULL;
 memcpy(&address,state+80,4);
 if(!nf_visibility_snapshot_read((NFVisibilitySnapshot*)source,address,projection,32))return NULL;
 size_t offset;if(address>=0x02000000&&address<=0x02040000-32)offset=address-0x02000000;
 else if(address>=0x03000000&&address<=0x03008000-32)offset=0x40000+address-0x03000000;
 else return NULL;
 NFVisibilitySnapshot*copy=malloc(sizeof(*copy));if(!copy)return NULL;
 memcpy(copy,source,sizeof(*copy));copy->assets->refs++;memcpy(copy->ram+offset+28,&focal,4);return copy;
}
typedef struct {NFVisibilitySnapshot*s;uint32_t address;const uint32_t*view;} NFPreparedViewRead;
static int prepared_view_read(void*context,uint32_t address,void*out,size_t size){
 NFPreparedViewRead*r=context;if(!nf_visibility_snapshot_read(r->s,address,out,size))return 0;
 uint64_t end=(uint64_t)address+size,limit=(uint64_t)r->address+48;
 uint64_t lo=address>r->address?address:r->address,hi=end<limit?end:limit;
 if(lo<hi)memcpy((uint8_t*)out+(size_t)(lo-address),(const uint8_t*)r->view+(size_t)(lo-r->address),(size_t)(hi-lo));
 return 1;
}
static uint32_t sampled_root_trace[4];
__declspec(dllexport) void nf_sampled_root_trace(uint32_t out[4]){if(out)memcpy(out,sampled_root_trace,sizeof(sampled_root_trace));}
static uint32_t prepared_queue_trace[1+512];
__declspec(dllexport) void nf_prepared_queue_trace(uint32_t out[513]){if(out)memcpy(out,prepared_queue_trace,sizeof(prepared_queue_trace));}
static int prepared_view_evaluate(NFVisibilitySnapshot*s,const uint32_t view[12],NFVisibilityResult*out){
 if(!s||!s->prepared||!view||!out)return 0;
 NFVisibilityResult result;uint32_t queue,groups,address;
 if(!nf_visibility_snapshot_read(s,s->state_address,result.state,256))return 0;
 memcpy(&queue,result.state+0x60,4);memcpy(&groups,result.state+0x64,4);memcpy(&address,result.state+0x54,4);
 if(!nf_visibility_snapshot_read(s,queue,result.queue,NF_VISIBILITY_QUEUE_BYTES)||!nf_visibility_snapshot_read(s,groups,result.groups,4096))return 0;
 NFPreparedViewRead read={s,address,view};result.selected=s->selected;
 /* Spatial selection must precede traversal when a sampled camera leaves its captured seed. Exact captured views retain the original root bytes. */
 sampled_root_trace[0]=getenv("NF_TEST_SAMPLED_ROOT_SELECTION")!=NULL;sampled_root_trace[1]=memcmp(view,s->view,48)!=0;sampled_root_trace[2]=s->selected;sampled_root_trace[3]=65535;if(sampled_root_trace[0]&&sampled_root_trace[1]){uint32_t point_x=0u-view[9],point_z=0u-view[11],found;memcpy(result.state+192,&point_x,4);memcpy(result.state+200,&point_z,4);uint16_t selected=(uint16_t)s->selected;memcpy(result.state+234,&selected,2);if(!nfs_visibility_select(result.state,prepared_view_read,&read,&found)||found==65535)return 0;uint32_t query[12]={0},offset[3],pair[2],chosen;for(unsigned i=0;i<3;i++)for(unsigned j=0;j<3;j++)query[i*3+j]=view[j*3+i];if(!nfs_visibility_offset(query,offset))return 0;uint32_t point[4]={point_x*256u,point_z*256u,offset[0],offset[2]};if(!nfs_visibility_pair(result.state,s->selected,point,prepared_view_read,&read,pair))return 0;uint8_t root[16]={0};if(!nfs_visibility_choose_root(result.state,pair,prepared_view_read,&read,&chosen,root))return 0;/* Original build_pair initializes a fresh seed including depth/pass flags. Captured traversal metadata must not follow a newly selected descriptor. */memset(result.queue,0,16);memcpy(result.queue+2,result.state+0x58,8);memcpy(result.queue,root,2);result.selected=chosen;sampled_root_trace[3]=chosen;}
 if(!nfs_visibility_build(result.state,result.queue,result.groups,prepared_view_read,&read,(const uint32_t*)(s->assets->rom+0x627700)))return 0;
 memset(prepared_queue_trace,0,sizeof(prepared_queue_trace));uint16_t trace_count;memcpy(&trace_count,result.state+238,2);prepared_queue_trace[0]=trace_count;for(unsigned i=0;i<trace_count&&i<512;i++){uint16_t region;memcpy(&region,result.queue+i*16,2);prepared_queue_trace[i+1]=region;}
 memcpy(out,&result,sizeof(result));return 1;
}
int nf_visibility_snapshot_evaluate_prepared_view(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const uint32_t view[12],NFVisibilityResult*out){
 if(!s||!s->prepared||!view||!out||!s->bound||s->identity.epoch!=epoch||s->identity.serial!=serial||s->identity.begin_refresh!=begin||s->identity.end_refresh!=end)return 0;
 return prepared_view_evaluate(s,view,out);
}
NFVisibilitySnapshot* nf_visibility_snapshot_clone(const NFVisibilitySnapshot*s){
 if(!s||s->assets->refs==UINT_MAX)return NULL;
 NFVisibilitySnapshot*copy=malloc(sizeof(*copy));if(!copy)return NULL;
 memcpy(copy,s,sizeof(*copy));copy->assets->refs++;return copy;
}
void nf_visibility_snapshot_destroy(NFVisibilitySnapshot*s){if(s){nf_visibility_assets_release(s->assets);free(s);}}
int nf_visibility_snapshot_set_palette(NFVisibilitySnapshot*s,const void*palette,size_t size){
 if(!s||!palette||size!=512||s->bound||s->palette_present)return 0;
 memcpy(s->palette,palette,512);s->palette_present=1;return 1;
}
int nf_visibility_snapshot_bind(NFVisibilitySnapshot*s,const NFVisibilityIdentity*id){
 if(!s||!id||s->bound||!id->epoch||id->begin_refresh>id->query_refresh||id->query_refresh>id->builder_refresh||id->builder_refresh>id->end_refresh)return 0;
 s->identity=*id;s->bound=1;return 1;
}
int nf_visibility_snapshot_evaluate_for(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin_refresh,uint32_t end_refresh,NFVisibilityResult*out){
 if(!s||!s->bound||s->identity.epoch!=epoch||s->identity.serial!=serial||s->identity.begin_refresh!=begin_refresh||s->identity.end_refresh!=end_refresh)return 0;
 return nf_visibility_snapshot_evaluate(s,out);
}
static int visibility_snapshot_evaluate_inputs(NFVisibilitySnapshot*s,const NFVisibilityPoseInputs*pose,NFVisibilityResult*out){
 if(!s||!out)return 0;
 NFVisibilityResult result;uint32_t queue,groups;
 if(!nf_visibility_snapshot_read(s,s->state_address,result.state,256))return 0;
 memcpy(&queue,result.state+0x60,4);memcpy(&groups,result.state+0x64,4);
 if(!nf_visibility_snapshot_read(s,queue,result.queue,NF_VISIBILITY_QUEUE_BYTES)||!nf_visibility_snapshot_read(s,groups,result.groups,4096))return 0;
 result.selected=s->selected;
 if(s->prepared){if(pose||!nfs_visibility_build(result.state,result.queue,result.groups,retained_read,s,(const uint32_t*)(s->assets->rom+0x627700)))return 0;}
 else if(!nfs_visibility_evaluate(result.state,result.queue,result.groups,&result.selected,s->recovery,pose?pose->base:s->base,pose?pose->query:s->query,pose?pose->view:s->view,retained_read,s,(const uint32_t*)(s->assets->rom+0x627700)))return 0;
 memcpy(out,&result,sizeof(result));return 1;
}
int nf_visibility_snapshot_evaluate(NFVisibilitySnapshot*s,NFVisibilityResult*out){return visibility_snapshot_evaluate_inputs(s,NULL,out);}
int nf_visibility_snapshot_evaluate_at(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin_refresh,uint32_t end_refresh,const NFVisibilityPoseInputs*pose,NFVisibilityResult*out){
 if(!s||!pose||!s->bound||s->identity.epoch!=epoch||s->identity.serial!=serial||s->identity.begin_refresh!=begin_refresh||s->identity.end_refresh!=end_refresh)return 0;
 return visibility_snapshot_evaluate_inputs(s,pose,out);
}

int nf_visibility_snapshot_pose(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin_refresh,uint32_t end_refresh,NFVisibilityPoseInputs*out){
 if(!s||s->prepared||!out||!s->bound||s->identity.epoch!=epoch||s->identity.serial!=serial||s->identity.begin_refresh!=begin_refresh||s->identity.end_refresh!=end_refresh)return 0;
 NFVisibilityPoseInputs pose;memcpy(pose.base,s->base,sizeof(pose.base));memcpy(pose.query,s->query,sizeof(pose.query));memcpy(pose.view,s->view,sizeof(pose.view));memcpy(out,&pose,sizeof(pose));return 1;
}

typedef struct {NFVisibilitySnapshot*s;uint32_t address;const uint32_t*view;} NFRegionPoseRead;
static int region_pose_read(void*context,uint32_t address,void*out,size_t size){
 NFRegionPoseRead*r=context;
 if(!nf_visibility_snapshot_read(r->s,address,out,size))return 0;
 uint64_t end=(uint64_t)address+size,limit=(uint64_t)r->address+48;
 uint64_t lo=address>r->address?address:r->address,hi=end<limit?end:limit;
 if(lo<hi)memcpy((uint8_t*)out+(size_t)(lo-address),(const uint8_t*)r->view+(size_t)(lo-r->address),(size_t)(hi-lo));
 return 1;
}
int nf_visibility_snapshot_region_at(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,unsigned ordinal,NFVisibilityRegionResult*out){
 NFVisibilityResult evaluated;NFVisibilityRegionResult result={0};uint16_t count;uint32_t address;
 if(!out||ordinal>=NF_VISIBILITY_QUEUE_CAPACITY||!nf_visibility_snapshot_evaluate_at(s,epoch,serial,begin,end,pose,&evaluated))return 0;
 memcpy(&count,evaluated.state+0xee,2);if(count>NF_VISIBILITY_QUEUE_CAPACITY||ordinal>=count)return 0;
 memcpy(result.state,evaluated.state,256);memcpy(result.record,evaluated.queue+ordinal*16,16);memcpy(&address,result.state+0x54,4);
 if(address>UINT32_MAX-48)return 0;
 NFRegionPoseRead reader={s,address,pose->view};
 if(nfs_visibility_region_reconstruct(result.state,result.record,region_pose_read,&reader,(const uint32_t*)(s->assets->rom+0x627700),result.edges,sizeof(result.edges),result.stream,sizeof(result.stream))!=1)return 0;
 memcpy(out,&result,sizeof(result));return 1;
}

static int snapshot_region_wall_plan(NFVisibilitySnapshot*s,const NFVisibilityRegionResult*region,NFSampledWallPlan*out){
 NFSampledWallPlan result={0};uint16_t flags,index,first,count;uint32_t table,base;
 memcpy(result.record,region->record,16);memcpy(&flags,region->record+10,2);
 if(flags&8){memcpy(out,&result,sizeof(result));return 1;}
 memcpy(&index,region->record,2);memcpy(&table,region->state+20,4);memcpy(&base,region->state+16,4);
 uint8_t descriptor[48],vertices[32*68];uint64_t address=(uint64_t)table+index*48u;
 if(address>UINT32_MAX||!nf_visibility_snapshot_read(s,(uint32_t)address,descriptor,48))return 0;
 memcpy(&first,descriptor,2);memcpy(&count,descriptor+2,2);address=(uint64_t)base+first*68u;
 if(count>32||address>UINT32_MAX||!nf_visibility_snapshot_read(s,(uint32_t)address,vertices,count*68u))return 0;
 uint32_t mask=0;unsigned n;NFVisibilityWallDraw draws[32];
 for(unsigned pass=0;pass<2;pass++){
  uint32_t next;if(pass&&!mask)break;
  if(!nfs_visibility_wall_draw_plan(region->state,vertices,count,region->edges,pass?mask:0,retained_read,s,draws,32,&n,&next))return 0;
  /* Original region wrapper at03002980 retains only the low byte. */
  if(!pass)mask=next&0xffu;
  for(unsigned i=0;i<n;i++){if(draws[i].edge>=count)return 0;NFSampledWallDraw*d=&result.draws[result.count++];d->source=(uint32_t)address+draws[i].edge*68u;d->pass=pass;d->draw=draws[i];}
 }
 memcpy(out,&result,sizeof(result));return 1;
}

int nf_visibility_snapshot_wall_plan(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,unsigned ordinal,NFSampledWallPlan*out){
 NFVisibilityRegionResult region;
 if(!out||!nf_visibility_snapshot_region_at(s,epoch,serial,begin,end,pose,ordinal,&region))return 0;
 return snapshot_region_wall_plan(s,&region,out);
}
int nf_visibility_snapshot_object_plan(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,const uint8_t state[256],const uint8_t object[164],NFSampledWallPlan*out){
 NFVisibilityPoseInputs check;NFVisibilityRegionResult region={0};uint32_t address;
 if(!out||!pose||!state||!object||!nf_visibility_snapshot_pose(s,epoch,serial,begin,end,&check))return 0;
 memcpy(region.state,state,256);
 if(nfs_visibility_object_region(state,object,region.record)!=1)return 0;
 memcpy(&address,state+0x54,4);if(address>UINT32_MAX-48)return 0;
 NFRegionPoseRead reader={s,address,pose->view};
 if(nfs_visibility_region_reconstruct(region.state,region.record,region_pose_read,&reader,(const uint32_t*)(s->assets->rom+0x627700),region.edges,sizeof(region.edges),region.stream,sizeof(region.stream))!=1)return 0;
 return snapshot_region_wall_plan(s,&region,out);
}

int nf_visibility_snapshot_queue_plans(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,NFSampledQueuePlans*out){
 NFVisibilityResult evaluated;uint16_t count;uint32_t address;
 if(!out||!nf_visibility_snapshot_evaluate_at(s,epoch,serial,begin,end,pose,&evaluated))return 0;
 memcpy(&count,evaluated.state+0xee,2);memcpy(&address,evaluated.state+0x54,4);
 if(count>NF_VISIBILITY_QUEUE_CAPACITY||address>UINT32_MAX-48)return 0;
 NFSampledQueuePlans*result=calloc(1,sizeof(*result));if(!result)return 0;result->count=count;
 NFRegionPoseRead reader={s,address,pose->view};int ok=1;
 for(unsigned i=0;i<count;i++){
  NFVisibilityRegionResult region={0};uint16_t flags;
  memcpy(region.state,evaluated.state,256);memcpy(region.record,evaluated.queue+i*16,16);memcpy(&flags,region.record+10,2);
  if(flags&8){memcpy(result->plans[i].record,region.record,16);continue;}
  if(nfs_visibility_region_reconstruct(region.state,region.record,region_pose_read,&reader,(const uint32_t*)(s->assets->rom+0x627700),region.edges,sizeof(region.edges),region.stream,sizeof(region.stream))!=1||!snapshot_region_wall_plan(s,&region,&result->plans[i])){ok=0;break;}
 }
 if(ok)memcpy(out,result,sizeof(*result));
 free(result);return ok;
}

typedef struct {NFRegionPoseRead pose;uint32_t pool_address;uint8_t*pool;size_t pool_size;uint32_t scratch_address;uint8_t*scratch;} NFSceneSnapshotRead;
static int scene_snapshot_read(void*user,uint32_t address,void*out,size_t size){
 NFSceneSnapshotRead*r=user;if(!region_pose_read(&r->pose,address,out,size))return 0;
 uint64_t end=(uint64_t)address+size,limit=(uint64_t)r->pool_address+r->pool_size;
 uint64_t lo=address>r->pool_address?address:r->pool_address,hi=end<limit?end:limit;
 if(lo<hi)memcpy((uint8_t*)out+(size_t)(lo-address),r->pool+(size_t)(lo-r->pool_address),(size_t)(hi-lo));
 if(r->scratch){limit=(uint64_t)r->scratch_address+3072;lo=address>r->scratch_address?address:r->scratch_address;hi=end<limit?end:limit;if(lo<hi)memcpy((uint8_t*)out+(size_t)(lo-address),r->scratch+(size_t)(lo-r->scratch_address),(size_t)(hi-lo));}
 return 1;
}
typedef struct {uint8_t state[256],scratch[3072];uint32_t counter;NFSceneSnapshotRead*reader;unsigned calls,sounds;} NFNativeSnapshotCallback;
static int scene_native_callback(void*user,unsigned index,unsigned selector,uint8_t*objects,unsigned count,uint8_t bits[32],uint32_t matrix[12],uint32_t*head,uint32_t*maximum){
 NFNativeSnapshotCallback*c=user;uint32_t table,function;unsigned event;
 (void)bits;(void)matrix;(void)head;(void)maximum;
 if(index>=count||selector!=12)return 0;
 memcpy(&table,c->state+120,4);if(table>UINT32_MAX-48||!scene_snapshot_read(c->reader,table+48,&function,4)||function!=0x0801fc7du)return 0;
 uint8_t*before_pool=c->reader->pool;c->reader->pool=objects;
 int ok=nf_object_callback12_owned(c->state,objects+index*164,&c->counter,c->scratch,scene_snapshot_read,c->reader,&event);c->reader->pool=before_pool;
 if(!ok)return 0;
 c->calls++;c->sounds+=event!=0;return 1;
}
typedef struct {NFSceneObjectCallback callback;void*user;} NFSceneSnapshotCallback;
static int scene_snapshot_callback(void*user,unsigned index,unsigned selector,uint8_t*objects,unsigned count,uint8_t bits[32],uint32_t matrix[12],uint32_t*head,uint32_t*maximum){
 NFSceneSnapshotCallback*c=user;uint32_t before[12];memcpy(before,matrix,48);
 return c->callback(c->user,index,selector,objects,count,bits,matrix,head,maximum)&&!memcmp(before,matrix,48);
}
static uint32_t snapshot_command_trace[2+NF_VISIBILITY_QUEUE_CAPACITY*4+144*16];
static size_t snapshot_command_trace_bytes;
static uint8_t snapshot_query_fixture[120+0x48000];static size_t snapshot_query_fixture_bytes;
size_t nf_visibility_snapshot_query_fixture(void*out,size_t capacity){if(!out||capacity<snapshot_query_fixture_bytes)return 0;memcpy(out,snapshot_query_fixture,snapshot_query_fixture_bytes);return snapshot_query_fixture_bytes;}
size_t nf_visibility_snapshot_command_trace(void*out,size_t capacity){if(!out||capacity<snapshot_command_trace_bytes)return 0;memcpy(out,snapshot_command_trace,snapshot_command_trace_bytes);return snapshot_command_trace_bytes;}
static uint32_t snapshot_packet_detail[6];
void nf_visibility_snapshot_packet_detail(uint32_t out[6]){if(out)memcpy(out,snapshot_packet_detail,sizeof(snapshot_packet_detail));}
static int snapshot_packet_impl(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,double alpha,uint32_t page,const uint8_t*objects,unsigned object_count,const int32_t rotation[12],NFSceneObjectCallback callback,void*callback_user,NFScenePalette selector,void*selector_user,void**out,size_t*out_size,unsigned native_callbacks,NFSceneModelInputs model_selector,void*model_user,unsigned indexed,NFScenePaletteAssets assets,const uint32_t*prepared_view){
 snapshot_command_trace_bytes=0;snapshot_query_fixture_bytes=0;
 memset(snapshot_packet_detail,0,sizeof(snapshot_packet_detail));snapshot_packet_detail[0]=1;
 NFVisibilityResult evaluated;uint16_t queue_count;uint32_t pool_address,matrix_address;
 if(!out||!out_size||!rotation||!object_count||object_count>256||!s||(!s->palette_present&&!selector&&!assets)||
    !(prepared_view?nf_visibility_snapshot_evaluate_prepared_view(s,epoch,serial,begin,end,prepared_view,&evaluated):nf_visibility_snapshot_evaluate_at(s,epoch,serial,begin,end,pose,&evaluated)))return 0;
 memcpy(&queue_count,evaluated.state+238,2);memcpy(&pool_address,evaluated.state+60,4);memcpy(&matrix_address,evaluated.state+84,4);
 if(queue_count>NF_VISIBILITY_QUEUE_CAPACITY)return 0;
 snapshot_packet_detail[0]=2;
 size_t pool_size=object_count*164u;uint8_t*pool=malloc(pool_size);unsigned capacity=model_selector?144u:129u;NFNativeSceneCommand*commands=calloc(capacity,sizeof(*commands));
 if(!pool||!commands){free(pool);free(commands);return 0;}
 int ok=1;if(objects)memcpy(pool,objects,pool_size);else ok=nf_visibility_snapshot_read(s,pool_address,pool,pool_size);
 NFSceneSnapshotRead reader={{s,matrix_address,prepared_view?prepared_view:pose->view},pool_address,pool,pool_size,0,NULL};uint8_t bits[32]={0},palette[512];unsigned count=0;
 NFNativeSnapshotCallback native={0};
 if(native_callbacks){memcpy(native.state,evaluated.state,256);native.reader=&reader;memcpy(&reader.scratch_address,evaluated.state+252,4);ok=ok&&nf_visibility_snapshot_read(s,0x03005ac8,&native.counter,4)&&nf_visibility_snapshot_read(s,reader.scratch_address,native.scratch,3072);reader.scratch=native.scratch;callback=scene_native_callback;callback_user=&native;}
 const uint32_t*reciprocal=(const uint32_t*)(s->assets->rom+0x627700);
 NFSceneSnapshotCallback adapter={callback,callback_user};snapshot_packet_detail[0]=3;
 if(ok)ok=nf_scene_command_plan(evaluated.state,evaluated.queue,queue_count,pool,object_count,bits,scene_snapshot_read,&reader,reciprocal,callback?scene_snapshot_callback:NULL,&adapter,commands,capacity,&count);
 if(ok&&!prepared_view&&getenv("NF_TRACE_NATIVE_COMMANDS")){
  uint32_t header[4]={0x3146514e,s->state_address,s->selected,s->recovery};memcpy(snapshot_query_fixture,header,16);
  if(pose)memcpy(snapshot_query_fixture+16,pose,104);else{memcpy(snapshot_query_fixture+16,s->base,8);memcpy(snapshot_query_fixture+24,s->query,48);memcpy(snapshot_query_fixture+72,s->view,48);}
  memcpy(snapshot_query_fixture+120,s->ram,sizeof(s->ram));snapshot_query_fixture_bytes=sizeof(snapshot_query_fixture);
  snapshot_command_trace[0]=count;snapshot_command_trace[1]=queue_count;
  memcpy(snapshot_command_trace+2,evaluated.queue,queue_count*16u);
  for(unsigned i=0;i<count;i++){
   const NFNativeSceneCommand*c=commands+i;uint32_t*row=snapshot_command_trace+2+queue_count*4+i*16;
   row[0]=c->kind;row[1]=c->owner;row[2]=c->pass;row[3]=c->mask;row[4]=c->object;row[5]=c->source;
   for(unsigned j=0;j<4;j++)row[6+j]=c->bounds[j];memcpy(row+10,c->record,16);
   uint16_t viewport[2];memcpy(viewport,c->state+226,4);row[14]=viewport[0];row[15]=viewport[1];
  }
  snapshot_command_trace_bytes=(2+queue_count*4+count*16)*4u;
 }
 snapshot_packet_detail[1]=count;
 snapshot_packet_detail[5]=native.calls;
 uint32_t identities[144*5];
 for(unsigned i=0;i<count&&ok;i++){
  NFNativeSceneCommand*c=commands+i;snapshot_packet_detail[2]+=c->kind==5;snapshot_packet_detail[3]+=c->kind==6;snapshot_packet_detail[4]+=c->kind==1&&c->xyz[2];uint32_t*id=identities+i*5;id[0]=c->kind==5?3:c->kind;id[1]=s->state_address;id[2]=c->source;id[3]=c->kind==2?c->material[0]:c->kind==1?8:0;id[4]=0;
  if(c->kind==5)memcpy(id+3,c->model+12,4);
 }
 if(ok)snapshot_packet_detail[0]=4;
 if(ok&&assets&&model_selector)ok=((indexed&8)?nf_assembly_commands_road_attributes_assets_model_inputs:nf_assembly_commands_classified_assets_model_inputs)(commands,count,identities,NULL,alpha,scene_snapshot_read,&reader,assets,selector_user,rotation,model_selector,model_user,serial,begin,end,page,reciprocal,out,out_size);
 else if(ok&&model_selector)ok=((indexed&16)?nf_assembly_commands_road_camera_model_inputs:(indexed&8)?nf_assembly_commands_road_attributes_model_inputs:(indexed&4)?nf_assembly_commands_classified_world_model_inputs:(indexed&2)?nf_assembly_commands_indexed_world_model_inputs:indexed?nf_assembly_commands_indexed_model_inputs:nf_assembly_commands_model_inputs)(commands,count,identities,NULL,alpha,scene_snapshot_read,&reader,selector,selector_user,rotation,model_selector,model_user,serial,begin,end,page,reciprocal,out,out_size);
 else if(ok&&selector)ok=nf_assembly_commands_palettes(commands,count,identities,NULL,alpha,scene_snapshot_read,&reader,selector,selector_user,rotation,serial,begin,end,page,reciprocal,out,out_size);
 else if(ok)ok=nf_visibility_snapshot_read(s,0x05000000,palette,512)&&nf_assembly_commands(commands,count,identities,NULL,alpha,scene_snapshot_read,&reader,palette,rotation,serial,begin,end,page,reciprocal,out,out_size);
 if(ok)snapshot_packet_detail[0]=0;
 free(commands);free(pool);return ok;
}

int nf_visibility_snapshot_packet_at(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,double alpha,uint32_t page,const uint8_t*objects,unsigned object_count,const int32_t rotation[12],NFSceneObjectCallback callback,void*callback_user,void**out,size_t*out_size){return snapshot_packet_impl(s,epoch,serial,begin,end,pose,alpha,page,objects,object_count,rotation,callback,callback_user,NULL,NULL,out,out_size,0,NULL,NULL,0,NULL,NULL);}

int nf_visibility_snapshot_packet_palettes_at(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,double alpha,uint32_t page,const uint8_t*objects,unsigned object_count,const int32_t rotation[12],NFSceneObjectCallback callback,void*callback_user,NFScenePalette selector,void*selector_user,void**out,size_t*out_size){return selector&&snapshot_packet_impl(s,epoch,serial,begin,end,pose,alpha,page,objects,object_count,rotation,callback,callback_user,selector,selector_user,out,out_size,0,NULL,NULL,0,NULL,NULL);}
int nf_visibility_snapshot_packet_native_at(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,double alpha,uint32_t page,const uint8_t*objects,unsigned object_count,const int32_t rotation[12],void**out,size_t*out_size){return snapshot_packet_impl(s,epoch,serial,begin,end,pose,alpha,page,objects,object_count,rotation,NULL,NULL,NULL,NULL,out,out_size,1,NULL,NULL,0,NULL,NULL);}
int nf_visibility_snapshot_packet_native_palettes_at(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,double alpha,uint32_t page,const uint8_t*objects,unsigned object_count,const int32_t rotation[12],NFScenePalette selector,void*selector_user,void**out,size_t*out_size){return selector&&snapshot_packet_impl(s,epoch,serial,begin,end,pose,alpha,page,objects,object_count,rotation,NULL,NULL,selector,selector_user,out,out_size,1,NULL,NULL,0,NULL,NULL);}

int nf_visibility_snapshot_packet_native_model_inputs_at(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,double alpha,uint32_t page,const uint8_t*objects,unsigned object_count,const int32_t rotation[12],NFScenePalette selector,void*selector_user,NFSceneModelInputs models,void*model_user,void**out,size_t*out_size){return selector&&models&&snapshot_packet_impl(s,epoch,serial,begin,end,pose,alpha,page,objects,object_count,rotation,NULL,NULL,selector,selector_user,out,out_size,1,models,model_user,0,NULL,NULL);}

int nf_visibility_snapshot_packet_native_indexed_model_inputs_at(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,double alpha,uint32_t page,const uint8_t*objects,unsigned object_count,const int32_t rotation[12],NFScenePalette selector,void*selector_user,NFSceneModelInputs models,void*model_user,void**out,size_t*out_size){return selector&&models&&snapshot_packet_impl(s,epoch,serial,begin,end,pose,alpha,page,objects,object_count,rotation,NULL,NULL,selector,selector_user,out,out_size,1,models,model_user,1,NULL,NULL);}

int nf_visibility_snapshot_packet_native_indexed_world_model_inputs_at(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,double alpha,uint32_t page,const uint8_t*objects,unsigned object_count,const int32_t rotation[12],NFScenePalette selector,void*selector_user,NFSceneModelInputs models,void*model_user,void**out,size_t*out_size){return selector&&models&&snapshot_packet_impl(s,epoch,serial,begin,end,pose,alpha,page,objects,object_count,rotation,NULL,NULL,selector,selector_user,out,out_size,1,models,model_user,3,NULL,NULL);}

int nf_visibility_snapshot_packet_native_classified_world_model_inputs_at(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,double alpha,uint32_t page,const uint8_t*objects,unsigned object_count,const int32_t rotation[12],NFScenePalette selector,void*selector_user,NFSceneModelInputs models,void*model_user,void**out,size_t*out_size){return selector&&models&&snapshot_packet_impl(s,epoch,serial,begin,end,pose,alpha,page,objects,object_count,rotation,NULL,NULL,selector,selector_user,out,out_size,1,models,model_user,7,NULL,NULL);}
int nf_visibility_snapshot_packet_native_classified_assets_model_inputs_at(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,double alpha,uint32_t page,const uint8_t*objects,unsigned object_count,const int32_t rotation[12],NFScenePaletteAssets assets,void*asset_user,NFSceneModelInputs models,void*model_user,void**out,size_t*out_size){return assets&&models&&snapshot_packet_impl(s,epoch,serial,begin,end,pose,alpha,page,objects,object_count,rotation,NULL,NULL,NULL,asset_user,out,out_size,1,models,model_user,7,assets,NULL);}

int nf_visibility_snapshot_packet_native_road_attributes_model_inputs_at(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,double alpha,uint32_t page,const uint8_t*objects,unsigned object_count,const int32_t rotation[12],NFScenePalette selector,void*selector_user,NFSceneModelInputs models,void*model_user,void**out,size_t*out_size){return selector&&models&&snapshot_packet_impl(s,epoch,serial,begin,end,pose,alpha,page,objects,object_count,rotation,NULL,NULL,selector,selector_user,out,out_size,1,models,model_user,15,NULL,NULL);}

int nf_visibility_snapshot_packet_native_road_attributes_assets_model_inputs_at(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,double alpha,uint32_t page,const uint8_t*objects,unsigned object_count,const int32_t rotation[12],NFScenePaletteAssets assets,void*asset_user,NFSceneModelInputs models,void*model_user,void**out,size_t*out_size){return assets&&models&&snapshot_packet_impl(s,epoch,serial,begin,end,pose,alpha,page,objects,object_count,rotation,NULL,NULL,NULL,asset_user,out,out_size,1,models,model_user,15,assets,NULL);}
int nf_visibility_snapshot_packet_prepared_assets_models(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const uint32_t view[12],double alpha,uint32_t page,const uint8_t*objects,unsigned count,const int32_t rotation[12],NFScenePaletteAssets assets,void*asset_user,NFSceneModelInputs models,void*model_user,unsigned road_attributes,void**out,size_t*out_size){
 return view&&assets&&models&&snapshot_packet_impl(s,epoch,serial,begin,end,NULL,alpha,page,objects,count,rotation,NULL,NULL,NULL,asset_user,out,out_size,1,models,model_user,road_attributes?15:7,assets,view);
}
static uint32_t prepared_command_detail[8];
void nf_visibility_snapshot_prepared_command_detail(uint32_t out[8]){if(out)memcpy(out,prepared_command_detail,32);}
static int prepared_commands_impl(NFVisibilitySnapshot*s,NFNativeSceneCommand*out,unsigned capacity,unsigned*out_count,unsigned captured,NFVisibilitySnapshot*builder,const uint32_t*view,uint32_t object_address,const uint8_t*object_record){
 memset(prepared_command_detail,0,32);prepared_command_detail[0]=1;
 if(!s||!s->prepared||!out||!out_count||capacity<144)return 0;
 prepared_command_detail[0]=2;NFVisibilityResult evaluated;if(view||captured){uint32_t queue,groups;if(!nf_visibility_snapshot_read(s,s->state_address,evaluated.state,256))return 0;memcpy(&queue,evaluated.state+96,4);memcpy(&groups,evaluated.state+100,4);if(!nf_visibility_snapshot_read(s,queue,evaluated.queue,NF_VISIBILITY_QUEUE_BYTES)||!nf_visibility_snapshot_read(s,groups,evaluated.groups,4096))return 0;}else if(!nf_visibility_snapshot_evaluate(s,&evaluated))return 0;
 prepared_command_detail[0]=3;if(builder){NFVisibilityResult built;int builder_ok=view?prepared_view_evaluate(builder,view,&built):nf_visibility_snapshot_evaluate(builder,&built);prepared_command_detail[1]=builder_ok;if(!builder_ok)return 0;prepared_command_detail[2]=memcmp(built.queue,evaluated.queue,NF_VISIBILITY_QUEUE_BYTES)!=0;prepared_command_detail[3]=memcmp(built.groups,evaluated.groups,4096)!=0;if(!view&&(prepared_command_detail[2]||prepared_command_detail[3]))return 0;memcpy(evaluated.queue,built.queue,NF_VISIBILITY_QUEUE_BYTES);memcpy(evaluated.groups,built.groups,4096);/* The rebuilt queue owns its count; retaining the captured count visits stale tail records. */if(view)memcpy(evaluated.state+238,built.state+238,2);}
 prepared_command_detail[0]=4;uint16_t count;uint32_t pool_address,matrix_address;memcpy(&count,evaluated.state+238,2);memcpy(&pool_address,evaluated.state+60,4);memcpy(&matrix_address,evaluated.state+84,4);prepared_command_detail[4]=count;if(count>NF_VISIBILITY_QUEUE_CAPACITY)return 0;
 uint8_t*pool=malloc(256*164u);NFNativeSceneCommand*commands=calloc(144,sizeof(*commands));if(!pool||!commands){free(pool);free(commands);return 0;}
 unsigned used=0;uint8_t bits[32]={0};NFSceneSnapshotRead reader={{s,matrix_address,view?view:s->view},pool_address,pool,256*164u,0,NULL};
 prepared_command_detail[0]=5;int ok=nf_visibility_snapshot_read(s,pool_address,pool,256*164u);prepared_command_detail[5]=ok;
 if(ok&&object_record){ok=object_address>=pool_address&&(uint64_t)object_address+164<=(uint64_t)pool_address+256*164u&&(object_address-pool_address)%164==0;if(ok)memcpy(pool+object_address-pool_address,object_record,164);}
 NFNativeSnapshotCallback native={0};NFSceneSnapshotCallback adapter={0};
 if(ok&&(snapshot_owned_callbacks||getenv("NF_TEST_RACING_OWNED_CAPTURE"))){memcpy(native.state,evaluated.state,256);native.reader=&reader;memcpy(&reader.scratch_address,evaluated.state+252,4);ok=nf_visibility_snapshot_read(s,0x03005ac8,&native.counter,4)&&nf_visibility_snapshot_read(s,reader.scratch_address,native.scratch,3072);reader.scratch=native.scratch;adapter.callback=scene_native_callback;adapter.user=&native;}
 if(ok){prepared_command_detail[0]=6;ok=nf_scene_command_plan(evaluated.state,evaluated.queue,count,pool,256,bits,scene_snapshot_read,&reader,(const uint32_t*)(s->assets->rom+0x627700),adapter.callback?scene_snapshot_callback:NULL,&adapter,commands,144,&used);prepared_command_detail[6]=used;prepared_command_detail[7]=native.calls;}
 if(ok){prepared_command_detail[0]=0;memcpy(out,commands,used*sizeof(*out));*out_count=used;}free(pool);free(commands);return ok;
}

int nf_visibility_snapshot_prepared_commands(NFVisibilitySnapshot*s,NFNativeSceneCommand*out,unsigned capacity,unsigned*count){return prepared_commands_impl(s,out,capacity,count,0,NULL,NULL,0,NULL);}
int nf_visibility_snapshot_prepared_captured_commands(NFVisibilitySnapshot*s,NFNativeSceneCommand*out,unsigned capacity,unsigned*count){return prepared_commands_impl(s,out,capacity,count,1,NULL,NULL,0,NULL);}

int nf_visibility_snapshot_prepared_builder_commands(NFVisibilitySnapshot*root,NFVisibilitySnapshot*builder,NFNativeSceneCommand*out,unsigned capacity,unsigned*count){if(!builder)return 0;return prepared_commands_impl(root,out,capacity,count,1,builder,NULL,0,NULL);}

int nf_visibility_snapshot_prepared_builder_commands_view(NFVisibilitySnapshot*root,NFVisibilitySnapshot*builder,const uint32_t view[12],NFNativeSceneCommand*out,unsigned capacity,unsigned*count){
 if(!builder||!view)return 0;return prepared_commands_impl(root,out,capacity,count,0,builder,view,0,NULL);
}

int nf_visibility_snapshot_prepared_builder_commands_object(NFVisibilitySnapshot*root,NFVisibilitySnapshot*builder,const uint32_t view[12],uint32_t address,const uint8_t record[164],NFNativeSceneCommand*out,unsigned capacity,unsigned*count){
 if(!builder||!view||!record)return 0;return prepared_commands_impl(root,out,capacity,count,0,builder,view,address,record);
}
int nf_visibility_snapshot_prepared_builder_commands_focal(NFVisibilitySnapshot*root,NFVisibilitySnapshot*builder,const uint32_t view[12],uint32_t focal,uint32_t builder_focal,uint32_t address,const uint8_t*record,NFNativeSceneCommand*out,unsigned capacity,unsigned*count){
 if(!view||!out||!count||capacity<144)return 0;
 NFVisibilitySnapshot*a=nf_visibility_snapshot_clone_focal(root,focal),*b=nf_visibility_snapshot_clone_focal(builder,builder_focal);
 int ok=a&&b&&prepared_commands_impl(a,out,capacity,count,0,b,view,address,record);
 nf_visibility_snapshot_destroy(a);nf_visibility_snapshot_destroy(b);return ok;
}
int nf_visibility_snapshot_query_sample(const NFVisibilitySnapshot*a,const NFVisibilitySnapshot*b,double alpha,NFVisibilityPoseInputs*out){
 if(!a||!b||!out||!a->query_owned||!b->query_owned||!isfinite(alpha)||alpha<0||alpha>1)return 0;
 NFVisibilityPoseInputs p; if(!nf_visibility_view_sample(a->view,b->view,alpha,p.view))return 0;
 for(unsigned i=0;i<2;i++){double v=alpha==0?(int32_t)a->base[i]:alpha==1?(int32_t)b->base[i]:round((1-alpha)*(double)(int32_t)a->base[i]+alpha*(double)(int32_t)b->base[i]);if(v<INT32_MIN||v>INT32_MAX)return 0;p.base[i]=(uint32_t)(int32_t)v;}
 memset(p.query,0,48);for(unsigned i=0;i<3;i++)for(unsigned j=0;j<3;j++)p.query[i*3+j]=p.view[j*3+i];
 p.view[9]=(uint32_t)(int32_t)-floor((double)(int32_t)p.base[0]/256.);p.view[11]=(uint32_t)(int32_t)-floor((double)(int32_t)p.base[1]/256.);
 if(alpha==0){memcpy(p.query,a->query,48);memcpy(p.view,a->view,48);}if(alpha==1){memcpy(p.query,b->query,48);memcpy(p.view,b->view,48);}memcpy(out,&p,sizeof(p));return 1;
}
int nf_visibility_snapshot_packet_native_road_camera_model_inputs_at(NFVisibilitySnapshot*s,uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,double alpha,uint32_t page,const uint8_t*objects,unsigned object_count,const int32_t rotation[12],NFScenePalette selector,void*selector_user,NFSceneModelInputs models,void*model_user,void**out,size_t*out_size){return selector&&models&&snapshot_packet_impl(s,epoch,serial,begin,end,pose,alpha,page,objects,object_count,rotation,NULL,NULL,selector,selector_user,out,out_size,1,models,model_user,31,NULL,NULL);}

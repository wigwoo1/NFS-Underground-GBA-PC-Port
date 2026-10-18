/* Opt-in bounded diagnostics, attached only to existing source-copy operations.
   No emulated writes, hooks, draw replacement, source packet changes or scheduling. */
#define NFPC_HISTORY_ROOTS 4096u
#define NFPC_HISTORY_EVENTS 65536u
#define NFPC_HISTORY_PREFIX 1292u
typedef struct {uint64_t sequence,epoch,cycles;unsigned frame,serial,bytes,identity[5],camera[12];unsigned char prefix[NFPC_HISTORY_PREFIX];} NFPCHistoryRoot;
typedef struct {uint64_t epoch,ordinal,root,cycles,command_hash;unsigned frame,texture;} NFPCHistoryEvent;
typedef struct {uint64_t key[5];unsigned valid;uint64_t cells[2][38400];} NFPCHistoryOwner;
static struct {NFPCHistoryOwner owners[2];uint64_t owner_failures;uint64_t epoch,sequence,active;NFPCHistoryRoot roots[NFPC_HISTORY_ROOTS];NFPCHistoryEvent events[2][NFPC_HISTORY_EVENTS];uint64_t notes,missing,reads;}*nf_pc_history_provenance;
static uint64_t nf_pc_history_hash(const void*data,size_t n){const unsigned char*p=data;uint64_t h=14695981039346656037ull;for(size_t i=0;i<n;i++){h^=p[i];h*=1099511628211ull;}return h;}
__declspec(dllexport) int nf_pc_history_provenance_enable(int enabled){
 free(nf_pc_history_provenance);nf_pc_history_provenance=NULL;
 if(enabled){nf_pc_history_provenance=calloc(1,sizeof(*nf_pc_history_provenance));if(!nf_pc_history_provenance)return 0;}
 return 1;
}
static void nf_pc_history_epoch(uint64_t epoch){if(nf_pc_history_provenance->epoch!=epoch){memset(nf_pc_history_provenance,0,sizeof(*nf_pc_history_provenance));nf_pc_history_provenance->epoch=epoch;}}
static void nf_pc_history_surface_note(const uint32_t id[5],const void*surface,size_t size){
 if(!nf_pc_history_provenance)return;
 uint64_t epoch=nf_native_scene_epoch();nf_pc_history_epoch(epoch);nf_pc_history_provenance->active=0;
 if(!id||!surface||size<12||(id[0]!=1&&id[0]!=2))return;
 unsigned count;memcpy(&count,surface,4);size_t bytes=12+(size_t)count*40;if(count<3||count>32||bytes>size||bytes>NFPC_HISTORY_PREFIX)return;
 unsigned camera[12];if(!native_surface_read(NULL,rd32(id[1]+84),camera,48))return;
 uint64_t sequence=++nf_pc_history_provenance->sequence;NFPCHistoryRoot*r=nf_pc_history_provenance->roots+sequence%NFPC_HISTORY_ROOTS;
 memset(r,0,sizeof(*r));r->sequence=sequence;r->epoch=epoch;r->cycles=mTimingGlobalTime(c->timing);r->frame=c->frameCounter(c);r->serial=live_scene.serial;r->bytes=(unsigned)bytes;memcpy(r->identity,id,20);memcpy(r->camera,camera,48);memcpy(r->prefix,surface,bytes);nf_pc_history_provenance->active=sequence;
}
static void nf_pc_history_event_note(uint64_t epoch,unsigned refresh,const NFSceneEvent*event,uint64_t ordinal){
 if(!nf_pc_history_provenance||!event||(event->kind!=1&&event->kind!=2))return;
 nf_pc_history_epoch(epoch);nf_pc_history_provenance->notes++;uint64_t sequence=nf_pc_history_provenance->active;NFPCHistoryRoot*r=nf_pc_history_provenance->roots+sequence%NFPC_HISTORY_ROOTS;
 if(!sequence||r->sequence!=sequence||r->epoch!=epoch||r->identity[0]!=event->kind||r->frame>refresh){nf_pc_history_provenance->missing++;sequence=0;}
 NFPCHistoryEvent*e=nf_pc_history_provenance->events[event->kind-1]+ordinal%NFPC_HISTORY_EVENTS;
 *e=(NFPCHistoryEvent){epoch,ordinal,sequence,mTimingGlobalTime(c->timing),nf_pc_history_hash(event->commands,event->kind==1?68:80),refresh,event->texture_address};
}
/* Output:16u64 +5u32 source identity +12u32 original camera + surface prefix.
   words:epoch,kind,ordinal,event refresh,root sequence,root refresh,root serial,
   root cycles,event cycles,prefix bytes,texture address,1,command FNV64,
   original xyz/uv-prefix FNV64,reserved0,reserved0. All validation before write.
   Provenance is bounded: overwritten/missing roots/events reject explicitly.
   Owner thread only, matching the existing observer API. Disable before close. */
__declspec(dllexport) size_t nf_pc_history_provenance_read(uint64_t epoch,unsigned kind,uint64_t ordinal,void*out,size_t capacity){
 if(!c||!nf_pc_history_provenance||epoch!=nf_native_scene_epoch()||epoch!=nf_pc_history_provenance->epoch||kind<1||kind>2||!ordinal)return 0;
 NFPCHistoryEvent*e=nf_pc_history_provenance->events[kind-1]+ordinal%NFPC_HISTORY_EVENTS;
 if(e->epoch!=epoch||e->ordinal!=ordinal||!e->root)return 0;NFPCHistoryRoot*r=nf_pc_history_provenance->roots+e->root%NFPC_HISTORY_ROOTS;
 if(r->epoch!=epoch||r->sequence!=e->root||r->identity[0]!=kind||r->frame>e->frame||r->cycles>e->cycles||r->bytes>NFPC_HISTORY_PREFIX)return 0;
 size_t bytes=196+r->bytes;if(out&&capacity<bytes)return 0;
 if(out){uint64_t h[16]={epoch,kind,ordinal,e->frame,r->sequence,r->frame,r->serial,r->cycles,e->cycles,r->bytes,e->texture,1,e->command_hash,nf_pc_history_hash(r->prefix,r->bytes),0,0};unsigned char*p=out;memcpy(p,h,128);memcpy(p+128,r->identity,20);memcpy(p+148,r->camera,48);memcpy(p+196,r->prefix,r->bytes);nf_pc_history_provenance->reads++;}return bytes;
}
__declspec(dllexport) int nf_pc_history_provenance_stats(uint64_t out[8]){if(!out||!nf_pc_history_provenance)return 0;uint64_t v[8]={nf_pc_history_provenance->epoch,nf_pc_history_provenance->sequence,nf_pc_history_provenance->notes,nf_pc_history_provenance->missing,nf_pc_history_provenance->reads,sizeof(*nf_pc_history_provenance),NFPC_HISTORY_ROOTS,NFPC_HISTORY_EVENTS};memcpy(out,v,64);return 1;}

extern size_t nf_road_history_cell_ordinals(void*,uint64_t,unsigned,void*,size_t);
extern size_t nf_wall_history_cell_ordinals(void*,uint64_t,unsigned,void*,size_t);
typedef char NFPCHistoryBudget[(sizeof(*nf_pc_history_provenance)<=16u*1024u*1024u)?1:-1];
static void nf_pc_history_owner_publish(uint64_t epoch,const NFScenePacket*packet,const unsigned char*proof){
 if(!nf_pc_history_provenance)return;nf_pc_history_epoch(epoch);
 nf_pc_history_provenance->owners[0]=nf_pc_history_provenance->owners[1];NFPCHistoryOwner*o=nf_pc_history_provenance->owners+1;memset(o,0,sizeof(*o));
 if(nf_road_history_cell_ordinals(android_road_store,epoch,packet->page,o->cells[0],307200)!=307200||nf_wall_history_cell_ordinals(android_wall_store,epoch,packet->page,o->cells[1],307200)!=307200){nf_pc_history_provenance->owner_failures++;return;}
 for(unsigned kind=0;kind<2;kind++)for(unsigned cell=0;cell<38400;cell++)if(proof[80+cell]!=kind+1)o->cells[kind][cell]=0;
 uint64_t key[5]={epoch,packet->serial,packet->begin_refresh,packet->end_refresh,packet->page};memcpy(o->key,key,40);o->valid=1;
}
/* Exact immutable owner key, then kind1road/2wall. Output8u64 header:
   epoch,serial,begin,end,page,kind,38400,totalBytes; followed38400u64 ordinals.
   Zero means original ownership proof assigned a different layer/no history.
   Cell ordinals come directly from original history store, never image matching. */
__declspec(dllexport) size_t nf_pc_history_owner_cells(const uint64_t key[5],unsigned kind,void*out,size_t capacity){
 if(!c||!nf_pc_history_provenance||!key||key[0]!=nf_native_scene_epoch()||key[0]!=nf_pc_history_provenance->epoch||kind<1||kind>2)return 0;
 NFPCHistoryOwner*o=NULL;for(unsigned i=0;i<2;i++)if(nf_pc_history_provenance->owners[i].valid&&!memcmp(nf_pc_history_provenance->owners[i].key,key,40)){if(o)return 0;o=nf_pc_history_provenance->owners+i;}
 size_t bytes=64+307200;if(!o||(out&&capacity<bytes))return 0;
 if(out){uint64_t h[8]={key[0],key[1],key[2],key[3],key[4],kind,38400,bytes};memcpy(out,h,64);memcpy((unsigned char*)out+64,o->cells[kind-1],307200);}return bytes;
}

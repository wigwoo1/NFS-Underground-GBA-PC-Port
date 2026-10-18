/* Isolated original wall call-lineage capture. No guessed screen association. */
typedef struct {uint64_t id;unsigned sp,lr,state,source,material,descriptor,flags,columns;uint8_t*texture;unsigned texture_address;} PCWallCall;
static PCWallCall pc_wall_stack[32];static unsigned pc_wall_depth,pc_wall_failed;static uint64_t pc_wall_entries,pc_wall_recipes,pc_wall_columns,pc_wall_returns;static uint8_t*pc_wall_pending;static size_t pc_wall_bytes;
static void pc_wall_emit(const uint64_t*h,unsigned words,const void*data,size_t n){
 if(pc_wall_failed)return;size_t added=words*8+n;if(added>64u*1024*1024-pc_wall_bytes){pc_wall_failed=1;return;}uint8_t*p=realloc(pc_wall_pending,pc_wall_bytes+added);if(!p){pc_wall_failed=1;return;}pc_wall_pending=p;memcpy(p+pc_wall_bytes,h,words*8);if(n)memcpy(p+pc_wall_bytes+words*8,data,n);pc_wall_bytes+=added;
}
void nf_pc_wall_lineage_reset(void){for(unsigned i=0;i<32;i++)free(pc_wall_stack[i].texture);memset(pc_wall_stack,0,sizeof(pc_wall_stack));pc_wall_depth=pc_wall_failed=0;pc_wall_entries=pc_wall_recipes=pc_wall_columns=pc_wall_returns=0;free(pc_wall_pending);pc_wall_pending=NULL;pc_wall_bytes=0;}
void nf_pc_wall_lineage_tick(struct ARMCore*cpu,unsigned pc){
 if(!android_wall_enabled||android_wall_failed||pc_wall_failed)return;
 while(pc_wall_depth){PCWallCall*s=pc_wall_stack+pc_wall_depth-1;if(pc!=(s->lr&~1u)||cpu->gprs[13]!=s->sp)break;uint64_t h[8]={4,64,android_wall_epoch,c->frameCounter(c),s->id,pc,cpu->gprs[13],s->columns};pc_wall_emit(h,8,NULL,0);free(s->texture);memset(s,0,sizeof(*s));pc_wall_depth--;pc_wall_returns++;}
 if(pc!=0x03000304)return;
 if(pc_wall_depth==32){pc_wall_failed=1;return;}PCWallCall*s=pc_wall_stack+pc_wall_depth++;*s=(PCWallCall){++pc_wall_entries,cpu->gprs[13],cpu->gprs[14],cpu->gprs[1],cpu->gprs[6],cpu->gprs[0],cpu->gprs[3],cpu->gprs[2],0,NULL,0};
 uint64_t h[14]={1,112,android_wall_epoch,c->frameCounter(c),s->id,s->sp,s->lr,s->state,s->source,s->material,s->descriptor,s->flags,rd32(pc),pc_wall_depth};pc_wall_emit(h,14,NULL,0);
}
void nf_pc_wall_lineage_recipe(unsigned state,const uint8_t*const*blocks,const unsigned*sizes){
 if(pc_wall_failed)return;if(!pc_wall_depth){pc_wall_failed=1;return;}PCWallCall*s=pc_wall_stack+pc_wall_depth-1;if(s->state!=state||s->texture||sizes[8]!=65536||sizes[4]!=48){pc_wall_failed=1;return;}
 size_t bytes=0;for(unsigned i=0;i<12;i++)bytes+=4+sizes[i];uint8_t*data=malloc(bytes);s->texture=malloc(65536);if(!data||!s->texture){free(data);pc_wall_failed=1;return;}memcpy(s->texture,blocks[8],65536);memcpy(&s->texture_address,blocks[4]+40,4);size_t at=0;for(unsigned i=0;i<12;i++){memcpy(data+at,sizes+i,4);at+=4;memcpy(data+at,blocks[i],sizes[i]);at+=sizes[i];}
 uint64_t h[8]={2,64+bytes,android_wall_epoch,c->frameCounter(c),s->id,s->texture_address,65536,12};pc_wall_emit(h,8,data,bytes);free(data);pc_wall_recipes++;
}
void nf_pc_wall_lineage_event(uint64_t epoch,unsigned refresh,uint64_t ordinal,const NFSceneEvent*e){
 if(pc_wall_failed)return;if(!pc_wall_depth||e->kind!=2||e->count!=1||e->shift>1||e->texture_size!=65536+(e->shift?4081:0)){pc_wall_failed=1;return;}PCWallCall*s=pc_wall_stack+pc_wall_depth-1;
 if(!s->texture||epoch!=android_wall_epoch||s->texture_address!=e->texture_address||memcmp(s->texture,e->texture,65536)){pc_wall_failed=1;return;}
 unsigned shade=e->shift?4081:0;uint8_t data[80+4081];memcpy(data,e->commands,80);if(shade)memcpy(data+80,e->texture+65536,shade);uint64_t h[10]={3,160+shade,epoch,refresh,s->id,ordinal,e->shift,e->texture_address,1,shade};pc_wall_emit(h,10,data,80+shade);s->columns++;pc_wall_columns++;
}
__declspec(dllexport) int nf_pc_wall_lineage_read(void*out,size_t capacity,size_t*bytes){if(!bytes||pc_wall_failed)return 0;if(!out){*bytes=pc_wall_bytes;return 1;}if(capacity<pc_wall_bytes)return 0;if(pc_wall_bytes)memcpy(out,pc_wall_pending,pc_wall_bytes);*bytes=pc_wall_bytes;return 1;}
__declspec(dllexport) void nf_pc_wall_lineage_consume(void){free(pc_wall_pending);pc_wall_pending=NULL;pc_wall_bytes=0;}
__declspec(dllexport) int nf_pc_wall_lineage_status(uint64_t out[8]){if(!out)return 0;uint64_t a[8]={android_wall_epoch,pc_wall_entries,pc_wall_recipes,pc_wall_columns,pc_wall_returns,pc_wall_depth,pc_wall_failed,android_wall_ordinal};memcpy(out,a,sizeof(a));return 1;}

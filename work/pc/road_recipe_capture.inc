/* Isolated diagnostic ownership bridge; never linked into the playable host. */
static uint8_t*pc_road_pending;static size_t pc_road_used;static uint64_t pc_road_records;static unsigned pc_road_failed;
void nf_pc_road_recipe_reset(void){free(pc_road_pending);pc_road_pending=NULL;pc_road_used=0;pc_road_records=0;pc_road_failed=0;}
uint64_t nf_pc_road_event_receipt(void){return android_wall_failed?0:android_road_ordinal;}
void nf_pc_road_recipe_capture(uint64_t last,unsigned refresh,unsigned state,unsigned source,unsigned descriptor,const uint32_t*commands,unsigned count,unsigned shift,const uint8_t*const*blocks,const unsigned*sizes,const void*scratch,unsigned scratch_bytes){
 if(pc_road_failed||!count)return;
 if(!last||last<count||!commands||!blocks||!sizes||!scratch||scratch_bytes<4||scratch_bytes>6148){pc_road_failed=1;return;}
 size_t bytes=84+(size_t)count*68+scratch_bytes;for(unsigned i=0;i<12;i++){if(!blocks[i]||sizes[i]>0x100000){pc_road_failed=1;return;}bytes+=4+sizes[i];}
 if(bytes>64u*1024*1024-pc_road_used){pc_road_failed=1;return;}
 uint8_t*next=realloc(pc_road_pending,pc_road_used+bytes);if(!next){pc_road_failed=1;return;}pc_road_pending=next;
 uint64_t h[10]={0x3152524e,bytes,android_wall_epoch,refresh,last-count+1,count,state,source,descriptor,shift};size_t at=pc_road_used;
 memcpy(next+at,h,80);at+=80;memcpy(next+at,commands,(size_t)count*68);at+=(size_t)count*68;
 for(unsigned i=0;i<12;i++){memcpy(next+at,sizes+i,4);at+=4;memcpy(next+at,blocks[i],sizes[i]);at+=sizes[i];}
 memcpy(next+at,&scratch_bytes,4);at+=4;memcpy(next+at,scratch,scratch_bytes);at+=scratch_bytes;pc_road_used=at;pc_road_records++;
}
__declspec(dllexport) int nf_pc_road_recipe_progress(uint64_t out[3]){if(!out)return 0;out[0]=android_wall_epoch;out[1]=android_road_ordinal;out[2]=pc_road_failed;return 1;}
__declspec(dllexport) int nf_pc_road_recipes_read(void*out,size_t capacity,size_t*bytes){if(!bytes||pc_road_failed)return 0;if(!out){*bytes=pc_road_used;return 1;}if(capacity<pc_road_used)return 0;if(pc_road_used)memcpy(out,pc_road_pending,pc_road_used);*bytes=pc_road_used;return 1;}
__declspec(dllexport) void nf_pc_road_recipes_consume(void){free(pc_road_pending);pc_road_pending=NULL;pc_road_used=0;pc_road_records=0;}
__declspec(dllexport) int nf_pc_road_recipes_table(void*out,size_t n){if(!out||n!=sizeof(native_model_plan_table))return 0;memcpy(out,native_model_plan_table,n);return 1;}
/* Replay uses only caller-owned blocks/table, including after core shutdown.
   This reuses the original source-run algorithm; it is a completeness test,
   not an independent proof of that algorithm's rendering accuracy. */
__declspec(dllexport) int nf_pc_road_recipe_replay(const void*data,size_t n,const uint32_t*table,size_t tn,void*out,size_t capacity,unsigned*written){
 if(!data||n<80||!table||tn!=131072||!out||!written||capacity<8192u*68)return 0;
 uint64_t h[10];memcpy(h,data,80);if(h[0]!=0x3152524e||h[1]!=n||!h[5]||h[5]>8192)return 0;
 const uint8_t*b=data,*p[12];unsigned sizes[12];size_t at=80+(size_t)h[5]*68;if(at>n)return 0;
 for(unsigned i=0;i<12;i++){if(n-at<4)return 0;memcpy(sizes+i,b+at,4);at+=4;if(sizes[i]>n-at)return 0;p[i]=b+at;at+=sizes[i];}if(n-at<4)return 0;unsigned scratch_bytes;memcpy(&scratch_bytes,b+at,4);at+=4;if(scratch_bytes!=n-at)return 0;const void*scratch_data=b+at;
 if(sizes[6]!=32||sizes[2]!=20||sizes[3]!=48||sizes[4]!=48||sizes[5]!=8)return 0;
 uint32_t config[8];memcpy(config,p[6],32);if(!config[0]||config[0]>32||sizes[0]!=config[0]*68||sizes[1]!=config[0]*32)return 0;
 void*scratch=nf_pc_road_scratch_read(scratch_data,scratch_bytes);if(!scratch)return 0;uint64_t missing=0;unsigned count=0;
 int ok=nf_road_source_runs(scratch,p[0],sizes[0],p[1],sizes[1],p[2],p[3],config[0],config[1],(const int32_t*)p[4],(const uint16_t*)p[5],config[4],config[3],table,config[5],config[2],config+6,out,8192,&count,&missing);
 nf_road_scratch_destroy(scratch);if(!ok||missing)return 0;*written=count;return 1;
}

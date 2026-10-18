/* Opt-in diagnostic build only. Snapshot RAM without changing CPU or game state. */
static FILE* visibility_file;
static unsigned visibility_skip,visibility_seen,visibility_stage,visibility_state;
static unsigned visibility_selector;
static uint8_t*visibility_pending;
static uint32_t visibility_pending_header[22];
static unsigned visibility_current;
static unsigned visibility_watch,visibility_watch_size,visibility_exit_frame,visibility_write_count;
static uint32_t visibility_writes[256][7];
API unsigned nf_visibility_writes(uint32_t*out,unsigned capacity){
 unsigned n=visibility_write_count<capacity?visibility_write_count:capacity;
 if(out)memcpy(out,visibility_writes,n*sizeof(visibility_writes[0]));return visibility_write_count;
}
static void visibility_write(struct ARMCore*cpu,unsigned address,unsigned size,uint32_t value){
 if(visibility_stage!=2||visibility_write_count>=256||c->frameCounter(c)>visibility_exit_frame+4||
    address<visibility_watch||(uint64_t)address+size>visibility_watch+visibility_watch_size)return;
 uint32_t*row=visibility_writes[visibility_write_count++];
 row[0]=c->frameCounter(c);row[1]=cpu->gprs[15]-(cpu->cpsr.t?4:8);row[2]=live_scene.serial;
 row[3]=address-visibility_watch;row[4]=size;row[5]=value;row[6]=cpu->cpsr.t;
}
static void visibility_close(void){if(visibility_file)fclose(visibility_file);visibility_file=NULL;free(visibility_pending);visibility_pending=NULL;}
API int nf_visibility_capture(const char*path,unsigned skip){
 visibility_close();visibility_skip=skip;visibility_seen=visibility_stage=0;
 visibility_selector=0;
 visibility_write_count=visibility_watch=visibility_watch_size=0;
 if(!c||!path)return 0;
 visibility_file=fopen(path,"wb");if(visibility_file)nfsArmHook=onArm;
 return visibility_file!=NULL;
}
API int nf_visibility_selector_capture(const char*path,unsigned skip){
 int result=nf_visibility_capture(path,skip);visibility_selector=1;return result;
}
/* Keep unmatched entry snapshots in RAM only; publish the first change/miss. */
API int nf_visibility_transition_capture(const char*path){
 int result=nf_visibility_capture(path,0);visibility_selector=2;return result;
}
API int nf_visibility_fallback_capture(const char*path){
 int result=nf_visibility_capture(path,0);visibility_selector=3;
 if(result)nfsThumbTrace=thumbTrace;return result;
}
API int nf_visibility_pair_capture(const char*path,unsigned skip){
 int result=nf_visibility_capture(path,skip);visibility_selector=4;
 if(result)nfsThumbTrace=thumbTrace;return result;
}
/* Four snapshots: query input/output, builder input/output. Status 4 complete,
   5 error; statuses 0..3 identify the next pending boundary in this mode. */
API int nf_visibility_pipeline_capture(const char*path,unsigned skip){
 int result=nf_visibility_capture(path,skip);visibility_selector=5;
 if(result)nfsThumbTrace=thumbTrace;return result;
}
API unsigned nf_visibility_status(void){return visibility_stage;}
static void visibility_event(struct ARMCore*cpu,unsigned pc){
 if(!visibility_file)return;
 unsigned entry=visibility_selector?0x03000bd0:0x03004c74,leave=visibility_selector?0x03000d44:0x03004d50;
 if(visibility_selector==3){entry=0x08022d78;leave=0x08022eda;}
 if(visibility_selector==4){entry=0x08002cf2;leave=0x08002d92;}
 if(visibility_selector==5){
  static const unsigned boundaries[4]={0x08002cb4,0x08002d92,0x03004c74,0x03004d50};
  if(visibility_stage>=4||pc!=boundaries[visibility_stage])return;
  if(!visibility_stage){if(visibility_seen++!=visibility_skip)return;visibility_state=cpu->gprs[10];}
 }else{
 if(pc==entry&&visibility_stage==0){
  if(visibility_selector!=2&&visibility_seen++!=visibility_skip)return;
  visibility_state=cpu->gprs[visibility_selector==4?10:0];
  visibility_current=rd16(visibility_state+0xea);
 }else if(pc!=leave||visibility_stage!=1)return;
 }
 if(visibility_selector==2&&visibility_stage==1){
  if((unsigned)cpu->gprs[0]==visibility_current){free(visibility_pending);visibility_pending=NULL;visibility_stage=0;return;}
  if(!visibility_pending||fwrite(visibility_pending_header,sizeof(visibility_pending_header),1,visibility_file)!=1||fwrite(visibility_pending,1,0x48000,visibility_file)!=0x48000){visibility_stage=3;visibility_close();return;}
  free(visibility_pending);visibility_pending=NULL;
 }
 uint32_t header[22]={0x3151564e,visibility_stage,pc,c->frameCounter(c),visibility_state,live_scene.serial};
 memcpy(header+6,cpu->gprs,64);
 uint8_t*ram=malloc(0x48000);
 if(!ram||!native_surface_read(NULL,0x02000000,ram,0x40000)||!native_surface_read(NULL,0x03000000,ram+0x40000,0x8000)){
  free(ram);visibility_stage=visibility_selector==5?5:3;visibility_close();return;
 }
 if(visibility_selector==2&&visibility_stage==0){visibility_pending=ram;memcpy(visibility_pending_header,header,sizeof(header));visibility_stage=1;return;}
 if(fwrite(header,sizeof(header),1,visibility_file)!=1||fwrite(ram,1,0x48000,visibility_file)!=0x48000){
  free(ram);visibility_stage=visibility_selector==5?5:3;visibility_close();return;
 }
 free(ram);visibility_stage++;
 if(visibility_stage==(visibility_selector==5?4:2)){
  visibility_watch=rd32(visibility_state+0x60);visibility_watch_size=visibility_selector?0:rd16(visibility_state+0xee)*16;
  if(visibility_watch_size>320)visibility_watch_size=0;
  visibility_exit_frame=c->frameCounter(c);visibility_close();
 }
}

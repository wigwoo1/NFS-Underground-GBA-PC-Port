/* Bounded, opt-in original producer/consumer history. Diagnostic only. */
#define NF_ROT_TRACE_RECORDS 512
#define NF_ROT_TRACE_WORDS 128
static uint32_t nf_rot_trace_ring[NF_ROT_TRACE_RECORDS][NF_ROT_TRACE_WORDS];
static uint32_t nf_rot_trace_frozen[16+NF_ROT_TRACE_RECORDS*NF_ROT_TRACE_WORDS];
static unsigned nf_rot_trace_target,nf_rot_trace_count,nf_rot_trace_ready;
static uint32_t nf_rot_trace_pending_key,nf_rot_trace_pending_frame,nf_rot_trace_code[8192],nf_rot_trace_write_args[3];
void nf_rotation_trace_reset(void){nf_rot_trace_target=nf_rot_trace_count=nf_rot_trace_ready=nf_rot_trace_pending_key=nf_rot_trace_pending_frame=0;}
int nf_android_rotation_trace_enable(unsigned target){if(!c||!target)return 0;nf_rotation_trace_reset();nf_rot_trace_target=target;return 1;}
void nf_rotation_trace_event(struct ARMCore*cpu,unsigned pc){
 unsigned serial=live_scene.serial;if(!nf_rot_trace_target||nf_rot_trace_ready||serial>nf_rot_trace_target||serial+8<nf_rot_trace_target)return;
 unsigned type=pc==0x0806db14?1:pc==0x0806d9d8?2:pc==0x03002628?3:pc==0x030045e0?4:pc==0x03004770?5:pc==0x08023452?6:pc==0xfffffff0?7:0;if(!type)return;
 uint32_t w[NF_ROT_TRACE_WORDS]={pc,c->frameCounter(c),serial,type};memcpy(w+4,cpu->gprs,64);
 uint64_t epoch=nf_native_scene_epoch();w[20]=live_scene.context;w[21]=live_scene.object;w[22]=live_scene.camera;w[23]=live_scene.state;w[24]=live_scene.begin;w[25]=(uint32_t)epoch;w[26]=(uint32_t)(epoch>>32);w[27]=nf_rot_trace_count;
 if(type==1){nf_rot_trace_pending_key=cpu->gprs[2];nf_rot_trace_pending_frame=c->frameCounter(c);}
 if(type<=2){w[56]=native_surface_read(NULL,cpu->gprs[0],w+32,48);w[57]=native_surface_read(NULL,cpu->gprs[1],w+44,48);}
 else if(type<=5){uint8_t context[68];w[30]=type==5?live_scene.context:cpu->gprs[0];w[28]=native_surface_read(NULL,w[30],context,68);if(w[28])memcpy(w+29,context+60,4);w[31]=live_scene.model!=NULL;if(w[28]){memcpy(w+64,context,68);w[122]=native_surface_read(NULL,w[29],w+110,48);}}
 else if(type==6){w[29]=nf_rot_trace_pending_key;w[122]=native_surface_read(NULL,w[29],w+110,48);}
 w[108]=native_surface_read(NULL,0x0200c24c,w+84,48);w[109]=native_surface_read(NULL,0x0200c27c,w+96,48);w[123]=nf_rot_trace_pending_key;w[124]=nf_rot_trace_pending_frame;
 if(type==7){w[0]=cpu->gprs[15]-(cpu->cpsr.t?4:8);memcpy(w+64,nf_rot_trace_write_args,12);}
 w[58]=live_object_model_context.verified;w[59]=live_object_model_context.frame;w[60]=live_object_model_context.object;
 memcpy(nf_rot_trace_ring[nf_rot_trace_count%NF_ROT_TRACE_RECORDS],w,sizeof(w));nf_rot_trace_count++;
}
void nf_rotation_trace_freeze(void){
 if(!nf_rot_trace_target||nf_rot_trace_ready||live_scene.serial!=nf_rot_trace_target)return;
 unsigned count=nf_rot_trace_count<NF_ROT_TRACE_RECORDS?nf_rot_trace_count:NF_ROT_TRACE_RECORDS,start=nf_rot_trace_count-count;
 uint64_t epoch=nf_native_scene_epoch();uint32_t h[16]={0x3154524e,3,16+count*NF_ROT_TRACE_WORDS,count,(uint32_t)epoch,(uint32_t)(epoch>>32),live_scene.serial,c->frameCounter(c),nf_rot_trace_count-count,NF_ROT_TRACE_WORDS};memcpy(nf_rot_trace_frozen,h,64);
 for(unsigned i=0;i<count;i++)memcpy(nf_rot_trace_frozen+16+i*NF_ROT_TRACE_WORDS,nf_rot_trace_ring[(start+i)%NF_ROT_TRACE_RECORDS],NF_ROT_TRACE_WORDS*4);
 nf_rot_trace_frozen[10]=native_surface_read(NULL,0x03000000,nf_rot_trace_code,sizeof(nf_rot_trace_code));nf_rot_trace_ready=1;
}
size_t nf_android_rotation_trace_copy(void*out,size_t bytes){if(!c||!nf_rot_trace_ready)return 0;size_t n=(size_t)nf_rot_trace_frozen[2]*4;if(!out)return n;if(bytes<n)return 0;memcpy(out,nf_rot_trace_frozen,n);return n;}

size_t nf_android_rotation_trace_code(void*out,size_t bytes){if(!c||!nf_rot_trace_ready)return 0;size_t n=sizeof(nf_rot_trace_code);if(!out)return n;if(bytes<n)return 0;memcpy(out,nf_rot_trace_code,n);return n;}


void nf_rotation_trace_write(struct ARMCore*cpu,uint32_t address,uint32_t size,uint32_t value){if(address>=0x0200c2ac||(uint64_t)address+size<=0x0200c24c)return;nf_rot_trace_write_args[0]=address;nf_rot_trace_write_args[1]=size;nf_rot_trace_write_args[2]=value;nf_rotation_trace_event(cpu,0xfffffff0);}

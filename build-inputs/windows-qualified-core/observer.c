void nf_android_geometry_cache_reset(int);
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <mgba/core/core.h>
#include <mgba/internal/arm/arm.h>
#include <mgba/internal/gba/gba.h>
#include <mgba/internal/arm/isa-inlines.h>
#include "native_span.h"
#include "v2/scene.h"
#include "camera/bitmap_layer.h"
#include <mgba-util/vfs.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef NF_PROBE_EXPORTS
#define API __declspec(dllexport)
#else
#define API
#endif
static unsigned capture_profile_enabled;
static uint64_t capture_profile_ticks[6];static LARGE_INTEGER capture_profile_frequency;
static struct {uint32_t pc;uint64_t ticks,calls;} capture_event_profile[64];
static void capture_profile_event(unsigned pc,uint64_t ticks){for(unsigned i=0;i<64;i++)if(!capture_event_profile[i].pc||capture_event_profile[i].pc==pc){capture_event_profile[i].pc=pc;capture_event_profile[i].ticks+=ticks;capture_event_profile[i].calls++;return;}}
API int nf_capture_event_profile_read(unsigned index,uint64_t out[3]){if(!out||index>=64||!capture_profile_enabled||!capture_profile_frequency.QuadPart||!capture_event_profile[index].pc)return 0;out[0]=capture_event_profile[index].pc;out[1]=capture_event_profile[index].calls;out[2]=(uint64_t)((double)capture_event_profile[index].ticks*1e9/capture_profile_frequency.QuadPart);return 1;}
static uint64_t capture_profile_now(void){LARGE_INTEGER t;QueryPerformanceCounter(&t);return (uint64_t)t.QuadPart;}
API void nf_capture_profile_enable(unsigned enabled){capture_profile_enabled=enabled!=0;QueryPerformanceFrequency(&capture_profile_frequency);memset(capture_event_profile,0,sizeof(capture_event_profile));memset(capture_profile_ticks,0,sizeof(capture_profile_ticks));}
API int nf_capture_profile_read(uint64_t out[6]){if(!out||!capture_profile_enabled||!capture_profile_frequency.QuadPart)return 0;for(unsigned i=0;i<6;i++)out[i]=(i&1)?capture_profile_ticks[i]:(uint64_t)((double)capture_profile_ticks[i]*1e9/capture_profile_frequency.QuadPart);return 1;}
static unsigned arm_stage_profile_enabled;
static uint64_t arm_stage_ticks[3],arm_stage_calls[3];
static LARGE_INTEGER arm_stage_frequency;
API void nf_arm_stage_profile_enable(unsigned enabled){arm_stage_profile_enabled=enabled!=0;QueryPerformanceFrequency(&arm_stage_frequency);memset(arm_stage_ticks,0,sizeof(arm_stage_ticks));memset(arm_stage_calls,0,sizeof(arm_stage_calls));}
API int nf_arm_stage_profile_read(uint64_t out[6]){if(!out||!arm_stage_profile_enabled||!arm_stage_frequency.QuadPart)return 0;for(unsigned i=0;i<3;i++){out[i*2]=(uint64_t)((double)arm_stage_ticks[i]*1e9/arm_stage_frequency.QuadPart);out[i*2+1]=arm_stage_calls[i];}return 1;}
#define NF_ARM_STAGE(index,call) do{if(arm_stage_profile_enabled){uint64_t began=capture_profile_now();call;arm_stage_ticks[index]+=capture_profile_now()-began;arm_stage_calls[index]++;}else{call;}}while(0)
static struct mCore* c;
static uint32_t*pixels;
static void (*old16)(struct ARMCore*,uint32_t,int16_t,int*);
static void (*old32)(struct ARMCore*,uint32_t,int32_t,int*);
static void (*old8)(struct ARMCore*,uint32_t,int8_t,int*);
static uint32_t (*oldMultiple)(struct ARMCore*,uint32_t,int,enum LSMDirection,int*);
static unsigned hist[0x200000], ihist[0x8000];
static unsigned stores, flips;
static FILE* trace_file;
static FILE* dma_file;
API void nf_dma_log(const char* path){if(dma_file)fclose(dma_file);dma_file=path?fopen(path,"w"):NULL;}
static void quiet(struct mLogger* l,int cat,enum mLogLevel level,const char* fmt,va_list args){(void)l;if(dma_file&&strstr(fmt,"Starting DMA")){fprintf(dma_file,"%u pc %08x ",c->frameCounter(c),((struct ARMCore*)c->cpu)->gprs[15]);vfprintf(dma_file,fmt,args);fputc('\n',dma_file);}else if(level==mLOG_FATAL||level==mLOG_ERROR)vfprintf(stderr,fmt,args);}
static struct mLogger logger={quiet,0};
extern bool (*nfsArmHook)(struct ARMCore*);
extern unsigned nfsCpuSpeed;
extern bool (*nfsThumbGate)(struct ARMCore*);
static unsigned pace_frame=~0u;
static int mode60;
static bool paceGate(struct ARMCore* cpu){
 if(cpu->gprs[15]-2!=0x08000c0c || c->busRead32(c,0x03005f14)!=5)return false;
 unsigned frame=c->frameCounter(c);if(frame!=pace_frame){pace_frame=frame;return false;}
 cpu->cycles=cpu->nextEvent;return true;
}
API void nf_pace(int enabled){pace_frame=~0u;nfsThumbGate=enabled?paceGate:NULL;}
extern void (*nfsThumbTrace)(struct ARMCore*);
API void nf_speed(unsigned factor){nfsCpuSpeed=(factor==2||factor==4||factor==8||factor==16)?factor:1;}
static int native_enabled;
static unsigned native_calls,native_rejected;
static bool nativeSpan(struct ARMCore* cpu){
 struct GBA* gba=c->board;
 uint32_t words[12],a=cpu->gprs[0];
 if(a<0x03000000 || a>0x03007fd0)return false;
 for(int i=0;i<12;i++)words[i]=c->busRead32(c,a+i*4);
 uint32_t texaddr=words[5],dest=words[6];
 if(texaddr<0x08000000 || texaddr>=0x08000000+gba->memory.romSize || dest<0x06000000 || dest>=0x06014000)return false;
 NfsSpan s={words[0],words[1],words[2],words[8],words[9],words[10],words[11],words[7],c->busRead32(c,0x03007098)!=0};
 size_t len=s.count*2+(s.duplicate_row?240:0);
 if(dest+len>0x06014000 || len>480){native_rejected++;return false;}
 uint8_t buf[480];
 if(!nfs_draw_span(buf,sizeof(buf),((uint8_t*)gba->memory.rom)+(texaddr-0x08000000),gba->memory.romSize-(texaddr-0x08000000),&s)){native_rejected++;return false;}
 for(unsigned i=0;i<s.count;i++){
  uint16_t val=buf[i*2]|buf[i*2+1]<<8;
  c->busWrite16(c,dest+i*2,val);
  if(s.duplicate_row)c->busWrite16(c,dest+i*2+240,val);
 }
 cpu->gprs[0]=texaddr;cpu->gprs[1]=s.v;cpu->gprs[12]=s.u;
 if(s.count){
  uint32_t u=(s.u-s.du)&s.u_mask,v=(s.v-s.dv)&s.v_mask;
  cpu->gprs[2]=s.duplicate_row?((u>>16)+((v>>16)<<s.width_shift))*2:v>>16;
  cpu->gprs[3]=buf[(s.count-1)*2]|buf[(s.count-1)*2+1]<<8;
 }else{cpu->gprs[2]=s.duplicate_row;cpu->gprs[3]=0x03007098;}
 cpu->cpsr.n=0;cpu->cpsr.z=1;cpu->cpsr.c=1;cpu->cpsr.v=0;
 cpu->gprs[15]=cpu->gprs[14];
 _ARMSetMode(cpu,cpu->gprs[14]&1?MODE_THUMB:MODE_ARM);
 if(cpu->executionMode==MODE_THUMB)ThumbWritePC(cpu);else ARMWritePC(cpu);
 /* Modal instruction cost observed in the reference trace. DMA/IRQ
    interleaving is not reproduced: this path remains experimental. */
 cpu->cycles+=(s.duplicate_row?60+23*s.count:59+21*s.count);
 native_calls++;return true;
}
static FILE* hookfile;
static unsigned hooked;
static uint64_t span_start;
static uint32_t span_return,span_n,span_double;
static FILE* cycle_file;
static FILE* poly_file;
static bool onArm(struct ARMCore* cpu);
static int scene_enabled,scene_page=-1,scene_count[2];
static NFPoly scene_polys[2][NF_MAX_POLYS];
static int scene_dirty[2];
static NFPoly visible_polys[NF_MAX_POLYS];
static int visible_count;
static unsigned visible_version;
API unsigned nf_scene_version(void){return visible_version;}
static uint32_t visible_overlay[240*160];
static void (*original_scanline)(struct GBAVideoRenderer*,int);
static unsigned debug_pc,debug_count,debug_regs[256][16],watch_base,watch_end;
static unsigned debug_memory_reg=16,debug_memory_size;static uint8_t debug_memory[256][256];
static FILE* calls_file;
static FILE* image_copy_calls_file;static unsigned image_copy_calls_count;
static unsigned indexed_copy_capture_enabled;
static FILE* timing_file;
static unsigned dt_percent=100;
static int normalize_steering;
static uint64_t steering_previous;
static unsigned steering_cycles=280896;
static void (*world_thumb)(struct ARMCore*,unsigned);
static void (*native_model_thumb)(struct ARMCore*,unsigned);
static void (*native_scene_thumb)(struct ARMCore*,unsigned);
static void native_scene_flip(unsigned);
#ifdef NF_VISIBILITY_CAPTURE
static void visibility_event(struct ARMCore*,unsigned);
static void live_visibility_event(struct ARMCore*,unsigned);
static void live_visibility_reset(void);
static void live_visibility_packet(const void*,size_t);
static void indexed_copy_capture(struct ARMCore*,unsigned);
static void indexed_fill_capture(struct ARMCore*,unsigned);
#endif
static void bitmap_glyph_call(struct ARMCore*,unsigned,unsigned);
static void bitmap_glyph_completion(struct ARMCore*,unsigned);
static int bitmap_glyph_capture_active(void);
static void thumbTrace(struct ARMCore* cpu){
 unsigned pc=cpu->gprs[15]-2,op=cpu->prefetch[0];
 bitmap_glyph_completion(cpu,pc);
#ifdef NF_VISIBILITY_CAPTURE
 visibility_event(cpu,pc);
 live_visibility_event(cpu,pc);
#endif
 if(world_thumb)world_thumb(cpu,pc);
 if(native_model_thumb)native_model_thumb(cpu,pc);
 if(native_scene_thumb)native_scene_thumb(cpu,pc);
 if(normalize_steering&&pc==0x080095e8){uint64_t t=mTimingGlobalTime(c->timing);steering_cycles=steering_previous?(unsigned)(t-steering_previous):280896;steering_previous=t;}
 if(normalize_steering&&pc==0x080097ee){
  /* Research hypothesis: preserve the observed four-refresh reference ramp.
     This does not normalize the rest of the physics or the clamp timing. */
  cpu->gprs[7]=(int32_t)((int64_t)(int32_t)cpu->gprs[7]*steering_cycles/(4*280896));
 }

 if((pc==0x08007540||pc==0x080095e8)&&dt_percent!=100){unsigned sp=cpu->gprs[13],fps=c->busRead32(c,sp);c->busWrite32(c,sp,(fps*dt_percent+50)/100);}
 if(timing_file && (pc==0x08007540||pc==0x080095e8)){
  unsigned car=cpu->gprs[1],fps=c->busRead32(c,cpu->gprs[13]);
  fprintf(timing_file,"%u,%llu,%08x,%u,%d,%d,%d\n",c->frameCounter(c),(unsigned long long)mTimingGlobalTime(c->timing),car,fps,(int)c->busRead32(c,car+12),(int)c->busRead32(c,car+20),(int)c->busRead32(c,car+44));
 }

 if((calls_file||image_copy_calls_file||indexed_copy_capture_enabled||bitmap_glyph_capture_active())&&pc>=0x08000000&&pc<0x08078000&&(op&0xf800)==0xf000){
  unsigned second=c->busRead16(c,pc+2);if((second&0xf800)!=0xf800)return;
  int32_t offset=((op&0x7ff)<<12)|((second&0x7ff)<<1);if(offset&0x400000)offset|=0xff800000;
  unsigned target=pc+4+offset;
#ifdef NF_VISIBILITY_CAPTURE
  if(target>=0x080775c8&&target<=0x080775f4&&!((target-0x080775c8)&3)&&((cpu->gprs[3+(target-0x080775c8)/4]&~1u)==0x03003814))indexed_copy_capture(cpu,pc);
  if(target>=0x080775c8&&target<=0x080775f4&&!((target-0x080775c8)&3)&&((cpu->gprs[3+(target-0x080775c8)/4]&~1u)==0x030002c0))indexed_fill_capture(cpu,pc);
#endif
  if(image_copy_calls_file&&image_copy_calls_count<4096&&target>=0x080775c8&&target<=0x080775f4&&!((target-0x080775c8)&3)){
   unsigned reg=3+(target-0x080775c8)/4;
   if((cpu->gprs[reg]&~1u)==0x03003814){unsigned sp=cpu->gprs[13];
    fprintf(image_copy_calls_file,"%u,%llu,%08x,%08x,%08x,%u,%u,%u,%u,%08x\n",c->frameCounter(c),(unsigned long long)mTimingGlobalTime(c->timing),pc,cpu->gprs[0],cpu->gprs[1],cpu->gprs[2],cpu->gprs[3],c->busRead32(c,sp),c->busRead32(c,sp+4),sp);image_copy_calls_count++;}
  }
  /* Observational opt-in: compiler BX-register veneers hide indirect fills
     from the ordinary direct-call filter. Preserve execution and arguments. */
  if(calls_file&&getenv("NF_TRACE_INDIRECT_CALLS")&&target>=0x080775c8&&target<=0x080775f4&&!((target-0x080775c8)&3)){
   unsigned reg=3+(target-0x080775c8)/4;
   fprintf(calls_file,"%u,%08x,%08x,%08x,%08x,%08x,%08x\n",c->frameCounter(c),pc,cpu->gprs[reg]&~1u,cpu->gprs[0],cpu->gprs[1],cpu->gprs[2],cpu->gprs[3]);
  }
  if(target==0x0806fc60)bitmap_glyph_call(cpu,pc,target);
  if(calls_file&&(pc<0x08002000||target<0x08020000||target==0x0806fc60))fprintf(calls_file,"%u,%08x,%08x,%08x,%08x,%08x,%08x\n",c->frameCounter(c),pc,target,cpu->gprs[0],cpu->gprs[1],cpu->gprs[2],cpu->gprs[3]);
 }
}
API void nf_calls(const char* path){if(calls_file)fclose(calls_file);calls_file=path?fopen(path,"w"):NULL;nfsThumbTrace=(native_scene_thumb||native_model_thumb||world_thumb||calls_file||image_copy_calls_file||timing_file||dt_percent!=100||normalize_steering)?thumbTrace:NULL;if(calls_file)fprintf(calls_file,"frame,caller,target,r0,r1,r2,r3\n");}
API int nf_image_copy_trace(const char*path){if(image_copy_calls_file)fclose(image_copy_calls_file);image_copy_calls_file=NULL;image_copy_calls_count=0;if(path&&*path){image_copy_calls_file=fopen(path,"w");if(!image_copy_calls_file)return 0;fprintf(image_copy_calls_file,"refresh,cycles,caller,destination,source,width,height,source_stride,destination_stride,sp\n");}nfsThumbTrace=(native_scene_thumb||native_model_thumb||world_thumb||calls_file||image_copy_calls_file||timing_file||dt_percent!=100||normalize_steering)?thumbTrace:NULL;return 1;}
API void nf_timing(const char* path){if(timing_file)fclose(timing_file);timing_file=path?fopen(path,"w"):NULL;nfsThumbTrace=(native_scene_thumb||native_model_thumb||world_thumb||calls_file||timing_file||dt_percent!=100||normalize_steering)?thumbTrace:NULL;if(timing_file)fprintf(timing_file,"vblank,cycles,car,fps_arg,x,z,speed\n");}
API void nf_dt(unsigned percent){dt_percent=percent?percent:100;nfsThumbTrace=(native_scene_thumb||native_model_thumb||world_thumb||calls_file||timing_file||dt_percent!=100||normalize_steering)?thumbTrace:NULL;}
API void nf_normalize_steering(int enabled){normalize_steering=enabled;steering_previous=0;nfsThumbTrace=(native_scene_thumb||native_model_thumb||world_thumb||calls_file||timing_file||dt_percent!=100||normalize_steering)?thumbTrace:NULL;}
API void nf_debug(unsigned pc){debug_pc=pc;debug_count=0;}
API int nf_debug_memory_config(unsigned reg,unsigned size){if(reg>=16||!size||size>256){debug_memory_reg=16;debug_memory_size=0;return 0;}debug_memory_reg=reg;debug_memory_size=size;memset(debug_memory,0,sizeof(debug_memory));return 1;}
API const uint8_t* nf_debug_memory_data(unsigned*count,unsigned*size){if(!count||!size)return NULL;*count=debug_count;*size=debug_memory_size;return &debug_memory[0][0];}
API const unsigned* nf_debug_data(int* n){*n=debug_count;return &debug_regs[0][0];}
API void nf_watch(unsigned base,unsigned size){watch_base=base;watch_end=base+size;memset(hist,0,sizeof(hist));memset(ihist,0,sizeof(ihist));}
static int validmem(uint32_t p,uint32_t n){return n<0x100000 && ((p>=0x02000000&&p+n<=0x02040000)||(p>=0x03000000&&p+n<=0x03008000)||(p>=0x08000000&&p+n<=0x08800000));}
static uint32_t rd32(uint32_t p){return c->busRead32(c,p);}
static uint32_t rd16(uint32_t p){return c->busRead16(c,p);}
static int16_t s16(uint32_t p){return (int16_t)rd16(p);}
/* Both menu/attract state 1 and race state 5 can render geometry.
   Each displayed page must have new geometry since its previous presentation;
   page flips without a fresh capture retire the old geometry. */
static int scene_race_active(void){unsigned state=rd32(0x03005f14);return state==1||state==5;}
API void nf_scene_reset(void){scene_page=-1;scene_count[0]=scene_count[1]=0;scene_dirty[0]=scene_dirty[1]=0;visible_count=0;memset(visible_overlay,0,sizeof(visible_overlay));}
API void nf_arm_hook_status(unsigned out[3]){if(out){out[0]=nfsArmHook!=NULL;out[1]=nfsArmHook==onArm;out[2]=scene_enabled;}}
API void nf_scene_enable(int e){scene_enabled=e;nf_scene_reset();nfsArmHook=(e||native_enabled||hookfile||poly_file)?onArm:0;}
API const NFPoly* nf_scene(int* n){*n=visible_count;return visible_polys;}
static NFPoly* scene_add(uint32_t material){
 if(!validmem(material,48))return NULL;
 uint32_t target=rd32(material+8);if(!validmem(target,16))return NULL;target=rd32(target);
 if(target!=0x06000000&&target!=0x0600a000)return NULL;
 int page=target==0x0600a000;
 if(page!=scene_page){scene_count[page]=0;scene_page=page;}
 if(scene_count[page]>=NF_MAX_POLYS)return NULL;
 NFPoly* p=&scene_polys[page][scene_count[page]];memset(p,0,sizeof(*p));
 unsigned shift=rd16(material+0x24),height=rd16(material+0x26);
 if(shift>10||height<1||height>1024)return NULL;
 p->address=rd32(material+0x28);p->width=1u<<shift;p->height=height;p->stride=p->width;
 return p;
}
static void scene_capture(struct ARMCore* cpu,unsigned pc){
 if(pc!=0x030053e8 && pc!=0x03005320 && pc!=0x030032f0 && pc!=0x03003d74)return;
 if(!scene_race_active())return;
 if(pc==0x030053e8 || pc==0x03005320){
  unsigned state=cpu->gprs[0],dest=cpu->gprs[1],n=cpu->gprs[3];
  if(!validmem(state,68)||n==0||n>320||dest<0x06000000||dest>=0x06014000)return;
  int page=dest>=0x0600a000;
  if(page!=scene_page){scene_count[page]=0;scene_page=page;}
  if(scene_count[page]>=NF_MAX_POLYS)return;
  unsigned shift=rd32(state+12),height=rd32(state+16),tex=rd32(state+36),dv=rd32(state+44),uvshift=15;
  if(shift>10||height<1||height>1024||!dv)return;
  if(rd32(state+24)&&dv>0x1b000){if(shift<2)return;shift-=2;height/=4;uvshift+=2;tex+=rd32(state+28);}
  if(!height||!validmem(tex,(1u<<shift)*height))return;
  NFPoly*p=&scene_polys[page][scene_count[page]];memset(p,0,sizeof(*p));
  p->address=tex;p->width=1u<<shift;p->height=height;p->stride=p->width;p->kind=3;p->count=4;
  if(pc==0x03005320){p->shade=rd32(state+20)+s16(state+42);if(!validmem(p->shade,4081))return;}
  float x=dest-(page?0x0600a000:0x06000000),y=rd32(state+4)/16384.0f;
  float q=32768.0f/dv,s=(int32_t)rd32(state+52)/(float)(1u<<uvshift)/p->width;
  float t=(int32_t)cpu->gprs[2]/(float)(1u<<uvshift)/height;
  float bottom=t+n*dv/(float)(1u<<uvshift)/height;
  p->v[0]=(NFVertex){x,y,s*q,t*q,q};p->v[1]=(NFVertex){x+2,y,s*q,t*q,q};p->v[2]=(NFVertex){x+2,y+n,s*q,bottom*q,q};p->v[3]=(NFVertex){x,y+n,s*q,bottom*q,q};
  if(scene_count[page]){
   NFPoly*prev=p-1;
   if(prev->kind==3&&prev->address==p->address&&prev->shade==p->shade&&fabsf(prev->v[1].x-x)<.01f&&fabsf(prev->v[1].y-y)<32&&fabsf(prev->v[1].s/prev->v[1].q-s)<.5f){prev->v[1]=p->v[0];prev->v[2]=p->v[3];}
  }
  scene_count[page]++;scene_dirty[page]=1;
 }else if(pc==0x030032f0){
  uint32_t material=cpu->gprs[0],state=cpu->gprs[1],uv=cpu->gprs[2];
  if(!validmem(state,256)||!validmem(uv,8))return;
  unsigned n=rd16(state+0xf4),vertices=rd32(state+0x6c)+rd16(state+0xf2)*24;
  if(n<3||n>NF_MAX_VERTS||!validmem(vertices,n*24))return;
  NFPoly* p=scene_add(material);if(!p)return;
  p->stride*=2;p->height/=2;p->count=n;p->kind=1;
  if(!p->height||!validmem(p->address,p->stride*p->height))return;
  int affine=rd32(cpu->gprs[13])!=0;
  float pw=p->width*0.5f,ox=s16(uv+4)/512.0f,oy=s16(uv+6)/512.0f;
  for(unsigned i=0;i<n;i++){
   uint32_t a=vertices+i*24;NFVertex* v=&p->v[i];
   v->x=(int32_t)rd32(a);v->y=(int32_t)rd32(a+4);
   v->q=affine?1.0f:(int32_t)rd32(a+12)/65536.0f;
   v->s=((int32_t)rd32(a+16)/65536.0f+ox*v->q)/pw;
   v->t=((int32_t)rd32(a+20)/65536.0f+oy*v->q)/p->height;
  }
  scene_count[scene_page]++;scene_dirty[scene_page]=1;
 }else if(pc==0x03003d74){
  uint32_t material=cpu->gprs[9],poly=cpu->gprs[4];
  if(!validmem(poly,32))return;
  unsigned n=rd32(poly+0x14),xy=rd32(poly),uv=rd32(poly+4),xi=rd32(poly+8),ui=rd32(poly+12);
  if(n<3||n>NF_MAX_VERTS||!validmem(xi,n*2)||!validmem(ui,n*2))return;
  NFPoly* p=scene_add(material);if(!p||!validmem(p->address,p->stride*p->height))return;
  p->count=n;p->kind=2;
  for(unsigned i=0;i<n;i++){
   unsigned a=xy+rd16(xi+i*2)*4,b=uv+rd16(ui+i*2)*4;
   if(!validmem(a,4)||!validmem(b,4))return;
   p->v[i]=(NFVertex){s16(a),s16(a+2),rd16(b)/32768.0f,rd16(b+2)/32768.0f,1.0f};
  }
  scene_count[scene_page]++;scene_dirty[scene_page]=1;
 }
}
static uint32_t rgb(uint16_t v){uint32_t p=((v&31)<<3)|(((v>>5)&31)<<11)|(((v>>10)&31)<<19);return p|((p>>5)&0x070707)|0xff000000;}
/* Match geometry and overlay to the scanout being drawn, not DISPCNT after
   runFrame returns: the game may already have flipped to its next page. */
#ifdef NF_VISIBILITY_CAPTURE
#include <mgba/internal/gba/renderers/video-software.h>
#include "camera/layer_snapshot.h"
static unsigned layer_dirty_enabled,layer_dirty_verify;static uint32_t layer_dirty_mask=0x1ffffffu;
static void(*layer_old_vram)(struct GBAVideoRenderer*,uint32_t);
static void(*layer_old_palette)(struct GBAVideoRenderer*,uint32_t,uint16_t);
static void(*layer_old_oam)(struct GBAVideoRenderer*,uint32_t);
static void layer_write_vram(struct GBAVideoRenderer*r,uint32_t address){if(address<0x18000)layer_dirty_mask|=1u<<(address/4096);else layer_dirty_mask=0x1ffffffu;layer_old_vram(r,address);}
static void layer_write_palette(struct GBAVideoRenderer*r,uint32_t address,uint16_t value){layer_dirty_mask|=1u<<24;layer_old_palette(r,address,value);}
static void layer_write_oam(struct GBAVideoRenderer*r,uint32_t address){layer_dirty_mask|=1u<<24;layer_old_oam(r,address);}
static int layer_add(NFLayerSnapshot*s,const void*row,struct GBAVideoRenderer*r){return layer_dirty_enabled?nf_layer_snapshot_add_dirty(s,row,r->vram,r->palette,r->oam,layer_dirty_mask,layer_dirty_verify):nf_layer_snapshot_add_parts(s,row,r->vram,r->palette,r->oam);}
static NFLayerSnapshot*layer_snapshot;static unsigned layer_capture_state,layer_capture_count;
API unsigned nf_layer_row_size(void){return sizeof(NFHardwareLayerRow);}
API int nf_layer_capture_arm(void){if(!c||layer_capture_state==2)return 0;NFLayerSnapshot*next=nf_layer_snapshot_create();if(!next)return 0;nf_layer_snapshot_destroy(layer_snapshot);layer_snapshot=next;layer_capture_state=1;layer_capture_count=0;return 1;}
API unsigned nf_layer_capture_status(void){return layer_capture_state;}
API unsigned nf_layer_capture_bytes(void){return (unsigned)nf_layer_snapshot_bytes(layer_snapshot);}
API unsigned nf_layer_capture_pages(void){return nf_layer_snapshot_pages(layer_snapshot);}
API int nf_layer_capture_row(unsigned row,void*out,unsigned size){if(layer_capture_state!=3||row>=160||!out||size!=sizeof(NFHardwareLayerRow))return 0;return nf_layer_snapshot_read(layer_snapshot,row,out);}
API uint64_t nf_native_scene_epoch(void);
#ifndef NF_LAYER_QUEUE_CAPACITY
#define NF_LAYER_QUEUE_CAPACITY 16
#endif
#if NF_LAYER_QUEUE_CAPACITY < 16 || NF_LAYER_QUEUE_CAPACITY > 64
#error Invalid layer queue capacity
#endif
API unsigned nf_layer_queue_capacity(void){return NF_LAYER_QUEUE_CAPACITY;}
static unsigned page_write_audit_enabled;
static uint64_t page_write_audit_generation[2],page_write_audit_version=1;
API uint64_t nf_page_write_audit_version(void){return page_write_audit_version;}
static uint64_t layer_pending_generation[160][2],layer_pending_generation_version[160];
static uint16_t layer_pending_display_control[160];
static int bitmap_text_scanline(const NFHardwareLayerHeader*,const uint8_t*,uint8_t*,uint8_t*);
static struct {uint64_t epoch;unsigned refresh;NFLayerSnapshot*snapshot;uint32_t mode,frontend,kind,text_valid;uint64_t generation[160][2],generation_version[160];uint16_t display_control[160];uint8_t text[38400],text_coverage[38400];} layer_queue[NF_LAYER_QUEUE_CAPACITY];
static NFLayerSnapshot*layer_pending,*layer_spare;static unsigned layer_queue_enabled,layer_queue_count,layer_queue_latest=~0u,layer_pending_count;static uint64_t layer_queue_epoch;
static uint32_t layer_pending_mode,layer_pending_frontend,layer_pending_context_stable,layer_pending_text_valid;
static uint8_t layer_pending_text[38400],layer_pending_text_coverage[38400];
/* Original Thumb08001804 selects byte03006710 from ROM08653AE0.
   State1/frontend1 includes attract3D; never treat missing capture as bitmap.
   Only independently verified startup/name/language/title handlers are2D. */
static unsigned layer_context_kind(uint32_t mode,uint32_t frontend){if(mode==5||(mode==1&&(frontend==1||(frontend==13&&rd32(0x08653ae0+13*4)==0x08011f1d))))return 1;if(mode!=1)return 0;uint32_t expected=frontend==0?0x080014cd:frontend==3?0x08011a1d:frontend==4?0x08013a29:frontend==18?0x08011b85:0;return expected&&rd32(0x08653ae0+frontend*4)==expected?2:0;}
API int nf_layer_queue_context(uint64_t epoch,unsigned refresh,uint32_t out[3]){if(!c||!out||epoch!=nf_native_scene_epoch())return 0;for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==epoch&&layer_queue[i].refresh==refresh){out[0]=layer_queue[i].mode;out[1]=layer_queue[i].frontend;out[2]=layer_queue[i].kind;return 1;}return 0;}
/* Emulation-owner guard for bounded frontend13 hidden-page loading intervals. */
API int nf_layer_queue_selection_page_equal(uint64_t epoch,unsigned source,unsigned target){
 if(!c||epoch!=nf_native_scene_epoch()||target<source||target-source>32)return 0;
 const NFLayerSnapshot*a=NULL,*b=NULL;
 for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++){
  if(!layer_queue[i].snapshot||layer_queue[i].epoch!=epoch||layer_queue[i].mode!=1||layer_queue[i].frontend!=13||layer_queue[i].kind!=1)continue;
  if(layer_queue[i].refresh==source)a=layer_queue[i].snapshot;
  if(layer_queue[i].refresh==target)b=layer_queue[i].snapshot;
 }
 return a&&b&&nf_layer_snapshot_display_page_equal(a,b);
}
/* First full scanout after publication must select the published scene page. */
API int nf_layer_queue_selection_scene_hold(uint64_t epoch,unsigned end,unsigned page,unsigned target){
 if(!c||epoch!=nf_native_scene_epoch()||end==~0u||page>1||target<end||target-end>32)return 0;
 const NFLayerSnapshot*a=NULL,*b=NULL;
 for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++){
  if(!layer_queue[i].snapshot||layer_queue[i].epoch!=epoch||layer_queue[i].mode!=1||layer_queue[i].frontend!=13||layer_queue[i].kind!=1)continue;
  if(layer_queue[i].refresh==end+1)a=layer_queue[i].snapshot;
  if(layer_queue[i].refresh==target)b=layer_queue[i].snapshot;
 }
 return a&&b&&nf_layer_snapshot_display_page(a,page)&&nf_layer_snapshot_display_page(b,page)&&nf_layer_snapshot_display_page_equal(a,b);
}
/* Verified one-switch scanout partition. Rejects absent/future/stale context. */
API int nf_layer_queue_selection_split(uint64_t epoch,unsigned older_end,unsigned older_page,unsigned newer_end,unsigned newer_page,unsigned target,unsigned*out){
 if(!c||!out||epoch!=nf_native_scene_epoch()||older_page>1||newer_page>1||older_page==newer_page||older_end>=newer_end||target!=newer_end||target-older_end>32||newer_end==~0u)return 0;
 const NFLayerSnapshot*a=NULL,*b=NULL,*t=NULL;
 for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++){
  if(!layer_queue[i].snapshot||layer_queue[i].epoch!=epoch||layer_queue[i].mode!=1||layer_queue[i].frontend!=13||layer_queue[i].kind!=1)continue;
  if(layer_queue[i].refresh==older_end+1)a=layer_queue[i].snapshot;
  if(layer_queue[i].refresh==newer_end+1)b=layer_queue[i].snapshot;
  if(layer_queue[i].refresh==target)t=layer_queue[i].snapshot;
 }
 if(!a||!b||!t)return 0;
 for(unsigned split=1;split<160;split++)if(nf_layer_snapshot_display_rows_equal(a,t,older_page,0,split)&&nf_layer_snapshot_display_rows_equal(b,t,newer_page,split,160)){*out=split;return 1;}
 return 0;
}
API int nf_layer_queue_text_row(uint64_t epoch,unsigned refresh,unsigned row,void*indices,void*coverage,unsigned size){if(!c||epoch!=nf_native_scene_epoch()||row>=160||!indices||!coverage||size!=240)return 0;for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==epoch&&layer_queue[i].refresh==refresh&&layer_queue[i].text_valid&&layer_queue[i].kind==1&&((layer_queue[i].mode==1&&layer_queue[i].frontend==13)||(getenv("NF_TEST_RACING_OWNED_CAPTURE")&&layer_queue[i].mode==5&&layer_queue[i].frontend==4))){memcpy(indices,layer_queue[i].text+row*240,240);memcpy(coverage,layer_queue[i].text_coverage+row*240,240);return 1;}return 0;}
static void layer_queue_clear(void){for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++){nf_layer_snapshot_destroy(layer_queue[i].snapshot);memset(layer_queue+i,0,sizeof(layer_queue[i]));}nf_layer_snapshot_destroy(layer_pending);nf_layer_snapshot_destroy(layer_spare);layer_pending=layer_spare=NULL;layer_queue_count=layer_pending_count=0;layer_queue_latest=~0u;}
API int nf_layer_queue_enable(unsigned enabled){if(!c||layer_capture_state==2)return 0;layer_queue_clear();layer_queue_enabled=enabled!=0;layer_queue_epoch=nf_native_scene_epoch();return 1;}
API unsigned nf_layer_queue_latest(void){return layer_queue_latest;}
/* Emulation-owner call only. Native VRAM is supplied by the scene producer;
   historical queue state is never replaced with current hardware memory. */
extern int nfs_native_snapshot_rgb4(const NFLayerSnapshot*,uint32_t,const uint8_t*,uint32_t*);
API int nf_layer_queue_native_rgb4(uint64_t epoch,unsigned refresh,const void*native_vram,unsigned bytes,void*out,unsigned out_bytes){
 if(!c||epoch!=nf_native_scene_epoch()||!native_vram||bytes!=0x18000||!out||out_bytes!=38400*4)return 0;
 for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==epoch&&layer_queue[i].refresh==refresh)
  return nfs_native_snapshot_rgb4(layer_queue[i].snapshot,refresh,native_vram,out);
 return 0;
}

API unsigned nf_layer_queue_bytes(void){size_t size=nf_layer_snapshot_bytes(layer_pending)+nf_layer_snapshot_bytes(layer_spare);for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)size+=nf_layer_snapshot_bytes(layer_queue[i].snapshot);return (unsigned)size;}
/* Emulation-owner only deep capture; consumer owns detached snapshot pages. */
API void* nf_layer_queue_clone(uint64_t epoch,unsigned refresh){
 if(!c||epoch!=nf_native_scene_epoch())return NULL;
 for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==epoch&&layer_queue[i].refresh==refresh)return nf_layer_snapshot_clone(layer_queue[i].snapshot);
 return NULL;
}
API int nf_layer_queue_row(uint64_t epoch,unsigned refresh,unsigned row,void*out,unsigned size){
 if(!c||epoch!=nf_native_scene_epoch()||!out||size!=sizeof(NFHardwareLayerRow)||row>=160)return 0;
 for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==epoch&&layer_queue[i].refresh==refresh)return nf_layer_snapshot_read(layer_queue[i].snapshot,row,out);return 0;
}
API unsigned nf_layer_hud_row_size(void){return sizeof(NFHudLayerRow);}
API int nf_layer_queue_zero_colors(uint64_t epoch,unsigned refresh,void*out,unsigned size){
 if(!c||epoch!=nf_native_scene_epoch()||!out||size!=320)return 0;
 for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==epoch&&layer_queue[i].refresh==refresh)return nf_layer_snapshot_zero_colors(layer_queue[i].snapshot,refresh,out);
 return 0;
}
API int nf_layer_queue_hud_row(uint64_t epoch,unsigned refresh,unsigned row,void*out,unsigned size){
 if(!c||epoch!=nf_native_scene_epoch()||!out||size!=sizeof(NFHudLayerRow)||row>=160)return 0;
 for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==epoch&&layer_queue[i].refresh==refresh)return nf_layer_snapshot_read_hud(layer_queue[i].snapshot,row,out);return 0;
}
/* Exact historical snapshot; rejects any generation change during its160rows.
   Observer reset/direct bus mutation invalidates all earlier versions. */
API int nf_layer_queue_page_generation(uint64_t epoch,unsigned refresh,unsigned page,uint64_t*out){
 if(!c||!out||page>1||!page_write_audit_enabled||epoch!=nf_native_scene_epoch())return 0;
 for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==epoch&&layer_queue[i].refresh==refresh){uint64_t generation=layer_queue[i].generation[0][page];for(unsigned y=0;y<160;y++)if(layer_queue[i].generation_version[y]!=page_write_audit_version||layer_queue[i].generation[y][page]!=generation)return 0;*out=generation;return 1;}return 0;
}
/* Producer supplies actual matching completion generations, not framebuffer
   pixels. Every exposed row must belong to exactly one unchanged owner. */
API int nf_layer_queue_split_generations(uint64_t epoch,unsigned refresh,unsigned older_page,uint64_t older_generation,unsigned newer_page,uint64_t newer_generation,unsigned*out){
 if(!c||!out||older_page>1||newer_page>1||older_page==newer_page||!page_write_audit_enabled||epoch!=nf_native_scene_epoch())return 0;
 for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==epoch&&layer_queue[i].refresh==refresh){if(layer_queue[i].kind!=1||!((layer_queue[i].mode==1&&layer_queue[i].frontend==13)||(getenv("NF_TEST_RACING_OWNED_CAPTURE")&&layer_queue[i].mode==5&&layer_queue[i].frontend==4)))return 0;unsigned cut=0,new_part=0;
  for(unsigned y=0;y<160;y++){unsigned display=layer_queue[i].display_control[y],page=(display>>4)&1;if((display&7)!=4||(display&0x8080)||layer_queue[i].generation_version[y]!=page_write_audit_version)return 0;
   if(page==newer_page){if(!new_part){if(!y)return 0;cut=y;new_part=1;}if(layer_queue[i].generation[y][page]!=newer_generation)return 0;}
   else if(new_part||page!=older_page||layer_queue[i].generation[y][page]!=older_generation)return 0;
  }if(!new_part)return 0;*out=cut;return 1;
 }return 0;
}
static void layer_capture_scanline(struct GBAVideoRenderer*r,int y){
 if(y<0||y>=160)return;
 if(layer_queue_enabled&&y==0){if(layer_queue_epoch!=nf_native_scene_epoch()){layer_queue_clear();layer_queue_epoch=nf_native_scene_epoch();}nf_layer_snapshot_destroy(layer_pending);layer_pending=layer_spare;layer_spare=NULL;if(layer_pending)nf_layer_snapshot_reset(layer_pending);else layer_pending=nf_layer_snapshot_create();layer_pending_count=0;layer_pending_mode=rd32(0x03005f14);layer_pending_frontend=c->busRead8(c,0x03006710);layer_pending_context_stable=1;layer_pending_text_valid=1;}
 if(layer_capture_state==1&&y==0)layer_capture_state=2;
 int single=layer_capture_state==2,queued=layer_queue_enabled&&layer_pending;
 if(!single&&!queued)return;
 if(single&&(unsigned)y!=layer_capture_count){layer_capture_state=0;single=0;}
 if(queued&&(unsigned)y!=layer_pending_count){nf_layer_snapshot_destroy(layer_pending);layer_pending=NULL;queued=0;}
 if(!single&&!queued)return;
 NFHardwareLayerHeader owned;NFHardwareLayerHeader*row=&owned;struct GBAVideoSoftwareRenderer*software=(struct GBAVideoSoftwareRenderer*)r;struct GBAVideoSoftwareBackground*bg=software->bg+2;
 row->refresh=c->frameCounter(c);row->row=(unsigned)y;memcpy(row->registers,((struct GBA*)c->board)->memory.io,0x60);
 row->affine[0]=bg->dx;row->affine[1]=bg->dmx;row->affine[2]=bg->dy;row->affine[3]=bg->dmy;row->affine[4]=bg->sx;row->affine[5]=bg->sy;

 if(single){if(!layer_add(layer_snapshot,row,r))layer_capture_state=0;else if(++layer_capture_count==160)layer_capture_state=3;}
 if(queued){layer_pending_display_control[y]=row->registers[0]|((unsigned)row->registers[1]<<8);memcpy(layer_pending_generation[y],page_write_audit_generation,16);layer_pending_generation_version[y]=page_write_audit_enabled?page_write_audit_version:0;if(!bitmap_text_scanline(row,(const uint8_t*)r->vram,layer_pending_text+y*240,layer_pending_text_coverage+y*240))layer_pending_text_valid=0;if(rd32(0x03005f14)!=layer_pending_mode||c->busRead8(c,0x03006710)!=layer_pending_frontend)layer_pending_context_stable=0;if(!layer_add(layer_pending,row,r)){nf_layer_snapshot_destroy(layer_pending);layer_pending=NULL;}else if(++layer_pending_count==160){unsigned slot=layer_queue_count++%NF_LAYER_QUEUE_CAPACITY;nf_layer_snapshot_destroy(layer_spare);layer_spare=layer_queue[slot].snapshot;layer_queue[slot].snapshot=layer_pending;memcpy(layer_queue[slot].display_control,layer_pending_display_control,sizeof(layer_pending_display_control));memcpy(layer_queue[slot].generation,layer_pending_generation,sizeof(layer_pending_generation));memcpy(layer_queue[slot].generation_version,layer_pending_generation_version,sizeof(layer_pending_generation_version));layer_queue[slot].text_valid=layer_pending_text_valid;memcpy(layer_queue[slot].text,layer_pending_text,38400);memcpy(layer_queue[slot].text_coverage,layer_pending_text_coverage,38400);layer_queue[slot].epoch=layer_queue_epoch;layer_queue[slot].refresh=row->refresh;layer_queue[slot].mode=layer_pending_mode;layer_queue[slot].frontend=layer_pending_frontend;layer_queue[slot].kind=layer_pending_context_stable?layer_context_kind(layer_pending_mode,layer_pending_frontend):0;layer_queue_latest=row->refresh;layer_pending=NULL;}}
 layer_dirty_mask=0;
}

#endif
static void scene_scanline(struct GBAVideoRenderer* renderer,int y){
#ifdef NF_VISIBILITY_CAPTURE
 uint64_t layer_started=capture_profile_enabled?capture_profile_now():0;
 layer_capture_scanline(renderer,y);
 if(capture_profile_enabled){capture_profile_ticks[2]+=capture_profile_now()-layer_started;capture_profile_ticks[3]++;}
#endif
 unsigned display=rd16(0x04000000),page=(display>>4)&1;
 if(y==0){
  int next_count=scene_enabled&&scene_race_active()&&(display&7)==4?scene_count[page]:0;
  if(next_count!=visible_count||(next_count&&memcmp(visible_polys,scene_polys[page],next_count*sizeof(NFPoly))))visible_version++;
  visible_count=next_count;
  if(visible_count)memcpy(visible_polys,scene_polys[page],visible_count*sizeof(NFPoly));
 }
 uint64_t scanline_started=capture_profile_enabled?capture_profile_now():0;
 original_scanline(renderer,y);
 if(capture_profile_enabled){capture_profile_ticks[4]+=capture_profile_now()-scanline_started;capture_profile_ticks[5]++;}
 if(scene_enabled && y>=0 && y<160){
  uint32_t pal[256];for(int i=0;i<256;i++)pal[i]=rgb(rd16(0x05000000+i*2));
  unsigned base=0x06000000+page*0xa000+y*240;
  for(unsigned x=0;x<240;x++){
   unsigned i=y*240+x,bg=pal[c->busRead8(c,base+x)];
   visible_overlay[i]=((pixels[i]&0xffffff)==(bg&0xffffff))?0:(pixels[i]|0xff000000);
  }
 }
}
API int nf_texture(const NFPoly* p,uint32_t* out){
 if(!validmem(p->address,p->stride*p->height)||p->width>1024||p->height>1024)return 0;
 uint32_t pal[256];for(int i=0;i<256;i++)pal[i]=rgb(rd16(0x05000000+i*2));
 for(unsigned y=0;y<p->height;y++)for(unsigned x=0;x<p->width;x++){unsigned idx=c->busRead8(c,p->address+y*p->stride+x);if(p->kind==3&&idx==0)out[y*p->width+x]=0;else{if(p->shade)idx=c->busRead8(c,p->shade+idx*16);out[y*p->width+x]=pal[idx];}}
 return 1;
}
API void nf_overlay(uint32_t* out){
 memcpy(out,visible_overlay,sizeof(visible_overlay));
}
API void nf_polygons(const char* path){if(poly_file)fclose(poly_file);poly_file=path?fopen(path,"wb"):NULL;nfsArmHook=(scene_enabled||poly_file||hookfile||native_enabled)?onArm:0;}
#include "camera/world_trace.h"
#include "camera/native_surface.h"
static FILE*native_roads_file;static unsigned native_roads_count;
static FILE*native_walls_file;static unsigned native_walls_count,native_wall_state,native_wall_descriptor;
static FILE*native_models_file;static unsigned native_models_count,native_model_context,native_model_camera,native_model_object,native_rotation_slot;
static struct {unsigned address,frame;int32_t matrix[12];} native_rotations[16];
static uint64_t native_rom_copy_stats[3];
API void nf_capture_rom_copy_stats(uint64_t out[3]){if(out)memcpy(out,native_rom_copy_stats,sizeof(native_rom_copy_stats));}
static int native_surface_read(void*context,uint32_t address,void*out,size_t size){
 (void)context;if(!c||!out||size>UINT32_MAX||(uint64_t)address+size>0x100000000ull)return 0;
 if(!validmem(address,(unsigned)size)&&!(address>=0x05000000&&(uint64_t)address+size<=0x05000200))return 0;
 /* Canonical, non-mirrored RAM ranges only. No I/O, palette or ROM reads use this path. */
 if(getenv("NF_TEST_DIRECT_CAPTURE_RAM")){struct GBA*gba=c->board;const uint8_t*source=NULL;if(address>=0x02000000&&(uint64_t)address+size<=0x02040000)source=(const uint8_t*)gba->memory.wram+(address-0x02000000);else if(address>=0x03000000&&(uint64_t)address+size<=0x03008000)source=(const uint8_t*)gba->memory.iwram+(address-0x03000000);if(source){memcpy(out,source,size);if(getenv("NF_TEST_VERIFY_CAPTURE_RAM"))for(size_t i=0;i<size;i++)if(((uint8_t*)out)[i]!=c->busRead8(c,address+(unsigned)i))return 0;return 1;}}
 /* GBALoad8 uses direct ROM bytes inside the canonical cartridge image.
    Exclude mirrors and out-of-image reads, which have different semantics. */
 if(getenv("NF_TEST_DIRECT_CAPTURE_ROM")){struct GBA*gba=c->board;
  if(address>=0x08000000&&(uint64_t)address+size<=0x0a000000&&(uint64_t)address+size<=0x08000000ull+gba->memory.romSize){
   memcpy(out,(const uint8_t*)gba->memory.rom+(address-0x08000000),size);native_rom_copy_stats[0]+=size;
   if(getenv("NF_TEST_VERIFY_CAPTURE_ROM"))for(size_t i=0;i<size;i++){native_rom_copy_stats[1]++;if(((uint8_t*)out)[i]!=c->busRead8(c,address+(unsigned)i)){native_rom_copy_stats[2]++;return 0;}}
   return 1;
  }
 }
 uint8_t*bytes=out;for(size_t i=0;i<size;i++)bytes[i]=c->busRead8(c,address+(unsigned)i);return 1;
}
API int nf_capture_memory_read(unsigned address,void*out,size_t size){return native_surface_read(NULL,address,out,size);}

#ifdef NF_VISIBILITY_CAPTURE
static void live_owned_model_invalidate(void);
static int live_native_model_assemble(unsigned context,unsigned camera,unsigned object,const int32_t*rotation,void**model,size_t*size);
#endif
#include "camera/live_scene.h"
#ifdef NF_VISIBILITY_CAPTURE
#include "camera/visibility_capture.h"
#include "camera/live_visibility.h"
#endif
API int nf_native_roads(const char*path){
 if(native_roads_file)fclose(native_roads_file);native_roads_file=path&&c?fopen(path,"wb"):NULL;native_roads_count=0;
 if(native_roads_file)nf_scene_enable(1);return native_roads_file!=NULL;
}
API int nf_native_walls(const char*path){
 if(native_walls_file)fclose(native_walls_file);native_walls_file=path&&c?fopen(path,"wb"):NULL;native_walls_count=0;native_wall_state=native_wall_descriptor=0;
 if(native_walls_file)nf_scene_enable(1);return native_walls_file!=NULL;
}
static void native_model_rotation(struct ARMCore*cpu,unsigned pc){
 if(pc!=0x0806db14||!native_models_file)return;
 unsigned slot=0;for(;slot<16;slot++)if(native_rotations[slot].address==cpu->gprs[2])break;
 if(slot==16)slot=native_rotation_slot++%16;
 if(native_surface_read(NULL,cpu->gprs[0],native_rotations[slot].matrix,48)){native_rotations[slot].address=cpu->gprs[2];native_rotations[slot].frame=c->frameCounter(c);}
}
API int nf_native_models(const char*path){
 if(native_models_file)fclose(native_models_file);native_models_file=path&&c?fopen(path,"wb"):NULL;native_models_count=0;native_model_context=native_model_camera=native_model_object=native_rotation_slot=0;memset(native_rotations,0,sizeof(native_rotations));
 native_model_thumb=native_models_file?native_model_rotation:NULL;
 nfsThumbTrace=(native_scene_thumb||native_model_thumb||world_thumb||calls_file||timing_file||dt_percent!=100||normalize_steering)?thumbTrace:NULL;
 if(native_models_file)nf_scene_enable(1);return native_models_file!=NULL;
}
static bool onArm(struct ARMCore* cpu){
 unsigned pc=cpu->gprs[15]-4;
#ifdef NF_VISIBILITY_CAPTURE
 visibility_event(cpu,pc);
 live_visibility_event(cpu,pc);
#endif
 NF_ARM_STAGE(0,native_scene_event(cpu,pc));
 if(native_models_file&&pc==0x03002628){native_model_context=cpu->gprs[0];native_model_camera=rd32(cpu->gprs[6]+84);native_model_object=cpu->gprs[7];}
 if(native_models_file&&pc==0x030045e0&&cpu->gprs[0]==native_model_context&&native_models_count++<1024){
  unsigned address=rd32(native_model_context+60),frame=c->frameCounter(c);void*model=NULL;size_t size=0;int ok=0;
  /* Captured rotations precede drawing by 2-3 refreshes. This bounded diagnostic cache
     consumes each match once; scene assembly must reset it across transitions. */
  for(unsigned i=0;i<16;i++)if(native_rotations[i].address==address&&frame-native_rotations[i].frame<=4){ok=nf_extract_model(native_surface_read,NULL,native_model_context,native_model_camera,native_model_object,native_rotations[i].matrix,&model,&size);native_rotations[i].address=0;break;}
  uint32_t header[6]={0x334d464e,frame,native_model_context,native_model_object,native_model_camera,ok?(uint32_t)size:0};fwrite(header,sizeof(header),1,native_models_file);if(ok)fwrite(model,1,size,native_models_file);nf_surface_free(model);
 }
 if(native_walls_file&&pc==0x03001800){native_wall_state=cpu->gprs[0];native_wall_descriptor=cpu->gprs[3];}
 if(native_walls_file&&pc==0x03000304&&native_wall_state==cpu->gprs[1]&&native_wall_descriptor&&native_walls_count++<4096){
  void*surface=NULL,*lighting=NULL;size_t size=0,light_size=0;
  int ok=nf_extract_wall(native_surface_read,NULL,cpu->gprs[1],native_wall_descriptor,cpu->gprs[6],cpu->gprs[0],cpu->gprs[3],cpu->gprs[2],&surface,&size,&lighting,&light_size);
  uint32_t header[6]={0x3257464e,c->frameCounter(c),native_wall_descriptor,cpu->gprs[6],ok?(uint32_t)size:0,ok?(uint32_t)light_size:0};fwrite(header,sizeof(header),1,native_walls_file);
  if(ok){fwrite(surface,1,size,native_walls_file);fwrite(lighting,1,light_size,native_walls_file);}nf_surface_free(surface);nf_surface_free(lighting);
 }
 if(native_roads_file&&pc==0x030032f0&&native_roads_count++<4096){
  void*surface=NULL;size_t size=0;int ok=nf_extract_road(native_surface_read,NULL,cpu->gprs[1],cpu->gprs[7],cpu->gprs[0],cpu->gprs[2],&surface,&size);
  uint32_t header[4]={0x3152464e,c->frameCounter(c),cpu->gprs[7],ok?(uint32_t)size:0};fwrite(header,sizeof(header),1,native_roads_file);if(ok)fwrite(surface,1,size,native_roads_file);nf_surface_free(surface);
 }
 NF_ARM_STAGE(1,world_trace(cpu,pc));
 if(pc==debug_pc&&debug_count<256){memcpy(debug_regs[debug_count],cpu->gprs,sizeof(debug_regs[0]));if(debug_memory_reg<16&&validmem(cpu->gprs[debug_memory_reg],debug_memory_size))for(unsigned i=0;i<debug_memory_size;i++)debug_memory[debug_count][i]=c->busRead8(c,cpu->gprs[debug_memory_reg]+i);debug_count++;}
 if(scene_enabled)NF_ARM_STAGE(2,scene_capture(cpu,pc));
 if(poly_file && pc==0x030032f0){
  uint32_t a=cpu->gprs[0],b=cpu->gprs[1],uv=cpu->gprs[2];
  uint32_t start=c->busRead16(c,b+0xf2),n=c->busRead16(c,b+0xf4),verts=c->busRead32(c,b+0x6c)+start*24;
  if(n>=3 && n<=16){
   uint32_t data[112]={0};data[0]=c->frameCounter(c);data[1]=c->busRead32(c,a+0x28);data[2]=c->busRead16(c,a+0x24);data[3]=c->busRead16(c,a+0x26);data[4]=n;
   data[5]=c->busRead16(c,uv+4);data[6]=c->busRead16(c,uv+6);data[7]=c->busRead32(c,c->busRead32(c,a+8));data[8]=c->busRead16(c,b+0xe6);data[9]=c->busRead16(c,b+0xe8);
   for(unsigned i=0;i<n*6;i++)data[16+i]=c->busRead32(c,verts+i*4);
   fwrite(data,sizeof(data),1,poly_file);
  }
 }
 if(cycle_file && span_return==pc){fprintf(cycle_file,"%u,%u,%llu\n",span_n,span_double,(unsigned long long)(mTimingGlobalTime(c->timing)-span_start));span_return=0;}
 if(cycle_file && pc==0x30056d8){span_start=mTimingGlobalTime(c->timing);span_return=cpu->gprs[14];span_n=c->busRead32(c,cpu->gprs[0]+0x1c);span_double=c->busRead32(c,0x3007098);}
 if(hookfile && (pc==0x30056d8 || pc==0x3005920 || pc==0x30053e8 || pc==0x3005320) && hooked++<20000){
  uint32_t data[35];data[0]=c->frameCounter(c);data[1]=pc;memcpy(data+2,cpu->gprs,16*4);
  for(int i=0;i<17;i++)data[18+i]=c->busRead32(c,cpu->gprs[0]+i*4);
  fwrite(data,4,35,hookfile);
 }
 if(native_enabled && pc==0x30056d8)return nativeSpan(cpu);
 return false;
}
API void nf_native(int enabled){native_enabled=enabled;nfsArmHook=(scene_enabled||enabled||hookfile||poly_file)?onArm:0;}
API unsigned nf_native_calls(void){return native_calls;}
API unsigned nf_native_rejected(void){return native_rejected;}
API void nf_capture(const char* path){if(hookfile)fclose(hookfile);if(cycle_file)fclose(cycle_file);hookfile=path?fopen(path,"wb"):0;cycle_file=path?fopen("work/span-cycles.csv","w"):0;if(cycle_file)fprintf(cycle_file,"count,double,cycles\n");hooked=0;nfsArmHook=(scene_enabled||poly_file||hookfile||native_enabled)?onArm:0;}
API struct mCore* nf_core(void){return c;}
/* Opt-in original DMA register provenance; diagnostic only, bounded file output. */
static FILE*bitmap_dma_trace;static unsigned bitmap_dma_trace_count;
/* DMA SAD/DAD are write-only on hardware; bus reads return open-bus values.
   Use retained emulator channel state for observational provenance. */
API int nf_bitmap_dma_state(uint32_t out[4][7]){
 if(!c||!out)return 0;uint32_t values[4][7];struct GBA*gba=c->board;
 for(unsigned i=0;i<4;i++){const struct GBADMA*info=gba->memory.dma+i;
  values[i][0]=info->source;values[i][1]=info->dest;values[i][2]=((uint32_t)info->reg<<16)|((uint32_t)info->count&0xffffu);
  values[i][3]=info->nextSource;values[i][4]=info->nextDest;values[i][5]=(uint32_t)info->nextCount;values[i][6]=info->when;}
 memcpy(out,values,sizeof(values));return 1;
}
API int nf_bitmap_dma_trace(const char*path){if(bitmap_dma_trace)fclose(bitmap_dma_trace);bitmap_dma_trace=NULL;bitmap_dma_trace_count=0;if(!path||!*path)return 1;bitmap_dma_trace=fopen(path,"w");if(!bitmap_dma_trace)return 0;fprintf(bitmap_dma_trace,"refresh,pc,lr,address,size,value,channel,source,destination,count_control\n");return 1;}
static void bitmap_dma_write(struct ARMCore*cpu,uint32_t address,unsigned size,uint32_t value){
 if(!bitmap_dma_trace||bitmap_dma_trace_count>=16384||address<0x040000b0||address>=0x040000e0)return;
 unsigned channel=(address-0x040000b0)/12;const struct GBADMA*info=((struct GBA*)c->board)->memory.dma+channel;
 uint32_t source=info->source,destination=info->dest,control=((uint32_t)info->reg<<16)|((uint32_t)info->count&0xffffu);
 fprintf(bitmap_dma_trace,"%u,%08x,%08x,%08x,%u,%08x,%u,%08x,%08x,%08x\n",c->frameCounter(c),cpu->gprs[15]-(cpu->cpsr.t?4:8),cpu->gprs[14],address,size,value,channel,source,destination,control);bitmap_dma_trace_count++;
}
static FILE*bitmap_blit_trace,*bitmap_glyph_trace,*bitmap_glyph_done;static unsigned bitmap_blit_count,bitmap_glyph_count;
static NFBitmapLayer*bitmap_live_layer;static uint64_t bitmap_live_epoch;
static NFBitmapGlyph bitmap_live_glyph;static uint8_t bitmap_live_asset[4096];static unsigned bitmap_live_bytes;
static struct {unsigned valid,index,begin,return_pc,sp,destination,display,vcount;} bitmap_glyph_pending;
API int nf_bitmap_text_enable(unsigned enabled){nf_bitmap_layer_destroy(bitmap_live_layer);bitmap_live_layer=NULL;bitmap_live_epoch=nf_native_scene_epoch();bitmap_glyph_pending.valid=0;if(enabled)bitmap_live_layer=nf_bitmap_layer_create(bitmap_live_epoch);return !enabled||bitmap_live_layer!=NULL;}
API int nf_bitmap_text_plane(uint64_t epoch,unsigned page,void*indices,void*coverage,unsigned size){return bitmap_live_layer&&epoch==nf_native_scene_epoch()&&size==38400&&nf_bitmap_layer_plane(bitmap_live_layer,epoch,page,indices,coverage,size);}
static FILE*bitmap_invalidation_trace;static unsigned bitmap_invalidation_count;
API int nf_bitmap_text_invalidation_trace(const char*path){if(bitmap_invalidation_trace)fclose(bitmap_invalidation_trace);bitmap_invalidation_trace=NULL;bitmap_invalidation_count=0;if(!path||!*path)return 1;bitmap_invalidation_trace=fopen(path,"w");if(!bitmap_invalidation_trace)return 0;fprintf(bitmap_invalidation_trace,"refresh,pc,address,bytes,lost_coverage\n");return 1;}
static void bitmap_text_invalidate(struct ARMCore*cpu,uint32_t address,unsigned bytes){
 if(bitmap_invalidation_trace&&bitmap_invalidation_count<65536&&address>=0x06000000&&address<0x06014000){
  unsigned frame=c->frameCounter(c),page=address>=0x0600a000,base=0x06000000+page*0xa000,offset=address-base,lost=0;
  if(frame>=3515&&frame<=3550){uint8_t indices[240],coverage[240];
   for(unsigned i=0;i<bytes&&offset+i<38400;i++){unsigned pixel=offset+i;
    if(pixel%240==0||i==0)if(!nf_bitmap_layer_row(bitmap_live_layer,bitmap_live_epoch,page,pixel/240,indices,coverage))break;
    lost+=coverage[pixel%240]!=0;
   }
   if(lost){unsigned pc=cpu?cpu->gprs[15]-(cpu->cpsr.t?4:8):0;fprintf(bitmap_invalidation_trace,"%u,%08x,%08x,%u,%u\n",frame,pc,address,bytes,lost);bitmap_invalidation_count++;}
  }
 }
 nf_bitmap_layer_invalidate(bitmap_live_layer,bitmap_live_epoch,address,bytes);
}
static void bitmap_text_write(struct ARMCore*cpu,uint32_t address,uint32_t value,unsigned bytes){
 if(!bitmap_live_layer)return;uint64_t epoch=nf_native_scene_epoch();if(epoch!=bitmap_live_epoch){nf_bitmap_layer_reset(bitmap_live_layer,epoch);bitmap_live_epoch=epoch;bitmap_glyph_pending.valid=0;}
 if((address>>24)==6){
  unsigned offset=address&0x1ffffu;
  if(bytes==1){unsigned limit=(rd16(0x04000000)&7)>=3?0x14000:0x10000;if(offset>=limit)return;address=0x06000000+(offset&~1u);value=(value&255u)*257u;bytes=2;}
  else{address=0x06000000+(offset&~(bytes-1u));}
 }
 /* A byte-identical original store preserves existing asset provenance.
    Comparison uses retained asset bytes only; uncovered pixels need no bus reads. */
 if(address>=0x06000000&&address+bytes<=0x06014000){unsigned changed=nf_bitmap_layer_changed_mask(bitmap_live_layer,epoch,address,value,bytes);for(unsigned i=0;i<bytes;i++)if(changed&(1u<<i))bitmap_text_invalidate(cpu,address+i,1);}
 else bitmap_text_invalidate(cpu,address,bytes);
}

static int bitmap_text_scanline(const NFHardwareLayerHeader*h,const uint8_t*vram,uint8_t*indices,uint8_t*coverage){memset(indices,0,240);memset(coverage,0,240);if(!bitmap_live_layer)return 0;uint64_t epoch=nf_native_scene_epoch();unsigned display=h->registers[0]|((unsigned)h->registers[1]<<8),page=(display>>4)&1;if((display&7)!=4||(display&0x80)||h->affine[0]!=256||h->affine[1]||h->affine[2]||h->affine[3]!=256||h->affine[4]||h->affine[5]!=(int32_t)(h->row*256)||!nf_bitmap_layer_row(bitmap_live_layer,epoch,page,h->row,indices,coverage))return 0;unsigned base=page*0xa000+h->row*240;for(unsigned x=0;x<240;x++)if(coverage[x]&&indices[x]!=vram[base+x]){coverage[x]=0;bitmap_text_invalidate(NULL,0x06000000+base+x,1);}return 1;}
API int nf_bitmap_blit_trace(const char*path){if(bitmap_blit_trace)fclose(bitmap_blit_trace);if(bitmap_glyph_trace)fclose(bitmap_glyph_trace);if(bitmap_glyph_done)fclose(bitmap_glyph_done);bitmap_blit_trace=bitmap_glyph_trace=bitmap_glyph_done=NULL;memset(&bitmap_glyph_pending,0,sizeof(bitmap_glyph_pending));bitmap_blit_count=bitmap_glyph_count=0;if(!path||!*path)return 1;bitmap_blit_trace=fopen(path,"w");if(!bitmap_blit_trace)return 0;char glyphpath[1400];snprintf(glyphpath,sizeof(glyphpath),"%s.glyphs.bin",path);bitmap_glyph_trace=fopen(glyphpath,"wb");if(!bitmap_glyph_trace){fclose(bitmap_blit_trace);bitmap_blit_trace=NULL;return 0;}snprintf(glyphpath,sizeof(glyphpath),"%s.glyphs-done.csv",path);bitmap_glyph_done=fopen(glyphpath,"w");if(!bitmap_glyph_done){nf_bitmap_blit_trace(NULL);return 0;}fprintf(bitmap_glyph_done,"index,begin,end,return_pc,sp,destination,entry_display,exit_display,entry_vcount,exit_vcount\n");fprintf(bitmap_blit_trace,"refresh,pc,lr,destination,pixel_address,source,source_index,palette_offset,transparent_index,value\n");return 1;}
static int bitmap_glyph_capture_active(void){return bitmap_live_layer||bitmap_glyph_trace;}
static void bitmap_glyph_call(struct ARMCore*cpu,unsigned pc,unsigned target){
 if((!bitmap_glyph_trace&&!bitmap_live_layer)||bitmap_glyph_pending.valid||(bitmap_glyph_trace&&bitmap_glyph_count>=4096))return;
 uint8_t descriptor[20],pixels[4096],draw_width;uint32_t address=cpu->gprs[0],glyph=cpu->gprs[1];
 if(!glyph||glyph>255||!native_surface_read(NULL,address,descriptor,20))return;
 int16_t width,height;uint32_t base,table;memcpy(&width,descriptor+4,2);memcpy(&height,descriptor+6,2);memcpy(&base,descriptor+12,4);memcpy(&table,descriptor+16,4);
 if(width<=0||height<=0||(unsigned)width*(unsigned)height>4096)return;
 uint32_t size=(unsigned)width*(unsigned)height;uint64_t source=(uint64_t)base+size*(glyph-1);
 if(source>UINT32_MAX||!native_surface_read(NULL,(uint32_t)source,pixels,size)||!native_surface_read(NULL,table+glyph,&draw_width,1)||draw_width>width)return;
 uint32_t record[16]={c->frameCounter(c),pc,address,glyph,cpu->gprs[2],cpu->gprs[3],rd32(cpu->gprs[13]),width,height,draw_width,descriptor[1],descriptor[2],(uint32_t)source,size,cpu->gprs[14],target};
 if(bitmap_glyph_trace){fwrite(record,sizeof(record),1,bitmap_glyph_trace);fwrite(pixels,1,size,bitmap_glyph_trace);}
 bitmap_live_glyph=(NFBitmapGlyph){width,height,draw_width,cpu->gprs[3],descriptor[1],descriptor[2],record[6]};memcpy(bitmap_live_asset,pixels,size);bitmap_live_bytes=size;
 bitmap_glyph_pending.valid=1;bitmap_glyph_pending.index=bitmap_glyph_count;bitmap_glyph_pending.begin=record[0];bitmap_glyph_pending.return_pc=pc+4;bitmap_glyph_pending.sp=cpu->gprs[13];bitmap_glyph_pending.destination=cpu->gprs[2];bitmap_glyph_pending.display=rd16(0x04000000);bitmap_glyph_pending.vcount=rd16(0x04000006);bitmap_glyph_count++;
}
static void bitmap_glyph_completion(struct ARMCore*cpu,unsigned pc){
 if((!bitmap_glyph_done&&!bitmap_live_layer)||!bitmap_glyph_pending.valid||pc!=bitmap_glyph_pending.return_pc||cpu->gprs[13]!=bitmap_glyph_pending.sp)return;
 if(bitmap_glyph_done)fprintf(bitmap_glyph_done,"%u,%u,%u,%08x,%08x,%08x,%04x,%04x,%u,%u\n",bitmap_glyph_pending.index,bitmap_glyph_pending.begin,c->frameCounter(c),pc,cpu->gprs[13],bitmap_glyph_pending.destination,bitmap_glyph_pending.display,rd16(0x04000000),bitmap_glyph_pending.vcount,rd16(0x04000006));
 if(bitmap_live_layer&&bitmap_live_epoch==nf_native_scene_epoch()&&bitmap_glyph_pending.display==rd16(0x04000000))nf_bitmap_layer_glyph(bitmap_live_layer,bitmap_live_epoch,bitmap_glyph_pending.destination,&bitmap_live_glyph,bitmap_live_asset,bitmap_live_bytes);
 bitmap_glyph_pending.valid=0;
}
/* Bounded store-callback observation. Core DMA service uses these callbacks. */


/* Separate cumulative interval clock; per-update observer resets do not reset it. */
API void nf_page_write_audit_generation_reset(void){page_write_audit_version++;memset(page_write_audit_generation,0,sizeof(page_write_audit_generation));}
API int nf_page_write_audit_generation_copy(uint64_t out[2]){if(!out||!page_write_audit_enabled)return 0;memcpy(out,page_write_audit_generation,sizeof(page_write_audit_generation));return 1;}
static uint64_t page_write_audit_counts[2],page_write_audit_origins[2][2];
API int nf_page_write_audit_origins_copy(uint64_t out[2][2]){if(!out||!page_write_audit_enabled)return 0;memcpy(out,page_write_audit_origins,sizeof(page_write_audit_origins));return 1;}
API int nf_page_write_audit_counts_copy(uint64_t out[2]){if(!out||!page_write_audit_enabled)return 0;memcpy(out,page_write_audit_counts,sizeof(page_write_audit_counts));return 1;}
static uint32_t page_write_audit_pc[240*160];
static uint32_t page_write_audit_source[240*160];
API void nf_page_write_audit_enable(unsigned enabled){if(page_write_audit_enabled!=(enabled!=0))page_write_audit_version++;page_write_audit_enabled=enabled!=0;memset(page_write_audit_counts,0,sizeof(page_write_audit_counts));memset(page_write_audit_origins,0,sizeof(page_write_audit_origins));memset(page_write_audit_pc,0,sizeof(page_write_audit_pc));memset(page_write_audit_source,0,sizeof(page_write_audit_source));}
API int nf_page_write_audit_copy(void*out,unsigned bytes){if(!out||!page_write_audit_enabled||bytes!=sizeof(page_write_audit_pc))return 0;memcpy(out,page_write_audit_pc,bytes);return 1;}
API int nf_page_write_audit_sources(void*out,unsigned bytes){if(!out||!page_write_audit_enabled||bytes!=sizeof(page_write_audit_source))return 0;memcpy(out,page_write_audit_source,bytes);return 1;}
static void page_write_audit(struct ARMCore*cpu,uint32_t address,unsigned bytes){
 if(!page_write_audit_enabled)return;
 /* Separate CPU and DMA origins using the core execution flag. Counts do
    not establish scanline timing or external/direct VRAM mutation coverage. */
 for(unsigned page=0;page<2;page++){uint64_t start=0x06000000ull+page*0xa000,end=start+240*160,lo=address,hi=lo+bytes;if(lo<end&&hi>start){if(lo<start)lo=start;if(hi>end)hi=end;page_write_audit_counts[page]+=hi-lo;page_write_audit_generation[page]+=hi-lo;page_write_audit_origins[((struct GBA*)c->board)->performingDMA?1:0][page]+=hi-lo;}}
 if(address<0x06000000||address>=0x06009600)return;
 uint32_t offset=address-0x06000000,pc=cpu->gprs[15]-(cpu->cpsr.t?4:8);
 if(bytes>sizeof(page_write_audit_pc)/4-offset)bytes=sizeof(page_write_audit_pc)/4-offset;
 /* Verified ARM copy loop: two postincrement LDRH precede each STR. */
 uint32_t source=(!cpu->cpsr.t&&pc>=0x0300386c&&pc<=0x030038dc&&!((pc-0x0300386c)&15)&&bytes==4)?cpu->gprs[12]-4:0;
 for(unsigned i=0;i<bytes;i++){page_write_audit_pc[offset+i]=pc;page_write_audit_source[offset+i]=source?source+i:0;}
}
static void store8(struct ARMCore* cpu,uint32_t a,int8_t v,int* cycles){
 page_write_audit(cpu,a&~1u,2); /* GBA VRAM byte stores duplicate to aligned halfword. */
 bitmap_dma_write(cpu,a,1,(uint32_t)v);
 bitmap_text_write(cpu,a,(uint32_t)v,1);
 world_framebuffer_write(a,1);
#ifdef NF_VISIBILITY_CAPTURE
 visibility_write(cpu,a,1,(uint8_t)v);
#endif
 if(a==0x04000000&&((rd16(a)^(uint8_t)v)&16))world_flip(rd16(a),(rd16(a)&0xff00)|(uint8_t)v);
 unsigned pc=cpu->gprs[15]-(cpu->cpsr.t?4:8);
 if(watch_end?(a>=watch_base&&a<watch_end):((a>>24)==6)){if(pc>=0x08000000&&pc<0x08800000)hist[(pc-0x08000000)/4]++;if(pc>=0x03000000&&pc<0x03008000)ihist[(pc-0x03000000)/4]++;}
 old8(cpu,a,v,cycles);
}
static uint32_t storeMultiple(struct ARMCore* cpu,uint32_t a,int mask,enum LSMDirection dir,int* cycles){
 world_framebuffer_write(a,4*(unsigned)__builtin_popcount((unsigned)mask));
 /* Match original GBAStoreMultiple address ordering/alignment. Empty mask
    stores one PC word even though original writeback advances by64. */
 if(bitmap_live_layer||page_write_audit_enabled){
  unsigned count=(unsigned)__builtin_popcount((unsigned)mask&0xffffu);uint32_t first=a;
  if(dir&LSM_D)first-=count*4-4;
  if(dir&LSM_B)first+=(dir&LSM_D)?-4:4;
  first&=~3u;
  unsigned reg=0;
  for(unsigned i=0;i<(count?count:1);i++){
   while(count&&reg<16&&!(mask&(1u<<reg)))reg++;
   uint32_t value=count?cpu->gprs[reg++]:cpu->gprs[15]+(cpu->cpsr.t?2:4);
   uint32_t address=first+i*4;
   page_write_audit(cpu,address,4);
   if((address>>24)==6){unsigned offset=address&0x1ffffu;
    if(offset<0x18000)bitmap_text_write(cpu,0x06000000+offset,value,4);
   }
  }
 }
 unsigned pc=cpu->gprs[15]-(cpu->cpsr.t?4:8);
 if(watch_end?(a>=watch_base&&a<watch_end):((a>>24)==6)){if(pc>=0x08000000&&pc<0x08800000)hist[(pc-0x08000000)/4]++;if(pc>=0x03000000&&pc<0x03008000)ihist[(pc-0x03000000)/4]++;}
 uint32_t result=oldMultiple(cpu,a,mask,dir,cycles);
 /* Post-store observation: bounded diagnostic, no claimed pre-enable ordering. */
 if(bitmap_dma_trace&&a>=0x04000090&&a<0x04000100)for(unsigned channel=0;channel<4;channel++){unsigned base=0x040000b0+channel*12;bitmap_dma_write(cpu,base+8,0,rd32(base+8));}
 return result;
}
static void store32(struct ARMCore* cpu,uint32_t a,int32_t v,int* cycles){
 page_write_audit(cpu,a&~3u,4);
 bitmap_dma_write(cpu,a,4,(uint32_t)v);
 bitmap_text_write(cpu,a,(uint32_t)v,4);
 world_framebuffer_write(a,4);
#ifdef NF_VISIBILITY_CAPTURE
 visibility_write(cpu,a,4,(uint32_t)v);
#endif
 if(a==0x04000000&&((rd16(a)^(uint16_t)v)&16))world_flip(rd16(a),(uint16_t)v);
 unsigned pc=cpu->gprs[15]-(cpu->cpsr.t?4:8);
 if(watch_end?(a>=watch_base&&a<watch_end):((a>>24)==6)){if(pc>=0x08000000&&pc<0x08800000)hist[(pc-0x08000000)/4]++;if(pc>=0x03000000&&pc<0x03008000)ihist[(pc-0x03000000)/4]++;}
 old32(cpu,a,v,cycles);
}
static void store16(struct ARMCore* cpu,uint32_t a,int16_t v,int* cycles){
 page_write_audit(cpu,a&~1u,2);
 bitmap_dma_write(cpu,a,2,(uint32_t)v);
 bitmap_text_write(cpu,a,(uint32_t)v,2);
 world_framebuffer_write(a,2);
#ifdef NF_VISIBILITY_CAPTURE
 visibility_write(cpu,a,2,(uint16_t)v);
#endif
 if(a==0x04000000&&((rd16(a)^(uint16_t)v)&16))world_flip(rd16(a),(uint16_t)v);
 if(scene_enabled && a==0x04000000 && ((rd16(a)^(uint16_t)v)&16)){int page=((uint16_t)v>>4)&1;if(!scene_dirty[page])scene_count[page]=0;scene_dirty[page]=0;}
 unsigned pc=cpu->gprs[15]-(cpu->cpsr.t?4:8);
 if(bitmap_blit_trace&&bitmap_blit_count<65536&&pc==0x0806fcf0&&a>=0x06000000&&a<0x06014000){
  fprintf(bitmap_blit_trace,"%u,%08x,%08x,%08x,%08x,%08x,%u,%u,%u,%04x\n",c->frameCounter(c),pc,cpu->gprs[14],a,cpu->gprs[4],cpu->gprs[5]-1,c->busRead8(c,cpu->gprs[5]-1),rd32(cpu->gprs[13]+0x2c),cpu->gprs[10],(uint16_t)v);bitmap_blit_count++;
 }
 if(a==0x04000000 && trace_file){fprintf(trace_file,"%u,%08x,%08x,%04x\n",c->frameCounter(c),pc,cpu->gprs[14],(uint16_t)v);fflush(trace_file);flips++;}
 if(watch_end?(a>=watch_base&&a<watch_end):((a>>24)==6)){stores++; if(pc>=0x08000000 && pc<0x08800000)hist[(pc-0x08000000)/4]++; if(pc>=0x03000000 && pc<0x03008000)ihist[(pc-0x03000000)/4]++;}
 old16(cpu,a,v,cycles);
}

API void nf_60(int enabled){mode60=enabled;nf_pace(enabled);nfsCpuSpeed=1;}
API void nf_frame(unsigned keys){
 if(capture_profile_enabled)memset(capture_profile_ticks,0,sizeof(capture_profile_ticks));
 if(mode60)nfsCpuSpeed=c->busRead32(c,0x03005f14)==5?8:1;
 if(scene_enabled&&!scene_race_active())nf_scene_reset();
 native_scene_check_mode();
 c->setKeys(c,keys);c->runFrame(c);
 native_scene_check_mode();
 if(scene_enabled&&!scene_race_active())nf_scene_reset();
}
API void* nf_pixels(void){return pixels;}
API unsigned nf_read(unsigned a,int width){return width==4?c->busRead32(c,a):width==2?c->busRead16(c,a):c->busRead8(c,a);}
#ifdef NF_VISIBILITY_CAPTURE
/* Read-only owned register shadows, including write-only display registers.
   Post-refresh diagnostic; not a scanline-latched display snapshot. */
API int nf_display_registers(void*out,unsigned bytes){
 if(!c||!out||bytes!=0x60)return 0;
 memcpy(out,((struct GBA*)c->board)->memory.io,0x60);return 1;
}
#endif
API void nf_write(unsigned a,unsigned v,int width){page_write_audit_version++;if(width==4)c->busWrite32(c,a,v);else if(width==2)c->busWrite16(c,a,v);else c->busWrite8(c,a,v);}
API unsigned nf_reg(int n){return ((struct ARMCore*)c->cpu)->gprs[n];}
API unsigned nf_cpsr(void){return ((struct ARMCore*)c->cpu)->cpsr.packed;}
API void nf_step(void){c->step(c);}
API int nf_state(const char* path,int save){size_t n=c->stateSize(c);void* b=malloc(n);if(!b)return 0;FILE* f=fopen(path,save?"wb":"rb");if(!f){free(b);return 0;}int ok;if(save){ok=c->saveState(c,b);ok=ok && fwrite(b,1,n,f)==n;}else{ok=fread(b,1,n,f)==n;ok=ok && c->loadState(c,b);if(ok){
#ifdef NF_VISIBILITY_CAPTURE
 layer_capture_state=layer_capture_count=0;layer_queue_clear();
#endif
 nf_scene_reset();nf_native_scene_discontinuity();}}fclose(f);free(b);return ok;}
API void nf_dump(const char* path,unsigned a,unsigned n){FILE*f=fopen(path,"wb");if(!f)return;for(unsigned i=0;i<n;i++)fputc(c->busRead8(c,a+i),f);fclose(f);}
API void nf_hist(const char* path){FILE*f=fopen(path,"w");if(!f)return;fprintf(f,"pc,vram_halfword_stores\n");for(unsigned i=0;i<0x200000;i++)if(hist[i])fprintf(f,"%08x,%u\n",0x08000000+i*4,hist[i]);for(unsigned i=0;i<0x2000;i++)if(ihist[i])fprintf(f,"%08x,%u\n",0x03000000+i*4,ihist[i]);fclose(f);}
API void nf_close(void){
 indexed_copy_capture_enabled=0;
 nf_image_copy_trace(NULL);
 nf_bitmap_text_invalidation_trace(NULL);
#ifdef NF_VISIBILITY_CAPTURE
 layer_queue_clear();layer_queue_enabled=0;nf_layer_snapshot_destroy(layer_snapshot);layer_snapshot=NULL;layer_capture_state=layer_capture_count=0;
 visibility_close();
 live_visibility_close();
#endif
 nf_native_scenes(NULL);
 native_model_thumb=NULL;if(native_models_file)fclose(native_models_file);native_models_file=NULL;
 if(native_walls_file)fclose(native_walls_file);native_walls_file=NULL;
 if(native_roads_file)fclose(native_roads_file);native_roads_file=NULL;
 world_thumb=NULL;
 if(world_file)fclose(world_file);world_file=NULL;
 nfsArmHook=NULL;native_enabled=0;nfsThumbGate=NULL;
 nfsThumbTrace=NULL;if(timing_file)fclose(timing_file);timing_file=NULL;if(calls_file)fclose(calls_file);calls_file=NULL;
 if(trace_file)fclose(trace_file);trace_file=NULL;nf_bitmap_dma_trace(NULL);nf_bitmap_blit_trace(NULL);nf_bitmap_text_enable(0);
 if(hookfile)fclose(hookfile);hookfile=NULL;
 if(cycle_file)fclose(cycle_file);cycle_file=NULL;
 if(poly_file)fclose(poly_file);poly_file=NULL;
 if(dma_file)fclose(dma_file);dma_file=NULL;
 c=NULL;
}





int nf_android_observer_sky_enable(int);
#include "camera/wall_history_store.h"
#include "camera/write_ownership.h"
#include "camera/road_history_store.h"
int nf_android_observer_wall_history_enable(int);
static void android_wall_boundary(int);
static void android_wall_close_owner(uint64_t,const NFScenePacket*);
static int android_source_world;
static uint8_t*android_previous;static size_t android_previous_bytes;
static uint64_t android_previous_epoch,android_previous_generation,android_previous_version;
static void android_previous_clear(void){free(android_previous);android_previous=NULL;android_previous_bytes=0;android_previous_epoch=android_previous_generation=android_previous_version=0;}
static int android_layers;
static uint64_t android_packet_generation,android_packet_audit_version;
static uint8_t*android_packet;static size_t android_packet_bytes;static uint64_t android_packet_epoch;
static int android_sink(void*context,uint64_t epoch,const void*data,size_t bytes){
 (void)context;NFScenePacket view;
 if(!nf_scene_packet_view(data,bytes,&view))return 0;
 android_wall_close_owner(epoch,&view);
 void*copy=malloc(bytes);if(!copy)return 0;memcpy(copy,data,bytes);
 android_previous_clear();
 if(android_packet&&android_packet_epoch==epoch){android_previous=android_packet;android_previous_bytes=android_packet_bytes;android_previous_epoch=android_packet_epoch;android_previous_generation=android_packet_generation;android_previous_version=android_packet_audit_version;android_packet=NULL;}
 uint64_t generation[2];
 android_packet_audit_version=0;
 if(android_layers&&nf_page_write_audit_generation_copy(generation)){android_packet_generation=generation[view.page];android_packet_audit_version=nf_page_write_audit_version();}
 free(android_packet);android_packet=copy;android_packet_bytes=bytes;android_packet_epoch=epoch;return 1;
}
int nf_android_observer_attach(struct mCore*core,uint32_t*framebuffer){
 if(c||!core||!framebuffer||nfsArmHook||nfsThumbTrace||nfsThumbGate)return 0;
 c=core;pixels=framebuffer;mode60=0;native_enabled=0;dt_percent=100;normalize_steering=0;
 nf_page_write_audit_enable(0);
struct ARMCore* cpu=c->cpu;old16=cpu->memory.store16;cpu->memory.store16=store16;
 old32=cpu->memory.store32;cpu->memory.store32=store32;
 old8=cpu->memory.store8;cpu->memory.store8=store8;
  oldMultiple=cpu->memory.storeMultiple;cpu->memory.storeMultiple=storeMultiple;
  struct GBAVideoRenderer* renderer=((struct GBA*)c->board)->video.renderer;
  original_scanline=renderer->drawScanline;renderer->drawScanline=scene_scanline;
#ifdef NF_VISIBILITY_CAPTURE
 layer_dirty_enabled=getenv("NF_LAYER_DIRTY")!=NULL;layer_dirty_verify=getenv("NF_VERIFY_LAYER_DIRTY")!=NULL;layer_dirty_mask=0x1ffffffu;
 if(layer_dirty_enabled){layer_old_vram=renderer->writeVRAM;layer_old_palette=renderer->writePalette;layer_old_oam=renderer->writeOAM;renderer->writeVRAM=layer_write_vram;renderer->writePalette=layer_write_palette;renderer->writeOAM=layer_write_oam;}
#endif

 if(!nf_native_scene_sink(android_sink,NULL))return 0;
 if(!nf_native_scene_multimodel(1))return 0;
 return 1;
}
void nf_android_observer_detach(void){
 nf_android_geometry_cache_reset(1);
 if(!c)return;
 nf_android_observer_sky_enable(0);nf_android_observer_wall_history_enable(0);
 struct ARMCore*cpu=c->cpu;
 cpu->memory.store16=old16;cpu->memory.store32=old32;cpu->memory.store8=old8;cpu->memory.storeMultiple=oldMultiple;
 struct GBAVideoRenderer*r=((struct GBA*)c->board)->video.renderer;r->drawScanline=original_scanline;
#ifdef NF_VISIBILITY_CAPTURE
 if(layer_dirty_enabled){r->writeVRAM=layer_old_vram;r->writePalette=layer_old_palette;r->writeOAM=layer_old_oam;}
#endif
 android_source_world=0;android_layers=0;nf_layer_queue_enable(0);
 nf_scene_enable(0);nf_close();android_previous_clear();free(android_packet);android_packet=NULL;android_packet_bytes=0;android_packet_epoch=0;
}
void nf_android_observer_boundary(void){if(c){native_scene_check_mode();android_wall_boundary(0);}}
void nf_android_observer_reset(void){
 nf_android_geometry_cache_reset(0);
 if(!c)return;android_previous_clear();nf_scene_reset();nf_native_scene_discontinuity();android_wall_boundary(1);
 if(android_layers)nf_layer_queue_enable(1);
 free(android_packet);android_packet=NULL;android_packet_bytes=0;android_packet_epoch=0;
}
size_t nf_android_observer_copy(void*out,size_t capacity){
 if(!c||!android_packet||android_packet_epoch!=nf_native_scene_epoch())return 0;
 if(!out)return android_packet_bytes;
 if(capacity<android_packet_bytes)return 0;memcpy(out,android_packet,android_packet_bytes);return android_packet_bytes;
}
void nf_android_observer_stats(uint64_t out[8]){
 uint32_t s[4]={0};nf_native_scene_stats(s);
 uint64_t values[8]={c!=NULL,nf_native_scene_epoch(),s[0],s[1],s[2],s[3],nf_android_observer_copy(NULL,0),0};
 if(android_packet&&android_packet_epoch==nf_native_scene_epoch()){NFScenePacket p;if(nf_scene_packet_view(android_packet,android_packet_bytes,&p))values[7]=p.serial;}
 memcpy(out,values,sizeof(values));
}

/* Auxiliary capture is opt-in and keeps the original scanline-owned state.
   A refresh is not claimed to belong to a geometry packet by this interface. */
int nf_android_observer_layers(int enabled){
 if(!c||!nf_layer_queue_enable(enabled!=0))return 0;
 android_layers=enabled!=0;nf_page_write_audit_enable(android_layers);
 nf_page_write_audit_generation_reset();android_packet_audit_version=0;android_previous_clear();return 1;
}
int nf_android_observer_layer_info(uint64_t out[5]){
 if(!c||!android_layers||!out)return 0;
 unsigned refresh=nf_layer_queue_latest();uint32_t context[3];
 uint64_t epoch=nf_native_scene_epoch();
 if(!nf_layer_queue_context(epoch,refresh,context))return 0;
 uint64_t info[5]={epoch,refresh,context[0],context[1],context[2]};
 memcpy(out,info,sizeof(info));return 1;
}
size_t nf_android_observer_layer_row(uint64_t epoch,unsigned refresh,unsigned row,void*out,size_t capacity){
 if(!c||!android_layers||row>=160||epoch!=nf_native_scene_epoch())return 0;
 uint32_t context[3];if(!nf_layer_queue_context(epoch,refresh,context))return 0;
 size_t bytes=sizeof(NFHardwareLayerRow);if(!out)return bytes;
 if(capacity<bytes)return 0;
 return nf_layer_queue_row(epoch,refresh,row,out,(unsigned)bytes)?bytes:0;
}

/* Strict whole-scanout join. Transitional/split pages are deliberately rejected;
   split-scene support must carry two explicit owners rather than guess. */
int nf_android_observer_pair(unsigned refresh,uint64_t out[8]){
 if(!c||!android_layers||!out||!android_packet_audit_version||!nf_android_observer_copy(NULL,0))return 0;
 if(android_packet_audit_version!=nf_page_write_audit_version())return 0;
 NFScenePacket packet;uint64_t generation;
 if(!nf_scene_packet_view(android_packet,android_packet_bytes,&packet)||refresh<=packet.end_refresh)return 0;
 if(!nf_layer_queue_page_generation(android_packet_epoch,refresh,packet.page,&generation)||generation!=android_packet_generation)return 0;
 for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==android_packet_epoch&&layer_queue[i].refresh==refresh){
  if(!layer_queue[i].kind||!nf_layer_snapshot_display_page(layer_queue[i].snapshot,packet.page))return 0;
  uint64_t info[8]={android_packet_epoch,packet.serial,packet.end_refresh,packet.page,generation,android_packet_audit_version,refresh,layer_queue[i].kind};
  memcpy(out,info,sizeof(info));return 1;
 }return 0;
}

size_t nf_android_observer_owned_packet(uint64_t epoch,unsigned serial,void*out,size_t capacity){
 if(!c||epoch!=nf_native_scene_epoch())return 0;
 const uint8_t*data[2]={android_previous,android_packet};size_t sizes[2]={android_previous_bytes,android_packet_bytes};
 uint64_t epochs[2]={android_previous_epoch,android_packet_epoch};
 for(unsigned i=0;i<2;i++){NFScenePacket packet;if(!data[i]||epochs[i]!=epoch||!nf_scene_packet_view(data[i],sizes[i],&packet)||packet.serial!=serial)continue;
  if(!out)return sizes[i];if(capacity<sizes[i])return 0;memcpy(out,data[i],sizes[i]);return sizes[i];
 }return 0;
}
int nf_android_observer_split(unsigned refresh,uint64_t out[12]){
 if(!c||!android_layers||!out||!android_previous||!android_packet||!android_previous_version||android_previous_version!=android_packet_audit_version||android_packet_audit_version!=nf_page_write_audit_version()||android_previous_epoch!=android_packet_epoch||android_packet_epoch!=nf_native_scene_epoch())return 0;
 NFScenePacket older,newer;
 if(!nf_scene_packet_view(android_previous,android_previous_bytes,&older)||!nf_scene_packet_view(android_packet,android_packet_bytes,&newer)||older.page==newer.page||older.end_refresh>=newer.end_refresh||refresh!=newer.end_refresh)return 0;
 for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==android_packet_epoch&&layer_queue[i].refresh==refresh){
  if(!layer_queue[i].kind)return 0;unsigned cut=0;
  for(unsigned y=0;y<160;y++){
   unsigned display=layer_queue[i].display_control[y],page=(display>>4)&1;
   if((display&7)!=4||(display&0x8080)||layer_queue[i].generation_version[y]!=android_packet_audit_version)return 0;
   if(page==newer.page){if(!cut){if(!y)return 0;cut=y;}if(layer_queue[i].generation[y][page]!=android_packet_generation)return 0;}
   else if(cut||page!=older.page||layer_queue[i].generation[y][page]!=android_previous_generation)return 0;
  }
  if(!cut)return 0;
  uint64_t info[12]={android_packet_epoch,older.serial,newer.serial,older.end_refresh,newer.end_refresh,older.page,newer.page,android_previous_generation,android_packet_generation,android_packet_audit_version,refresh,cut};
  memcpy(out,info,sizeof(info));return 1;
 }return 0;
}

/* Test both retained owners independently. Exactly one complete page owner
   must match; publication time alone never selects an owner. */
int nf_android_observer_display_owner(unsigned refresh,uint64_t out[8]){
 if(!c||!android_layers||!out)return 0;
 const uint8_t*data[2]={android_previous,android_packet};size_t sizes[2]={android_previous_bytes,android_packet_bytes};
 uint64_t epochs[2]={android_previous_epoch,android_packet_epoch},generations[2]={android_previous_generation,android_packet_generation},versions[2]={android_previous_version,android_packet_audit_version};
 uint64_t candidate[8];unsigned matches=0;
 for(unsigned owner=0;owner<2;owner++){
  NFScenePacket packet;uint64_t generation;
  if(!data[owner]||epochs[owner]!=nf_native_scene_epoch()||!versions[owner]||versions[owner]!=nf_page_write_audit_version()||!nf_scene_packet_view(data[owner],sizes[owner],&packet)||refresh<packet.end_refresh)continue;
  if(!nf_layer_queue_page_generation(epochs[owner],refresh,packet.page,&generation)||generation!=generations[owner])continue;
  for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==epochs[owner]&&layer_queue[i].refresh==refresh){
   if(layer_queue[i].kind&&nf_layer_snapshot_display_page(layer_queue[i].snapshot,packet.page)){
    uint64_t info[8]={epochs[owner],packet.serial,packet.end_refresh,packet.page,generation,versions[owner],refresh,layer_queue[i].kind};memcpy(candidate,info,sizeof(info));matches++;
   }break;
  }
 }
 if(matches!=1)return 0;memcpy(out,candidate,sizeof(candidate));return 1;
}

/* Copied diagnostic provenance, never current-memory reconstruction. */
size_t nf_android_observer_provenance(uint64_t epoch,unsigned refresh,void*out,size_t capacity){
 if(!c||!android_layers||epoch!=nf_native_scene_epoch())return 0;
 for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==epoch&&layer_queue[i].refresh==refresh){
  const size_t bytes=664*sizeof(uint64_t);if(!out)return bytes;if(capacity<bytes)return 0;
  uint64_t words[664]={epoch,refresh,layer_queue[i].mode,layer_queue[i].frontend,layer_queue[i].kind,nf_page_write_audit_version(),160,1};
  const uint8_t*data[2]={android_previous,android_packet};size_t sizes[2]={android_previous_bytes,android_packet_bytes};
  uint64_t epochs[2]={android_previous_epoch,android_packet_epoch},generations[2]={android_previous_generation,android_packet_generation},versions[2]={android_previous_version,android_packet_audit_version};
  for(unsigned owner=0;owner<2;owner++){NFScenePacket packet;if(data[owner]&&epochs[owner]==epoch&&nf_scene_packet_view(data[owner],sizes[owner],&packet)){
   uint64_t meta[8]={epochs[owner],packet.serial,packet.begin_refresh,packet.end_refresh,packet.page,generations[owner],versions[owner],1};memcpy(words+8+owner*8,meta,sizeof(meta));
  }}
  for(unsigned y=0;y<160;y++){unsigned offset=24+y*4;words[offset]=layer_queue[i].display_control[y];words[offset+1]=layer_queue[i].generation[y][0];words[offset+2]=layer_queue[i].generation[y][1];words[offset+3]=layer_queue[i].generation_version[y];}
  memcpy(out,words,bytes);return bytes;
 }return 0;
}

extern size_t nf_android_layer_pack(const NFLayerSnapshot*,void*,size_t);
/* Owner-thread atomic assembly; all four sections are caller-owned copies. */
static size_t android_bundle_owned(uint64_t epoch,unsigned refresh,uint8_t**owned){
 *owned=NULL;
 if(!c||!android_layers||epoch!=nf_native_scene_epoch())return 0;
 uint64_t whole[8],split[12];unsigned kind,count,cut=0,serials[2];
 if(nf_android_observer_display_owner(refresh,whole)){kind=1;count=1;serials[0]=(unsigned)whole[1];}
 else if(nf_android_observer_split(refresh,split)){kind=2;count=2;cut=(unsigned)split[11];serials[0]=(unsigned)split[1];serials[1]=(unsigned)split[2];}
 else return 0;
 const NFLayerSnapshot*layers=NULL;for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==epoch&&layer_queue[i].refresh==refresh){layers=layer_queue[i].snapshot;break;}
 size_t sizes[4]={nf_android_observer_owned_packet(epoch,serials[0],NULL,0),count==2?nf_android_observer_owned_packet(epoch,serials[1],NULL,0):0,nf_android_layer_pack(layers,NULL,0),nf_android_observer_provenance(epoch,refresh,NULL,0)};
 if(!sizes[0]||(count==2&&!sizes[1])||!sizes[2]||sizes[3]!=5312)return 0;
 uint64_t header[16]={0x3142414e,1,128,epoch,refresh,kind,cut,count};size_t total=128;
 for(unsigned i=0;i<4;i++){if(sizes[i]>64*1024*1024-total)return 0;header[8+i*2]=total;header[9+i*2]=sizes[i];total+=sizes[i];}header[2]=total;
 
 /* Build privately so a downstream validation failure cannot partially write. */
 uint8_t*copy=malloc(total);if(!copy)return 0;memcpy(copy,header,128);int ok=1;
 for(unsigned i=0;i<count;i++)if(nf_android_observer_owned_packet(epoch,serials[i],copy+header[8+i*2],sizes[i])!=sizes[i])ok=0;
 if(nf_android_layer_pack(layers,copy+header[12],sizes[2])!=sizes[2]||nf_android_observer_provenance(epoch,refresh,copy+header[14],sizes[3])!=sizes[3])ok=0;
 if(!ok){free(copy);return 0;}*owned=copy;return total;
}
size_t nf_android_observer_bundle(uint64_t epoch,unsigned refresh,void*out,size_t capacity){
 uint8_t*packet=NULL;size_t bytes=android_bundle_owned(epoch,refresh,&packet);if(!bytes)return 0;
 if(out&&capacity<bytes){free(packet);return 0;}if(out)memcpy(out,packet,bytes);free(packet);return bytes;
}

/* Source-regenerated exact endpoints, independent of original raster packets.
   Enable only on the core owner thread; immutable ROM assets copied once. */
int nf_android_observer_source_world_enable(int enabled){
 if(!c)return 0;if(!enabled){nf_android_geometry_cache_reset(0);if(android_source_world)nf_live_source_world_capture_disable();android_source_world=0;return 1;}
 if(android_source_world)return 1;
 struct GBA*gba=c->board;if(!nf_live_source_world_capture_enable(gba->memory.rom,gba->memory.romSize,64u*1024u*1024u))return 0;
 android_source_world=1;return 1;
}
size_t nf_android_observer_source_world(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void*out,size_t capacity){
 if(!c||!android_source_world||epoch!=nf_native_scene_epoch()||begin>end)return 0;
 void*packet=NULL;size_t bytes=0;unsigned stage;
 if(!nf_live_completed_native_multimodel_world_classified_owned(epoch,serial,begin,end,&packet,&bytes,&stage))return 0;
 if(out&&capacity<bytes){nf_scene_packet_free(packet);return 0;}
 if(out)memcpy(out,packet,bytes);nf_scene_packet_free(packet);return bytes;
}

/* Opt-in original wall capture: bounded source store, two immutable exact owners.
   This is one component of complete assets, not permission to publish a live frame. */
static unsigned android_wall_enabled,android_wall_failed,android_wall_owns_plan;
static unsigned android_wall_old_copy,android_wall_old_sky_only;
static uint64_t android_road_ordinal;static void*android_road_store;static void*android_write_ownership;static void*android_wall_store;static uint64_t android_wall_epoch,android_wall_ordinal;
static struct {uint64_t epoch;unsigned serial,begin,end,page;size_t bytes,road_bytes;uint8_t*data,*proof,*road;} android_wall_owners[2];
static void android_wall_clear(void){nf_road_history_destroy(android_road_store);android_road_store=NULL;android_road_ordinal=0;nf_write_ownership_destroy(android_write_ownership);android_write_ownership=NULL;nf_wall_history_destroy(android_wall_store);android_wall_store=NULL;for(unsigned i=0;i<2;i++)free(android_wall_owners[i].data);memset(android_wall_owners,0,sizeof(android_wall_owners));android_wall_epoch=android_wall_ordinal=0;android_wall_failed=0;}
static int android_wall_event(uint64_t epoch,unsigned refresh,const NFSceneEvent*event){
 if(!android_wall_enabled||android_wall_failed)return 0;if(epoch!=android_wall_epoch)android_wall_boundary(1);
 if(android_wall_failed||!android_wall_store||!android_write_ownership||!nf_write_ownership_apply(android_write_ownership,epoch,refresh,event)||(event->kind==2&&!nf_wall_history_append(android_wall_store,epoch,++android_wall_ordinal,refresh,event))){android_wall_failed=1;return 0;}
 if(event->kind==1){for(unsigned i=0;i<event->count;i++){NFSceneEvent run=*event;run.count=1;run.commands=event->commands+i*17;if(!nf_road_history_append(android_road_store,epoch,++android_road_ordinal,refresh,&run)){android_wall_failed=1;return 0;}}}return 1;
}
static void android_wall_boundary(int force){
 if(!android_wall_enabled||(!force&&android_wall_epoch==nf_native_scene_epoch()))return;
 android_wall_clear();android_wall_epoch=nf_native_scene_epoch();
 /* Loaded state/mode changes must not leave an old shadow framebuffer as seed. */
 if(!nf_native_model_plan_trace("",live_scene.reciprocals,sizeof(live_scene.reciprocals))||!nf_native_original_wall_spans(1)){android_wall_failed=1;return;}
 android_wall_store=nf_wall_history_create(android_wall_epoch,8u*1024u*1024u);android_write_ownership=nf_write_ownership_create(android_wall_epoch);android_road_store=nf_road_history_create(android_wall_epoch,8u*1024u*1024u);if(!android_wall_store||!android_write_ownership||!android_road_store)android_wall_failed=1;
}
int nf_android_observer_wall_history_enable(int enabled){
 if(!c)return 0;
 if(!enabled){native_source_event_sink=NULL;android_wall_enabled=0;android_wall_clear();if(android_wall_owns_plan){nf_world_trace(NULL);nf_native_model_plan_trace(NULL,NULL,0);indexed_copy_capture_enabled=android_wall_old_copy;indexed_sky_only_capture=android_wall_old_sky_only;}android_wall_owns_plan=0;return 1;}
 if(android_wall_enabled)return !android_wall_failed&&!native_original_wall_failed;
 if(native_plan_enabled||native_background_capture_only||!live_scene.assembly)return 0;
 android_wall_old_copy=indexed_copy_capture_enabled;android_wall_old_sky_only=indexed_sky_only_capture;android_wall_enabled=android_wall_owns_plan=1;android_wall_boundary(1);
 if(android_wall_failed||!nf_world_trace("")){nf_android_observer_wall_history_enable(0);return 0;}
 indexed_sky_only_capture=0;indexed_copy_capture_enabled=1;native_source_event_sink=android_wall_event;return 1;
}
static void android_wall_close_owner(uint64_t epoch,const NFScenePacket*packet){
 if(!android_wall_enabled||android_wall_failed||epoch!=android_wall_epoch||native_original_wall_failed)return;
 size_t bytes=nf_wall_history_snapshot(android_wall_store,epoch,NULL,0);if(!bytes)return;
 size_t road_bytes=nf_road_history_snapshot(android_road_store,epoch,NULL,0);if(road_bytes>64u*1024u*1024u-bytes-192080){android_wall_failed=1;return;}
 uint8_t*copy=malloc(bytes+192080+road_bytes);if(!copy||nf_wall_history_snapshot(android_wall_store,epoch,copy,bytes)!=bytes){free(copy);android_wall_failed=1;return;}
 uint64_t proof_header[10]={0x3150524e,1,192080,epoch,packet->serial,packet->begin_refresh,packet->end_refresh,(uint64_t)packet->end_refresh+1,packet->page,38400};memcpy(copy+bytes,proof_header,80);if(nf_write_ownership_page(android_write_ownership,epoch,packet->page,copy+bytes+80,192000)!=192000){free(copy);android_wall_failed=1;return;}
 if(road_bytes&&nf_road_history_snapshot(android_road_store,epoch,copy+bytes+192080,road_bytes)!=road_bytes){free(copy);android_wall_failed=1;return;}
 free(android_wall_owners[0].data);android_wall_owners[0]=android_wall_owners[1];memset(&android_wall_owners[1],0,sizeof(android_wall_owners[1]));android_wall_owners[1].epoch=epoch;android_wall_owners[1].serial=packet->serial;android_wall_owners[1].begin=packet->begin_refresh;android_wall_owners[1].end=packet->end_refresh;android_wall_owners[1].page=packet->page;android_wall_owners[1].bytes=bytes;android_wall_owners[1].data=copy;android_wall_owners[1].proof=copy+bytes;android_wall_owners[1].road=copy+bytes+192080;android_wall_owners[1].road_bytes=road_bytes;
}
size_t nf_android_observer_wall_history(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void*out,size_t capacity){
 if(!c||!android_wall_enabled||android_wall_failed||native_original_wall_failed||epoch!=android_wall_epoch||epoch!=nf_native_scene_epoch())return 0;
 for(unsigned i=0;i<2;i++)if(android_wall_owners[i].data&&android_wall_owners[i].epoch==epoch&&android_wall_owners[i].serial==serial&&android_wall_owners[i].begin==begin&&android_wall_owners[i].end==end){size_t bytes=android_wall_owners[i].bytes;if(out&&capacity<bytes)return 0;if(out)memcpy(out,android_wall_owners[i].data,bytes);return bytes;}return 0;
}
int nf_android_observer_wall_stats(uint64_t out[8]){if(!c||!out)return 0;memset(out,0,64);out[0]=android_wall_enabled;out[1]=android_wall_failed||native_original_wall_failed;out[2]=android_wall_epoch;out[3]=android_wall_ordinal;if(android_wall_store){uint64_t stats[5];if(!nf_wall_history_stats(android_wall_store,stats))return 0;out[4]=stats[0];out[5]=stats[1];out[6]=stats[2];uint64_t road_stats[5]={0};nf_road_history_stats(android_road_store,road_stats);out[7]=stats[4]+road_stats[4]+android_wall_owners[0].road_bytes+android_wall_owners[1].road_bytes+nf_write_ownership_size()+android_wall_owners[0].bytes+android_wall_owners[1].bytes+(android_wall_owners[0].data?192080:0)+(android_wall_owners[1].data?192080:0);}return 1;}


size_t nf_android_observer_write_ownership(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void*out,size_t capacity){if(!nf_android_observer_wall_history(epoch,serial,begin,end,NULL,0)||(out&&capacity<192080))return 0;for(unsigned i=0;i<2;i++)if(android_wall_owners[i].epoch==epoch&&android_wall_owners[i].serial==serial&&android_wall_owners[i].begin==begin&&android_wall_owners[i].end==end){if(out)memcpy(out,android_wall_owners[i].proof,192080);return 192080;}return 0;}

size_t nf_android_observer_road_history(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void*out,size_t capacity){if(!nf_android_observer_wall_history(epoch,serial,begin,end,NULL,0))return 0;for(unsigned i=0;i<2;i++)if(android_wall_owners[i].epoch==epoch&&android_wall_owners[i].serial==serial&&android_wall_owners[i].begin==begin&&android_wall_owners[i].end==end){size_t bytes=android_wall_owners[i].road_bytes;if(out&&capacity<bytes)return 0;if(out&&bytes)memcpy(out,android_wall_owners[i].road,bytes);return bytes;}return 0;}

static int android_sky_enabled;
int nf_android_observer_sky_enable(int enabled){if(!c)return 0;if(android_sky_enabled==(enabled!=0))return 1;if(!nf_live_sky_capture_enable(enabled))return 0;android_sky_enabled=enabled!=0;if(android_wall_enabled||android_source_world){indexed_copy_capture_enabled=1;indexed_sky_only_capture=0;}return 1;}
size_t nf_android_observer_sky(uint64_t epoch,unsigned serial,void*out,size_t capacity){
 if(!c||!android_sky_enabled||epoch!=nf_native_scene_epoch())return 0;size_t bytes=0;
 if(!nf_live_completed_sky_read(epoch,serial,0,NULL,0,&bytes)||bytes!=15192||(out&&capacity<bytes))return 0;
 if(!out)return bytes;uint8_t copy[15192];size_t written=0;if(!nf_live_completed_sky_read(epoch,serial,0,copy,sizeof(copy),&written)||written!=bytes||epoch!=nf_native_scene_epoch())return 0;memcpy(out,copy,bytes);return bytes;
}
/* NSB1 embeds the original NAB1 plus one verified NFSK/full ROM asset per owner. */
static size_t android_sky_scene_owned(uint64_t epoch,unsigned refresh,uint8_t**owned){
 *owned=NULL;
 if(!android_sky_enabled)return 0;uint8_t*scene=NULL;size_t scene_bytes=android_bundle_owned(epoch,refresh,&scene);if(!scene_bytes)return 0;
 uint64_t owner[16];memcpy(owner,scene,128);unsigned count=(unsigned)owner[7];if(count<1||count>2){free(scene);return 0;}size_t bytes=128+scene_bytes+count*30568;
 uint8_t*copy=malloc(bytes);if(!copy){free(scene);return 0;}uint64_t header[16]={0x3142534e,1,bytes,epoch,refresh,owner[5],owner[6],count,128,scene_bytes};memcpy(copy+128,scene,scene_bytes);int ok=1;
 for(unsigned i=0;i<count;i++){
  NFScenePacket packet;if(!nf_scene_packet_view(scene+owner[8+i*2],(size_t)owner[9+i*2],&packet)){ok=0;break;}size_t at=128+scene_bytes+i*30568;header[10+i*2]=at;header[11+i*2]=30568;
  if(nf_android_observer_sky(epoch,packet.serial,copy+at,15192)!=15192){ok=0;break;}uint32_t sky[14];memcpy(sky,copy+at,56);uint64_t captured=(uint64_t)sky[2]|((uint64_t)sky[3]<<32);
  if(captured!=epoch||sky[4]<packet.begin_refresh||sky[4]>packet.end_refresh||sky[10]!=0x06002940+packet.page*0xa000||sky[12]||sky[8]<sky[9]||sky[8]-sky[9]>238||sky[9]<0x08000000||sky[9]>0x0a000000-15376||!native_surface_read(NULL,sky[9],copy+at+15192,15376)||memcmp(copy+at+56,copy+at+15192+sky[8]-sky[9],15136)){ok=0;break;}
 }
 if(ok&&epoch==nf_native_scene_epoch()){memcpy(copy,header,128);*owned=copy;}else{free(copy);ok=0;}free(scene);return ok?bytes:0;
}
size_t nf_android_observer_sky_scene(uint64_t epoch,unsigned refresh,void*out,size_t capacity){
 uint8_t*packet=NULL;size_t bytes=android_sky_scene_owned(epoch,refresh,&packet);if(!bytes)return 0;
 if(out&&capacity<bytes){free(packet);return 0;}if(out)memcpy(out,packet,bytes);free(packet);return bytes;
}

/* NRB1 normal initial SOURCE background. Requires normal source replay and exact
   closed owner; never samples current hardware framebuffer to fill unknown cells. */
static size_t android_background_scene_owned(uint64_t epoch,unsigned refresh,uint8_t**owned){
 *owned=NULL;
 if(!c||!android_wall_enabled||android_wall_failed||native_original_wall_failed||epoch!=android_wall_epoch||epoch!=nf_native_scene_epoch())return 0;
 uint8_t*sky=NULL;size_t sn=android_sky_scene_owned(epoch,refresh,&sky);if(!sn)return 0;if(sn>64u*1024u*1024u-128-2*76880){free(sky);return 0;}
 uint64_t sh[16],nh[16];memcpy(sh,sky,128);memcpy(nh,sky+sh[8],128);unsigned count=(unsigned)sh[7];size_t bytes=128+sn+count*76880;
 if(count<1||count>2){free(sky);return 0;}uint8_t*copy=malloc(bytes);if(!copy){free(sky);return 0;}uint64_t header[16]={0x3142524e,1,bytes,epoch,refresh,sh[5],sh[6],count,128,sn};memcpy(copy+128,sky,sn);int ok=1;
 for(unsigned i=0;i<count;i++){
  NFScenePacket p;if(!nf_scene_packet_view(sky+sh[8]+nh[8+i*2],(size_t)nh[9+i*2],&p)||!nf_android_observer_wall_history(epoch,p.serial,p.begin_refresh,p.end_refresh,NULL,0)||p.end_refresh==UINT32_MAX){ok=0;break;}
  unsigned closed=p.end_refresh+1,slot=closed%16,base=p.page*0xa000;size_t at=128+sn+i*76880;header[10+i*2]=at;header[11+i*2]=76880;
  if(!native_background_frames[slot].valid||native_background_frames[slot].refresh!=closed){ok=0;break;}
  uint64_t bg[10]={0x3147424e,1,76880,epoch,p.serial,p.begin_refresh,p.end_refresh,closed,p.page,38400};memcpy(copy+at,bg,80);unsigned any=0;
  for(unsigned cell=0;cell<38400;cell++){uint8_t mask=native_background_frames[slot].coverage[base+cell];if(mask>1){ok=0;break;}any|=mask;copy[at+80+cell]=native_background_frames[slot].vram[base+cell];copy[at+38480+cell]=mask;}
  if(!ok||!any){ok=0;break;}
  size_t sky_at=(size_t)sh[10+i*2];for(unsigned cell=10560;cell<25696;cell++)if(!copy[at+38480+cell]||copy[at+80+cell]!=sky[sky_at+56+cell-10560]){ok=0;break;}if(!ok)break;
 }
 if(ok&&epoch==nf_native_scene_epoch()){memcpy(copy,header,128);*owned=copy;}else{free(copy);ok=0;}free(sky);return ok?bytes:0;
}
size_t nf_android_observer_background_scene(uint64_t epoch,unsigned refresh,void*out,size_t capacity){
 uint8_t*packet=NULL;size_t bytes=android_background_scene_owned(epoch,refresh,&packet);if(!bytes)return 0;
 if(out&&capacity<bytes){free(packet);return 0;}if(out)memcpy(out,packet,bytes);free(packet);return bytes;
}

#define nf_android_observer_source_world_take nf_android_observer_source_world_take_uncached
#include "source_transfer_observer.inc"
#undef nf_android_observer_source_world_take
#include "geometry_cache_observer.inc"

#include "scene_rejection_observer.inc"

#include "model_context_diag_observer.inc"

int nf_android_traffic_rotation_stats(uint64_t out[6]){if(!c||!out)return 0;memcpy(out,nf_traffic_stats,48);return 1;}

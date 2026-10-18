#include <mgba/core/core.h>
#include <mgba/internal/arm/arm.h>
#include <mgba/internal/gba/gba.h>
#include <mgba/internal/arm/isa-inlines.h>
#include "../outputs/nfsug-research/native_span.h"
#include "v2/scene.h"
#include <mgba-util/vfs.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define API __declspec(dllexport)
static struct mCore* c;
static uint32_t pixels[240*160];
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
static unsigned debug_pc,debug_count,debug_regs[256][16],watch_base,watch_end;
static FILE* calls_file;
static void thumbTrace(struct ARMCore* cpu){
 unsigned pc=cpu->gprs[15]-2,op=cpu->prefetch[0];
 if(calls_file&&pc>=0x08000000&&pc<0x08078000&&(op&0xf800)==0xf000){
  unsigned second=c->busRead16(c,pc+2);if((second&0xf800)!=0xf800)return;
  int32_t offset=((op&0x7ff)<<12)|((second&0x7ff)<<1);if(offset&0x400000)offset|=0xff800000;
  unsigned target=pc+4+offset;
  if(pc<0x08002000||target<0x08020000)fprintf(calls_file,"%u,%08x,%08x,%08x,%08x,%08x,%08x\n",c->frameCounter(c),pc,target,cpu->gprs[0],cpu->gprs[1],cpu->gprs[2],cpu->gprs[3]);
 }
}
API void nf_calls(const char* path){if(calls_file)fclose(calls_file);calls_file=path?fopen(path,"w"):NULL;nfsThumbTrace=calls_file?thumbTrace:NULL;if(calls_file)fprintf(calls_file,"frame,caller,target,r0,r1,r2,r3\n");}
API void nf_debug(unsigned pc){debug_pc=pc;debug_count=0;}
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
API void nf_scene_reset(void){scene_page=-1;scene_count[0]=scene_count[1]=0;scene_dirty[0]=scene_dirty[1]=0;}
API void nf_scene_enable(int e){scene_enabled=e;nf_scene_reset();nfsArmHook=(e||native_enabled||hookfile||poly_file)?onArm:0;}
API const NFPoly* nf_scene(int* n){int page=(rd16(0x04000000)>>4)&1;*n=scene_race_active()?scene_count[page]:0;return scene_polys[page];}
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
API int nf_texture(const NFPoly* p,uint32_t* out){
 if(!validmem(p->address,p->stride*p->height)||p->width>1024||p->height>1024)return 0;
 uint32_t pal[256];for(int i=0;i<256;i++)pal[i]=rgb(rd16(0x05000000+i*2));
 for(unsigned y=0;y<p->height;y++)for(unsigned x=0;x<p->width;x++){unsigned idx=c->busRead8(c,p->address+y*p->stride+x);if(p->kind==3&&idx==0)out[y*p->width+x]=0;else{if(p->shade)idx=c->busRead8(c,p->shade+idx*16);out[y*p->width+x]=pal[idx];}}
 return 1;
}
API void nf_overlay(uint32_t* out){
 uint32_t pal[256];for(int i=0;i<256;i++)pal[i]=rgb(rd16(0x05000000+i*2));
 unsigned base=0x06000000+((rd16(0x04000000)&16)?0xa000:0);
 for(unsigned i=0;i<240*160;i++){unsigned bg=pal[c->busRead8(c,base+i)];out[i]=((pixels[i]&0xffffff)==(bg&0xffffff))?0:(pixels[i]|0xff000000);}
}
API void nf_polygons(const char* path){if(poly_file)fclose(poly_file);poly_file=path?fopen(path,"wb"):NULL;nfsArmHook=(scene_enabled||poly_file||hookfile||native_enabled)?onArm:0;}
static bool onArm(struct ARMCore* cpu){
 unsigned pc=cpu->gprs[15]-4;
 if(pc==debug_pc&&debug_count<256)memcpy(debug_regs[debug_count++],cpu->gprs,sizeof(debug_regs[0]));
 if(scene_enabled)scene_capture(cpu,pc);
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
static void store8(struct ARMCore* cpu,uint32_t a,int8_t v,int* cycles){
 unsigned pc=cpu->gprs[15]-(cpu->cpsr.t?4:8);
 if(watch_end?(a>=watch_base&&a<watch_end):((a>>24)==6)){if(pc>=0x08000000&&pc<0x08800000)hist[(pc-0x08000000)/4]++;if(pc>=0x03000000&&pc<0x03008000)ihist[(pc-0x03000000)/4]++;}
 old8(cpu,a,v,cycles);
}
static uint32_t storeMultiple(struct ARMCore* cpu,uint32_t a,int mask,enum LSMDirection dir,int* cycles){
 unsigned pc=cpu->gprs[15]-(cpu->cpsr.t?4:8);
 if(watch_end?(a>=watch_base&&a<watch_end):((a>>24)==6)){if(pc>=0x08000000&&pc<0x08800000)hist[(pc-0x08000000)/4]++;if(pc>=0x03000000&&pc<0x03008000)ihist[(pc-0x03000000)/4]++;}
 return oldMultiple(cpu,a,mask,dir,cycles);
}
static void store32(struct ARMCore* cpu,uint32_t a,int32_t v,int* cycles){
 unsigned pc=cpu->gprs[15]-(cpu->cpsr.t?4:8);
 if(watch_end?(a>=watch_base&&a<watch_end):((a>>24)==6)){if(pc>=0x08000000&&pc<0x08800000)hist[(pc-0x08000000)/4]++;if(pc>=0x03000000&&pc<0x03008000)ihist[(pc-0x03000000)/4]++;}
 old32(cpu,a,v,cycles);
}
static void store16(struct ARMCore* cpu,uint32_t a,int16_t v,int* cycles){
 if(scene_enabled && a==0x04000000 && ((rd16(a)^(uint16_t)v)&16)){int page=((uint16_t)v>>4)&1;if(!scene_dirty[page])scene_count[page]=0;scene_dirty[page]=0;}
 unsigned pc=cpu->gprs[15]-(cpu->cpsr.t?4:8);
 if(a==0x04000000 && trace_file){fprintf(trace_file,"%u,%08x,%08x,%04x\n",c->frameCounter(c),pc,cpu->gprs[14],(uint16_t)v);fflush(trace_file);flips++;}
 if(watch_end?(a>=watch_base&&a<watch_end):((a>>24)==6)){stores++; if(pc>=0x08000000 && pc<0x08800000)hist[(pc-0x08000000)/4]++; if(pc>=0x03000000 && pc<0x03008000)ihist[(pc-0x03000000)/4]++;}
 old16(cpu,a,v,cycles);
}
API int nf_init(const char* rom,const char* trace_fileile){
 mLogSetDefaultLogger(&logger);
 c=mCoreFind(rom);if(!c || !c->init(c))return 0;
 mCoreInitConfig(c,"nfsug-research");c->opts.useBios=false;c->opts.skipBios=true;
 c->setVideoBuffer(c,pixels,240);c->setAudioBufferSize(c,4096);
 if(!mCoreLoadFile(c,rom))return 0;
 uint32_t crc=0;c->checksum(c,&crc,mCHECKSUM_CRC32);
 if(crc!=0x828020e9){mCoreConfigDeinit(&c->config);c->deinit(c);c=NULL;return 0;}
 c->reset(c);struct ARMCore* cpu=c->cpu;old16=cpu->memory.store16;cpu->memory.store16=store16;
 old32=cpu->memory.store32;cpu->memory.store32=store32;
 old8=cpu->memory.store8;cpu->memory.store8=store8;
 oldMultiple=cpu->memory.storeMultiple;cpu->memory.storeMultiple=storeMultiple;
 if(trace_fileile && *trace_fileile){trace_file=fopen(trace_fileile,"w");if(trace_file)fprintf(trace_file,"vblank,pc,lr,dispcnt\n");}return 1;
}
API void nf_frame(unsigned keys){
 if(scene_enabled&&!scene_race_active())nf_scene_reset();
 c->setKeys(c,keys);c->runFrame(c);
 if(scene_enabled&&!scene_race_active())nf_scene_reset();
}
API void* nf_pixels(void){return pixels;}
API unsigned nf_read(unsigned a,int width){return width==4?c->busRead32(c,a):width==2?c->busRead16(c,a):c->busRead8(c,a);}
API void nf_write(unsigned a,unsigned v,int width){if(width==4)c->busWrite32(c,a,v);else if(width==2)c->busWrite16(c,a,v);else c->busWrite8(c,a,v);}
API unsigned nf_reg(int n){return ((struct ARMCore*)c->cpu)->gprs[n];}
API unsigned nf_cpsr(void){return ((struct ARMCore*)c->cpu)->cpsr.packed;}
API void nf_step(void){c->step(c);}
API int nf_state(const char* path,int save){size_t n=c->stateSize(c);void* b=malloc(n);if(!b)return 0;FILE* f=fopen(path,save?"wb":"rb");if(!f){free(b);return 0;}int ok;if(save){ok=c->saveState(c,b);ok=ok && fwrite(b,1,n,f)==n;}else{ok=fread(b,1,n,f)==n;ok=ok && c->loadState(c,b);if(ok)nf_scene_reset();}fclose(f);free(b);return ok;}
API void nf_dump(const char* path,unsigned a,unsigned n){FILE*f=fopen(path,"wb");if(!f)return;for(unsigned i=0;i<n;i++)fputc(c->busRead8(c,a+i),f);fclose(f);}
API void nf_hist(const char* path){FILE*f=fopen(path,"w");if(!f)return;fprintf(f,"pc,vram_halfword_stores\n");for(unsigned i=0;i<0x200000;i++)if(hist[i])fprintf(f,"%08x,%u\n",0x08000000+i*4,hist[i]);for(unsigned i=0;i<0x2000;i++)if(ihist[i])fprintf(f,"%08x,%u\n",0x03000000+i*4,ihist[i]);fclose(f);}
API void nf_close(void){
 nfsArmHook=NULL;native_enabled=0;
 nfsThumbTrace=NULL;if(calls_file)fclose(calls_file);calls_file=NULL;
 if(trace_file)fclose(trace_file);trace_file=NULL;
 if(hookfile)fclose(hookfile);hookfile=NULL;
 if(cycle_file)fclose(cycle_file);cycle_file=NULL;
 if(poly_file)fclose(poly_file);poly_file=NULL;
 if(dma_file)fclose(dma_file);dma_file=NULL;
 if(c){mCoreConfigDeinit(&c->config);c->deinit(c);c=NULL;}
}


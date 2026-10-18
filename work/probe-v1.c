#include <mgba/core/core.h>
#include <mgba/internal/arm/arm.h>
#include <mgba/internal/gba/gba.h>
#include <mgba/internal/arm/isa-inlines.h>
#include "../outputs/nfsug-research/native_span.h"
#include <mgba-util/vfs.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define API __declspec(dllexport)
static struct mCore* c;
static uint32_t pixels[240*160];
static void (*old16)(struct ARMCore*,uint32_t,int16_t,int*);
static unsigned hist[0x200000], ihist[0x8000];
static unsigned stores, flips;
static FILE* trace_file;
static void quiet(struct mLogger* l,int cat,enum mLogLevel level,const char* fmt,va_list args){(void)l;(void)cat;if(level==mLOG_FATAL||level==mLOG_ERROR)vfprintf(stderr,fmt,args);}
static struct mLogger logger={quiet,0};
extern bool (*nfsArmHook)(struct ARMCore*);
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
API void nf_polygons(const char* path){if(poly_file)fclose(poly_file);poly_file=path?fopen(path,"wb"):NULL;nfsArmHook=(poly_file||hookfile||native_enabled)?onArm:0;}
static bool onArm(struct ARMCore* cpu){
 unsigned pc=cpu->gprs[15]-4;
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
 if(hookfile && (pc==0x30056d8 || pc==0x3005920) && hooked++<20000){
  uint32_t data[35];data[0]=c->frameCounter(c);data[1]=pc;memcpy(data+2,cpu->gprs,16*4);
  for(int i=0;i<17;i++)data[18+i]=c->busRead32(c,cpu->gprs[0]+i*4);
  fwrite(data,4,35,hookfile);
 }
 if(native_enabled && pc==0x30056d8)return nativeSpan(cpu);
 return false;
}
API void nf_native(int enabled){native_enabled=enabled;nfsArmHook=(enabled||hookfile)?onArm:0;}
API unsigned nf_native_calls(void){return native_calls;}
API unsigned nf_native_rejected(void){return native_rejected;}
API void nf_capture(const char* path){if(hookfile)fclose(hookfile);if(cycle_file)fclose(cycle_file);hookfile=path?fopen(path,"wb"):0;cycle_file=path?fopen("work/span-cycles.csv","w"):0;if(cycle_file)fprintf(cycle_file,"count,double,cycles\n");hooked=0;nfsArmHook=(hookfile||native_enabled)?onArm:0;}
API struct mCore* nf_core(void){return c;}
static void store16(struct ARMCore* cpu,uint32_t a,int16_t v,int* cycles){
 unsigned pc=cpu->gprs[15]-(cpu->cpsr.t?4:8);
 if(a==0x04000000 && trace_file){fprintf(trace_file,"%u,%08x,%08x,%04x\n",c->frameCounter(c),pc,cpu->gprs[14],(uint16_t)v);fflush(trace_file);flips++;}
 if((a>>24)==6){stores++; if(pc>=0x08000000 && pc<0x08800000)hist[(pc-0x08000000)/4]++; if(pc>=0x03000000 && pc<0x03008000)ihist[(pc-0x03000000)/4]++;}
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
 if(trace_fileile && *trace_fileile){trace_file=fopen(trace_fileile,"w");if(trace_file)fprintf(trace_file,"vblank,pc,lr,dispcnt\n");}return 1;
}
API void nf_frame(unsigned keys){c->setKeys(c,keys);c->runFrame(c);}
API void* nf_pixels(void){return pixels;}
API unsigned nf_read(unsigned a,int width){return width==4?c->busRead32(c,a):width==2?c->busRead16(c,a):c->busRead8(c,a);}
API void nf_write(unsigned a,unsigned v,int width){if(width==4)c->busWrite32(c,a,v);else if(width==2)c->busWrite16(c,a,v);else c->busWrite8(c,a,v);}
API unsigned nf_reg(int n){return ((struct ARMCore*)c->cpu)->gprs[n];}
API unsigned nf_cpsr(void){return ((struct ARMCore*)c->cpu)->cpsr.packed;}
API void nf_step(void){c->step(c);}
API int nf_state(const char* path,int save){size_t n=c->stateSize(c);void* b=malloc(n);FILE* f=fopen(path,save?"wb":"rb");if(!f){free(b);return 0;}int ok;if(save){ok=c->saveState(c,b);ok=ok && fwrite(b,1,n,f)==n;}else{ok=fread(b,1,n,f)==n;ok=ok && c->loadState(c,b);}fclose(f);free(b);return ok;}
API void nf_dump(const char* path,unsigned a,unsigned n){FILE*f=fopen(path,"wb");if(!f)return;for(unsigned i=0;i<n;i++)fputc(c->busRead8(c,a+i),f);fclose(f);}
API void nf_hist(const char* path){FILE*f=fopen(path,"w");if(!f)return;fprintf(f,"pc,vram_halfword_stores\n");for(unsigned i=0;i<0x200000;i++)if(hist[i])fprintf(f,"%08x,%u\n",0x08000000+i*4,hist[i]);for(unsigned i=0;i<0x2000;i++)if(ihist[i])fprintf(f,"%08x,%u\n",0x03000000+i*4,ihist[i]);fclose(f);}
API void nf_close(void){
 nfsArmHook=NULL;native_enabled=0;
 if(trace_file)fclose(trace_file);trace_file=NULL;
 if(hookfile)fclose(hookfile);hookfile=NULL;
 if(cycle_file)fclose(cycle_file);cycle_file=NULL;
 if(poly_file)fclose(poly_file);poly_file=NULL;
 if(c){mCoreConfigDeinit(&c->config);c->deinit(c);c=NULL;}
}


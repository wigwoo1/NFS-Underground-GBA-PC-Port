#include "nfsug_android_core.h"
#include <mgba/core/core.h>
#include <mgba/core/blip_buf.h>
#include <mgba/core/config.h>
#include <mgba/core/log.h>
#include <mgba/internal/gba/input.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct NFAAndroidCore {struct mCore*core;uint32_t pixels[240*160];uint64_t steps;int paused;};
_Static_assert(sizeof(color_t)==4,"This boundary requires the 32-bit core framebuffer.");
_Static_assert(NFA_KEY_A==(1u<<GBA_KEY_A)&&NFA_KEY_B==(1u<<GBA_KEY_B)&&
 NFA_KEY_SELECT==(1u<<GBA_KEY_SELECT)&&NFA_KEY_START==(1u<<GBA_KEY_START)&&
 NFA_KEY_RIGHT==(1u<<GBA_KEY_RIGHT)&&NFA_KEY_LEFT==(1u<<GBA_KEY_LEFT)&&
 NFA_KEY_UP==(1u<<GBA_KEY_UP)&&NFA_KEY_DOWN==(1u<<GBA_KEY_DOWN)&&GBA_KEY_MAX==10,
 "Touch bits must match the actual core key enum.");
static void nfa_log(struct mLogger*logger,int category,enum mLogLevel level,const char*fmt,va_list args){
 (void)logger;(void)category;
 if(level==mLOG_ERROR||level==mLOG_FATAL){vfprintf(stderr,fmt,args);fputc(10,stderr);}
}
static struct mLogger nfa_logger={nfa_log,0};
static NFAAndroidCore*active_core;
extern unsigned nfsCpuSpeed;
static int valid(NFAAndroidCore*s){return s&&s==active_core&&s->core;}
NFAAndroidCore*nfa_core_open(const char*path){
 if(active_core||!path||!*path)return NULL;
 mLogSetDefaultLogger(&nfa_logger);
 NFAAndroidCore*s=calloc(1,sizeof(*s));if(!s)return NULL;
 struct mCore*c=mCoreFind(path);
 if(!c){free(s);return NULL;}
 if(!c->init(c)){free(c);free(s);return NULL;}
 mCoreInitConfig(c,"nfsug-android-core");
 c->opts.useBios=false;c->opts.skipBios=true;
 c->setVideoBuffer(c,(color_t*)s->pixels,240);c->setAudioBufferSize(c,4096);
 if(!mCoreLoadFile(c,path)){mCoreConfigDeinit(&c->config);c->deinit(c);free(s);return NULL;}
 uint32_t crc=0;c->checksum(c,&crc,mCHECKSUM_CRC32);
 if(crc!=0x828020e9u){mCoreConfigDeinit(&c->config);c->deinit(c);free(s);return NULL;}
 nfsCpuSpeed=1;c->reset(c);
 blip_set_rates(c->getAudioChannel(c,0),c->frequency(c),44100);
 blip_set_rates(c->getAudioChannel(c,1),c->frequency(c),44100);
 s->core=c;active_core=s;return s;
}
void nfa_core_close(NFAAndroidCore*s){
 if(!valid(s))return;
 struct mCore*c=s->core;active_core=NULL;
 mCoreConfigDeinit(&c->config);c->deinit(c);memset(s,0,sizeof(*s));free(s);
}
int nfa_core_step(NFAAndroidCore*s,uint32_t keys){
 if(!valid(s)||(keys&~1023u))return NFA_STEP_ERROR;
 if(s->paused)return NFA_STEP_PAUSED;
 struct mCore*c=s->core;uint32_t before=c->frameCounter(c);
 c->setKeys(c,keys);c->runFrame(c);
 if((uint32_t)(c->frameCounter(c)-before)!=1u)return NFA_STEP_ERROR;
 s->steps++;return NFA_STEP_OK;
}
int nfa_core_pause(NFAAndroidCore*s,int paused){
 if(!valid(s))return 0;s->paused=paused!=0;s->core->setKeys(s->core,0);
 blip_clear(s->core->getAudioChannel(s->core,0));blip_clear(s->core->getAudioChannel(s->core,1));return 1;
}
int nfa_core_timing(NFAAndroidCore*s,uint64_t out[4]){
 if(!valid(s)||!out)return 0;
 uint64_t data[4]={(uint64_t)s->core->frequency(s->core),(uint64_t)s->core->frameCycles(s->core),s->core->frameCounter(s->core),s->steps};
 memcpy(out,data,sizeof(data));return 1;
}
const uint32_t*nfa_core_pixels(NFAAndroidCore*s){return valid(s)?s->pixels:NULL;}
size_t nfa_core_state_size(NFAAndroidCore*s){return valid(s)?s->core->stateSize(s->core):0;}
int nfa_core_load_state(NFAAndroidCore*s,const void*data,size_t bytes){
 if(!valid(s)||!data||bytes!=s->core->stateSize(s->core))return 0;
 if(!s->core->loadState(s->core,data))return 0;
 s->core->setKeys(s->core,0);s->steps=0;
 blip_clear(s->core->getAudioChannel(s->core,0));blip_clear(s->core->getAudioChannel(s->core,1));return 1;
}
int nfa_core_save_state(NFAAndroidCore*s,void*out,size_t bytes){
 if(!valid(s)||!out||bytes<s->core->stateSize(s->core))return 0;
 return s->core->saveState(s->core,out);
}
size_t nfa_core_read_audio(NFAAndroidCore*s,int16_t*out,size_t capacity){
 if(!valid(s)||s->paused||!out||!capacity||capacity>4096)return 0;
 struct blip_t*l=s->core->getAudioChannel(s->core,0),*r=s->core->getAudioChannel(s->core,1);
 int left=blip_samples_avail(l),right=blip_samples_avail(r);
 int count=left<right?left:right;if(count>(int)capacity)count=(int)capacity;if(count<=0)return 0;
 blip_read_samples(l,out,count,1);blip_read_samples(r,out+1,count,1);return (size_t)count;
}
void nfa_touch_clear(NFATouch*t){if(t)memset(t,0,sizeof(*t));}
int nfa_touch_set(NFATouch*t,int32_t id,uint32_t mask){
 if(!t||id<0||(mask&~255u))return 0;
 unsigned slot=NFA_TOUCH_CAPACITY;
 for(unsigned i=0;i<NFA_TOUCH_CAPACITY;i++)if((t->used&(1u<<i))&&t->ids[i]==id){slot=i;break;}
 if(!mask){if(slot<NFA_TOUCH_CAPACITY){t->used&=~(1u<<slot);t->ids[slot]=0;t->masks[slot]=0;}return 1;}
 if(slot==NFA_TOUCH_CAPACITY)for(unsigned i=0;i<NFA_TOUCH_CAPACITY;i++)if(!(t->used&(1u<<i))){slot=i;break;}
 if(slot==NFA_TOUCH_CAPACITY)return 0;
 t->ids[slot]=id;t->masks[slot]=mask;t->used|=1u<<slot;return 1;
}
uint32_t nfa_touch_keys(const NFATouch*t){
 if(!t)return 0;uint32_t keys=0;
 for(unsigned i=0;i<NFA_TOUCH_CAPACITY;i++)if(t->used&(1u<<i))keys|=t->masks[i]&255u;
 if((keys&(NFA_KEY_RIGHT|NFA_KEY_LEFT))==(NFA_KEY_RIGHT|NFA_KEY_LEFT))keys&=~(NFA_KEY_RIGHT|NFA_KEY_LEFT);
 if((keys&(NFA_KEY_UP|NFA_KEY_DOWN))==(NFA_KEY_UP|NFA_KEY_DOWN))keys&=~(NFA_KEY_UP|NFA_KEY_DOWN);
 return keys;
}

size_t nfa_core_battery_size(NFAAndroidCore*s){
 if(!valid(s))return 0;
 void*data=NULL;size_t bytes=s->core->savedataClone(s->core,&data);
 free(data);return bytes;
}
size_t nfa_core_copy_battery(NFAAndroidCore*s,void*out,size_t capacity){
 if(!valid(s)||!out)return 0;
 void*data=NULL;size_t bytes=s->core->savedataClone(s->core,&data);
 if(!data||!bytes||bytes>capacity){free(data);return 0;}
 memcpy(out,data,bytes);free(data);return bytes;
}
int nfa_core_load_battery(NFAAndroidCore*s,const void*data,size_t bytes){
 if(!valid(s)||!data)return 0;
 if(bytes!=512&&bytes!=8192&&bytes!=32768&&bytes!=65536&&bytes!=131072)return 0;
 size_t current=nfa_core_battery_size(s);
 if(current&&current!=bytes)return 0;
 return s->core->savedataRestore(s->core,data,bytes,false);
}

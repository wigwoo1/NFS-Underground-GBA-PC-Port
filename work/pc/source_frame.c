#include "source_frame.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#endif
static uint64_t thread_id(void){
#ifdef _WIN32
 return GetCurrentThreadId();
#else
 static _Thread_local unsigned char token;return (uintptr_t)&token;
#endif
}
int nf_pc_source_api_bind_owner(NFPCSourceAPI*a){if(!a||a->size!=sizeof(*a)||!a->core||a->owner_thread)return 0;a->owner_thread=thread_id();return 1;}
#define LIMIT ((size_t)64*1024*1024)
typedef struct {unsigned char *p;size_t n;} Blob;
typedef struct {uint64_t serial,begin,end,page;Blob part[4],timing;NFPCOwnedRelease geometry_release;} Owner;
struct NFPCSourceFrame {uint64_t epoch,refresh,kind,cut,count;size_t used,limit;NFPCOwnedRelease background_release;Blob background;Owner owners[2];};
static uint32_t u32(const void*p,size_t at){uint32_t v;memcpy(&v,(const unsigned char*)p+at,4);return v;}
static uint64_t u64(const void*p,size_t at){uint64_t v;memcpy(&v,(const unsigned char*)p+at,8);return v;}
static int root(Blob b,uint64_t magic,const NFPCSourceFrame*f){return b.n>=128&&u64(b.p,0)==magic&&u64(b.p,8)==1&&u64(b.p,16)==b.n&&u64(b.p,24)==f->epoch&&u64(b.p,32)==f->refresh&&u64(b.p,40)==f->kind&&u64(b.p,48)==f->cut&&u64(b.p,56)==f->count;}
static int part(Blob b,unsigned index,Blob*out){if(b.n<128||index>3)return 0;uint64_t at=u64(b.p,64+16*index),n=u64(b.p,72+16*index);if(at>b.n||n>b.n-at)return 0;out->p=b.p+(size_t)at;out->n=(size_t)n;return 1;}
static int layout(Blob b,unsigned parts,int empty_second){size_t end=128;for(unsigned i=0;i<parts;i++){Blob v;if(!part(b,i,&v)||u64(b.p,64+16*i)!=end||(!v.n&&!(empty_second&&i==1)))return 0;end+=v.n;}if(end!=b.n)return 0;for(unsigned i=parts;i<4;i++)if(u64(b.p,64+16*i)||u64(b.p,72+16*i))return 0;return 1;}
static int packet(Blob b,Owner*out){if(b.n<92||u32(b.p,0)!=0x3150534e||u32(b.p,4)<1||u32(b.p,4)>2||u32(b.p,8)!=b.n||u32(b.p,12)!=5)return 0;out->serial=u32(b.p,16);out->begin=u32(b.p,20);out->end=u32(b.p,24);out->page=u32(b.p,28);if(out->end<out->begin||out->page>1)return 0;size_t end=92;for(unsigned i=0;i<5;i++){size_t at=u32(b.p,36+12*i),n=u32(b.p,40+12*i);if(u32(b.p,32+12*i)!=i+1||at<end||at>b.n||n>b.n-at)return 0;end=at+n;}return end==b.n;}
static int same(const Owner*a,const Owner*b){return a->serial==b->serial&&a->begin==b->begin&&a->end==b->end&&a->page==b->page;}
static int allocate(NFPCSourceFrame*f,Blob*b,size_t n){if(!n||n>f->limit-f->used)return 0;b->p=malloc(n);if(!b->p)return 0;b->n=n;f->used+=n;return 1;}
static int copy_owner(const NFPCSourceAPI*a,NFPCSourceFrame*f,Owner*o,NFPCOwnerRead read,unsigned part_index){Blob*b=&o->part[part_index];size_t n=read(a->core,f->epoch,(unsigned)o->serial,(unsigned)o->begin,(unsigned)o->end,NULL,0);return allocate(f,b,n)&&read(a->core,f->epoch,(unsigned)o->serial,(unsigned)o->begin,(unsigned)o->end,b->p,n)==n;}
static int history(Blob b,uint64_t magic,uint64_t epoch){
 if(b.n<64||u64(b.p,0)!=magic||u64(b.p,8)!=1||u64(b.p,16)!=b.n||u64(b.p,24)!=epoch||!u64(b.p,32)||u64(b.p,32)>1024||!u64(b.p,40)||u64(b.p,40)>65536||u64(b.p,48)||u64(b.p,56))return 0;
 size_t at=64;uint64_t assets=0,events=0,ordinal=0,refresh=0,payload=0,address_table[1024];unsigned category[1024];int road=magic==0x3148524e;
 while(at<b.n){if(b.n-at<64)return 0;const unsigned char*p=b.p+at;uint64_t tag=u64(p,0),n=u64(p,8);if(n<64||n>b.n-at)return 0;
  if(tag==1){uint64_t bytes=u64(p,40),address=u64(p,32),kind=u64(p,24);if(u64(p,16)!=assets+1||assets>=1024||!bytes||bytes>0x1000000||address>0x0a000000-bytes||n!=64+bytes||u64(p,48)||u64(p,56))return 0;
   if(road?(kind!=1||address<0x08000000):((kind!=1&&kind!=2)||address<0x02000000||bytes!=(kind==1?65536:4081)||(kind==1&&address<0x08000000)))return 0;
   payload+=bytes;if(payload>32u*1024*1024)return 0;address_table[assets]=address;category[assets++]=(unsigned)kind;
  }else{size_t expected=road?164:176;if(tag!=2||n!=expected)return 0;uint64_t texture=u64(p,32),shade=u64(p,40),shift=u64(p,64);if(tag!=2||n!=expected||u64(p,16)<=ordinal||u64(p,24)<refresh||u64(p,24)>UINT32_MAX||!texture||texture>assets||shade>assets||u64(p,56)!=1||shift>(road?15:1)||u64(p,72)||u64(p,80)||u64(p,88)||category[texture-1]!=1||u64(p,48)!=address_table[texture-1])return 0;
   const unsigned char*c=p+96;
   if(road){uint64_t destination=u32(c,24),width=u32(c,28),duplicate=u32(c,64);if(shade||u32(c,0)>15||u32(c,4)>INT32_MAX||u32(c,8)>INT32_MAX||width>512||duplicate>1||destination<0x06000000||destination+width*2+duplicate*240>0x06014000)return 0;}
   else{if(u32(c,36)!=address_table[texture-1]||u32(c,76)>320||u32(c,12)>10||u32(c,16)<1||u32(c,16)>1024)return 0;if(shift){uint32_t address=u32(c,20)+(int16_t)(u32(c,40)>>16);if(!shade||category[shade-1]!=2||address!=address_table[shade-1])return 0;}else if(shade)return 0;}
   ordinal=u64(p,16);refresh=u64(p,24);events++;
  }at+=(size_t)n;
 }return at==b.n&&assets==u64(b.p,32)&&events==u64(b.p,40);
}
static int proof(Blob b,NFPCSourceFrame*f,Owner*o){if(b.n!=192080||u64(b.p,0)!=0x3150524e||u64(b.p,8)!=1||u64(b.p,16)!=b.n||u64(b.p,24)!=f->epoch||u64(b.p,32)!=o->serial||u64(b.p,40)!=o->begin||u64(b.p,48)!=o->end||u64(b.p,56)!=o->end+1||u64(b.p,64)!=o->page||u64(b.p,72)!=38400)return 0;for(size_t i=0;i<38400;i++){unsigned kind=b.p[80+i];uint32_t refresh=u32(b.p,38480+i*4);if(kind>6||(kind==0?refresh!=0:refresh>o->end))return 0;}return 1;}
static int auxiliary(NFPCSourceFrame*f,Blob nab){Blob layer,p;if(!part(nab,2,&layer)||!part(nab,3,&p)||layer.n<28512||p.n!=5312)return 0;uint32_t pages=u32(layer.p,16);if(u32(layer.p,0)!=0x31504c4e||u32(layer.p,4)!=1||u32(layer.p,8)!=layer.n||u32(layer.p,12)!=160||!pages||pages>4000||u32(layer.p,20)!=25||u32(layer.p,24)!=4096||u32(layer.p,28)!=f->refresh||layer.n!=28512+(size_t)pages*4096)return 0;if(u64(p.p,0)!=f->epoch||u64(p.p,8)!=f->refresh||!u64(p.p,32)||!u64(p.p,40)||u64(p.p,48)!=160||u64(p.p,56)!=1)return 0;
 for(unsigned y=0;y<160;y++){if(u32(layer.p,32+y*128)!=f->refresh||u32(layer.p,36+y*128)!=y)return 0;for(unsigned z=0;z<25;z++){uint16_t ref;memcpy(&ref,layer.p+20512+(y*25+z)*2,2);if(ref>=pages)return 0;}}
 if(f->count==1){unsigned matches=0;uint64_t selected=0;for(unsigned j=0;j<2;j++){size_t at=(8+j*8)*8;uint64_t page=u64(p.p,at+32);if(u64(p.p,at+56)!=1||u64(p.p,at)!=f->epoch||u64(p.p,at+48)!=u64(p.p,40)||u64(p.p,at+24)>f->refresh||page>1)continue;int match=1;for(unsigned y=0;y<160;y++){size_t row=(24+y*4)*8;uint64_t control=u64(p.p,row);if((control&7)!=4||(control&128)||((control>>4)&1)!=page||u64(p.p,row+8+page*8)!=u64(p.p,at+40)||u64(p.p,row+24)!=u64(p.p,40)){match=0;break;}}if(match){matches++;selected=u64(p.p,at+8);}}if(matches!=1||selected!=f->owners[0].serial)return 0;}
 for(unsigned i=0;i<f->count;i++){Owner*o=&f->owners[i];int found=-1;for(unsigned j=0;j<2;j++){size_t at=(8+j*8)*8;if(u64(p.p,at+56)==1&&u64(p.p,at)==f->epoch&&u64(p.p,at+8)==o->serial){if(found>=0)return 0;found=(int)at;}}if(found<0||u64(p.p,found+16)!=o->begin||u64(p.p,found+24)!=o->end||u64(p.p,found+32)!=o->page||u64(p.p,found+48)!=u64(p.p,40)||o->end>f->refresh)return 0;unsigned top=i?f->cut:0,bottom=f->count==1||i?160:f->cut;for(unsigned y=top;y<bottom;y++){size_t at=(24+y*4)*8;uint64_t control=u64(p.p,at);uint16_t row;memcpy(&row,layer.p+40+y*128,2);if((control&7)!=4||(control&(f->count==2?0x8080:0x80))||((control>>4)&1)!=o->page||u64(p.p,at+8+o->page*8)!=u64(p.p,found+40)||u64(p.p,at+24)!=u64(p.p,40)||control!=row)return 0;}}
 return 1;}
static int background(NFPCSourceFrame*f){Blob nrb=f->background,nsb,nab;if(!root(nrb,0x3142524e,f)||!layout(nrb,1+(unsigned)f->count,0)||!part(nrb,0,&nsb)||!root(nsb,0x3142534e,f)||!layout(nsb,1+(unsigned)f->count,0)||!part(nsb,0,&nab)||!root(nab,0x3142414e,f)||!layout(nab,4,f->count==1))return 0;for(unsigned i=0;i<f->count;i++){Blob g,b,s;Owner*o=&f->owners[i];if(!part(nab,i,&g)||!packet(g,o)||!part(nrb,i+1,&b)||b.n!=76880||!part(nsb,i+1,&s)||s.n!=30568)return 0;if(u64(b.p,0)!=0x3147424e||u64(b.p,8)!=1||u64(b.p,16)!=b.n||u64(b.p,24)!=f->epoch||u64(b.p,32)!=o->serial||u64(b.p,40)!=o->begin||u64(b.p,48)!=o->end||u64(b.p,56)!=o->end+1||u64(b.p,64)!=o->page||u64(b.p,72)!=38400)return 0;int any=0;for(size_t z=38480;z<b.n;z++){if(b.p[z]>1)return 0;any|=b.p[z];}if(!any)return 0;if(u32(s.p,0)!=0x4b53464e||u32(s.p,4)!=1||u64(s.p,8)!=f->epoch||u32(s.p,16)<o->begin||u32(s.p,16)>o->end||u32(s.p,24)!=240||u32(s.p,28)!=64||u32(s.p,40)!=0x06002940+o->page*0xa000||u32(s.p,44)!=15136||u32(s.p,48)||u32(s.p,52))return 0;uint32_t origin=u32(s.p,36),source=u32(s.p,32),offset=((((u32(s.p,20)&16383)*240)>>12)%240)&~1u;if(origin<0x08000000||origin>0x0a000000-15376||source!=origin+offset||offset>238||memcmp(s.p+56,s.p+15192+offset,15136))return 0;for(unsigned z=0;z<15136;z++)if(b.p[38480+10560+z]!=1||b.p[80+10560+z]!=s.p[56+z])return 0;}
 if(f->count==2&&(f->owners[0].serial>=f->owners[1].serial||f->owners[0].end>=f->owners[1].end||f->owners[1].end!=f->refresh||f->owners[0].page==f->owners[1].page))return 0;
 return auxiliary(f,nab);}
static int take_geometry(const NFPCSourceAPI*a,NFPCSourceFrame*f,Owner*o,NFPCOwnerTake take,NFPCOwnedRelease release){
 void*owned=NULL;size_t n=take(a->core,f->epoch,(unsigned)o->serial,(unsigned)o->begin,(unsigned)o->end,&owned);
 if(!n||!owned||n>f->limit-f->used){if(owned)release(owned);return 0;}
 o->part[0].p=owned;o->part[0].n=n;o->geometry_release=release;f->used+=n;return 1;
}
static int timing_camera_packet(const unsigned char*p,size_t n,const unsigned char*camera){return n>=160&&u32(p,0)==0x324d464e&&!memcmp(p+48,camera,56);}
static int timing_binding(const NFPCSourceFrame*f,const Owner*o){
 const unsigned char*p=o->timing.p;uint64_t w[16];memcpy(w,p,128);
 if(w[0]!=f->epoch||w[1]!=o->serial||w[2]!=o->begin||w[3]!=o->end||w[12]!=o->page||w[13]>1||w[4]<o->begin||w[4]>w[5]||w[5]>o->end||w[7]<o->begin||w[7]>w[6]||w[6]>o->end||w[8]<o->begin||w[8]>w[9]||w[9]>o->end||!w[10]||w[10]>16||!w[11]||w[11]>256||w[14]>w[15])return 0;
 for(unsigned i=0;i<7;i++){double v;memcpy(&v,p+128+i*8,8);if(!isfinite(v))return 0;}
 const unsigned char*packet=o->part[0].p;size_t at=u32(packet,36),n=u32(packet,40);const unsigned char*m=packet+at;
 if(n<8)return 0;
 if(u32(m,0)==0x324d464e)return timing_camera_packet(m,n,p+128);
 unsigned count=u32(m,4);if(u32(m,0)!=0x314c4d4e||count<2||count>16||n<8+count*8)return 0;
 size_t end=8+count*8;
 for(unsigned i=0;i<count;i++){size_t a=u32(m,8+i*8),length=u32(m,12+i*8);if(a%8||a<end||a>n||length>n-a||!timing_camera_packet(m+a,length,p+128))return 0;end=a+length;}
 return end==n;
}
static NFPCSourceFrame* capture(const NFPCSourceAPI*a,size_t maximum,NFPCBackgroundTake take,NFPCOwnedRelease release,NFPCOwnerTake geometry_take,NFPCOwnedRelease geometry_release,NFPCOwnerRead timing_read){if(!a||a->size!=sizeof(*a)||a->owner_thread!=thread_id()||!a->core||!a->layer_info||!a->background||!a->geometry||!a->road||!a->wall||!a->proof||maximum<sizeof(NFPCSourceFrame)||maximum>LIMIT)return NULL;uint64_t info[5];if(!a->layer_info(a->core,info)||!info[0]||info[1]>UINT32_MAX)return NULL;NFPCSourceFrame*f=calloc(1,sizeof(*f));if(!f)return NULL;f->epoch=info[0];f->refresh=info[1];f->used=sizeof(*f);f->limit=maximum;size_t n;
 if(take){void*owned=NULL;n=take(a->core,f->epoch,(unsigned)f->refresh,&owned);
  if(!n||!owned||n>f->limit-f->used){if(owned)release(owned);goto fail;}
  f->background.p=owned;f->background.n=n;f->background_release=release;f->used+=n;
 }else{n=a->background(a->core,f->epoch,(unsigned)f->refresh,NULL,0);if(!allocate(f,&f->background,n)||a->background(a->core,f->epoch,(unsigned)f->refresh,f->background.p,n)!=n)goto fail;}if(n<128)goto fail;f->kind=u64(f->background.p,40);f->cut=u64(f->background.p,48);f->count=u64(f->background.p,56);if(!((f->kind==1&&!f->cut&&f->count==1)||(f->kind==2&&f->cut>0&&f->cut<160&&f->count==2))||!background(f))goto fail;for(unsigned i=0;i<f->count;i++){Owner*o=&f->owners[i],source={0};if(!(geometry_take?take_geometry(a,f,o,geometry_take,geometry_release):copy_owner(a,f,o,a->geometry,0))||!packet(o->part[0],&source)||!same(o,&source)||!copy_owner(a,f,o,a->road,1)||!history(o->part[1],0x3148524e,f->epoch)||!copy_owner(a,f,o,a->wall,2)||!history(o->part[2],0x3148574e,f->epoch)||!copy_owner(a,f,o,a->proof,3)||!proof(o->part[3],f,o))goto fail;if(timing_read){size_t tn=timing_read(a->core,f->epoch,(unsigned)o->serial,(unsigned)o->begin,(unsigned)o->end,NULL,0);if(tn!=184||!allocate(f,&o->timing,tn)||timing_read(a->core,f->epoch,(unsigned)o->serial,(unsigned)o->begin,(unsigned)o->end,o->timing.p,tn)!=tn||!timing_binding(f,o))goto fail;}}if(timing_read){uint64_t after[5];if(!a->layer_info(a->core,after)||memcmp(info,after,sizeof(info)))goto fail;}return f;
fail:nf_pc_source_frame_free(f);return NULL;}
NFPCSourceFrame* nf_pc_source_frame_capture(const NFPCSourceAPI*a,size_t maximum){return capture(a,maximum,NULL,NULL,NULL,NULL,NULL);}
NFPCSourceFrame* nf_pc_source_frame_capture_take_background(const NFPCSourceAPI*a,size_t maximum,NFPCBackgroundTake take,NFPCOwnedRelease release){if(!take||!release)return NULL;return capture(a,maximum,take,release,NULL,NULL,NULL);}
NFPCSourceFrame* nf_pc_source_frame_capture_take_sources(const NFPCSourceAPI*a,size_t maximum,NFPCBackgroundTake take,NFPCOwnedRelease release,NFPCOwnerTake geometry_take,NFPCOwnedRelease geometry_release){if(!take||!release||!geometry_take||!geometry_release)return NULL;return capture(a,maximum,take,release,geometry_take,geometry_release,NULL);}
NFPCSourceFrame* nf_pc_source_frame_capture_timed(const NFPCSourceAPI*a,size_t maximum,NFPCOwnerRead timing){return timing?capture(a,maximum,NULL,NULL,NULL,NULL,timing):NULL;}
NFPCSourceFrame* nf_pc_source_frame_capture_take_sources_timed(const NFPCSourceAPI*a,size_t maximum,NFPCBackgroundTake take,NFPCOwnedRelease release,NFPCOwnerTake geometry_take,NFPCOwnedRelease geometry_release,NFPCOwnerRead timing){return take&&release&&geometry_take&&geometry_release&&timing?capture(a,maximum,take,release,geometry_take,geometry_release,timing):NULL;}
void nf_pc_source_frame_free(NFPCSourceFrame*f){if(!f)return;for(unsigned i=0;i<2;i++)free(f->owners[i].timing.p);if(f->background_release)f->background_release(f->background.p);else free(f->background.p);for(unsigned i=0;i<2;i++)for(unsigned j=0;j<4;j++){if(j==0&&f->owners[i].geometry_release)f->owners[i].geometry_release(f->owners[i].part[j].p);else free(f->owners[i].part[j].p);}free(f);}
int nf_pc_source_frame_info(const NFPCSourceFrame*f,uint64_t out[8]){if(!f||!out)return 0;uint64_t v[8]={f->epoch,f->refresh,f->kind,f->cut,f->count,f->used,f->owners[0].serial,f->count==2?f->owners[1].serial:0};memcpy(out,v,sizeof(v));return 1;}
int nf_pc_source_frame_owner(const NFPCSourceFrame*f,unsigned owner,uint64_t out[5]){if(!f||owner>=f->count||!out)return 0;const Owner*o=&f->owners[owner];uint64_t v[5]={f->epoch,o->serial,o->begin,o->end,o->page};memcpy(out,v,sizeof(v));return 1;}
int nf_pc_source_frame_component(const NFPCSourceFrame*f,unsigned owner,unsigned kind,const void**p,size_t*n){if(!f||!p||!n||kind>4||owner>=f->count||(kind==0&&owner!=0))return 0;Blob b=kind?f->owners[owner].part[kind-1]:f->background;*p=b.p;*n=b.n;return 1;}


int nf_pc_source_frame_pose_timing(const NFPCSourceFrame*f,unsigned owner,const void**p,size_t*n){if(!f||owner>=f->count||!f->owners[owner].timing.p||!p||!n)return 0;*p=f->owners[owner].timing.p;*n=f->owners[owner].timing.n;return 1;}

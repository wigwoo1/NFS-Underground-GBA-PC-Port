#include "source_world.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
typedef struct{const unsigned char*p;size_t n;} View;
typedef struct{View raw,metadata,lighting,identity;unsigned mode,lit,clip[4],order;} Surface;
struct NFPCWorld{unsigned char*packet;size_t used;unsigned n,models;Surface surfaces[128];View sections[5],reciprocal,bounds;};
static uint32_t u32(const void*p,size_t at){uint32_t v;memcpy(&v,(const unsigned char*)p+at,4);return v;}
static int32_t i32(const void*p,size_t at){int32_t v;memcpy(&v,(const unsigned char*)p+at,4);return v;}
static uint16_t u16(const void*p,size_t at){uint16_t v;memcpy(&v,(const unsigned char*)p+at,2);return v;}
static double d64(const void*p,size_t at){double v;memcpy(&v,(const unsigned char*)p+at,8);return v;}
static int take(View b,size_t*at,size_t n,View*out){if(*at>b.n||n>b.n-*at)return 0;out->p=b.p+*at;out->n=n;*at+=n;return 1;}
static int metadata(Surface*s){const unsigned char*p=s->metadata.p;unsigned c=u32(s->raw.p,0),w=u32(s->raw.p,4),h=u32(s->raw.p,8),mode=s->mode,planes=mode==3||mode==8?17:1;size_t pixels=(size_t)w*h;
 if(mode==5||mode==6||mode==9||mode==10){size_t extra=mode>=9?56:0,at=pixels+extra;const unsigned char*a=p+at;if(extra&&(u32(p,pixels)!=1||u32(p,pixels+4)%4||(uint64_t)u32(p,pixels+4)+48>0x100000000ULL))return 0;
 if(u32(a,0)!=c||u32(a,4)>10||(1u<<u32(a,4))!=w||u32(a,8)!=h*2||u32(a,12)!=(unsigned)(mode==6||mode==10)||!u32(a,16)||u32(a,16)%4||!u32(a,20)||u32(a,20)%2)return 0;
int32_t u=i32(a,24),v=i32(a,28);if(u< -32768||u>32767||v< -32768||v>32767)return 0;
 for(unsigned i=0;i<32;i++){int32_t x=i32(a,32+i*8),y=i32(a,36+i*8);if(i>=c){if(x||y)return 0;}else{double eu=x/16384.0+u/(256.0*w),ev=y/16384.0+v/(512.0*h);if(fabs(d64(s->raw.p,12+c*24+i*16)-eu)>1e-10||fabs(d64(s->raw.p,20+c*24+i*16)-ev)>1e-10)return 0;}}}
 if(mode==2||mode==3||mode==7||mode==8){size_t bytes=pixels*planes;for(size_t i=0;i<bytes;i++){unsigned state=p[i];if(state>2||((mode==7||mode==8)&&((state==2)!=(p[bytes+i]!=0))))return 0;}for(size_t i=0;i<pixels;i++){if(p[i]==1)return 0;for(unsigned level=1;level<planes;level++)if((p[i]==0)!=(p[level*pixels+i]==0))return 0;}}
 return 1;}
NFPCWorld* nf_pc_world_decode(const void*data,size_t n,size_t maximum){if(!data||n<92||n>64u*1024*1024||maximum>64u*1024*1024||maximum<sizeof(NFPCWorld)||n>maximum-sizeof(NFPCWorld))return NULL;const unsigned char*p=data;
 if(u32(p,0)!=0x3150534e||(u32(p,4)!=1&&u32(p,4)!=2)||u32(p,8)!=n||u32(p,12)!=5||u32(p,24)<u32(p,20)||u32(p,28)>1)return NULL;
 size_t end=92;for(unsigned i=0;i<5;i++){size_t at=u32(p,36+i*12),size=u32(p,40+i*12);if(u32(p,32+i*12)!=i+1||at<end||at>n||size>n-at)return NULL;end=at+size;}if(end!=n)return NULL;
 NFPCWorld*w=calloc(1,sizeof(*w));if(!w)return NULL;w->packet=malloc(n);if(!w->packet){free(w);return NULL;}memcpy(w->packet,data,n);w->used=sizeof(*w)+n;for(unsigned i=0;i<5;i++){w->sections[i].p=w->packet+u32(p,36+i*12);w->sections[i].n=u32(p,40+i*12);}View model=w->sections[0],world=w->sections[1],id=w->sections[4],order=w->sections[2],light=w->sections[3];
 if(model.n<8)goto fail;
if(u32(model.p,0)==0x324d464e)w->models=1;else if(u32(model.p,0)==0x314c4d4e&&u32(model.p,4)>=2&&u32(model.p,4)<=16)w->models=u32(model.p,4);else goto fail;

 if(world.n<8||u32(world.p,0)!=0x31444652||u32(world.p,4)>128)goto fail;
w->n=u32(world.p,4);size_t at=8;
 for(unsigned i=0;i<w->n;i++){if(at>world.n||world.n-at<12)goto fail;
unsigned c=u32(world.p,at),width=u32(world.p,at+4),height=u32(world.p,at+8);if(c<3||c>32||!width||width>1024||!height||height>1024)goto fail;
Surface*s=&w->surfaces[i];if(!take(world,&at,12+c*40+(size_t)width*height*4,&s->raw))goto fail;
for(unsigned j=0;j<c*5;j++)if(!isfinite(d64(s->raw.p,12+j*8)))goto fail;
s->metadata.p=world.p+at;s->clip[1]=240;s->clip[3]=160;}
 if(at!=world.n){if(world.n-at<8||u32(world.p,at)!=0x3149574e||u32(world.p,at+4)!=w->n)goto fail;
at+=8;for(unsigned i=0;i<w->n;i++){Surface*s=&w->surfaces[i];if(world.n-at<8)goto fail;
unsigned mode=u32(world.p,at);size_t bytes=u32(world.p,at+4),pixels=(size_t)u32(s->raw.p,4)*u32(s->raw.p,8);at+=8;if(mode>10)goto fail;
size_t expected=mode?pixels*(mode==3?17:mode==7?2:mode==8?34:1)+(mode==5||mode==6?288:mode==9||mode==10?344:0):0;if(bytes!=expected||!take(world,&at,bytes,&s->metadata))goto fail;
s->mode=mode;if(!metadata(s))goto fail;
}if(at!=world.n)goto fail;
}
 unsigned entries=w->n+w->models;size_t base=8+entries*20;if(id.n<base||u32(id.p,0)!=0x3149464e||u32(id.p,4)!=entries)goto fail;

 for(unsigned i=0;i<entries;i++){unsigned kind=u32(id.p,8+i*20);if(i>=w->n){if(kind!=3)goto fail;
continue;}Surface*s=&w->surfaces[i];unsigned m=s->mode;if((kind!=1&&kind!=2)||((m==2||m==3||m==7||m==8)&&kind!=2)||((m==1||m==4||m==5||m==6)&&kind!=1))goto fail;
s->identity=(View){id.p+8+i*20,20};}
 if(id.n!=base){if(id.n-base<16)goto fail;
unsigned magic=u32(id.p,base),count=u32(id.p,base+4);double alpha=d64(id.p,base+8);if(!((magic==0x3142464e&&count==w->n)||(magic==0x3242464e&&count==entries))||id.n!=base+16+count*8||!isfinite(alpha)||alpha<0||alpha>=1)goto fail;
for(unsigned i=0;i<count;i++){unsigned clip[4];for(unsigned j=0;j<4;j++)clip[j]=u16(id.p,base+16+i*8+j*2);if(clip[0]>clip[1]||clip[1]>240||clip[2]>clip[3]||clip[3]>160)goto fail;
if(i<w->n)memcpy(w->surfaces[i].clip,clip,sizeof(clip));}w->bounds=(View){id.p+base,id.n-base};}
 if(order.n!=8+entries*4||u32(order.p,0)!=0x314f464e||u32(order.p,4)!=entries)goto fail;
unsigned char seen[144]={0};for(unsigned i=0;i<entries;i++){uint32_t value=u32(order.p,8+i*4);unsigned is_model=value>=0xfffffff0u,index=is_model?UINT32_MAX-value:value;if(index>=(is_model?w->models:w->n))goto fail;
unsigned slot=index+(is_model?w->n:0);if(seen[slot])goto fail;
seen[slot]=1;if(!is_model)w->surfaces[index].order=i;}
 if(light.n<8||u32(light.p,0)!=0x314c464e||u32(light.p,4)!=w->n)goto fail;
at=8;
 for(unsigned i=0;i<w->n;i++){Surface*s=&w->surfaces[i];if(light.n-at<4)goto fail;
size_t start=at;unsigned enabled=u32(light.p,at),mode=s->mode;at+=4;if(enabled>1||((mode==2||mode==4||mode==5||mode==6||mode==7||mode==9||mode==10)&&enabled)||((mode==3||mode==8)&&!enabled))goto fail;
s->lit=enabled;
 if(enabled){if(light.n-at<16||u32(light.p,at)>15||u32(light.p,at+4)>15||u32(light.p,at+8)!=u32(s->raw.p,4)||u32(light.p,at+12)!=u32(s->raw.p,8))goto fail;
size_t bytes=16+(size_t)u32(s->raw.p,4)*u32(s->raw.p,8)*64;if(bytes>light.n-at)goto fail;
at+=bytes;}s->lighting=(View){light.p+start,at-start};}
 if(light.n-at!=32768*4)goto fail;
w->reciprocal=(View){light.p+at,32768*4};return w;
fail:nf_pc_world_free(w);return NULL;}
NFPCWorld* nf_pc_source_world(const NFPCSourceFrame*f,unsigned owner,size_t maximum){const void*p;size_t n;return nf_pc_source_frame_component(f,owner,NFPC_GEOMETRY,&p,&n)?nf_pc_world_decode(p,n,maximum):NULL;}
void nf_pc_world_free(NFPCWorld*w){if(w){free(w->packet);free(w);}}
int nf_pc_world_info(const NFPCWorld*w,uint64_t out[4]){if(!w||!out)return 0;uint64_t v[4]={w->n,w->models,w->n+w->models,w->used};memcpy(out,v,sizeof(v));return 1;}
int nf_pc_world_surface_info(const NFPCWorld*w,unsigned i,uint64_t out[12]){if(!w||i>=w->n||!out)return 0;const Surface*s=w->surfaces+i;uint64_t v[12]={u32(s->raw.p,0),u32(s->raw.p,4),u32(s->raw.p,8),u32(s->identity.p,0),s->mode,s->lit,s->mode==3||s->mode==8?17:1,s->clip[0],s->clip[1],s->clip[2],s->clip[3],s->order};memcpy(out,v,sizeof(v));return 1;}
int nf_pc_world_surface_buffer(const NFPCWorld*w,unsigned i,unsigned kind,const void**p,size_t*n){if(!w||i>=w->n||kind>9||!p||!n)return 0;const Surface*s=w->surfaces+i;size_t c=u32(s->raw.p,0),pixels=(size_t)u32(s->raw.p,4)*u32(s->raw.p,8),planes=s->mode==3||s->mode==8?17:1;View b={NULL,0};unsigned m=s->mode;
 switch(kind){case 0:b=(View){s->raw.p+12,c*24};break;case 1:b=(View){s->raw.p+12+c*24,c*16};break;case 2:b=(View){s->raw.p+12+c*40,pixels*4};break;case 3:b=s->metadata;break;case 4:b=s->lighting;break;case 5:if(m==2||m==3||m==7||m==8)b=(View){s->metadata.p,pixels*planes};break;case 6:if(m==7||m==8)b=(View){s->metadata.p+pixels*planes,pixels*planes};else if(m==1||m==4||m==5||m==6||m==9||m==10)b=(View){s->metadata.p,pixels};break;case 7:if(m==5||m==6||m==9||m==10)b=(View){s->metadata.p+s->metadata.n-288,288};break;case 8:if(m==9||m==10)b=(View){s->metadata.p+pixels,56};break;case 9:b=s->identity;break;}*p=b.p;*n=b.n;return 1;}
int nf_pc_world_buffer(const NFPCWorld*w,unsigned kind,const void**p,size_t*n){if(!w||kind>2||!p||!n)return 0;View b=kind==0?w->reciprocal:kind==1?w->bounds:w->sections[2];*p=b.p;*n=b.n;return 1;}
int nf_pc_world_command(const NFPCWorld*w,unsigned i,uint64_t out[2]){if(!w||i>=w->n+w->models||!out)return 0;uint32_t v=u32(w->sections[2].p,8+i*4);uint64_t b[2]={v>=0xfffffff0u,v>=0xfffffff0u?UINT32_MAX-v:v};memcpy(out,b,sizeof(b));return 1;}


int nf_pc_world_model(const NFPCWorld*w,unsigned index,const void**p,size_t*n){
 if(!w||index>=w->models||!p||!n)return 0;
 View b=w->sections[0];
 if(w->models>1){
  size_t end=8+w->models*8;if(b.n<end)return 0;
  for(unsigned i=0;i<w->models;i++){size_t at=u32(b.p,8+i*8),size=u32(b.p,12+i*8);if(at%8||at<end||at>b.n||size<160||size>b.n-at)return 0;end=at+size;}
  if(end!=b.n)return 0;
  size_t at=u32(b.p,8+index*8),size=u32(b.p,12+index*8);b=(View){b.p+at,size};
 }
 if(b.n<160)return 0;
 *p=b.p;*n=b.n;return 1;
}

int nf_pc_world_model_identity(const NFPCWorld*w,unsigned i,uint32_t out[5]){if(!w||i>=w->models||!out)return 0;memcpy(out,w->sections[4].p+8+(w->n+i)*20,20);return 1;}

int nf_pc_world_packet(const NFPCWorld*w,const void**p,size_t*n){if(!w||!p||!n)return 0;*p=w->packet;*n=w->used-sizeof(*w);return 1;}

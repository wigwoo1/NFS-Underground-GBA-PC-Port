/* Derived from the verified retention interpreter; preserve exact accepted
   ordinal while replaying original writes. No screen-shape association. */
#include "recipe_coverage.h"
#include <stdlib.h>
#include <string.h>
#define CELLS 38400u
#define LIMIT (64u*1024*1024)
typedef struct {const unsigned char*p;uint64_t address;size_t n;unsigned category;} Asset;
typedef struct {uint32_t asset,offset,refresh;uint64_t writer;} Sample;
struct NFPCRecipeCoverage {uint64_t info[10];unsigned char rgba[CELLS*4];uint32_t records[CELLS*4];uint64_t writers[CELLS*6];};
static uint32_t u32(const void*p,size_t at){uint32_t v;memcpy(&v,(const unsigned char*)p+at,4);return v;}
static uint64_t u64(const void*p,size_t at){uint64_t v;memcpy(&v,(const unsigned char*)p+at,8);return v;}
static void assign(Sample*s,uint64_t address,unsigned page,uint32_t asset,uint32_t offset,uint32_t refresh,uint64_t writer){uint64_t base=0x06000000u+page*0xa000u;if(address>=base&&address-base<CELLS)s[address-base]=(Sample){asset,offset,refresh,writer};}
/* All original ARM/Java integer operations below use defined unsigned wraps. */
static int road(const unsigned char*c,const Asset*a,unsigned id,uint32_t refresh,unsigned page,uint64_t writer,Sample*s){
 unsigned shift=u32(c,0),width=u32(c,28),duplicate=u32(c,64);uint32_t um=u32(c,4),vm=u32(c,8),u=u32(c,32),v=u32(c,36),du=u32(c,40),dv=u32(c,44),offsets[512];uint64_t source=u32(c,20),dest=u32(c,24);
 for(unsigned k=0;k<width;k++){u&=um;v&=vm;uint64_t address=source+2*((u>>16)+((uint64_t)(v>>16)<<shift));if(address<a->address||address-a->address+2>a->n)return 0;offsets[k]=(uint32_t)(address-a->address);u+=du;v+=dv;}
 for(unsigned d=0;d<=duplicate;d++)for(unsigned k=0;k<width;k++)for(unsigned lane=0;lane<2;lane++)assign(s,dest+k*2u+d*240u+lane,page,id,offsets[k]+lane,refresh,writer);
 return 1;
}
static int wall(const unsigned char*c,const Asset*a,unsigned id,unsigned shade,uint32_t refresh,unsigned page,uint64_t writer,Sample*s){
 unsigned shift=u32(c,12),uvshift=15;uint32_t texture=u32(c,36),step=u32(c,44),stride=u32(c,8),vertical=u32(c,72),mask=(u32(c,16)<<15)-1;
 if(u32(c,24)&&step>0x1b000u){if(shift<2)return 0;shift-=2;uvshift=17;texture+=u32(c,28);}
 texture=(texture+((u32(c,52)&u32(c,64))>>uvshift))&~1u;uint32_t dest=u32(c,68)+((stride*(u32(c,4)>>14))<<1);
 for(unsigned row=0;row<u32(c,76);row++){vertical&=mask;uint32_t address=texture+((vertical>>uvshift)<<shift);if(address<a->address||(uint64_t)address-a->address>=a->n)return 0;uint32_t offset=(uint32_t)(address-a->address),index=a->p[offset];if(index){unsigned asset=id;if(shade!=UINT32_MAX){asset=shade;offset=index*16;}for(unsigned lane=0;lane<2;lane++)assign(s,(uint32_t)((dest&~1u)+lane),page,asset,offset,refresh,writer);}dest+=stride<<1;vertical+=step;}
 return 1;
}
NFPCRecipeCoverage* nf_pc_recipe_coverage_decode(const void*history,size_t n,const void*proof,size_t pn,const uint64_t owner[5],unsigned kind,unsigned top,unsigned bottom,size_t maximum){
 if(!history||!proof||!owner||n<64||n>LIMIT||pn!=192080||maximum<sizeof(NFPCRecipeCoverage)||maximum>LIMIT||top>bottom||bottom>160||(kind!=NFPC_ROAD&&kind!=NFPC_WALL)||!owner[0]||owner[0]>INT64_MAX||owner[2]>owner[3]||owner[3]>UINT32_MAX||owner[4]>1)return NULL;
 const unsigned char*b=history,*p=proof;int isroad=kind==NFPC_ROAD;uint64_t assets=u64(b,32),events=u64(b,40);
 if(u64(b,0)!=(isroad?0x3148524e:0x3148574e)||u64(b,8)!=1||u64(b,16)!=n||u64(b,24)!=owner[0]||!assets||assets>1024||!events||events>65536||u64(b,48)||u64(b,56))return NULL;
 if(u64(p,0)!=0x3150524e||u64(p,8)!=1||u64(p,16)!=pn||u64(p,24)!=owner[0]||u64(p,32)!=owner[1]||u64(p,40)!=owner[2]||u64(p,48)!=owner[3]||u64(p,56)!=owner[3]+1||u64(p,64)!=owner[4]||u64(p,72)!=CELLS)return NULL;
 NFPCRecipeCoverage*r=calloc(1,sizeof(*r));Asset*a=calloc((size_t)assets,sizeof(*a));Sample*s=malloc(CELLS*sizeof(*s));if(!r||!a||!s)goto fail;
 for(unsigned i=0;i<CELLS;i++)s[i]=(Sample){UINT32_MAX,0,0,0};
 size_t at=64,payload=0;uint64_t ac=0,ec=0,ordinal=0,refresh=0;
 while(at<n){if(n-at<64)goto fail;const unsigned char*q=b+at;uint64_t tag=u64(q,0),bytes=u64(q,8);if(bytes<64||bytes>n-at)goto fail;
  if(tag==1){uint64_t id=u64(q,16),category=u64(q,24),address=u64(q,32),length=u64(q,40);if(ac>=assets||id!=ac+1||!length||length>0x1000000||length>0x0a000000||address>0x0a000000-length||bytes!=64+length||u64(q,48)||u64(q,56))goto fail;
   if(isroad?(category!=1||address<0x08000000):((category!=1&&category!=2)||length!=(category==1?65536:4081)||address<0x02000000||(category==1&&address<0x08000000)))goto fail;
   payload+=(size_t)length;if(payload>32u*1024*1024)goto fail;a[ac++]=(Asset){q+64,address,(size_t)length,(unsigned)category};
  }else{if(tag!=2||bytes!=(isroad?164:176)||ec>=events)goto fail;uint64_t id=u64(q,32),shade=u64(q,40),shift=u64(q,64),frame=u64(q,24),order=u64(q,16);if(order<=ordinal||order>INT64_MAX||frame<refresh||frame>UINT32_MAX||!id||id>ac||shade>ac||u64(q,56)!=1||shift>(isroad?15:1)||u64(q,72)||u64(q,80)||u64(q,88)||a[id-1].category!=1||u64(q,48)!=a[id-1].address)goto fail;
   const unsigned char*c=q+96;
   if(isroad){uint64_t dest=u32(c,24),width=u32(c,28),dup=u32(c,64);if(shade||u32(c,0)>15||u32(c,4)>INT32_MAX||u32(c,8)>INT32_MAX||width>512||dup>1||dest<0x06000000||dest+width*2+dup*240>0x06014000)goto fail;if(frame<=owner[3]&&!road(c,a+id-1,(unsigned)id-1,(uint32_t)frame,(unsigned)owner[4],order,s))goto fail;
   }else{if(u32(c,36)!=a[id-1].address||u32(c,76)>320||u32(c,12)>10||u32(c,16)<1||u32(c,16)>1024)goto fail;uint32_t high=u32(c,40)>>16,delta=high&0x8000?high|0xffff0000u:high;
    if(shift?(!shade||a[shade-1].category!=2||a[shade-1].address!=(uint32_t)(u32(c,20)+delta)):shade!=0)goto fail;
    if(frame<=owner[3]&&!wall(c,a+id-1,(unsigned)id-1,shade?(unsigned)shade-1:UINT32_MAX,(uint32_t)frame,(unsigned)owner[4],order,s))goto fail;
   }ordinal=order;refresh=frame;ec++;
  }at+=(size_t)bytes;
 }
 if(at!=n||ac!=assets||ec!=events)goto fail;
 memcpy(r->info,owner,5*sizeof(uint64_t));r->info[5]=kind;r->info[6]=top;r->info[7]=bottom;r->info[9]=sizeof(*r);
 for(unsigned cell=0;cell<CELLS;cell++){unsigned k=p[80+cell];uint32_t frame=u32(p,38480+cell*4);if(k>6||(k==0?frame!=0:frame>owner[3]))goto fail;if(k!=(isroad?1:2))continue;Sample v=s[cell];if(v.asset>=assets||v.offset>=a[v.asset].n||v.refresh!=frame||!v.writer)goto fail;unsigned y=cell/240;if(y<top||y>=bottom)continue;uint64_t*writer=r->writers+r->info[8]*6;writer[0]=cell;writer[1]=owner[0];writer[2]=isroad?1:2;writer[3]=v.writer;writer[4]=frame;writer[5]=a[v.asset].p[v.offset];uint32_t*record=r->records+r->info[8]++*4;record[0]=cell;record[1]=v.asset;record[2]=v.offset;record[3]=frame;r->rgba[cell*4]=a[v.asset].p[v.offset];r->rgba[cell*4+3]=255;}
 free(a);free(s);return r;
fail:free(r);free(a);free(s);return NULL;
}
NFPCRecipeCoverage* nf_pc_source_recipe_coverage(const NFPCSourceFrame*f,unsigned owner,unsigned kind,size_t maximum){uint64_t meta[8],o[5];const void*h,*p;size_t n,pn;if((kind!=NFPC_ROAD&&kind!=NFPC_WALL)||!nf_pc_source_frame_info(f,meta)||!nf_pc_source_frame_owner(f,owner,o)||!nf_pc_source_frame_component(f,owner,kind,&h,&n)||!nf_pc_source_frame_component(f,owner,NFPC_PROOF,&p,&pn))return NULL;return nf_pc_recipe_coverage_decode(h,n,p,pn,o,kind,owner? (unsigned)meta[3]:0,meta[4]==1||owner?160:(unsigned)meta[3],maximum);}
void nf_pc_recipe_coverage_free(NFPCRecipeCoverage*r){free(r);}
int nf_pc_recipe_coverage_info(const NFPCRecipeCoverage*r,uint64_t out[10]){if(!r||!out)return 0;memcpy(out,r->info,sizeof(r->info));return 1;}
int nf_pc_recipe_coverage_buffer(const NFPCRecipeCoverage*r,unsigned kind,const void**p,size_t*n){if(!r||kind>2||!p||!n)return 0;*p=kind==2?(const void*)r->writers:kind?(const void*)r->records:r->rgba;*n=kind==2?(size_t)r->info[8]*48:kind?(size_t)r->info[8]*16:sizeof(r->rgba);return 1;}

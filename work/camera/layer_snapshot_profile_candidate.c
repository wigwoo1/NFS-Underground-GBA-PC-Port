#include "layer_snapshot.h"
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdlib.h>
#include <string.h>
#define PAGE 4096u
#define PARTS 25u
#define MAXPAGES (160u*PARTS)
static uint64_t dirty_stats[3],storage_profile[12];
static uint64_t storage_cycles(void){ULONG64 value=0;QueryThreadCycleTime(GetCurrentThread(),&value);return value;}
static uint64_t storage_now(void){LARGE_INTEGER q,f;QueryPerformanceCounter(&q);QueryPerformanceFrequency(&f);return (uint64_t)(q.QuadPart*1000000000.0/f.QuadPart);}
static void storage_end(unsigned stage,uint64_t began,uint64_t cycles){storage_profile[stage*3]++;storage_profile[stage*3+1]+=storage_now()-began;storage_profile[stage*3+2]+=storage_cycles()-cycles;}
__declspec(dllexport) void nf_storage_profile_reset(void){memset(storage_profile,0,sizeof(storage_profile));}
__declspec(dllexport) void nf_storage_profile_read(uint64_t*out){if(out)memcpy(out,storage_profile,sizeof(storage_profile));}
void nf_layer_snapshot_dirty_stats(uint64_t out[3]){if(out)memcpy(out,dirty_stats,sizeof(dirty_stats));}
struct NFLayerSnapshot {unsigned count,pages,capacity;uint8_t headers[160][128];uint16_t refs[160][PARTS];uint64_t hashes[MAXPAGES];uint8_t*data;};
_Static_assert(sizeof(NFHardwareLayerHeader)==128,"header layout");
_Static_assert(offsetof(NFHardwareLayerRow,vram)==128,"row prefix layout");
_Static_assert(sizeof(NFHardwareLayerRow)==100480,"row layout");
static uint64_t layer_hash(const uint8_t*p){uint64_t h=14695981039346656037ULL;for(unsigned i=0;i<PAGE;i++){h^=p[i];h*=1099511628211ULL;}return h;}
NFLayerSnapshot*nf_layer_snapshot_create(void){return calloc(1,sizeof(NFLayerSnapshot));}
NFLayerSnapshot*nf_layer_snapshot_clone(const NFLayerSnapshot*s){
 if(!s||s->count!=160)return NULL;
 NFLayerSnapshot*copy=malloc(sizeof(*copy));if(!copy)return NULL;
 memcpy(copy,s,sizeof(*copy));copy->capacity=s->pages;copy->data=NULL;
 if(s->pages){copy->data=malloc((size_t)s->pages*PAGE);if(!copy->data){free(copy);return NULL;}memcpy(copy->data,s->data,(size_t)s->pages*PAGE);}
 return copy;
}
void nf_layer_snapshot_destroy(NFLayerSnapshot*s){if(s){free(s->data);free(s);}}
int nf_layer_snapshot_reset(NFLayerSnapshot*s){if(!s)return 0;s->count=0;s->pages=0;return 1;}
int nf_layer_snapshot_add_dirty(NFLayerSnapshot*s,const void*header,const void*vram,const void*palette,const void*oam,uint32_t dirty,unsigned verify){
 if(!s||!header||!vram||!palette||!oam||s->count>=160)return 0;
 NFHardwareLayerHeader prefix;memcpy(&prefix,header,sizeof(prefix));const NFHardwareLayerHeader*r=&prefix;
 if(r->row!=s->count)return 0;
 uint32_t refresh=0;if(s->count){memcpy(&refresh,s->headers[0],4);if(r->refresh!=refresh)return 0;}
 uint16_t refs[PARTS];uint8_t last[PAGE]={0};const uint8_t*input=vram;
 for(unsigned part=0;part<PARTS;part++){
 const uint8_t*p=input+part*PAGE;if(part==PARTS-1){memcpy(last,palette,1024);memcpy(last+1024,oam,1024);p=last;}
 if(s->count&&!(dirty&(1u<<part))){unsigned previous=s->refs[s->count-1][part];dirty_stats[0]++;if(verify){dirty_stats[1]++;if(memcmp(p,s->data+previous*PAGE,PAGE)){dirty_stats[2]++;return 0;}}refs[part]=(uint16_t)previous;continue;}
 if(s->count){unsigned previous=s->refs[s->count-1][part];uint64_t t=storage_now(),c=storage_cycles();int equal=!memcmp(p,s->data+previous*PAGE,PAGE);storage_end(0,t,c);if(equal){refs[part]=(uint16_t)previous;continue;}}
 uint64_t t=storage_now(),c=storage_cycles();uint64_t h=layer_hash(p);storage_end(1,t,c);t=storage_now();c=storage_cycles();unsigned found=0;for(;found<s->pages;found++)if(s->hashes[found]==h&&!memcmp(p,s->data+found*PAGE,PAGE))break;storage_end(2,t,c);t=storage_now();c=storage_cycles();
 if(found==s->pages){if(s->pages>=MAXPAGES)return 0;if(s->pages==s->capacity){unsigned capacity=s->capacity?s->capacity*2:32;if(capacity>MAXPAGES)capacity=MAXPAGES;uint8_t*data=realloc(s->data,(size_t)capacity*PAGE);if(!data)return 0;s->data=data;s->capacity=capacity;}memcpy(s->data+found*PAGE,p,PAGE);s->hashes[found]=h;s->pages++;}refs[part]=(uint16_t)found;storage_end(3,t,c);
 }
 memcpy(s->headers[s->count],r,128);memcpy(s->refs[s->count],refs,sizeof(refs));s->count++;return 1;
}
int nf_layer_snapshot_add_parts(NFLayerSnapshot*s,const void*header,const void*vram,const void*palette,const void*oam){return nf_layer_snapshot_add_dirty(s,header,vram,palette,oam,0x1ffffffu,0);}
int nf_layer_snapshot_add(NFLayerSnapshot*s,const NFHardwareLayerRow*r){
 return r?nf_layer_snapshot_add_parts(s,r,r->vram,r->palette,r->oam):0;
}
int nf_layer_snapshot_read(const NFLayerSnapshot*s,unsigned row,NFHardwareLayerRow*out){
 if(!s||!out||s->count!=160||row>=160)return 0;
 memcpy(out,s->headers[row],128);for(unsigned p=0;p<PARTS;p++)memcpy((uint8_t*)out+128+p*PAGE,s->data+s->refs[row][p]*PAGE,p==PARTS-1?2048:PAGE);return 1;
}
size_t nf_layer_snapshot_bytes(const NFLayerSnapshot*s){return s?sizeof(*s)+(size_t)s->capacity*PAGE:0;}
int nf_layer_snapshot_refresh(const NFLayerSnapshot*s,uint32_t*out){if(!s||!out||s->count!=160)return 0;memcpy(out,s->headers[0],4);return 1;}
unsigned nf_layer_snapshot_pages(const NFLayerSnapshot*s){return s?s->pages:0;}
int nf_layer_snapshot_zero_colors(const NFLayerSnapshot*s,uint32_t refresh,uint16_t out[160]){
 if(!s||!out||s->count!=160)return 0;
 uint32_t owned_refresh;memcpy(&owned_refresh,s->headers[0],4);
 if(owned_refresh!=refresh)return 0;
 uint16_t colors[160];
 for(unsigned y=0;y<160;y++)memcpy(colors+y,s->data+s->refs[y][24]*PAGE,2);
 memcpy(out,colors,sizeof(colors));return 1;
}
int nf_layer_snapshot_bg_palettes(const NFLayerSnapshot*s,uint32_t refresh,uint16_t out[160][256]){
 if(!s||!out||s->count!=160)return 0;
 uint32_t owned_refresh;memcpy(&owned_refresh,s->headers[0],4);
 if(owned_refresh!=refresh)return 0;
 for(unsigned y=0;y<160;y++)memcpy(out[y],s->data+s->refs[y][24]*PAGE,512);
 return 1;
}

_Static_assert(sizeof(NFHudLayerRow)==34944,"HUD row layout");
int nf_layer_snapshot_read_hud(const NFLayerSnapshot*s,unsigned row,NFHudLayerRow*out){
 if(!s||!out||s->count!=160||row>=160)return 0;
 memcpy(out,s->headers[row],128);for(unsigned p=16;p<24;p++)memcpy(out->obj_vram+(p-16)*PAGE,s->data+s->refs[row][p]*PAGE,PAGE);
 memcpy((uint8_t*)out+128+0x8000,s->data+s->refs[row][24]*PAGE,2048);return 1;
}

int nf_layer_snapshot_display_page_equal(const NFLayerSnapshot*a,const NFLayerSnapshot*b){
 if(!a||!b||a->count!=160||b->count!=160)return 0;
 for(unsigned y=0;y<160;y++){
  NFHardwareLayerHeader ah,bh;memcpy(&ah,a->headers[y],128);memcpy(&bh,b->headers[y],128);
  uint16_t ac,bc;memcpy(&ac,ah.registers,2);memcpy(&bc,bh.registers,2);
  if((ac&7)!=4||(bc&7)!=4||(ac&0x80)||(bc&0x80)||ac!=bc)return 0;
  if(memcmp(ah.registers,bh.registers,0x40)||memcmp(ah.affine,bh.affine,sizeof(ah.affine)))return 0;
  if(memcmp(a->data+a->refs[y][24]*PAGE,b->data+b->refs[y][24]*PAGE,512))return 0;
  unsigned base=(ac&0x10)?0xa000:0;
  for(unsigned offset=base;offset<base+38400;){
   unsigned part=offset/PAGE,within=offset%PAGE,n=PAGE-within;
   if(n>base+38400-offset)n=base+38400-offset;
   if(memcmp(a->data+a->refs[y][part]*PAGE+within,b->data+b->refs[y][part]*PAGE+within,n))return 0;
   offset+=n;
  }
 }
 return 1;
}

int nf_layer_snapshot_display_page(const NFLayerSnapshot*s,unsigned page){
 if(!s||s->count!=160||page>1)return 0;
 for(unsigned y=0;y<160;y++){uint16_t control;memcpy(&control,s->headers[y]+8,2);if((control&7)!=4||(control&0x80)||((control>>4)&1)!=page)return 0;}
 return 1;
}

/* Identity-affine BG2 row comparison for native scene scanout ownership.
   Original indices are equality evidence only, never renderer output. */
int nf_layer_snapshot_display_rows_equal(const NFLayerSnapshot*a,const NFLayerSnapshot*b,unsigned page,unsigned begin,unsigned end){
 if(!a||!b||a->count!=160||b->count!=160||page>1||begin>=end||end>160)return 0;
 for(unsigned y=begin;y<end;y++){
  NFHardwareLayerHeader ah,bh;memcpy(&ah,a->headers[y],128);memcpy(&bh,b->headers[y],128);
  uint16_t ac,bc;memcpy(&ac,ah.registers,2);memcpy(&bc,bh.registers,2);
  if((ac&7)!=4||(ac&0x80)||ac!=bc||((ac>>4)&1)!=page)return 0;
  if(memcmp(ah.registers,bh.registers,0x40)||memcmp(ah.affine,bh.affine,sizeof(ah.affine)))return 0;
  if(ah.affine[0]!=256||ah.affine[1]||ah.affine[2]||ah.affine[3]!=256||ah.affine[4]||ah.affine[5]!=(int32_t)y*256)return 0;
  if(memcmp(a->data+a->refs[y][24]*PAGE,b->data+b->refs[y][24]*PAGE,512))return 0;
  unsigned start=page*0xa000+y*240,limit=start+240;
  while(start<limit){unsigned part=start/PAGE,within=start%PAGE,n=PAGE-within;if(n>limit-start)n=limit-start;
   if(memcmp(a->data+a->refs[y][part]*PAGE+within,b->data+b->refs[y][part]*PAGE+within,n))return 0;
   start+=n;}
 }
 return 1;
}

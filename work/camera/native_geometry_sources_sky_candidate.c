#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
/* Owned model sources for GPU consumers. Records carry raw source bytes,
   never pointers into emulator memory or original projected polygons. */
typedef struct {uint8_t *data;size_t size,capacity;unsigned refresh,valid,failed;} Geometry;
static Geometry building,frames[16];
static int reject_build(void){building.failed=1;return 0;}
__declspec(dllexport) void nf_geometry_sources_reset(void){
 free(building.data);memset(&building,0,sizeof(building));
 for(unsigned i=0;i<16;i++){free(frames[i].data);memset(frames+i,0,sizeof(frames[i]));}
}
__declspec(dllexport) int nf_geometry_sources_append(unsigned kind,unsigned context,const uint8_t*const*blocks,const unsigned*sizes,unsigned count){
 if(!blocks||!sizes||count!=12||kind<1||kind>3)return reject_build();
 size_t added=16;for(unsigned i=0;i<count;i++){if(!blocks[i]||sizes[i]>0x100000)return reject_build();added+=4+sizes[i];}
 if(building.failed)return 0;
 if(added>0x800000-building.size)return reject_build();
 size_t needed=building.size+added;
 if(needed>building.capacity){
  size_t capacity=building.capacity?building.capacity:0x10000;
  while(capacity<needed){if(capacity>=0x400000){capacity=0x800000;break;}capacity*=2;}
  uint8_t *grown=realloc(building.data,capacity);if(!grown)return reject_build();
  building.data=grown;building.capacity=capacity;
 }
 uint8_t *next=building.data;
 uint32_t header[4]={0x3147534e,kind,context,count};size_t offset=building.size;
 memcpy(next+offset,header,16);offset+=16;
 for(unsigned i=0;i<count;i++){memcpy(next+offset,sizes+i,4);offset+=4;memcpy(next+offset,blocks[i],sizes[i]);offset+=sizes[i];}
 building.size=offset;return 1;
}
__declspec(dllexport) int nf_geometry_sources_close(unsigned refresh){
 unsigned slot=refresh%16;free(frames[slot].data);frames[slot]=building;frames[slot].refresh=refresh;frames[slot].valid=!building.failed;
 unsigned valid=frames[slot].valid;
 memset(&building,0,sizeof(building));return valid;
}
__declspec(dllexport) int nf_geometry_sources_read(unsigned refresh,void*out,size_t capacity,size_t*size){
 Geometry*f=frames+refresh%16;
 if(!size||!f->valid||f->refresh!=refresh)return 0;
 if(!out){*size=f->size;return 1;}
 if(capacity<f->size)return 0;
 if(f->size)memcpy(out,f->data,f->size);
 *size=f->size;return 1;
}

/* Match the scene adapter's pointer-free GPU model context. */
__declspec(dllexport) int nf_geometry_sources_model(unsigned context,const uint8_t*const*blocks,const unsigned*sizes,unsigned count){
 if(!blocks||!sizes||count!=12||!blocks[0]||sizes[0]!=68)return reject_build();
 uint8_t gpu_context[68]={0};const uint8_t*owned[12];
 memcpy(gpu_context+56,blocks[0]+56,4);memcpy(gpu_context+64,blocks[0]+64,4);
 for(unsigned i=0;i<12;i++)owned[i]=blocks[i];owned[0]=gpu_context;
 return nf_geometry_sources_append(3,context,owned,sizes,count);
}

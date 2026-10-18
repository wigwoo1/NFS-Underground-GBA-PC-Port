#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include "road_source_attributes.h"
static int16_t h(const uint8_t*p){int16_t v;memcpy(&v,p,2);return v;}
static int32_t w(const uint8_t*p){int32_t v;memcpy(&v,p,4);return v;}
/* Decode owned source records and resolved offsets without bus pointers.
   Output world and attributes publish together only after validation. */
__declspec(dllexport) int nf_road_source_decode(const uint8_t*vertices,size_t vertex_bytes,const uint8_t*offsets,size_t offset_bytes,const uint8_t*face,const uint8_t*material,unsigned count,unsigned affine,double*out,NFRoadSourceAttributes*attributes){
 if(!vertices||!offsets||!face||!material||!out||!attributes||!count||count>32||affine>1||vertex_bytes!=count*68||offset_bytes!=count*32)return 0;
 unsigned shift=(uint16_t)h(material+36),height=(uint16_t)h(material+38);
 if(shift>10||!height||height>1024)return 0;
 double world[96];NFRoadSourceAttributes raw;memset(&raw,0,sizeof(raw));
 raw.count=count;raw.shift=shift;raw.stored_height=height;raw.affine=affine;
 for(unsigned i=0;i<count;i++){
  const uint8_t*v=vertices+i*68,*o=offsets+i*32;
  world[i*3]=(double)w(v)+h(o);
  world[i*3+1]=(double)h(v+56)+h(o+6)+h(face+6);
  world[i*3+2]=(double)w(v+4)+h(o+2);
  raw.attributes[i][0]=w(v+32);raw.attributes[i][1]=w(v+36);
 }
 memcpy(out,world,count*3*sizeof(*out));memcpy(attributes,&raw,sizeof(raw));return 1;
}

typedef struct {unsigned count;uint32_t address[512];double depth[512];} RoadScratch;
static int slot(RoadScratch*s,uint32_t address,int create){
 for(unsigned i=0;i<s->count;i++)if(s->address[i]==address)return (int)i;
 if(!create||s->count==512)return -1;
 unsigned i=s->count++;s->address[i]=address;s->depth[i]=0;return (int)i;
}
__declspec(dllexport) void *nf_road_scratch_create(void){return calloc(1,sizeof(RoadScratch));}
__declspec(dllexport) void nf_road_scratch_destroy(void*handle){free(handle);}
__declspec(dllexport) int nf_road_scratch_ring(void*handle,uint32_t base,const double*points,unsigned count,unsigned affine,double*out,uint64_t*missing){
 if(!handle||!points||!out||!missing||count>64||affine>1||(uint64_t)base+count*24+12>UINT32_MAX)return 0;
 RoadScratch next=*(RoadScratch*)handle;double ring[384];uint64_t mask=0;
 for(unsigned i=0;i<count;i++){
  const double*p=points+i*5;double*r=ring+i*6;int index=slot(&next,base+i*24+12,!affine);
  if(index<0&&!affine)return 0;
  if(index<0)mask|=UINT64_C(1)<<i;
  if(!affine)next.depth[index]=p[2];
  r[0]=p[0];r[1]=r[2]=p[1];r[3]=index<0?0:next.depth[index];r[4]=p[3];r[5]=p[4];
 }
 memcpy(out,ring,count*6*sizeof(*out));*(RoadScratch*)handle=next;*missing=mask;return 1;
}
__declspec(dllexport) int nf_road_scratch_commit(void*handle,uint32_t base,unsigned first,const double*ring,unsigned count){
 if(!handle||!ring||count>128||(uint64_t)base+((uint64_t)first+count)*24+12>UINT32_MAX)return 0;
 RoadScratch next=*(RoadScratch*)handle;
 for(unsigned i=0;i<count;i++){int index=slot(&next,base+(first+i)*24+12,1);if(index<0)return 0;next.depth[index]=ring[i*6+3];}
 *(RoadScratch*)handle=next;return 1;
}

extern int nf_road_source_ring(const double*,unsigned,const NFRoadSourceAttributes*,const int32_t*,const int32_t*,const uint32_t*,double*,unsigned,unsigned*);
extern int nf_road_clip_continuous(const double*,unsigned,double,double,const uint32_t*,double*,unsigned,unsigned*);
/* Whole owned raw-source to clipped-ring dispatch. Scratch and outputs commit
   together; initial missing depth slots remain explicitly reported. */
__declspec(dllexport) int nf_road_source_clipped(void*handle,const uint8_t*vertices,size_t vertex_bytes,const uint8_t*offsets,size_t offset_bytes,const uint8_t*face,const uint8_t*material,unsigned count,unsigned affine,const int32_t*matrix,const uint16_t*bounds,uint32_t base,unsigned first,const uint32_t*table,double*out,unsigned capacity,unsigned*out_count,uint64_t*missing){
 if(!handle||!matrix||!bounds||!table||!out||!out_count||!missing)return 0;
 RoadScratch next=*(RoadScratch*)handle;double world[96],points[320],ring[384],clipped[768];NFRoadSourceAttributes attributes;
 int32_t projection[3]={120,87,128};unsigned n,cn;uint64_t mask;
 if(!nf_road_source_decode(vertices,vertex_bytes,offsets,offset_bytes,face,material,count,affine,world,&attributes))return 0;
 if(!nf_road_source_ring(world,count,&attributes,matrix,projection,table,points,64,&n))return 0;
 if(!nf_road_scratch_ring(&next,base,points,n,affine,ring,&mask))return 0;
 if(!nf_road_clip_continuous(ring,n,bounds[0],bounds[1],table,clipped,128,&cn)||cn>capacity)return 0;
 if(!nf_road_scratch_commit(&next,base,first,clipped,cn))return 0;
 memcpy(out,clipped,cn*6*sizeof(*out));*(RoadScratch*)handle=next;*out_count=cn;*missing=mask;return 1;
}

extern int nf_road_draw_runs(const int32_t*,unsigned,const int32_t*,unsigned,unsigned,const uint32_t*,uint32_t,const uint8_t*,const uint32_t*,uint32_t*,unsigned,unsigned*);
__declspec(dllexport) int nf_road_source_runs(void*handle,const uint8_t*vertices,size_t vertex_bytes,const uint8_t*offsets,size_t offset_bytes,const uint8_t*face,const uint8_t*material,unsigned count,unsigned affine,const int32_t*matrix,const uint16_t*bounds,uint32_t base,unsigned first,const uint32_t*table,uint32_t framebuffer,unsigned orientation,const uint32_t*uv_offsets,uint32_t*out,unsigned capacity,unsigned*out_count,uint64_t*missing){
 if(!handle||!out||!out_count||!missing||!uv_offsets||capacity>8192)return 0;
 RoadScratch next=*(RoadScratch*)handle;double clipped[768];unsigned n;uint64_t mask;
 if(!nf_road_source_clipped(&next,vertices,vertex_bytes,offsets,offset_bytes,face,material,count,affine,matrix,bounds,base,first,table,clipped,128,&n,&mask))return 0;
 int32_t ring[768],clipbounds[4];for(unsigned i=0;i<4;i++)clipbounds[i]=bounds[i];
 for(unsigned i=0;i<n*6;i++){if(!isfinite(clipped[i])||clipped[i]<INT32_MIN||clipped[i]>INT32_MAX)return 0;ring[i]=(int32_t)clipped[i];}
 unsigned runs=0;
 /* Missing initial depth is diagnostic warmup, never silently rendered. */
 if(!mask&&!nf_road_draw_runs(ring,n,clipbounds,orientation,affine,table,framebuffer,material,uv_offsets,out,capacity,&runs))return 0;
 *(RoadScratch*)handle=next;*out_count=runs;*missing=mask;return 1;
}

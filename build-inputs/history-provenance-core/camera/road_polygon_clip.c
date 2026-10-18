#include <stdlib.h>
#include "road_polygon_clip.h"
#include <stddef.h>
#include <string.h>
/* Original 03000EFC: clip projected six-word attributes to left/right.
   Input is generated from owned world geometry, not polygon matching. */
static int endpoint(int32_t a[6],const int32_t b[6],int32_t boundary,const uint32_t *reciprocal){
 int64_t delta=(int64_t)b[0]-a[0];
 int64_t distance=delta<0?-delta:delta;
 if(distance>=32768)return 0;
 uint32_t factor=((uint32_t)boundary-(uint32_t)a[0])*reciprocal[distance];
 if(delta<0||(delta==0&&boundary<a[0]))factor=0u-factor;
 for(unsigned j=1;j<6;j++){
  int32_t difference=(int32_t)((uint32_t)b[j]-(uint32_t)a[j]);
  int64_t product=(int64_t)difference*(int32_t)factor;
  a[j]=(int32_t)((uint32_t)a[j]+(uint32_t)((uint64_t)product>>24));
 }
 a[0]=boundary;return 1;
}
__declspec(dllexport) int nf_road_polygon_clip(const int32_t *input,unsigned count,int32_t left,int32_t right,const uint32_t *reciprocal,int32_t *out,unsigned capacity,unsigned *out_count){
 if(!input||!reciprocal||!out||!out_count||count>64)return 0;
 int32_t result[128*6];unsigned n=0;
 for(unsigned i=0;i<count;i++){
  int32_t a[6],b[6];memcpy(a,input+((i+count-1)%count)*6,24);memcpy(b,input+i*6,24);
  /* Original left classification takes precedence even for reversed bounds. */
  if(a[0]<left){if(b[0]<left)continue;if(!endpoint(a,b,left,reciprocal))return 0;}
  else if(a[0]>right){if(b[0]>right)continue;if(!endpoint(a,b,right,reciprocal))return 0;}
  int extra=0;
  if(b[0]<left){if(!endpoint(b,a,left,reciprocal))return 0;extra=1;}
  else if(b[0]>right){if(!endpoint(b,a,right,reciprocal))return 0;extra=1;}
  memcpy(result+n++*6,a,24);if(extra)memcpy(result+n++*6,b,24);
 }
 if(n>capacity)return 0;
 memcpy(out,result,n*24);*out_count=n;return 1;
}
/* Original03002F88 edge traversal and top trimming. Context keeps owned
   address identities; vertices and framebuffer descriptor are explicit inputs. */
__declspec(dllexport) int nf_road_edge_step(const uint32_t context[18],unsigned side,unsigned orientation,const int32_t *vertices,unsigned count,const uint32_t reciprocal[32768],const uint32_t framebuffer[4],uint32_t out[18]){
 if(!context||!vertices||!reciprocal||!framebuffer||!out||!count||count>128||context[11]!=count||context[2]>=count||side>1)return -1;
 uint32_t c[18];memcpy(c,context,sizeof(c));unsigned index=c[2],remaining=c[8];
 orientation=orientation!=0;
 const int32_t *b=vertices+index*6;
 if(b[1]>=(int32_t)c[13])return 0;
 for(unsigned guard=0;guard<count;guard++){
  const int32_t *a=b;
  if(side==orientation)index=(index+1)%count;else index=(index+count-1)%count;
  if(!remaining)return 0;
  remaining--;
  b=vertices+index*6;
  int32_t height=b[1]<(int32_t)c[12]?0:(int32_t)((uint32_t)b[1]-(uint32_t)a[1]);
  if(height<=0)continue;
  if(height>=32768)return -1;
  c[4]=(reciprocal[height]>>8)*((uint32_t)b[0]-(uint32_t)a[0]);
  const unsigned fields[3]={4,5,3},slots[3]={5,6,7};
  for(unsigned j=0;j<3;j++){
   int32_t diff=(int32_t)((uint32_t)b[fields[j]]-(uint32_t)a[fields[j]]);
   int64_t product=(int64_t)diff*(int32_t)reciprocal[height];
   c[slots[j]]=(uint32_t)((uint64_t)product>>24);
  }
  uint32_t y=(uint32_t)a[1],x=(uint32_t)a[0]<<16,u=(uint32_t)a[4],v=(uint32_t)a[5],q=(uint32_t)a[3];
  if(a[1]<(int32_t)c[12]){
   uint32_t dy=c[12]-(uint32_t)a[1];y=c[12];height-=(int32_t)dy;
   x+=dy*c[4];u+=dy*c[5];v+=dy*c[6];q+=dy*c[7];
  }
  c[8]=remaining;c[2]=index;c[0]=x;c[3]=y;c[9]=framebuffer[0]+framebuffer[3]*y;
  c[14]=u;c[15]=v;c[16]=q;c[1]=(uint32_t)height;
  memcpy(out,c,sizeof(c));return 1;
 }
 return 0;
}
/* Coverage scheduler; texture evaluation remains separate. */
static uint32_t road_sar(uint32_t,unsigned);
static int road_unproject(uint32_t,uint32_t,uint32_t,const uint32_t*,uint32_t*,uint32_t*);
static int road_span_plan(const int32_t *vertices,unsigned count,int32_t top,int32_t bottom,unsigned orientation,unsigned affine,const uint32_t reciprocal[32768],const uint32_t framebuffer[4],const uint32_t *material,uint32_t *out,unsigned capacity,unsigned *out_count){
 if(!vertices||!reciprocal||!framebuffer||!out||!out_count||(count&&count<3)||count>128||top<0||bottom>160||top>bottom||affine>1)return 0;
 if(!count){*out_count=0;return 1;}
 unsigned first=0;int32_t ymin=vertices[1],ymax=ymin;
 for(unsigned i=1;i<count;i++){int32_t y=vertices[i*6+1];if(y<ymin){ymin=y;first=i;}if(y>=ymax)ymax=y;}
 uint32_t result[512*20];unsigned n=0,stride=material?20:4;
 if(ymin==ymax||ymax<=top||ymin>=bottom){*out_count=0;return 1;}
 uint32_t edge[2][18]={{0}};
 for(unsigned side=0;side<2;side++){edge[side][2]=first;edge[side][8]=count;edge[side][11]=count;edge[side][12]=(uint32_t)top;edge[side][13]=(uint32_t)bottom;}
 uint32_t pointer=framebuffer[0]+framebuffer[3]*(uint32_t)ymin;unsigned doubled=0;
 for(unsigned guard=0;guard<512;guard++){
  for(int side=1;side>=0;side--)if((int32_t)edge[side][1]<=0){
   uint32_t next[18];int status=nf_road_edge_step(edge[side],(unsigned)side,orientation,vertices,count,reciprocal,framebuffer,next);
   if(status<0)return 0;
   if(!status)goto finished;
   memcpy(edge[side],next,sizeof(next));pointer=next[9];
  }
  int32_t distance=(int32_t)(edge[0][0]-edge[1][0]);
  if(distance>0){
   unsigned width=(unsigned)(distance>>17)+2;
   if((int32_t)edge[1][16]>0xc000)doubled=1;
   int32_t x=(int32_t)edge[1][0]>>17;
   if(n>=512)return 0;
   uint32_t *span=result+n*stride;
   span[0]=pointer+(uint32_t)x*2;span[1]=width;
   span[2]=!affine&&width>32?0x03003190:0x030056d8;span[3]=doubled;
   if(material){
    uint32_t *c=span+4;memcpy(c,material,64);c[6]=span[0];c[7]=width;
    if(width>=32768)return 0;
    uint32_t inverse=reciprocal[width]>>8;
    if(!affine&&width>32){
     c[4]=inverse;c[8]=edge[1][14];c[9]=edge[1][15];c[10]=edge[1][16];
     c[11]=edge[0][14];c[12]=edge[0][15];c[13]=edge[0][16];
    }else{
     uint32_t a=edge[1][14],b=edge[1][15],end_a=edge[0][14],end_b=edge[0][15];
     if(!affine&&(!road_unproject(edge[1][16],a,b,reciprocal,&a,&b)||!road_unproject(edge[0][16],end_a,end_b,reciprocal,&end_a,&end_b)))return 0;
     c[8]=a+c[14];c[9]=b+c[15];
     c[10]=road_sar(inverse*road_sar(end_a-a,8),8);c[11]=road_sar(inverse*road_sar(end_b-b,8),8);
    }
   }
   n++;
  }
  unsigned step=doubled?2:1;
  for(unsigned side=0;side<2;side++){
   edge[side][0]+=edge[side][4]*step;edge[side][14]+=edge[side][5]*step;
   edge[side][15]+=edge[side][6]*step;edge[side][16]+=edge[side][7]*step;edge[side][1]-=step;
  }
  pointer+=framebuffer[3]*step;
  if(pointer>=framebuffer[0]+framebuffer[3]*(uint32_t)bottom+120)goto finished;
 }
 return 0;
finished:
 if(n>capacity)return 0;
 memcpy(out,result,n*stride*4);*out_count=n;return 1;
}
__declspec(dllexport) int nf_road_span_plan(const int32_t *v,unsigned n,int32_t t,int32_t b,unsigned o,unsigned a,const uint32_t r[32768],const uint32_t f[4],uint32_t *out,unsigned cap,unsigned *count){return road_span_plan(v,n,t,b,o,a,r,f,NULL,out,cap,count);}
__declspec(dllexport) int nf_road_span_contexts(const int32_t *v,unsigned n,int32_t t,int32_t b,unsigned o,unsigned a,const uint32_t r[32768],const uint32_t f[4],const uint32_t material[16],uint32_t *out,unsigned cap,unsigned *count){if(!material)return 0;return road_span_plan(v,n,t,b,o,a,r,f,material,out,cap,count);}
/* Original030056D8 samples a pre-resolved16bit texture. Row duplication is
   represented by span coverage and does not change these sampled colors. */
__declspec(dllexport) int nf_road_span_pixels(const uint32_t params[12],int (*read)(void*,uint32_t,void*,size_t),void *context,uint16_t *out,unsigned capacity){
 if(!params||!read||!out||params[0]>15||params[7]>512||params[7]>capacity||(params[1]&0x80000000u)||(params[2]&0x80000000u))return 0;
 uint16_t result[512];uint32_t u=params[8],v=params[9];
 for(unsigned i=0;i<params[7];i++){
  u&=params[1];v&=params[2];
  uint64_t index=(u>>16)+((uint64_t)(v>>16)<<params[0]);
  uint64_t address=(uint64_t)params[5]+index*2;
  if(address>UINT32_MAX||!read(context,(uint32_t)address,result+i,2))return 0;
  u+=params[10];v+=params[11];
 }
 memcpy(out,result,params[7]*2u);return 1;
}
static uint32_t road_sar(uint32_t value,unsigned bits){return (uint32_t)((int32_t)value>>bits);}
static int road_unproject(uint32_t q,uint32_t u,uint32_t v,const uint32_t *reciprocal,uint32_t *out_u,uint32_t *out_v){
 int32_t index=(int32_t)q>>4;if(index<0||index>=32768)return 0;
 *out_u=road_sar(reciprocal[index]*road_sar(u,8),4);
 *out_v=road_sar(reciprocal[index]*road_sar(v,8),4);return 1;
}
/* Original03003190 decomposes perspective spans into16sample affine runs. */
__declspec(dllexport) int nf_road_perspective_plan(const uint32_t params[16],const uint32_t reciprocal[32768],uint32_t *out,unsigned capacity,unsigned *out_count,uint32_t final[16]){
 if(!params||!reciprocal||!out||!out_count||!final||params[7]>512)return 0;
 uint32_t c[16],result[32*16];memcpy(c,params,sizeof(c));unsigned remaining=c[7],n=0;
 uint32_t q=c[10],u=c[8],v=c[9],a,b;
 int64_t product=(int64_t)(int32_t)(c[13]-q)*(int32_t)c[4];
 uint32_t dq=(uint32_t)((uint64_t)product>>12);
 uint32_t du=road_sar(road_sar(c[11]-u,8)*c[4],4),dv=road_sar(road_sar(c[12]-v,8)*c[4],4);
 if(!road_unproject(q,u,v,reciprocal,&a,&b))return 0;
 c[7]=16;
 while(remaining){
  uint32_t next_a,next_b;q+=dq;u+=du;v+=dv;
  if(!road_unproject(q,u,v,reciprocal,&next_a,&next_b))return 0;
  c[8]=a+c[14];c[9]=b+c[15];c[10]=road_sar(next_a-a,4);c[11]=road_sar(next_b-b,4);
  if(remaining<=15)c[7]=remaining;
  memcpy(result+n++*16,c,sizeof(c));c[6]+=32;a=next_a;b=next_b;
  remaining=remaining>16?remaining-16:0;
 }
 if(n>capacity)return 0;
 memcpy(out,result,n*64);*out_count=n;memcpy(final,c,sizeof(c));return 1;
}
static uint16_t road_half(const uint8_t *p){uint16_t v;memcpy(&v,p,2);return v;}
static uint32_t road_word(const uint8_t *p){uint32_t v;memcpy(&v,p,4);return v;}
/* Resolve primary road material and animation from the owned state tables. */
__declspec(dllexport) int nf_road_material_seed(const uint8_t state[256],const uint8_t descriptor[48],int (*read)(void*,uint32_t,void*,size_t),void *context,uint32_t out[16]){
 if(!state||!descriptor||!read||!out)return 0;
 unsigned index=road_half(descriptor+8);if(!index)return 0;
 uint8_t material[32],animation[8];
 uint64_t address=(uint64_t)road_word(state+32)+index*32ull;
 if(address>UINT32_MAX||!read(context,(uint32_t)address,material,32))return 0;
 address=(uint64_t)road_word(state+72)+road_half(material)*8ull;
 if(address>UINT32_MAX||!read(context,(uint32_t)address,animation,8))return 0;
 address=(uint64_t)road_word(state+32)+(index+(uint64_t)road_half(animation+2))*32;
 if(address>UINT32_MAX||!read(context,(uint32_t)address,material,32))return 0;
 unsigned shift=road_half(material+26),height=road_half(material+10);
 if(shift>15||!height)return 0;
 uint64_t texture=(uint64_t)road_word(state)+road_word(material+4);if(texture>UINT32_MAX)return 0;
 uint32_t seed[16]={0};seed[0]=shift;seed[1]=(1u<<(shift+15))-1;seed[2]=(height<<15)-1;seed[5]=(uint32_t)texture;
 seed[14]=(uint32_t)(int32_t)(int16_t)road_half(animation+4)<<7;
 seed[15]=(uint32_t)(int32_t)(int16_t)road_half(animation+6)<<7;
 memcpy(out,seed,sizeof(seed));return 1;
}

__declspec(dllexport) int nf_road_clip_bounds(const uint16_t inherited[4],const uint32_t framebuffer[4],const uint32_t *spans,unsigned count,uint16_t out[4],unsigned *cell_end){
 if(!inherited||!framebuffer||!out||!cell_end||(count&&!spans)||count>512||framebuffer[3]!=240||inherited[0]>inherited[1]||inherited[1]>240||inherited[2]>inherited[3]||inherited[3]>160)return 0;
 unsigned end=0;
 for(unsigned i=0;i<count;i++){
  const uint32_t *s=spans+i*20;
  if(!s[1]||s[1]>121||s[3]>1||s[0]<framebuffer[0])return 0;
  uint64_t offset=(uint64_t)s[0]-framebuffer[0];unsigned x=(unsigned)(offset%240);uint64_t y=offset/240;
  if(x%2||x+s[1]*2>242||y>=160)return 0;
  /* Packed 121-pair spans may spill two bytes into the following row. */ unsigned finish=(unsigned)y+(x+s[1]*2+239)/240+s[3];if(finish>160)finish=160;if(finish>end)end=finish;
 }
 uint16_t result[4];memcpy(result,inherited,sizeof(result));if(end>result[3])result[3]=(uint16_t)end;
 memcpy(out,result,sizeof(result));*cell_end=end;return 1;
}



/* Atomic owned road writer batch: 16 context words plus doubled-row flag.
   Pixels and destination writes execute natively; reader owns texture inputs. */
__declspec(dllexport) int nf_road_spans_write(const uint32_t*spans,unsigned count,int(*read)(void*,uint32_t,void*,size_t),void*context,uint8_t*vram,size_t bytes){
 if(!spans||!read||!vram||count>8192||bytes!=0x18000)return 0;
 uint8_t*next=malloc(bytes);if(!next)return 0;memcpy(next,vram,bytes);int ok=0;
 for(unsigned i=0;i<count;i++){
  const uint32_t*p=spans+i*17;unsigned width=p[7],doubled=p[16];uint16_t pixels[512];
  if(doubled>1||width>512||p[6]<0x06000000||!nf_road_span_pixels(p,read,context,pixels,512))goto done;
  size_t offset=p[6]-0x06000000,size=width*2;
  if(offset>0x14000||size>0x14000-offset||(doubled&&(offset+240>0x14000||size>0x14000-offset-240)))goto done;
  memcpy(next+offset,pixels,size);if(doubled)memcpy(next+offset+240,pixels,size);
 }
 memcpy(vram,next,bytes);ok=1;
 done:free(next);return ok;
}

/* Complete owned clipped-ring/material dispatch including perspective runs.
   Output is 17 words/run: writer context16 plus doubled-row flag. */
__declspec(dllexport) int nf_road_draw_runs(const int32_t *ring,unsigned vertices,const int32_t bounds[4],unsigned orientation,unsigned affine,const uint32_t *table,uint32_t framebuffer,const uint8_t *material,const uint32_t offsets[2],uint32_t *out,unsigned capacity,unsigned *out_count){
 if(!ring||!bounds||!table||!material||!offsets||!out||!out_count||capacity>8192)return 0;
 unsigned shift=road_half(material+36),height=road_half(material+38);
 if(shift>10||height>1024||!height)return 0;
 uint32_t seed[16]={0},fb[4]={framebuffer,0,0,240},spans[512*20];unsigned count;
 seed[0]=shift;seed[1]=(1u<<(shift+15))-1;seed[2]=(height<<15)-1;
 seed[5]=road_word(material+40);seed[14]=offsets[0]<<7;seed[15]=offsets[1]<<7;
 if(!nf_road_span_contexts(ring,vertices,bounds[2],bounds[3],orientation,affine,table,fb,seed,spans,512,&count))return 0;
 uint32_t *result=malloc((capacity?capacity:1)*17*sizeof(*result));if(!result)return 0;
 unsigned written=0;int ok=0;
 for(unsigned i=0;i<count;i++){
  uint32_t *span=spans+i*20,*params=span+4,runs[512],final[16];unsigned n=1;
  if(span[2]==0x03003190){if(!nf_road_perspective_plan(params,table,runs,32,&n,final))goto done;params=runs;}
  if(n>capacity-written)goto done;
  for(unsigned j=0;j<n;j++){memcpy(result+written*17,params+j*16,64);result[written*17+16]=span[3];written++;}
 }
 memcpy(out,result,written*17*sizeof(*out));*out_count=written;ok=1;
 done:free(result);return ok;
}

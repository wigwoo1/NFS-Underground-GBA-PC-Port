#include <stdlib.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
static uint32_t wall_word(const uint8_t*p){uint32_t v;memcpy(&v,p,4);return v;}
/* 030052D0 default vertical span scaling and 0300527C extended-UV scaling.
   Signed 64-bit multiply followed by extraction of the ARM result bits. */
__declspec(dllexport) int nfs_wall_texture_step(uint32_t span,unsigned rows,const uint32_t*reciprocal,unsigned extended,uint32_t*out){
 if(!reciprocal||!out||rows>=32768||extended>1)return 0;
 uint64_t product=(uint64_t)((int64_t)(int32_t)span*(int64_t)(int32_t)reciprocal[rows]);
 *out=(uint32_t)(product>>(extended?24:16));return 1;
}
/* Original 030053E8 unshaded column addressing. Return one source/destination
   byte address per row. Caller writes only nonzero source indices. Arithmetic
   deliberately wraps at 32 bits, as on ARM. This does not touch game memory. */
__declspec(dllexport) int nfs_wall_unshaded_addresses(const uint8_t*state,uint32_t destination,uint32_t vertical,unsigned count,uint32_t*source_out,uint32_t*destination_out){
 if(!state||count>320||(count&&(!source_out||!destination_out)))return 0;
 unsigned shift=wall_word(state+12),height=wall_word(state+16),uvshift=15;
 uint32_t step=wall_word(state+44),texture=wall_word(state+36),stride=wall_word(state+8);
 if(shift>10||!height||height>1024)return 0;
 uint32_t mask=(height<<15)-1;
 if(wall_word(state+24)&&step>0x1b000){if(shift<2)return 0;shift-=2;uvshift=17;texture+=wall_word(state+28);}
 texture=(texture+((wall_word(state+52)&wall_word(state+64))>>uvshift))&~1u;
 destination+=(stride*(wall_word(state+4)>>14))<<1;
 for(unsigned i=0;i<count;i++){
  vertical&=mask;source_out[i]=texture+((vertical>>uvshift)<<shift);destination_out[i]=destination;
  destination+=stride<<1;vertical+=step;
 }
 return 1;
}
static uint32_t sar(uint32_t x,unsigned n){return (x>>n)|((x&0x80000000u)?(~0u<<(32-n)):0);}
/* Original horizontal wall clipping. Inputs are signed prepared pixel edges;
   bounds are unsigned pixel coordinates. out = visible, first column, count,
   skipped columns (for advancing attributes). Rejected outputs are zero.
   This reference component must not freeze viewport bounds for moving poses. */
__declspec(dllexport) int nfs_wall_clip_horizontal(int left_pixel,int right_pixel,unsigned clip_left,unsigned clip_right,int out[4]){
 if(!out||left_pixel<-32768||left_pixel>32767||right_pixel<-32768||right_pixel>32767||clip_left>65535||clip_right>65535)return 0;
 int left=(int32_t)sar((uint32_t)left_pixel,1),right=(int32_t)sar((uint32_t)(right_pixel+1),1);
 int original=left,count=right-left,lo=(int)(clip_left>>1),hi=(int)(clip_right>>1);
 out[0]=out[1]=out[2]=out[3]=0;
 if(count<=1)return 1;
 if(left<lo){if(right<lo)return 1;left=lo;count=right-left;}
 if(right>hi){if(left>hi)return 1;count=hi-left+1;}
 if(count<=1)return 1;
 out[0]=1;out[1]=left;out[2]=count;out[3]=left-original;return 1;
}
/* Original 03000AFC..03000B38 vertical clipping. Output is fixed14 top,
   signed row count (stored as bits), and adjusted fixed-point texture V.
   Preserve the original extra terminal row; continuous 4K geometry need not
   copy this low-resolution raster coverage expansion. */
__declspec(dllexport) int nfs_wall_clip_column(uint32_t top,uint32_t bottom,unsigned clip_top,unsigned clip_bottom,uint32_t step,uint32_t vertical,uint32_t out[3]){
 if(!out||clip_top>65535||clip_bottom>65535)return 0;
 uint32_t first=sar(top,14),last=sar(bottom,14),count=last-first+1;
 if((int32_t)top<(int32_t)(clip_top<<14)){
  uint32_t skip=clip_top-first;top=clip_top<<14;count-=skip;vertical+=step*skip;
 }
 if((int32_t)bottom>=(int32_t)(clip_bottom<<14))count-=last-clip_bottom;
 count++;out[0]=top;out[1]=count;out[2]=vertical;
 return 1;
}
typedef int (*NFWallReadByte)(void*,uint32_t,uint8_t*);
/* Compose default step, clipping and sampling into a bounded write list.
   This is a native reference raster component, not screen-space motion code.
   Output arrays must hold 320 entries; failures leave all outputs unchanged. */
__declspec(dllexport) int nfs_wall_default_column(const uint8_t*state,uint32_t destination,uint32_t top,uint32_t bottom,unsigned clip_top,unsigned clip_bottom,uint32_t span,uint32_t vertical,const uint32_t*reciprocal,NFWallReadByte read,void*context,uint32_t*out_addresses,uint8_t*out_values,unsigned*out_count){
 if(!state||!read||!out_addresses||!out_values||!out_count)return 0;
 uint32_t rows=sar(bottom,14)-sar(top,14)+1,step,clipped[3];
 if(!rows||rows>=32768||!nfs_wall_texture_step(span,rows,reciprocal,0,&step)||!nfs_wall_clip_column(top,bottom,clip_top,clip_bottom,step,vertical,clipped))return 0;
 if((int32_t)clipped[1]<=0){*out_count=0;return 1;}
 if(clipped[1]>320)return 0;
 uint8_t adjusted[68],values[320];uint32_t sources[320],destinations[320],addresses[320];unsigned count=0;
 memcpy(adjusted,state,68);memcpy(adjusted+4,clipped,4);memcpy(adjusted+44,&step,4);
 if(!nfs_wall_unshaded_addresses(adjusted,destination,clipped[2],clipped[1],sources,destinations))return 0;
 for(unsigned i=0;i<clipped[1];i++){
  uint8_t value;if(!read(context,sources[i],&value))return 0;
  if(value){addresses[count]=destinations[i];values[count++]=value;}
 }
 memcpy(out_addresses,addresses,count*sizeof(*addresses));memcpy(out_values,values,count);*out_count=count;return 1;
}
/* Original 03000810..03000858 perspective attribute restoration.
   Inputs are the interpolated attribute/depth accumulator and reciprocal LUT
   result. Keep ARM's 32-bit multiply wrap before the arithmetic shift. */
__declspec(dllexport) uint32_t nfs_wall_restore_attribute(uint32_t attribute,uint32_t reciprocal){
 return sar(sar(attribute,4)*reciprocal,8);
}
static int16_t half(const uint8_t*p){int16_t v;memcpy(&v,p,2);return v;}
static uint32_t multiply_shift(int32_t a,uint32_t b,unsigned shift){return (uint32_t)(((int64_t)a*(int32_t)b)>>shift);}
/* Sample original shaded-wall columns (two GBA pixels per column).
   edge is the prepared 52-byte edge; reciprocal has at least 32768 entries. */
__declspec(dllexport) int nfs_wall_shade_column(const uint8_t*edge,int column,const uint32_t*reciprocal){
 int left=half(edge)>>1,right=(half(edge+2)+1)>>1,width=right-left;
 int reverse=(half(edge+48)&2)!=0;
 int z0=half(edge+(reverse?6:4)),z1=half(edge+(reverse?4:6));
 int shade0=half(edge+(reverse?42:40)),shade1=half(edge+(reverse?40:42));
 if(width<=1||width>=32768||z0<0||z1<0||z0>=32768||z1>=32768)return -1;
 uint32_t q0=reciprocal[z0]<<8,q1=reciprocal[z1]<<8;
 uint32_t a0=multiply_shift(shade0,reciprocal[z0],8),a1=multiply_shift(shade1,reciprocal[z1],8);
 uint32_t dq=multiply_shift((int32_t)(q1-q0),reciprocal[width],24);
 uint32_t da=multiply_shift((int32_t)(a1-a0),reciprocal[width],24);
 uint32_t step=(uint32_t)(column-left),q=q0+step*dq,a=a0+step*da;
 int32_t index=(int32_t)sar(q,12);if(index<0||index>=32768)return -1;
 return (int16_t)(nfs_wall_restore_attribute(a,reciprocal[index])>>16);
}

/* 03000478..0300059C: default wall perspective and screen accumulators.
   Endpoint association reverses with prepared flag bit 2; X is already ordered.
   out: Q,U,top,bottom,dQ,dU,dTop,dBottom. Atomic on rejection. */
__declspec(dllexport) int nfs_wall_edge_accumulators(const uint8_t*edge,const uint32_t*reciprocal,uint32_t out[8]){
 if(!edge||!reciprocal||!out)return 0;
 int width=(int32_t)sar((uint32_t)(half(edge+2)+1),1)-(int32_t)sar((uint32_t)half(edge),1);
 int rev=(half(edge+48)&2)!=0;
 int z0=half(edge+(rev?6:4)),z1=half(edge+(rev?4:6));
 if(width<=1||width>=32768||z0<0||z1<0||z0>=32768||z1>=32768)return 0;
 uint32_t a[8],end[4];
 a[0]=reciprocal[z0]<<8;end[0]=reciprocal[z1]<<8;
 a[1]=multiply_shift((int32_t)wall_word(edge+(rev?20:16)),reciprocal[z0],8);
 end[1]=multiply_shift((int32_t)wall_word(edge+(rev?16:20)),reciprocal[z1],8);
 a[2]=(uint32_t)(int32_t)half(edge+(rev?10:8))<<14;
 end[2]=(uint32_t)(int32_t)half(edge+(rev?8:10))<<14;
 a[3]=(uint32_t)(int32_t)half(edge+(rev?14:12))<<14;
 end[3]=(uint32_t)(int32_t)half(edge+(rev?12:14))<<14;
 for(unsigned i=0;i<4;i++)a[i+4]=multiply_shift((int32_t)(end[i]-a[i]),reciprocal[width],24);
 memcpy(out,a,sizeof(a));return 1;
}

/* Default unshaded column plan. Each output record contains top14, U,
   vertical step, destination base, V, row count. No texture writes here. */
__declspec(dllexport) int nfs_wall_default_plan(const uint8_t*edge,const uint32_t*table,const unsigned*bounds,uint32_t framebuffer,uint32_t*out,unsigned*count){
 if(!edge||!table||!bounds||!out||!count)return 0;
 uint32_t a[8],records[120*6];int clip[4];unsigned n=0;
 if(!nfs_wall_edge_accumulators(edge,table,a)||!nfs_wall_clip_horizontal(half(edge),half(edge+2),bounds[0],bounds[1],clip))return 0;
 if(!clip[0]){*count=0;return 1;}if(clip[2]>120)return 0;
 for(unsigned j=0;j<4;j++)a[j]+=(uint32_t)clip[3]*a[j+4];
 for(int col=0;col<clip[2];col++){
  int index=(int32_t)sar(a[0],12);
  if(index>=0&&index<=32766){
   uint32_t rows=sar(a[3],14)-sar(a[2],14)+1,step,c[3];
   if(rows>=32768)return 0;
   if(!nfs_wall_texture_step(wall_word(edge+28),rows,table,0,&step)||!nfs_wall_clip_column(a[2],a[3],bounds[2],bounds[3],step,wall_word(edge+24)<<8,c))return 0;
   if((int32_t)c[1]>0){
    uint32_t*r=records+n*6;r[0]=c[0];r[1]=nfs_wall_restore_attribute(a[1],table[index]);r[2]=step;r[3]=framebuffer+(uint32_t)(clip[1]+col)*2;r[4]=c[2];r[5]=c[1];n++;
   }
  }
  for(unsigned j=0;j<4;j++)a[j]+=a[j+4];
 }
 memcpy(out,records,n*6*sizeof(uint32_t));*count=n;return 1;
}

/* Mode4 BG VRAM byte store duplicates the index into both aligned lanes.
   Wall index zero is skipped before issuing the hardware byte store. */
__declspec(dllexport) int nfs_wall_mode4_write(uint32_t destination,uint8_t index,uint32_t addresses[2],uint8_t values[2],unsigned*count){
 if(!addresses||!values||!count||destination<0x06000000u||destination>=0x06014000u)return 0;
 if(!index){*count=0;return 1;}
 addresses[0]=destination&~1u;addresses[1]=addresses[0]+1;values[0]=values[1]=index;*count=2;return 1;
}

/* Atomic owned unshaded column batch: 20 words/column = state17,dest,V,count.
   Source zero skips writes; nonzero duplicates both aligned mode4 lanes. */
static int wall_columns_write_impl(const uint32_t*columns,unsigned count,uint32_t texture_address,const uint8_t*texture,size_t texture_size,uint8_t*vram,size_t vram_size,unsigned*out_writes,const uint8_t*shade,size_t shade_bytes){
 if(!columns||!texture||!vram||!out_writes||count>512||vram_size!=0x18000||(shade?(shade_bytes!=4081||count!=1):shade_bytes!=0))return 0;
 uint8_t*next=malloc(vram_size);if(!next)return 0;memcpy(next,vram,vram_size);unsigned writes=0;int ok=0;
 for(unsigned col=0;col<count;col++){
  const uint32_t*r=columns+col*20;uint32_t source[320],dest[320];
  if(!nfs_wall_unshaded_addresses((const uint8_t*)r,r[17],r[18],r[19],source,dest))goto done;
  for(unsigned i=0;i<r[19];i++){
   if(source[i]<texture_address||(uint64_t)source[i]-texture_address>=texture_size)goto done;
   uint8_t value=texture[source[i]-texture_address];if(!value)continue;uint8_t mapped=shade?shade[(unsigned)value<<4]:value;
   uint32_t addresses[2];uint8_t values[2];unsigned n;
   if(!nfs_wall_mode4_write(dest[i],value,addresses,values,&n))goto done;
   for(unsigned j=0;j<n;j++)next[addresses[j]-0x06000000]=mapped;
   writes++;
  }
 }
 memcpy(vram,next,vram_size);*out_writes=writes;ok=1;
 done:free(next);return ok;
}

__declspec(dllexport) int nfs_wall_columns_write(const uint32_t*c,unsigned n,uint32_t a,const uint8_t*t,size_t z,uint8_t*v,size_t b,unsigned*w){return wall_columns_write_impl(c,n,a,t,z,v,b,w,NULL,0);}
/* Original03005320: skip zero BEFORE lookup; a nonzero source may write mapped
   index zero. One original span owns its exact effective4081byte shade lookup. */
__declspec(dllexport) int nfs_wall_columns_write_shaded(const uint32_t*c,unsigned n,uint32_t a,const uint8_t*t,size_t z,const uint8_t*l,size_t lz,uint8_t*v,size_t b,unsigned*w){return l&&wall_columns_write_impl(c,n,a,t,z,v,b,w,l,lz);}

/* Owned default wall dispatch: prepared geometry, clip bounds and raw
   material/framebuffer/descriptor produce complete texture columns. */
__declspec(dllexport) int nfs_wall_source_columns(const uint8_t *edge,const uint32_t *table,const unsigned *bounds,const uint8_t *material,const uint8_t *framebuffer,const uint8_t *descriptor,uint32_t *out,unsigned capacity,unsigned *out_count){
 if(!edge||!table||!bounds||!material||!framebuffer||!descriptor||!out||!out_count)return 0;
 uint32_t columns[720],result[120*20];unsigned count;
 unsigned shift=(uint16_t)half(material+36),height=(uint16_t)half(material+38);
 if(shift>10||height>1024||!nfs_wall_default_plan(edge,table,bounds,wall_word(framebuffer),columns,&count)||count>capacity)return 0;
 for(unsigned i=0;i<count;i++){
  uint32_t *r=result+i*20,*c=columns+i*6;memset(r,0,20*sizeof(*r));
  r[1]=c[0];r[2]=wall_word(framebuffer+12)>>1;r[3]=shift;r[4]=height;
  r[6]=(((uint16_t)half(descriptor+2)>>4)^1)&1;r[7]=height<<shift;
  r[9]=wall_word(material+40);r[11]=c[2];r[13]=c[1];r[16]=(1u<<(shift+15))-1;
  r[17]=c[3];r[18]=c[4];r[19]=c[5];
 }
 memcpy(out,result,count*20*sizeof(*out));*out_count=count;return 1;
}

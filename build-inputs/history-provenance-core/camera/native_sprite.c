#include "layer_snapshot.h"
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stddef.h>
/* Source rules: mgba software-obj.c SPRITE_XBASE/YBASE_16 and affine accumulators.
 Returns 1 sampled, 2 outside source bounds, 0 unsupported/invalid. */
__declspec(dllexport) int nfs_sprite_local(unsigned width,unsigned height,int x,int y,unsigned affine,unsigned doubled,unsigned flipx,unsigned flipy,const int16_t*matrix,int*out){
 if(!out||!width||!height||width>64||height>64||affine>1||doubled>1)return 0;
 int sx=x,sy=y;
 if(affine){
  if(!matrix)return 0;
  int dx=x-(int)(width<<doubled)/2,dy=y-(int)(height<<doubled)/2;
  int ax=matrix[0]*dx+matrix[1]*dy+(int)width*128,ay=matrix[2]*dx+matrix[3]*dy+(int)height*128;
  sx=ax>=0?ax/256:-((-ax+255)/256);sy=ay>=0?ay/256:-((-ay+255)/256);
 }else{if(flipx)sx=(int)width-x-1;if(flipy)sy=(int)height-y-1;}
 if(sx<0||sy<0||sx>=(int)width||sy>=(int)height)return 2;
 out[0]=sx;out[1]=sy;return 1;
}
__declspec(dllexport) int nfs_sprite_sample4(const uint8_t*obj,size_t bytes,unsigned width,unsigned tile,unsigned mapping,unsigned x,unsigned y,unsigned bank,uint32_t*out){
 if(!obj||!out||bytes!=0x4000||!width||width>64||tile<512||tile>1023||mapping>1||x>=width||y>=64||bank>15)return 0;
 unsigned base=tile*32,stride=mapping?width/2:128,mask=mapping?0x7ffe:0x3fe,hi=mapping?0:base&0x7c00;
 unsigned xb=(x&~7u)*4+((x>>1)&2),yb=(y&~7u)*stride+(y&7)*4+hi;
 unsigned address=(yb+((xb+base)&mask))&0x7ffe;
 if(address<0x4000||address+1>=0x8000)return 0;
 unsigned word=obj[address-0x4000]|((unsigned)obj[address-0x4000+1]<<8),index=(word>>((x&3)*4))&15;
 out[0]=address+0x06010000;out[1]=index;out[2]=bank*16+index;return 1;
}

/* Lower priority number wins; equal priority uses lower OAM index. */
__declspec(dllexport) int nfs_sprite_merge(const uint16_t*plane,unsigned priority,unsigned index,uint16_t*indices,uint16_t*order){
 if(!plane||!indices||!order||priority>3||index>=128)return 0;
 unsigned key=priority*128+index;
 for(unsigned i=0;i<38400;i++)if(plane[i]!=0xffff&&key<order[i]){indices[i]=plane[i];order[i]=(uint16_t)key;}
 return 1;
}

__declspec(dllexport) int nfs_palette_rgb(const uint16_t*source,unsigned count,uint32_t*out){
 if(!source||!out||count>65536)return 0;
 for(unsigned i=0;i<count;i++){
  unsigned v=source[i],r=v&31,g=(v>>5)&31,b=(v>>10)&31;
  out[i]=((r<<3)|(r>>2))|(((g<<3)|(g>>2))<<8)|(((b<<3)|(b>>2))<<16);
 }
 return 1;
}

/* Mode4 snapshot profile, no windows/mosaic or global color effect.
 Semitransparent OBJ blends with BG2/backdrop when selected as target2. */
static int scene_rgb4_pixels(const uint8_t*bg,const uint16_t*sprites,const uint16_t*order,const uint16_t*oam,const uint16_t*palette,const uint16_t*io,uint32_t*out,unsigned count){
 if(!bg||!sprites||!order||!oam||!palette||!io||!out||(io[0]&7)!=4||(io[0]&0xe000)||io[0x26]||(io[0x28]&0xc0))return 0;
 uint32_t colors[512];if(!nfs_palette_rgb(palette,512,colors))return 0;
 unsigned bp=io[6]&3,wa=io[0x29]&31,wb=(io[0x29]>>8)&31;if(wa>16)wa=16;if(wb>16)wb=16;
 for(unsigned i=0;i<count;i++){
  unsigned bi=bg[i],si=sprites[i];uint32_t color=colors[bi];
  if(si!=0xffff&&(bi==0||order[i]/128<=bp)){
   if(si<256||si>=512||order[i]>=512)return 0;
   unsigned index=order[i]%128,mode=(oam[index*4]>>10)&3;
   if(mode>1)return 0;
   uint32_t front=colors[si];
   if(mode==1&&(io[0x28]&(bi?(1u<<10):(1u<<13)))){
    color=0;for(unsigned channel=0;channel<3;channel++){
     unsigned shift=channel*8,component=(((front>>shift)&255)*wa+((colors[bi]>>shift)&255)*wb)/16;
     if(component>255)component=255;
     color|=component<<shift;
    }
   }else color=front;
  }
  out[i]=color;
 }
 return 1;
}

__declspec(dllexport) int nfs_scene_rgb4(const uint8_t*bg,const uint16_t*sprites,const uint16_t*order,const uint16_t*oam,const uint16_t*palette,const uint16_t*io,uint32_t*out){
 return scene_rgb4_pixels(bg,sprites,order,oam,palette,io,out,38400);
}

/* Decode all OAM entries in native code; caller owns output buffers.
   Supported race profile is 4-bit OBJ in mode4, normal/semitransparent. */
__declspec(dllexport) int nfs_sprite_oam4(const uint8_t*obj,const uint16_t*oam,unsigned display,uint16_t*indices,uint16_t*order){
 static const unsigned widths[3][4]={{8,16,32,64},{16,32,32,64},{8,8,16,32}};
 static const unsigned heights[3][4]={{8,16,32,64},{8,8,16,32},{16,32,32,64}};
 if(!obj||!oam||!indices||!order||(display&7)!=4)return 0;
 for(unsigned i=0;i<38400;i++){indices[i]=0xffff;order[i]=0xffff;}
 if(!(display&0x1000))return 1;
 for(unsigned index=0;index<128;index++){
  unsigned a=oam[index*4],b=oam[index*4+1],c=oam[index*4+2],affine=(a>>8)&1,shape=a>>14,size=b>>14;
  if((!affine&&(a&0x200))||shape==3)continue;
  unsigned width=widths[shape][size],height=heights[shape][size],doubled=affine&&((a&0x200)!=0);
  int ox=b&511,oy=a&255;if(ox>=256)ox-=512;if(oy>=160)oy-=256;
  unsigned bw=width<<doubled,bh=height<<doubled;
  if(ox+(int)bw<=0||ox>=240||oy+(int)bh<=0||oy>=160)continue;
  if((a&0x2000)||((a>>10)&3)>1||(a&0x1000))return 0;
  unsigned tile=c&1023;if(tile<512)continue;
  unsigned matrix=(b>>9)&31;int16_t m[4];for(unsigned k=0;k<4;k++)m[k]=(int16_t)oam[matrix*16+3+k*4];
  for(unsigned y=0;y<bh;y++)for(unsigned x=0;x<bw;x++){
   int px=ox+(int)x,py=oy+(int)y;if(px<0||px>=240||py<0||py>=160)continue;
   int xy[2];int status=nfs_sprite_local(width,height,(int)x,(int)y,affine,doubled,!!(b&4096),!!(b&8192),m,xy);
   if(status==2)continue;
   if(status!=1)return 0;
   uint32_t sample[3];if(!nfs_sprite_sample4(obj,0x4000,width,tile,!!(display&64),(unsigned)xy[0],(unsigned)xy[1],c>>12,sample))return 0;
   unsigned pos=(unsigned)py*240+(unsigned)px,key=((c>>10)&3)*128+index;
   if(sample[1]&&key<order[pos]){indices[pos]=(uint16_t)(256+sample[2]);order[pos]=(uint16_t)key;}
  }
 }
 return 1;
}

/* Compose an owned actual scanout with caller-owned native world/OBJ VRAM.
   Reject mismatched display bytes; commit output only after all rows validate. */
__declspec(dllexport) int nfs_native_snapshot_rgb4(const NFLayerSnapshot*s,uint32_t refresh,const uint8_t*native_vram,uint32_t*out){
 if(!s||!native_vram||!out)return 0;
 NFHardwareLayerRow*row=malloc(sizeof(*row));uint32_t*result=malloc(38400*sizeof(*result));
 uint32_t*rgb=malloc(240*sizeof(*rgb));uint16_t*indices=malloc(38400*sizeof(*indices)),*order=malloc(38400*sizeof(*order));
 int ok=0;uint8_t previous_oam[1024];unsigned previous_display=0;int have_sprites=0;
 if(!row||!result||!rgb||!indices||!order)goto done;
 for(unsigned y=0;y<160;y++){
  if(!nf_layer_snapshot_read(s,y,row)||row->refresh!=refresh||row->row!=y)goto done;
  uint16_t io[48],palette[512],oam[512];memcpy(io,row->registers,96);memcpy(palette,row->palette,1024);memcpy(oam,row->oam,1024);
  unsigned display=io[0],page=(display&16)?0xa000:0;
  if((display&0x80)||!(display&0x400)||row->affine[0]!=256||row->affine[1]||row->affine[2]||row->affine[3]!=256||row->affine[4]||row->affine[5]!=(int32_t)(y*256))goto done;
  if(memcmp(row->vram+page,native_vram+page,38400)||memcmp(row->vram+0x14000,native_vram+0x14000,0x4000))goto done;
  if(!have_sprites||previous_display!=display||memcmp(previous_oam,row->oam,1024)){
   if(!nfs_sprite_oam4(native_vram+0x14000,oam,display,indices,order))goto done;
   memcpy(previous_oam,row->oam,1024);previous_display=display;have_sprites=1;
  }
  if(!scene_rgb4_pixels(native_vram+page+y*240,indices+y*240,order+y*240,oam,palette,io,rgb,240))goto done;
  memcpy(result+y*240,rgb,240*sizeof(*result));
 }
 memcpy(out,result,38400*sizeof(*result));ok=1;
 done:free(row);free(result);free(rgb);free(indices);free(order);return ok;
}

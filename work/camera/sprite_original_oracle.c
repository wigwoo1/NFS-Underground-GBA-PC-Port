#include <stdint.h>
#include <string.h>
#include <mgba/internal/gba/renderers/video-software.h>
int GBAVideoSoftwareRendererPreprocessSprite(struct GBAVideoSoftwareRenderer*,struct GBAObj*,int,int);
__declspec(dllexport) int nfs_original_sprite_plane(const uint8_t*obj,const uint8_t*oam,unsigned index,unsigned dispcnt,uint16_t*out){
 if(!obj||!oam||!out||index>=128)return 0;
 struct GBAVideoSoftwareRenderer r;memset(&r,0,sizeof(r));
 uint16_t vram[0xc000];memset(vram,0,sizeof(vram));memcpy((uint8_t*)vram+0x14000,obj,0x4000);
 union GBAOAM owned;memcpy(&owned,oam,1024);r.d.vram=vram;r.d.oam=&owned;
 r.dispcnt=dispcnt;r.start=0;r.end=240;r.currentWindow.packed=0x3f;
 for(unsigned i=0;i<512;i++)r.normalPalette[i]=i;
 struct GBAObj* sprite=(struct GBAObj*)(owned.raw+index*4);
 for(int y=0;y<160;y++){
  for(int x=0;x<240;x++){r.spriteLayer[x]=FLAG_UNWRITTEN;r.row[x]=FLAG_UNWRITTEN;}
  r.spriteCyclesRemaining=100000;
  unsigned a=sprite->a,b=sprite->b,shape=a>>14,size=b>>14;
  int height=shape<3?GBAVideoObjSizes[shape*4+size][1]:0;
  if((a&256)&&(a&512))height*=2;
  int inY=(y-(a&255))&255;
  if(inY<height)GBAVideoSoftwareRendererPreprocessSprite(&r,sprite,index,y);
  for(int x=0;x<240;x++)out[y*240+x]=(r.spriteLayer[x]&FLAG_ORDER_MASK)==(FLAG_UNWRITTEN&FLAG_ORDER_MASK)?0xffff:(uint16_t)(r.spriteLayer[x]&0xffff);
 }
 return 1;
}


__declspec(dllexport) int nfs_original_sprite_combined(const uint8_t*obj,const uint8_t*oam,unsigned ignored,unsigned dispcnt,uint16_t*out){
 if(!obj||!oam||!out||ignored!=0)return 0;
 struct GBAVideoSoftwareRenderer r;memset(&r,0,sizeof(r));
 uint16_t vram[0xc000];memset(vram,0,sizeof(vram));memcpy((uint8_t*)vram+0x14000,obj,0x4000);
 union GBAOAM owned;memcpy(&owned,oam,1024);r.d.vram=vram;r.d.oam=&owned;
 r.dispcnt=dispcnt;r.start=0;r.end=240;r.currentWindow.packed=0x3f;
 for(unsigned i=0;i<512;i++)r.normalPalette[i]=i;

 for(int y=0;y<160;y++){
  for(int x=0;x<240;x++){r.spriteLayer[x]=FLAG_UNWRITTEN;r.row[x]=FLAG_UNWRITTEN;}
  r.spriteCyclesRemaining=100000;
  for(unsigned index=0;index<128;index++){
  struct GBAObj* sprite=(struct GBAObj*)(owned.raw+index*4);
  unsigned a=sprite->a,b=sprite->b,shape=a>>14,size=b>>14;
  int height=shape<3?GBAVideoObjSizes[shape*4+size][1]:0;
  if((a&256)&&(a&512))height*=2;
  int inY=(y-(a&255))&255;
  if(shape<3&&!((a&512)&&!(a&256))&&inY<height)GBAVideoSoftwareRendererPreprocessSprite(&r,sprite,index,y);
  }
  for(int x=0;x<240;x++)out[y*240+x]=(r.spriteLayer[x]&FLAG_ORDER_MASK)==(FLAG_UNWRITTEN&FLAG_ORDER_MASK)?0xffff:(uint16_t)(r.spriteLayer[x]&0xffff);
 }
 return 1;
}


__declspec(dllexport) int nfs_original_palette_rgb(const uint16_t*source,unsigned count,uint32_t*out){
 if(!source||!out||count>65536)return 0;
 for(unsigned i=0;i<count;i++)out[i]=mColorFrom555(source[i]);return 1;
}

/* Static snapshot renderer: not a scanline-history or live emulator oracle. */
__declspec(dllexport) int nfs_original_snapshot_rgb(const uint8_t*bg,const uint8_t*obj,const uint8_t*oam,const uint16_t*palette,const uint16_t*io,uint32_t*out){
 if(!bg||!obj||!oam||!palette||!io||!out)return 0;
 struct GBAVideoSoftwareRenderer r;memset(&r,0,sizeof(r));
 uint16_t vram[0xc000];memset(vram,0,sizeof(vram));unsigned page=(io[0]&16)?0xa000:0;
 memcpy((uint8_t*)vram+page,bg,38400);memcpy((uint8_t*)vram+0x14000,obj,0x4000);
 union GBAOAM owned;memcpy(&owned,oam,1024);uint16_t palettes[512];memcpy(palettes,palette,1024);
 GBAVideoSoftwareRendererCreate(&r);r.d.vram=vram;r.d.oam=&owned;r.d.palette=palettes;r.outputBuffer=(color_t*)out;r.outputBufferStride=240;r.d.init(&r.d);
 for(unsigned i=0;i<512;i++)r.d.writePalette(&r.d,i*2,palette[i]);
 for(unsigned i=0;i<=0x2a;i++)if(i!=2&&i!=3&&i!=0x27)r.d.writeVideoRegister(&r.d,i*2,io[i]);
 for(unsigned i=0;i<128;i++)r.d.writeOAM(&r.d,i*8);
 for(int y=0;y<160;y++)r.d.drawScanline(&r.d,y);
 for(unsigned i=0;i<38400;i++)out[i]&=0x00ffffff;
 r.d.deinit(&r.d);return 1;
}

#include <stdint.h>
#include <string.h>
static uint32_t u32(const uint8_t*p){uint32_t v;memcpy(&v,p,4);return v;}
static uint16_t u16(const uint8_t*p){return p[0]|(uint16_t)p[1]<<8;}
static void put16(uint8_t*p,uint32_t v){p[0]=(uint8_t)v;p[1]=(uint8_t)(v>>8);}
static int32_t sar14(uint32_t v){return (int32_t)((v>>14)|((v&0x80000000u)?0xfffc0000u:0));}
/* Recovered 03000D48 memory contract. Source stride 68, destination stride 52.
   The optional offset table is indexed by source halfword +42; FFFF = absent.
   Caller validates buffers and table indices. Returns zero on far-depth cull.
   This reproduces the integer transform only; no temporal smoothing. */
__declspec(dllexport) int nfs_camera_transform(const uint8_t*camera,const uint8_t*source,const uint8_t*offsets,uint8_t*dest,unsigned count){
 for(unsigned i=0;i<count;i++){
  const uint8_t*s=source+i*68;uint8_t*d=dest+i*52;
  uint32_t x=u32(s)+u32(camera+36),z=u32(s+4)+u32(camera+44);
  uint32_t y1=u32(camera+40),y2=y1;unsigned index=u16(s+42);
  if(index!=65535){const uint8_t*o=offsets+index*32;x+=(int16_t)u16(o);z+=(int16_t)u16(o+2);y1+=(int16_t)u16(o+8);y2+=(int16_t)u16(o+10);}
  int32_t cx=sar14(z*u32(camera+24)+x*u32(camera));
  int32_t cz=sar14(z*u32(camera+32)+x*u32(camera+8));
  put16(d,cx);put16(d+8,u16(s+8)+y1);put16(d+12,u16(s+10)+y2);
  put16(d+10,u16(s+12)+y1);put16(d+14,u16(s+14)+y2);
  if(cz>0x5fff)return 0;
  put16(d+4,cz);put16(d+40,(unsigned)s[60]<<8);put16(d+42,(unsigned)s[61]<<8);
 }
 for(unsigned i=0;i<count;i++){
  uint8_t*previous=dest+((i+count-1)%count)*52;uint8_t*current=dest+i*52;
  put16(previous+2,u16(current));put16(previous+6,u16(current+4));
 }
 return 1;
}

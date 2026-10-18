#include <stdint.h>
#include <string.h>
static uint16_t get16(const uint8_t*p){return p[0]|(uint16_t)p[1]<<8;}
static uint32_t get32(const uint8_t*p){uint32_t v;memcpy(&v,p,4);return v;}
static void set16(uint8_t*p,uint32_t v){p[0]=(uint8_t)v;p[1]=(uint8_t)(v>>8);}
static void set32(uint8_t*p,uint32_t v){memcpy(p,&v,4);}
static int32_t asr(uint32_t v,unsigned bits){return (int32_t)((v>>bits)|((v&0x80000000u)?(~0u<<(32-bits)):0));}
/* ARM 030052A4: signed difference times unsigned Q24 fraction.
   Return the low 32 bits of the shifted full product, including wrap. */
static uint32_t fraction(uint32_t difference,uint32_t t){
 int64_t product=(int64_t)(int32_t)difference*(int64_t)t;
 return (uint32_t)((uint64_t)product>>24);
}
/* ARM 03001638: clip one endpoint in a 52-byte camera-space edge.
   The caller sets depth separately. This preserves all unrelated bytes.
   first!=0 moves endpoint 0 toward 1; otherwise endpoint 1 toward 0.
   flags bit 0x80 enables the two extra 32-bit attributes. */
__declspec(dllexport) void nfs_camera_clip_edge(uint8_t*edge,int first,uint32_t t,unsigned flags){
 static const unsigned pairs16[][2]={{0,2},{40,42},{8,10},{12,14}};
 static const unsigned pairs32[][2]={{16,20},{24,32},{28,36}};
 for(unsigned i=0;i<4;i++){
  unsigned a=pairs16[i][0],b=pairs16[i][1];
  uint32_t delta=fraction((uint32_t)(int32_t)(int16_t)get16(edge+b)-(uint32_t)(int32_t)(int16_t)get16(edge+a),t);
  set16(edge+(first?a:b),first?get16(edge+a)+delta:get16(edge+b)-delta);
 }
 for(unsigned i=0;i<((flags&128)?3u:1u);i++){
  unsigned a=pairs32[i][0],b=pairs32[i][1];
  uint32_t delta=fraction(get32(edge+b)-get32(edge+a),t);
  set32(edge+(first?a:b),first?get32(edge+a)+delta:get32(edge+b)-delta);
 }
 set16(edge+48,get16(edge+48)|(first?8:16));
}
/* Exact horizontal projection block 03001CB4..03001D24.
   Depth must already be clipped to the valid reciprocal-table range.
   reciprocal points at the game's table, not a newly approximated divide.
   Writes projected endpoint X into the same record as the original. */
__declspec(dllexport) void nfs_camera_project_x(uint8_t*edge,uint32_t scale,int32_t center,const uint32_t*reciprocal){
 for(unsigned i=0;i<2;i++){
  int32_t depth=(int16_t)get16(edge+4+i*2);
  int32_t factor=asr(scale*reciprocal[depth],7);
  int32_t coordinate=asr((uint32_t)(int32_t)(int16_t)get16(edge+i*2),1);
  uint32_t product=(uint32_t)coordinate*(uint32_t)factor;
  set16(edge+i*2,(uint32_t)center+(uint32_t)asr(product,16));
 }
}
/* Exact vertical edge projection block 03001F30..03001FA4.
   Uses the same endpoint depths and projection scale as horizontal X. */
__declspec(dllexport) void nfs_camera_project_heights(uint8_t*edge,uint32_t scale,int32_t center,const uint32_t*reciprocal){
 for(unsigned i=0;i<4;i++){
  int32_t depth=(int16_t)get16(edge+4+(i&1)*2);
  int32_t factor=asr(scale*reciprocal[depth],7);
  int32_t coordinate=asr((uint32_t)(int32_t)(int16_t)get16(edge+8+i*2),1);
  set16(edge+8+i*2,(uint32_t)center+(uint32_t)asr((uint32_t)coordinate*(uint32_t)factor,16));
 }
}

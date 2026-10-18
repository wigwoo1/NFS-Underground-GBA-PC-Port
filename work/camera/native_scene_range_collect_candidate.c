#include <stdint.h>
#include <stddef.h>
#include <string.h>
typedef struct {uint32_t address,source,offset,length;} Range;
static uint32_t u32(const uint8_t*p){uint32_t v;memcpy(&v,p,4);return v;}
static uint16_t u16(const uint8_t*p){uint16_t v;memcpy(&v,p,2);return v;}
static int emit(Range*out,size_t cap,size_t*count,uint64_t address,uint32_t source,size_t offset,size_t length){
 if(!length)return 1;
 if(address+length>UINT64_C(0x100000000)||offset>UINT32_MAX||length>UINT32_MAX||*count>=32768)return 0;
 if(out){if(*count>=cap)return 0;out[*count]=(Range){(uint32_t)address,source,(uint32_t)offset,(uint32_t)length};}
 ++*count;return 1;
}
static int collect(const uint8_t*c,const uint8_t*g,size_t gn,const uint8_t*o,size_t on,const uint8_t*m,size_t mn,Range*out,size_t cap,size_t*count){
 #define E(a,s,p,n) if(!emit(out,cap,count,a,s,p,n))return 0
 E(u32(c+84),0,256,48);E(u32(c+80),0,304,64);
 size_t at=0,offset=0;
 while(at<gn){
 if(gn-at<64)return 0;
 uint32_t n=u32(g+at+4);size_t ring=at+64;
 if(n>(gn-ring)/68||n>(on-offset)/32)return 0;
 E(u32(g+at+8),1,at+16,48);E(u32(g+at+12),1,ring,(size_t)n*68);
 for(size_t i=0;i<n;i++){uint16_t index=u16(g+ring+i*68+42);if(index!=65535){E((uint64_t)u32(c+24)+(uint64_t)index*32,2,offset+i*32,32);}}
 at=ring+(size_t)n*68;offset+=(size_t)n*32;
 }
 if(offset!=on)return 0;
 at=0;
 while(at<mn){
 if(mn-at<120)return 0;
 uint64_t base=(uint64_t)u32(c+32)+(uint64_t)u32(m+at+12)*32;uint16_t phase=u16(m+at+82);
 E(base,3,at+48,32);E((uint64_t)u32(c+72)+(uint64_t)u16(m+at+48)*8,3,at+80,8);E(base+(uint64_t)phase*32,3,at+88,32);
 size_t extra=u32(m+at+36)==1?u32(m+at+32):0;
 if(extra>mn-at-120)return 0;at+=120+extra;
 }
 return 1;
}
__declspec(dllexport) int nf_scene_ranges(const uint8_t*c,size_t cn,const uint8_t*g,size_t gn,const uint8_t*o,size_t on,const uint8_t*m,size_t mn,Range*out,size_t cap){
 if(!c||!g||!o||!m||cn<368||gn>16777216||on>16777216||mn>16777216||cap>32768)return -1;
 size_t count=0;if(!collect(c,g,gn,o,on,m,mn,NULL,0,&count))return -1;
 if(!out)return (int)count;if(count>cap)return -1;
 size_t written=0;if(!collect(c,g,gn,o,on,m,mn,out,cap,&written))return -1;
 return (int)written;
}

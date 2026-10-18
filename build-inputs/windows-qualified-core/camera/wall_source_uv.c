#include <stdint.h>
#include <string.h>
static uint16_t half(const uint8_t*p){uint16_t v;memcpy(&v,p,2);return v;}
static uint32_t word(const uint8_t*p){uint32_t v;memcpy(&v,p,4);return v;}
static int32_t signed_half(int16_t v){return v>=0?v/2:-((-(int32_t)v+1)/2);}
/* Raw source edge UV fields before near clipping and perspective scaling. */
__declspec(dllexport) int nf_wall_source_uv(const uint8_t source[68],const uint8_t animation[8],unsigned shift,unsigned flags,uint32_t out[6]){
 if(!source||!animation||!out||shift>10||flags>65535)return 0;
 uint32_t a=((uint32_t)half(source+40)<<7)+(uint32_t)signed_half((int16_t)half(animation+4));
 /* The original ARM LSL uses the low eight bits of the register shift; for
    exponent zero, (shift-1) is 0xffffffff and therefore contributes zero. */
 uint32_t span=shift?((uint32_t)half(source+64)<<(shift-1)):0u;
 uint32_t b=a+span;
 if(flags&2u){uint32_t t=a;a=b;b=t;}
 uint32_t offset=(uint32_t)signed_half((int16_t)half(animation+6));
 uint32_t result[6]={a,b,word(source+16)+offset,word(source+24)+offset,word(source+20)+offset,word(source+28)+offset};
 memcpy(out,result,sizeof(result));return 1;
}

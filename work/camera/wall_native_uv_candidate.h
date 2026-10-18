/* Raw per-edge base/span fields normalized for continuous native projection. */
#include <stdint.h>
extern int nf_wall_source_uv(const uint8_t*,const uint8_t*,unsigned,unsigned,uint32_t*);
__declspec(dllexport) int nf_wall_native_uv(const uint8_t*s,const uint8_t*a,unsigned shift,unsigned height,unsigned flags,double out[8]){
 if(!s||!a||!out||shift>10||!height||height>1024||flags>65535)return 0;
 uint32_t raw[6];if(!nf_wall_source_uv(s,a,shift,flags,raw))return 0;
 double w=128.0*(1u<<shift),h=128.0*height;
 double l=(int32_t)raw[0]/w,r=(int32_t)raw[1]/w,lt=(int32_t)raw[2]/h,rt=(int32_t)raw[4]/h;
 double result[8]={l,lt,r,rt,r,rt+(int32_t)raw[5]/h,l,lt+(int32_t)raw[3]/h};
 for(unsigned i=0;i<8;i++)out[i]=result[i];return 1;
}

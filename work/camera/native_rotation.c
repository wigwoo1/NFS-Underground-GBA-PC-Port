#include <stdint.h>
#include <string.h>
static int32_t asr14(uint32_t v){return (int32_t)((v>>14)|((v&0x80000000u)?0xfffc0000u:0));}
/* Thumb 0806DB14. Column-major Q14 rotation output = right * left.
   Translation is component-wise addition, NOT general affine composition.
   The caller supplies already prepared translations. Exact 32-bit wrapping.
   Supports disjoint buffers and output equal to either input. */
__declspec(dllexport) void nfs_rotation_combine(const uint8_t*left,const uint8_t*right,uint8_t*out){
 uint32_t a[12],b[12],result[12];memcpy(a,left,48);memcpy(b,right,48);
 for(unsigned column=0;column<3;column++)for(unsigned row=0;row<3;row++){
  uint32_t sum=0;
  for(unsigned k=0;k<3;k++)sum+=a[column*3+k]*b[k*3+row];
  result[column*3+row]=(uint32_t)asr14(sum);
 }
 for(unsigned i=9;i<12;i++)result[i]=a[i]+b[i];
 memcpy(out,result,48);
}

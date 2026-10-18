#include <stdint.h>
#include <stddef.h>
static int32_t q14(uint32_t v){int64_t s=v<0x80000000u?(int64_t)v:(int64_t)v-0x100000000ll;return (int32_t)(s>=0?s/16384:-((-s+16383)/16384));}
__declspec(dllexport) int nf_portal_transform_batch(const int32_t *points,size_t n,const int32_t *a,const int32_t *b,int32_t *out){
 if(!points||!a||!b||!out||!n||n>32)return 0;
 for(size_t i=0;i<n;i++)for(size_t j=0;j<2;j++){
 const int32_t *m=j?b:a;uint32_t x=(uint32_t)points[i*2]+(uint32_t)m[9],z=(uint32_t)points[i*2+1]+(uint32_t)m[11];
 out[i*4+j*2]=q14(x*(uint32_t)m[0]+z*(uint32_t)m[6]);
 out[i*4+j*2+1]=q14(x*(uint32_t)m[2]+z*(uint32_t)m[8]);
 }return 1;
}

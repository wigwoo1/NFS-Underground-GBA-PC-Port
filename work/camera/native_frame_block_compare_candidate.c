#include <stdint.h>
#include <stddef.h>
#include <string.h>
__declspec(dllexport) int nf_frame_block_compare(const void*a,const void*b,size_t n,size_t block,uint8_t*out,size_t capacity){
 if(!a||!b||!out||!n||n>16*1024*1024||block<1024||block>262144)return 37;
 size_t count=(n+block-1)/block;if(capacity<count)return 37;
 for(size_t i=0;i<count;i++){size_t at=i*block,size=n-at;if(size>block)size=block;out[i]=(uint8_t)(memcmp((const char*)a+at,(const char*)b+at,size)!=0);}
 return (int)count;
}

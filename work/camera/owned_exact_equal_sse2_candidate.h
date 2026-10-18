#include <stdint.h>
#include <stddef.h>
#include <emmintrin.h>
/* Exact bounded equality; no bytes outside [0,n), no retained ownership. */
static int owned_exact_equal_sse2(const void*left,const void*right,size_t n){
 const uint8_t*a=left,*b=right;
 while(n>=16){__m128i x=_mm_loadu_si128((const __m128i*)a),y=_mm_loadu_si128((const __m128i*)b);if(_mm_movemask_epi8(_mm_cmpeq_epi8(x,y))!=65535)return 0;a+=16;b+=16;n-=16;}
 while(n--){if(*a++!=*b++)return 0;}return 1;
}

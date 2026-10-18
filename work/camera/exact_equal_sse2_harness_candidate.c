#include <string.h>
#include "owned_exact_equal_sse2_candidate.h"
__declspec(dllexport) int equal_sse2(const void*a,const void*b,size_t n){return owned_exact_equal_sse2(a,b,n);}
__declspec(dllexport) int equal_original(const void*a,const void*b,size_t n){return !memcmp(a,b,n);}

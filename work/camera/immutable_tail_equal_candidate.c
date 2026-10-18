#include <stddef.h>
#include <string.h>
__declspec(dllexport) int nf_immutable_tail_equal(const void*a,const void*b,size_t n){if(!a||!b||n>64u*1024u*1024u)return -1;return memcmp(a,b,n)==0;}

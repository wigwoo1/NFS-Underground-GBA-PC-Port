#include <stdint.h>
#include <stddef.h>
#include <string.h>
__declspec(dllexport) int nf_shared_payload_copy(void *destination,size_t capacity,const void *source,size_t size){
 if(!destination||!source||!size||size>capacity||capacity>64u*1024u*1024u)return 37;
 uintptr_t d=(uintptr_t)destination,s=(uintptr_t)source;
 if(d>UINTPTR_MAX-size||s>UINTPTR_MAX-size)return 38;
 if(d<s+size&&s<d+size)return 39;
 memcpy(destination,source,size);return 1;
}

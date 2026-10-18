#include <stdint.h>
#include <stddef.h>
#include <string.h>
typedef struct { uint32_t address; size_t size; const unsigned char *data; } Range;
typedef struct { const unsigned char *rom; size_t rom_size; const Range *ranges; size_t count; } Reader;
__declspec(dllexport) int nf_owned_sparse_read(void *context,uint32_t address,void *output,size_t size){
 const Reader *r=(const Reader*)context;
 uint64_t end=(uint64_t)address+size,covered=address;
 size_t first=0,last=r->count;
 if(size>0x100000 || end>0x100000000ULL || (!output && size))return 0;
 if(!size)return 1;
 while(first<last){size_t middle=first+(last-first)/2;if(r->ranges[middle].address<=address)first=middle+1;else last=middle;}
 size_t index=first?first-1:0;
 int rom_backed=address>=0x08000000 && end-0x08000000<=r->rom_size;
 /* Validate coverage before any output mutation. */
 if(!rom_backed){
  for(size_t i=index;i<r->count && covered<end;i++){
   const Range *x=&r->ranges[i];uint64_t stop=(uint64_t)x->address+x->size;
   if(x->address>covered)break;
   if(stop>covered)covered=stop;
  }
  if(covered<end)return 0;
 }
 if(rom_backed)memcpy(output,r->rom+(address-0x08000000),size);
 for(size_t i=index;i<r->count;i++){
  const Range *x=&r->ranges[i];uint64_t stop=(uint64_t)x->address+x->size;
  if(x->address>=end)break;
  uint64_t lo=address>x->address?address:x->address,hi=end<stop?end:stop;
  if(lo<hi)memcpy((unsigned char*)output+(lo-address),x->data+(lo-x->address),(size_t)(hi-lo));
 }
 return 1;
}

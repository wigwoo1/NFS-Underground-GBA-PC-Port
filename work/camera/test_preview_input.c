#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <assert.h>
#include "preview_input.h"
int main(void){
 uint8_t source[]={1,2,3,4,5},out[6]={0};preview_memory[0]=(PreviewMemory){source,sizeof(source)};
 PreviewInput*in=preview_input(0,"does-not-exist");assert(in&&!preview_end(in));
 assert(read_bytes(in,out,3)&&!memcmp(out,source,3)&&in->position==3);
 memset(out,0xad,sizeof(out));assert(!read_bytes(in,out,3)&&in->position==3&&out[0]==0xad);
 assert(!read_bytes(in,out,SIZE_MAX)&&in->position==3);
 assert(read_bytes(in,out,2)&&out[0]==4&&out[1]==5&&preview_end(in));
 assert(!read_bytes(in,out,1)&&preview_end(in));preview_close(in);
 in=preview_input(0,"does-not-exist");assert(in&&read_bytes(in,out,5)&&!memcmp(out,source,5));preview_close(in);
 assert(source[0]==1&&source[4]==5);puts("PASS: bounded borrowed reads, unchanged failed read, exact end, reopen, source lifetime");return 0;
}

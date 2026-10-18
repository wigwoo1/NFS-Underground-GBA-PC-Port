#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "hash_region.h"

static uint32_t framebuffer[240u*160u];

int main(void){
 for(unsigned i=0;i<240u*160u;i++)framebuffer[i]=i*2654435761u+0x5a17u;
 const unsigned x=70,y=12,width=21,height=19;
 uint32_t original=nf_hash_u32_region(framebuffer,240u,160u,x,y,width,height);
 if(!original){fprintf(stderr,"valid region unexpectedly hashed to zero\n");return 1;}
 framebuffer[0]^=0x80000000u;
 if(nf_hash_u32_region(framebuffer,240u,160u,x,y,width,height)!=original){fprintf(stderr,"pixels outside region affected hash\n");return 2;}
 framebuffer[y*240u+x]^=1u;
 if(nf_hash_u32_region(framebuffer,240u,160u,x,y,width,height)==original){fprintf(stderr,"pixel change inside region was missed\n");return 3;}
 if(nf_hash_u32_region(NULL,240,160,0,0,1,1)||nf_hash_u32_region(framebuffer,240,160,240,0,1,1)||nf_hash_u32_region(framebuffer,240,160,0,160,1,1)||nf_hash_u32_region(framebuffer,240,160,0,0,0,1)||nf_hash_u32_region(framebuffer,240,160,0,0,241,1)){
  fprintf(stderr,"invalid region bounds were accepted\n");return 4;
 }
 puts("source-region hash bounds and pixel sensitivity: PASS");return 0;
}

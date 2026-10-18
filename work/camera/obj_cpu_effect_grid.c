#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "obj_tile.h"
int main(int argc,char**argv){if(argc!=3)return 1;uint32_t input[1024][8];FILE*f=fopen(argv[1],"rb");if(!f)return 2;if(fread(input,sizeof(input),1,f)!=1)return 3;fclose(f);uint32_t*out=malloc(3840u*2160*4);if(!out)return 4;
 for(unsigned y=0;y<2160;y++)for(unsigned x=0;x<3840;x++){unsigned gy=2159-y;uint32_t bg=0xff000000u|(x&255)|((gy&255)<<8)|(((x/16+gy/16)&255)<<16);unsigned index=(y/120)*60+x/64;uint32_t result=bg;if(index<1024){uint32_t*a=input[index];unsigned lx=(x%64)/8,ly=(y%120)/15;uint32_t obj=(lx+ly)%3==0?0:a[0];result=nf_obj_bg_backdrop_pixel(obj,a[1],bg,a[3],a[4],a[5],a[6],a[7]);}out[y*3840+x]=result;}
 f=fopen(argv[2],"wb");if(!f)return 5;int ok=fwrite(out,4,3840u*2160,f)==3840u*2160;fclose(f);free(out);return ok?0:6;}

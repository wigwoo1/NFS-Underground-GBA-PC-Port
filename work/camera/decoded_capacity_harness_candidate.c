#include <stdint.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned GLuint;
static uint8_t *output;static size_t output_bytes;
static int source_texture_own(unsigned w,unsigned h,const uint8_t*p){size_t n=(size_t)w*h*4;if(n>output_bytes)return 0;memcpy(output,p,n);return 1;}
#include "owned_decoded_capacity_candidate.h"
__declspec(dllexport) int decode(unsigned w,unsigned h,unsigned stride,const uint8_t*src,const uint8_t*pal,unsigned transparent,uint8_t*out,size_t bytes){output=out;output_bytes=bytes;int r=owned_indexed_texture(w,h,stride,src,pal,transparent);output=NULL;output_bytes=0;return r;}
__declspec(dllexport) void clear(void){owned_decoded_clear();}

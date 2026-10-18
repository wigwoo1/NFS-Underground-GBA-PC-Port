#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#define NF_PREVIEW_TEXTURE_BUDGET 1024
#include "preview_resources.h"
int main(void){
 (void)preview_keep_context;assert(!preview_context_open());assert(!preview_context_open()&&preview_contexts==1);preview_generation++;
 uint8_t pixels[64];GLuint first=0;
 for(unsigned i=0;i<16;i++){memset(pixels,(int)i,64);GLuint texture=preview_texture(4,4,pixels);assert(texture);if(!i)first=texture;}
 assert(preview_texture_bytes==1024&&preview_uploads==16);
 memset(pixels,0,64);assert(preview_texture(4,4,pixels)==first&&preview_hits==1);
 memset(pixels,17,64);assert(!preview_texture(4,4,pixels));assert(preview_uploads==16);
 preview_generation++;memset(pixels,0,64);assert(preview_texture(4,4,pixels)==first);
 for(unsigned i=32;i<47;i++){memset(pixels,(int)i,64);assert(preview_texture(4,4,pixels));assert(preview_texture_bytes==1024);}
 memset(pixels,48,64);assert(!preview_texture(4,4,pixels));
 glBindTexture(GL_TEXTURE_2D,first);memset(pixels,0xad,64);glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_UNSIGNED_BYTE,pixels);
 for(unsigned i=0;i<64;i++)assert(pixels[i]==0);
 assert(glGetError()==GL_NO_ERROR);preview_shutdown();assert(!preview_context&&preview_texture_bytes==0);
 /* Recently used low-slot texture must survive an older high-slot entry.
    All textures referenced in this generation remain protected. */
 assert(!preview_context_open());preview_generation++;
 GLuint resident[16];for(unsigned i=0;i<16;i++){memset(pixels,(int)i,64);resident[i]=preview_texture(4,4,pixels);assert(resident[i]);}
 preview_generation++;memset(pixels,0,64);assert(preview_texture(4,4,pixels)==resident[0]);
 preview_generation++;for(unsigned i=2;i<16;i++){memset(pixels,(int)i,64);assert(preview_texture(4,4,pixels)==resident[i]);}
 memset(pixels,99,64);assert(preview_texture(4,4,pixels));unsigned uploads=preview_uploads;
 memset(pixels,0,64);assert(preview_texture(4,4,pixels)==resident[0]&&preview_uploads==uploads);
 memset(pixels,100,64);assert(!preview_texture(4,4,pixels));
 preview_shutdown();assert(!preview_context&&preview_texture_bytes==0);
 puts("PASS: context, deduplication, budget rejection, oldest-generation eviction, recent and active textures preserved, shutdown");return 0;
}

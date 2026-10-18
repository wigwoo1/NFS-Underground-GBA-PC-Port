#include "nfsug_scene_owner.h"
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"scene check failed at line %d\n",__LINE__);return 1;}}while(0)
static uint32_t word(const uint8_t*p){uint32_t v;memcpy(&v,p,4);return v;}
static int filled(const uint8_t*p,size_t n,uint8_t v){for(size_t i=0;i<n;i++)if(p[i]!=v)return 0;return 1;}
int main(int argc,char**argv){
 CHECK(argc>1);unsigned sections=0,rejected=0;
 uint64_t sentinel[12];for(unsigned i=0;i<12;i++)sentinel[i]=77;
 CHECK(!nf_android_scene_info(NULL,sentinel));for(unsigned i=0;i<12;i++)CHECK(sentinel[i]==77);
 for(int index=1;index<argc;index++){
  FILE*f=fopen(argv[index],"rb");CHECK(f);CHECK(!fseek(f,0,SEEK_END));long length=ftell(f);CHECK(length>=92&&length<=256*1024*1024);rewind(f);
  size_t n=(size_t)length;uint8_t*raw=malloc(n),*expected=malloc(n),*out=malloc(n);CHECK(raw&&expected&&out);
  CHECK(fread(raw,1,n,f)==n);fclose(f);memcpy(expected,raw,n);
  void*scene=nf_android_scene_open(raw,n);CHECK(scene);memset(raw,0,n);
  uint64_t info[12];CHECK(nf_android_scene_info(scene,info));
  CHECK(info[0]==word(expected+16)&&info[1]==word(expected+20)&&info[2]==word(expected+24)&&info[3]==word(expected+28)&&info[4]==n);
  CHECK(nf_android_scene_copy(scene,out,n)==n&&!memcmp(out,expected,n));
  memset(out,165,n);CHECK(!nf_android_scene_copy(scene,out,n-1)&&filled(out,n,165));
  for(unsigned i=0;i<5;i++){
   size_t offset=word(expected+36+i*12),size=word(expected+40+i*12);
   CHECK(offset<=n&&size<=n-offset&&info[7+i]==size);
   CHECK(nf_android_scene_section(scene,i,out,n)==size&&!memcmp(out,expected+offset,size));
   memset(out,165,n);CHECK(!nf_android_scene_section(scene,i,out,size-1)&&filled(out,n,165));sections++;
  }
  CHECK(!nf_android_scene_section(scene,5,out,n));nf_android_scene_close(scene);
  CHECK(!nf_android_scene_open(expected,n-1));rejected++;
  uint32_t bad=0xffffffff;for(unsigned i=0;i<4;i++){size_t at=(size_t[]){0,8,12,36}[i];memcpy(raw,expected,n);memcpy(raw+at,&bad,4);CHECK(!nf_android_scene_open(raw,n));rejected++;}
  free(raw);free(expected);free(out);
 }
 printf("{\"result\":\"PASS_ANDROID_NATIVE_SCENE_OWNERSHIP\",\"real_packets\":%d,\"section_copies\":%u,\"malformed_rejected\":%u,\"input_poisoning_preserved\":true,\"short_buffer_atomic\":true,\"gpu_rendering\":false,\"live_capture\":false}\n",argc-1,sections,rejected);
 return 0;
}

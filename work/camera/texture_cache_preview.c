#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
int main(void){
 int result=preview_context_open();if(result)return result;
 uint8_t data[261],expected[260],actual[260];unsigned checks=0;
 for(unsigned width=1;width<=65;width+=2){
  preview_generation++;size_t bytes=width*4;
  for(unsigned i=0;i<bytes;i++)data[i+1]=(uint8_t)(i*71+width);
  memcpy(expected,data+1,bytes);GLuint first=preview_texture(width,1,data+1);
  if(!first||preview_texture(width,1,data+1)!=first)return 50;
  for(unsigned byte=0;byte<bytes;byte++){
   preview_generation++;data[byte+1]^=1;
   GLuint changed=preview_texture(width,1,data+1);if(!changed)return 51;
   glBindTexture(GL_TEXTURE_2D,changed);glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_UNSIGNED_BYTE,actual);
   if(memcmp(actual,data+1,bytes))return 52;
   data[byte+1]^=1;
   first=preview_texture(width,1,data+1);if(!first)return 53;
   glBindTexture(GL_TEXTURE_2D,first);glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_UNSIGNED_BYTE,actual);
   if(memcmp(actual,expected,bytes))return 54;
   checks++;
  }
 }
 if(glGetError()!=GL_NO_ERROR)return 55;
 preview_shutdown();printf("PASS texture_cache changed_bytes=%u widths=33 unaligned=1 tail4=1 exact_gpu_content=1\n",checks);return 0;
}


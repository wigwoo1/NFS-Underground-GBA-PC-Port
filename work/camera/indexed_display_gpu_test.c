#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
int main(void){
 if(preview_context_open())return 1;preview_generation++;preview_zero_valid=preview_display_palette_valid=1;
 uint8_t indices[256],rgba[1024]={0};for(unsigned i=0;i<256;i++)indices[i]=(uint8_t)i;
 for(unsigned y=0;y<160;y++)for(unsigned i=0;i<256;i++)preview_display_palette[y][i]=(uint16_t)((i*131+y*997)&32767);
 GLuint skin=model_zero_texture(256,1,rgba,indices);if(!skin||!model_zero_begin(skin,indices))return 2;
 glViewport(0,0,3840,2160);glMatrixMode(GL_PROJECTION);glLoadIdentity();glMatrixMode(GL_MODELVIEW);glLoadIdentity();glDisable(GL_BLEND);glDisable(GL_DEPTH_TEST);glDisable(GL_DITHER);
 glBegin(GL_QUADS);glTexCoord2f(0,0);glVertex2f(-1,-1);glTexCoord2f(1,0);glVertex2f(1,-1);glTexCoord2f(1,1);glVertex2f(1,1);glTexCoord2f(0,1);glVertex2f(-1,1);glEnd();
 uint8_t*out=malloc(3840u*2160u*3);if(!out)return 3;glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,out);if(glGetError()!=GL_NO_ERROR)return 4;
 for(unsigned y=0;y<2160;y++)for(unsigned x=0;x<3840;x++){
  unsigned row=(unsigned)floor((2160.0-y-.5)/13.5),index=x/15,color=preview_display_palette[row][index];
  for(unsigned k=0;k<3;k++)if(out[(y*3840+x)*3+k]!=((color>>(k*5))&31)*255/31){printf("mismatch x=%u y=%u row=%u index=%u\n",x,y,row,index);return 5;}
 }
 free(out);model_zero_end(indices);preview_shutdown();puts("PASS actual_indexed_shader pixels=8294400 rows=160 indices=256 zero_included=1");return 0;
}

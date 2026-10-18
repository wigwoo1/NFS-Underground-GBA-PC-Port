#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
int main(void){
 int result=preview_context_open();if(result)return result;preview_generation++;preview_zero_valid=1;preview_display_palette_valid=1;for(unsigned row=0;row<160;row++)for(unsigned i=0;i<256;i++)preview_display_palette[row][i]=(uint16_t)((row*137+i*53)&32767);
 for(unsigned y=0;y<160;y++)preview_zero_colors[y]=(uint16_t)((y*137)&32767);
 uint8_t rgba[12]={255,0,0,255,255,0,0,255,255,0,0,255},states[3]={0,1,2};
 uint8_t indices[3]={0,0,77};GLuint wall=wall_indexed_texture(3,1,rgba,states,indices);if(!wall)return 50;
 states[1]=3;if(wall_zero_texture(3,1,rgba,states))return 51;states[1]=1;
 glViewport(0,0,3840,2160);glMatrixMode(GL_PROJECTION);glLoadIdentity();glOrtho(0,3840,2160,0,-1,1);glMatrixMode(GL_MODELVIEW);glLoadIdentity();
 glClearColor(0,1,0,1);glClear(GL_COLOR_BUFFER_BIT);glEnable(GL_ALPHA_TEST);glAlphaFunc(GL_GREATER,.5);glDisable(GL_BLEND);glDisable(GL_DEPTH_TEST);
 if(!wall_zero_begin(wall,states))return 52;model_zero_uniform(model_zero_indexed_location,1);
 glBegin(GL_QUADS);glTexCoord4d(0,0,0,1);glVertex2i(0,0);glTexCoord4d(1,0,0,1);glVertex2i(3840,0);glTexCoord4d(1,1,0,1);glVertex2i(3840,2160);glTexCoord4d(0,1,0,1);glVertex2i(0,2160);glEnd();model_zero_end(states);
 if(!glIsEnabled(GL_ALPHA_TEST))return 53;
 uint8_t*pixels=malloc(3840u*2160*4);if(!pixels)return 54;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,pixels);
 for(unsigned y=0;y<2160;y++)for(unsigned x=0;x<3840;x++){
  unsigned row=(unsigned)((2159-y+.5)/13.5);unsigned c=preview_display_palette[row][x<2560?0:77];uint8_t expected[4];
  if(x<1280){expected[0]=0;expected[1]=255;expected[2]=0;expected[3]=255;}
  else if(x<2560){for(unsigned k=0;k<3;k++){unsigned v=(c>>(k*5))&31;expected[k]=v*255/31;}expected[3]=0;}
  else{for(unsigned k=0;k<3;k++)expected[k]=((c>>(k*5))&31)*255/31;expected[3]=255;}
  if(memcmp(pixels+((size_t)y*3840+x)*4,expected,4)){printf("mismatch x=%u y=%u\n",x,y);return 55;}
 }
 free(pixels);preview_shutdown();puts("PASS wall_indexed exact_rgba_pixels=8294400 skip_preserves_geometry=1 written_zero_clears_coverage=1 nonzero_opaque=1 alpha_test_restored=1 invalid_state_rejected=1");return 0;
}

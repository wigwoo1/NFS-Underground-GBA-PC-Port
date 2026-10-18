#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
int main(int argc,char**argv){
 if(argc!=2)return 1;
 FILE*f=fopen(argv[1],"rb");uint32_t h[3];
 if(!f||fread(h,4,3,f)!=3||!h[0]||h[0]>1024||!h[1]||h[1]>1024||h[2]!=2)return 2;
 size_t n=(size_t)h[0]*h[1];uint8_t*rgba=malloc(n*4),*states=malloc(n);
 if(!rgba||!states||fread(rgba,4,n,f)!=n||fread(states,1,n,f)!=n||fgetc(f)!=EOF)return 3;fclose(f);
 int result=preview_context_open();if(result)return result;preview_generation++;preview_zero_valid=1;
 GLuint wall=wall_zero_texture(h[0],h[1],rgba,states);if(!wall)return 4;
 glViewport(0,0,3840,2160);glMatrixMode(GL_PROJECTION);glLoadIdentity();glOrtho(0,3840,2160,0,-1,1);glMatrixMode(GL_MODELVIEW);glLoadIdentity();
 glClearColor(0,1,0,1);glClear(GL_COLOR_BUFFER_BIT);glEnable(GL_ALPHA_TEST);glAlphaFunc(GL_GREATER,.5);glDisable(GL_BLEND);glDisable(GL_DEPTH_TEST);
 if(!wall_zero_begin(wall,states))return 5;
 glBegin(GL_QUADS);glTexCoord4d(0,0,0,1);glVertex2i(0,0);glTexCoord4d(2,0,0,1);glVertex2i(3840,0);glTexCoord4d(2,1,0,1);glVertex2i(3840,2160);glTexCoord4d(0,1,0,1);glVertex2i(0,2160);glEnd();model_zero_end(states);
 uint8_t*pixels=malloc(3840u*2160*4);if(!pixels)return 6;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,pixels);
 unsigned skip=0,written=0,boundary=0;
 for(unsigned y=0;y<2160;y++)for(unsigned x=0;x<3840;x++){
  unsigned tx=(unsigned)(((x+.5)*2*h[0])/3840)%h[0],ty=(unsigned)(((2159-y+.5)*h[1])/2160)%h[1];size_t i=(size_t)ty*h[0]+tx;
  uint8_t expected[4]={0,255,0,255};if(states[i]==2){memcpy(expected,rgba+i*4,3);written++;}else if(states[i]==0)skip++;else return 7;
  if(memcmp(pixels+((size_t)y*3840+x)*4,expected,4)){
   /* Exact texel boundaries can fall on either neighboring nearest sample
      after float raster interpolation. Accept only that adjacent texel. */
   double fy=((2159-y+.5)*h[1])/2160;
   if(fabs(fy-round(fy))>1e-10){printf("mismatch x=%u y=%u tx=%u ty=%u\n",x,y,tx,ty);return 8;}
   size_t alt=(size_t)((ty+h[1]-1)%h[1])*h[0]+tx;uint8_t adjacent[4]={0,255,0,255};
   if(states[alt]==2)memcpy(adjacent,rgba+alt*4,3);else if(states[alt]!=0)return 9;
   if(memcmp(pixels+((size_t)y*3840+x)*4,adjacent,4))return 10;boundary++;
  }
 }
 printf("PASS captured_wall_gpu pixels=8294400 expected_skipped=%u expected_written=%u boundary_neighbor=%u repeat=2\n",skip,written,boundary);
 free(pixels);free(states);free(rgba);preview_shutdown();return 0;
}

#define main legacy_preview_main
#include "model_preview.c"
#undef main
int main(int argc,char**argv){
 if(argc!=3)return 2;FILE*f=fopen(argv[1],"rb");if(!f)return 3;unsigned h[6];if(fread(h,4,6,f)!=6||h[0]!=0x32504752||h[1]!=38400||h[2]>1024||h[3]>1024)return 4;
 int32_t samples[38400][4];if(fread(samples,16,38400,f)!=38400||!h[4]||!h[5])return 5;
 size_t n=(size_t)h[2]*h[3];uint8_t*rgba=malloc(n*4);if(!rgba)return 7;for(size_t i=0;i<n;i++){int index=fgetc(f);if(index==EOF)return 8;rgba[i*4]=index;rgba[i*4+1]=rgba[i*4+2]=0;rgba[i*4+3]=255;}if(fgetc(f)!=EOF)return 9;fclose(f);
 int error=preview_context_open();if(error)return error;glViewport(300,0,3240,2160);glMatrixMode(GL_PROJECTION);glLoadIdentity();glOrtho(0,240,160,0,-1,1);glMatrixMode(GL_MODELVIEW);glLoadIdentity();glDisable(GL_BLEND);glDisable(GL_DEPTH_TEST);glDisable(GL_ALPHA_TEST);glDisable(GL_DITHER);glClearColor(0,0,0,0);glClear(GL_COLOR_BUFFER_BIT);
 GLuint texture;glGenTextures(1,&texture);glBindTexture(GL_TEXTURE_2D,texture);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,h[2],h[3],0,GL_RGBA,GL_UNSIGNED_BYTE,rgba);glEnable(GL_TEXTURE_2D);glTexEnvi(GL_TEXTURE_ENV,GL_TEXTURE_ENV_MODE,GL_REPLACE);
 glBegin(GL_QUADS);for(unsigned i=0;i<38400;i++){
  if(samples[i][0]<0)continue;
  double u=(double)samples[i][2]/(65536.0*h[4]*.5),v=(double)samples[i][3]/(65536.0*h[5]*.5);
  int tx=(int)(2*floor(u*(h[2]/2)))+(samples[i][1]&1),ty=(int)floor(v*h[3]);
  glTexCoord2d((tx+.5)/h[2],(ty+.5)/h[3]);double x=i%240,y=i/240;
  glVertex2d(x,y);glVertex2d(x+1,y);glVertex2d(x+1,y+1);glVertex2d(x,y+1);
 }glEnd();glFinish();free(rgba);
 size_t bytes=3840ull*2160*4;uint8_t*p=malloc(bytes);if(!p)return 10;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,p);if(glGetError()!=GL_NO_ERROR)return 11;f=fopen(argv[2],"wb");if(!f)return 12;int ok=fwrite(p,1,bytes,f)==bytes;fclose(f);free(p);glDeleteTextures(1,&texture);preview_shutdown();return ok?0:13;
}

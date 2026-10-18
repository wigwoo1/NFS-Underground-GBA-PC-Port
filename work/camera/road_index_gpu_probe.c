#define main legacy_preview_main
#include "model_preview.c"
#undef main
int main(int argc,char**argv){
 if(argc!=3)return 2;FILE*f=fopen(argv[1],"rb");if(!f)return 3;unsigned h[4];if(fread(h,4,4,f)!=4||h[0]!=0x31504752||h[1]>192||h[2]>1024||h[3]>1024)return 4;
 RoadVertex triangles[192];if(fread(triangles,sizeof(RoadVertex),h[1],f)!=h[1])return 5;unsigned affine;if(fread(&affine,4,1,f)!=1||affine>1)return 6;
 size_t n=(size_t)h[2]*h[3];uint8_t*rgba=malloc(n*4);if(!rgba)return 7;for(size_t i=0;i<n;i++){int index=fgetc(f);if(index==EOF)return 8;rgba[i*4]=index;rgba[i*4+1]=rgba[i*4+2]=0;rgba[i*4+3]=255;}if(fgetc(f)!=EOF)return 9;fclose(f);
 int error=preview_context_open();if(error)return error;glViewport(300,0,3240,2160);glMatrixMode(GL_PROJECTION);glLoadIdentity();glOrtho(0,240,160,0,-1,1);glMatrixMode(GL_MODELVIEW);glLoadIdentity();glDisable(GL_BLEND);glDisable(GL_DEPTH_TEST);glDisable(GL_ALPHA_TEST);glDisable(GL_DITHER);glClearColor(0,0,0,0);glClear(GL_COLOR_BUFFER_BIT);
 GLuint texture;glGenTextures(1,&texture);glBindTexture(GL_TEXTURE_2D,texture);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,h[2],h[3],0,GL_RGBA,GL_UNSIGNED_BYTE,rgba);glEnable(GL_TEXTURE_2D);glTexEnvi(GL_TEXTURE_ENV,GL_TEXTURE_ENV_MODE,GL_REPLACE);
 glBegin(GL_TRIANGLES);for(unsigned i=0;i<h[1];i++){double q=affine?1:1/triangles[i].p.z;glTexCoord4d(triangles[i].u*q,triangles[i].v*q,0,q);glVertex2d(triangles[i].p.x,triangles[i].p.y);}glEnd();glFinish();free(rgba);
 size_t bytes=3840ull*2160*4;uint8_t*p=malloc(bytes);if(!p)return 10;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,p);if(glGetError()!=GL_NO_ERROR)return 11;f=fopen(argv[2],"wb");if(!f)return 12;int ok=fwrite(p,1,bytes,f)==bytes;fclose(f);free(p);glDeleteTextures(1,&texture);preview_shutdown();return ok?0:13;
}

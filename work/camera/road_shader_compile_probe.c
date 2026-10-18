#define main legacy_preview_main
#include "model_preview.c"
#undef main
typedef GLuint (APIENTRY *CreateShaderFn)(GLenum);
typedef void (APIENTRY *ShaderSourceFn)(GLuint,GLsizei,const char*const*,const GLint*);
typedef void (APIENTRY *ShaderFn)(GLuint);
typedef void (APIENTRY *GetShaderFn)(GLuint,GLenum,GLint*);
typedef void (APIENTRY *LogFn)(GLuint,GLsizei,GLsizei*,char*);
int main(int argc,char**argv){
 if(argc!=2)return 2;FILE*f=fopen(argv[1],"rb");if(!f)return 3;fseek(f,0,SEEK_END);long n=ftell(f);rewind(f);if(n<=0||n>100000)return 4;char*source=calloc(n+1,1);if(!source||fread(source,1,n,f)!=(size_t)n)return 5;fclose(f);
 int error=preview_context_open();if(error)return error;
 CreateShaderFn create=(CreateShaderFn)wglGetProcAddress("glCreateShader");ShaderSourceFn set=(ShaderSourceFn)wglGetProcAddress("glShaderSource");ShaderFn compile=(ShaderFn)wglGetProcAddress("glCompileShader");GetShaderFn get=(GetShaderFn)wglGetProcAddress("glGetShaderiv");LogFn log=(LogFn)wglGetProcAddress("glGetShaderInfoLog");ShaderFn dispose=(ShaderFn)wglGetProcAddress("glDeleteShader");
 if(!create||!set||!compile||!get||!log||!dispose)return 6;
 GLuint shader=create(0x8b30);set(shader,1,(const char*const*)&source,NULL);compile(shader);GLint ok=0;get(shader,0x8b81,&ok);char message[8192]={0};log(shader,sizeof(message),NULL,message);printf("GPU=%s\ncompile=%d\n%s\n",glGetString(GL_RENDERER),ok,message);dispose(shader);free(source);preview_shutdown();return ok?0:7;
}

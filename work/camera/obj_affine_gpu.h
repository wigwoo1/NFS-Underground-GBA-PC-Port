#ifndef NF_OBJ_AFFINE_GPU_H
#define NF_OBJ_AFFINE_GPU_H
/* Per-fragment inverse8.8 affine sampling from original sprite texture. */
static GLuint obj_affine_program;
static void(APIENTRY*obj_use)(GLuint);
static GLint(APIENTRY*obj_location)(GLuint,const char*);
static void(APIENTRY*obj_uniform2)(GLint,GLfloat,GLfloat);
static void(APIENTRY*obj_uniform4)(GLint,GLfloat,GLfloat,GLfloat,GLfloat);
static int obj_shader_create(const char*fs){
 GLuint(APIENTRY*create)(GLenum)=(void*)wglGetProcAddress("glCreateShader");void(APIENTRY*source)(GLuint,GLsizei,const char*const*,const GLint*)=(void*)wglGetProcAddress("glShaderSource");void(APIENTRY*compile)(GLuint)=(void*)wglGetProcAddress("glCompileShader");void(APIENTRY*get)(GLuint,GLenum,GLint*)=(void*)wglGetProcAddress("glGetShaderiv");GLuint(APIENTRY*program)(void)=(void*)wglGetProcAddress("glCreateProgram");void(APIENTRY*attach)(GLuint,GLuint)=(void*)wglGetProcAddress("glAttachShader");void(APIENTRY*link)(GLuint)=(void*)wglGetProcAddress("glLinkProgram");void(APIENTRY*getprogram)(GLuint,GLenum,GLint*)=(void*)wglGetProcAddress("glGetProgramiv");void(APIENTRY*remove)(GLuint)=(void*)wglGetProcAddress("glDeleteShader");obj_use=(void*)wglGetProcAddress("glUseProgram");obj_location=(void*)wglGetProcAddress("glGetUniformLocation");obj_uniform2=(void*)wglGetProcAddress("glUniform2f");obj_uniform4=(void*)wglGetProcAddress("glUniform4f");if(!create||!source||!compile||!get||!program||!attach||!link||!getprogram||!remove||!obj_use||!obj_location||!obj_uniform2||!obj_uniform4)return 0;
 const char*vs="#version 120\nvoid main(){gl_Position=gl_ModelViewProjectionMatrix*gl_Vertex;}";
 GLuint v=create(0x8b31),f=create(0x8b30);source(v,1,&vs,NULL);source(f,1,&fs,NULL);compile(v);compile(f);GLint a=0,b=0;get(v,0x8b81,&a);get(f,0x8b81,&b);if(!a||!b){remove(v);remove(f);return 0;}obj_affine_program=program();attach(obj_affine_program,v);attach(obj_affine_program,f);link(obj_affine_program);getprogram(obj_affine_program,0x8b82,&a);remove(v);remove(f);return a!=0;
}

static int obj_affine_shader(void){const char*fs="#version 120\nuniform sampler2D asset;uniform vec4 inverse;uniform vec2 origin,sourceSize,destSize;void main(){vec2 p=(vec2(gl_FragCoord.x,2160.0-gl_FragCoord.y)-origin)/13.5-vec2(0.5)-destSize/2.0;vec2 s=floor(vec2(inverse.x*p.x+inverse.y*p.y,inverse.z*p.x+inverse.w*p.y)/256.0+sourceSize/2.0+vec2(0.0001));if(s.x<0.0||s.y<0.0||s.x>=sourceSize.x||s.y>=sourceSize.y)discard;vec4 c=texture2D(asset,(s+vec2(0.5))/sourceSize);if(c.a<0.5)discard;gl_FragColor=c;}";return obj_shader_create(fs);}

#endif

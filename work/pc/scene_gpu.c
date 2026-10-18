#include "scene_sample_internal.h"
#include "scene_sample_gpu.h"
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "scene_gpu.h"
#include "scene_internal.h"
#include "hud_shader.h"
#include "empty_model_plane.h"
#define FRAMEBUFFER 0x8D40
#define ATTACHMENT 0x8CE0
#define COMPLETE 0x8CD5
#define VERTEX_SHADER 0x8B31
#define FRAGMENT_SHADER 0x8B30
#define COMPILE_STATUS 0x8B81
#define LINK_STATUS 0x8B82
#define CLAMP_EDGE 0x812F
#define TEXTURE0 0x84C0
typedef void(APIENTRY*GenFB)(GLsizei,GLuint*);typedef void(APIENTRY*BindFB)(GLenum,GLuint);typedef void(APIENTRY*AttachFB)(GLenum,GLenum,GLenum,GLuint,GLint);typedef GLenum(APIENTRY*CheckFB)(GLenum);typedef void(APIENTRY*DelFB)(GLsizei,const GLuint*);
typedef GLuint(APIENTRY*CreateShader)(GLenum);typedef void(APIENTRY*ShaderSource)(GLuint,GLsizei,const char*const*,const GLint*);typedef void(APIENTRY*ShaderOp)(GLuint);typedef void(APIENTRY*GetShader)(GLuint,GLenum,GLint*);typedef void(APIENTRY*ShaderLog)(GLuint,GLsizei,GLsizei*,char*);typedef GLuint(APIENTRY*CreateProgram)(void);typedef void(APIENTRY*AttachShader)(GLuint,GLuint);typedef GLint(APIENTRY*GetUniform)(GLuint,const char*);typedef void(APIENTRY*Uniform1i)(GLint,GLint);typedef void(APIENTRY*Uniform2f)(GLint,GLfloat,GLfloat);typedef void(APIENTRY*Uniform3fv)(GLint,GLsizei,const GLfloat*);typedef void(APIENTRY*ActiveTex)(GLenum);typedef void(APIENTRY*Uniform4f)(GLint,GLfloat,GLfloat,GLfloat,GLfloat);
struct NFPCSceneGPU {HWND window;HDC dc;HGLRC context;DWORD owner;int owns_window;BOOL (WINAPI *swap_interval)(int);int swap_interval_value;int (WINAPI *get_swap_interval)(void);int swap_requested,swap_reported;uint64_t swap_attempts,swap_failures,swap_reads,visible_swaps,hidden_swaps;GLuint input,palette,target,fbo,program,background,retention,hud,hudcopy;unsigned width,height;char renderer[256];GenFB gen;BindFB bind;AttachFB attach;CheckFB check;DelFB del;CreateShader create_shader;ShaderSource shader_source;ShaderOp compile_shader,delete_shader,link_program,use_program,delete_program;GetShader get_shader,get_program;ShaderLog shader_log,program_log;CreateProgram create_program;AttachShader attach_shader;GetUniform uniform;Uniform1i uniform1i;Uniform2f uniform2f;Uniform3fv uniform3fv;Uniform4f uniform4f;ActiveTex active;};
static char error_text[512];
const char* nf_pc_scene_gpu_error(void){return error_text;}
const char* nf_pc_scene_gpu_renderer(const NFPCSceneGPU*g){return g?g->renderer:"";}
static void error(const char*why){snprintf(error_text,sizeof(error_text),"%s",why);}
static PROC proc(const char*name){PROC p=wglGetProcAddress(name);if(!p||p==(PROC)1||p==(PROC)2||p==(PROC)3||p==(PROC)-1){snprintf(error_text,sizeof(error_text),"Missing Windows OpenGL function %s",name);return NULL;}return p;}
#define LOAD(member,type,name) do{PROC raw=proc(name);_Static_assert(sizeof(type)==sizeof(raw),"Windows GL function pointer size");memcpy(&g->member,&raw,sizeof(raw));if(!g->member)goto fail;}while(0)
static GLuint shader(NFPCSceneGPU*g,GLenum kind,const char*text){GLuint s=g->create_shader(kind);if(!s)return 0;g->shader_source(s,1,&text,NULL);g->compile_shader(s);GLint ok=0;g->get_shader(s,COMPILE_STATUS,&ok);if(!ok){g->shader_log(s,sizeof(error_text),NULL,error_text);g->delete_shader(s);return 0;}return s;}
static int background_program(NFPCSceneGPU*g){const char*v="#version 120\nvoid main(){gl_Position=vec4(gl_Vertex.x/120.0-1.0,1.0-gl_Vertex.y/80.0,0.0,1.0);}";const char*f="#version 120\nuniform sampler2D image;uniform vec2 viewport;void main(){int px=int(gl_FragCoord.x),py=int(gl_FragCoord.y),w=int(viewport.x),h=int(viewport.y);ivec2 cell=ivec2(((px*2+1)*120)/w,(((h-py)*2-1)*80)/h);vec4 c=texture2D(image,(vec2(cell)+vec2(0.5))/vec2(240.0,160.0));if(c.a<0.5)discard;gl_FragColor=c;}";GLuint a=shader(g,VERTEX_SHADER,v),b=shader(g,FRAGMENT_SHADER,f);if(!a||!b){if(a)g->delete_shader(a);if(b)g->delete_shader(b);return 0;}g->background=g->create_program();g->attach_shader(g->background,a);g->attach_shader(g->background,b);g->link_program(g->background);g->delete_shader(a);g->delete_shader(b);GLint ok=0;g->get_program(g->background,LINK_STATUS,&ok);if(!ok)g->program_log(g->background,sizeof(error_text),NULL,error_text);return ok;}
static int retention_program(NFPCSceneGPU*g){
 const char*v="#version 120\nvarying vec2 t;void main(){gl_Position=vec4(gl_Vertex.x/120.0-1.0,1.0-gl_Vertex.y/80.0,0.0,1.0);t=gl_MultiTexCoord0.xy;}";
 const char*f="#version 120\nvarying vec2 t;uniform sampler2D image;uniform sampler2D rows;uniform vec2 viewport;void main(){vec4 c=texture2D(image,t);if(c.a<0.5)discard;int py=int(gl_FragCoord.y),h=int(viewport.y);int row=((h-py)*2-1)*80/h;float index=floor(c.r*255.0+0.5);gl_FragColor=vec4(texture2D(rows,vec2((index+0.5)/256.0,(float(row)+0.5)/160.0)).rgb,1.0);}";
 GLuint a=shader(g,VERTEX_SHADER,v),b=shader(g,FRAGMENT_SHADER,f);if(!a||!b){if(a)g->delete_shader(a);if(b)g->delete_shader(b);return 0;}g->retention=g->create_program();g->attach_shader(g->retention,a);g->attach_shader(g->retention,b);g->link_program(g->retention);g->delete_shader(a);g->delete_shader(b);GLint ok=0;g->get_program(g->retention,LINK_STATUS,&ok);if(!ok)g->program_log(g->retention,sizeof(error_text),NULL,error_text);return ok;
}
static int hud_program(NFPCSceneGPU*g){
 const char*v="#version 120\nvoid main(){gl_Position=vec4(gl_Vertex.x/120.0-1.0,1.0-gl_Vertex.y/80.0,0.0,1.0);}";
 GLuint a=shader(g,VERTEX_SHADER,v),b=shader(g,FRAGMENT_SHADER,nf_pc_hud_fragment);if(!a||!b){if(a)g->delete_shader(a);if(b)g->delete_shader(b);return 0;}g->hud=g->create_program();g->attach_shader(g->hud,a);g->attach_shader(g->hud,b);g->link_program(g->hud);g->delete_shader(a);g->delete_shader(b);GLint ok=0;g->get_program(g->hud,LINK_STATUS,&ok);if(!ok)g->program_log(g->hud,sizeof(error_text),NULL,error_text);return ok;
}
static void swap_observe(NFPCSceneGPU*g,int wanted){
 int changed=wanted!=g->swap_requested,attempted=0;g->swap_requested=wanted;
 if(g->swap_interval&&(!g->swap_attempts||wanted!=g->swap_interval_value)){
  g->swap_attempts++;attempted=1;if(g->swap_interval(wanted))g->swap_interval_value=wanted;else g->swap_failures++;
 }
 if(g->get_swap_interval&&(changed||attempted||!g->swap_reads)){g->swap_reported=g->get_swap_interval();g->swap_reads++;}
}
int nf_pc_scene_gpu_swap_info(const NFPCSceneGPU*g,int64_t*out,size_t bytes){
 if(!g||g->owner!=GetCurrentThreadId()||!out||bytes!=10*sizeof(*out))return 0;
 int64_t state[10]={g->swap_interval!=NULL,g->get_swap_interval!=NULL,g->swap_requested,g->swap_interval_value,g->swap_reported,(int64_t)g->swap_attempts,(int64_t)g->swap_failures,(int64_t)g->swap_reads,(int64_t)g->visible_swaps,(int64_t)g->hidden_swaps};memcpy(out,state,sizeof(state));return 1;
}
NFPCSceneGPU* nf_pc_scene_gpu_open_window(void*host_window){HDC previous_dc=wglGetCurrentDC();HGLRC previous=wglGetCurrentContext();NFPCSceneGPU*g=calloc(1,sizeof(*g));if(!g){error("GPU allocation");return NULL;}g->owner=GetCurrentThreadId();g->swap_requested=g->swap_reported=-1;error_text[0]=0;if(host_window)g->window=(HWND)host_window;else{g->owns_window=1;WNDCLASSA klass={0};klass.style=CS_OWNDC;klass.lpfnWndProc=DefWindowProcA;klass.hInstance=GetModuleHandle(NULL);klass.lpszClassName="NFSUGSourceSceneDiagnostic";if(!RegisterClassA(&klass)&&GetLastError()!=ERROR_CLASS_ALREADY_EXISTS){error("Register hidden class");goto fail;}g->window=CreateWindowA(klass.lpszClassName,"NFSUG source scene",WS_POPUP,0,0,16,16,NULL,NULL,klass.hInstance,NULL);if(!g->window){error("Create hidden window");goto fail;}}g->dc=GetDC(g->window);PIXELFORMATDESCRIPTOR pfd={0};pfd.nSize=sizeof(pfd);pfd.nVersion=1;pfd.dwFlags=PFD_DRAW_TO_WINDOW|PFD_SUPPORT_OPENGL|(host_window?PFD_DOUBLEBUFFER:0);pfd.iPixelType=PFD_TYPE_RGBA;pfd.cColorBits=32;pfd.cAlphaBits=8;int format=ChoosePixelFormat(g->dc,&pfd);if(!format||!SetPixelFormat(g->dc,format,&pfd)||(g->context=wglCreateContext(g->dc))==NULL||!wglMakeCurrent(g->dc,g->context)){error("Create Windows GL context");goto fail;}
 LOAD(gen,GenFB,"glGenFramebuffers");LOAD(bind,BindFB,"glBindFramebuffer");LOAD(attach,AttachFB,"glFramebufferTexture2D");LOAD(check,CheckFB,"glCheckFramebufferStatus");LOAD(del,DelFB,"glDeleteFramebuffers");LOAD(create_shader,CreateShader,"glCreateShader");LOAD(shader_source,ShaderSource,"glShaderSource");LOAD(compile_shader,ShaderOp,"glCompileShader");LOAD(delete_shader,ShaderOp,"glDeleteShader");LOAD(get_shader,GetShader,"glGetShaderiv");LOAD(shader_log,ShaderLog,"glGetShaderInfoLog");LOAD(create_program,CreateProgram,"glCreateProgram");LOAD(attach_shader,AttachShader,"glAttachShader");LOAD(link_program,ShaderOp,"glLinkProgram");LOAD(use_program,ShaderOp,"glUseProgram");LOAD(delete_program,ShaderOp,"glDeleteProgram");LOAD(get_program,GetShader,"glGetProgramiv");LOAD(program_log,ShaderLog,"glGetProgramInfoLog");LOAD(uniform,GetUniform,"glGetUniformLocation");LOAD(uniform1i,Uniform1i,"glUniform1i");LOAD(uniform2f,Uniform2f,"glUniform2f");LOAD(uniform3fv,Uniform3fv,"glUniform3fv");LOAD(active,ActiveTex,"glActiveTexture");LOAD(uniform4f,Uniform4f,"glUniform4f");
 const char*vertex="#version 120\nvoid main(){gl_Position=vec4(gl_Vertex.x/120.0-1.0,1.0-gl_Vertex.y/80.0,0.0,1.0);}";const char*fragment="#version 120\nuniform sampler2D image;uniform sampler2D rows;uniform int indexed;uniform int wall;uniform vec2 viewport;uniform vec2 origin;uniform vec3 planeBase;uniform vec3 planeX;uniform vec3 planeY;void main(){vec2 delta=vec2(gl_FragCoord.x*240.0/viewport.x,(viewport.y-gl_FragCoord.y)*160.0/viewport.y)-origin;vec3 uvq=planeBase+planeX*delta.x+planeY*delta.y;vec4 c=texture2D(image,fract(uvq.xy/uvq.z));int py=int(gl_FragCoord.y),h=int(viewport.y);int row=((h-py)*2-1)*80/h;if(wall!=0&&c.a<0.25)discard;if(indexed!=0)c=texture2D(rows,vec2((floor(c.r*255.0+0.5)+0.5)/256.0,(float(row)+0.5)/160.0));else if(c.a<(wall!=0?0.75:0.5))c=texture2D(rows,vec2(0.5/256.0,(float(row)+0.5)/160.0));gl_FragColor=vec4(c.rgb,1.0);}";
 GLuint v=shader(g,VERTEX_SHADER,vertex),f=shader(g,FRAGMENT_SHADER,fragment);if(!v||!f){if(v)g->delete_shader(v);if(f)g->delete_shader(f);goto fail;}g->program=g->create_program();g->attach_shader(g->program,v);g->attach_shader(g->program,f);g->link_program(g->program);g->delete_shader(v);g->delete_shader(f);GLint linked=0;g->get_program(g->program,LINK_STATUS,&linked);if(!linked){g->program_log(g->program,sizeof(error_text),NULL,error_text);goto fail;}if(!background_program(g)||!retention_program(g)||!hud_program(g))goto fail;glGenTextures(1,&g->hudcopy);glGenTextures(1,&g->palette);glGenTextures(1,&g->input);glBindTexture(GL_TEXTURE_2D,g->input);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,CLAMP_EDGE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,CLAMP_EDGE);if(host_window){PROC raw=wglGetProcAddress("wglSwapIntervalEXT");if(raw&&raw!=(PROC)1&&raw!=(PROC)2&&raw!=(PROC)3&&raw!=(PROC)-1){memcpy(&g->swap_interval,&raw,sizeof(raw));}raw=wglGetProcAddress("wglGetSwapIntervalEXT");if(raw&&raw!=(PROC)1&&raw!=(PROC)2&&raw!=(PROC)3&&raw!=(PROC)-1)memcpy(&g->get_swap_interval,&raw,sizeof(raw));swap_observe(g,0);}snprintf(g->renderer,sizeof(g->renderer),"%s | %s",glGetString(GL_RENDERER),glGetString(GL_VERSION));wglMakeCurrent(previous_dc,previous);return g;
fail:nf_pc_scene_gpu_close(g);wglMakeCurrent(previous_dc,previous);return NULL;}
void nf_pc_scene_gpu_close(NFPCSceneGPU*g){if(!g)return;if(g->owner!=GetCurrentThreadId()){error("GPU close on wrong thread");return;}HDC dc=wglGetCurrentDC();HGLRC old=wglGetCurrentContext();if(g->context&&wglMakeCurrent(g->dc,g->context)){if(g->hud&&g->delete_program)g->delete_program(g->hud);if(g->hudcopy)glDeleteTextures(1,&g->hudcopy);if(g->retention&&g->delete_program)g->delete_program(g->retention);if(g->background&&g->delete_program)g->delete_program(g->background);if(g->program&&g->delete_program)g->delete_program(g->program);if(g->fbo&&g->del)g->del(1,&g->fbo);if(g->palette)glDeleteTextures(1,&g->palette);if(g->input)glDeleteTextures(1,&g->input);if(g->target)glDeleteTextures(1,&g->target);wglMakeCurrent(NULL,NULL);}if(g->context)wglDeleteContext(g->context);if(g->dc&&g->window)ReleaseDC(g->window,g->dc);if(g->window&&g->owns_window)DestroyWindow(g->window);if(old&&old!=g->context)wglMakeCurrent(dc,old);free(g);}


static int clip_edge(unsigned cell,unsigned extent,unsigned source){return (int)ceil((double)cell*extent/source-.5);}
static int render(NFPCSceneGPU*g,NFPCScene*scene,unsigned width,unsigned height,unsigned aw,unsigned ah,unsigned passes,void*out,size_t bytes,int readback,const NFPCSceneSample*sample){size_t count=(size_t)width*height*4;
 if((passes&~15u)||!g||g->owner!=GetCurrentThreadId()||!scene||(readback&&!out)||!width||!height||width>16384||height>16384||!aw||!ah||aw>width||ah>height||count>64u*1024*1024||(readback&&bytes<count)){error("Scene target/thread");return 0;}
 unsigned draw_count=sample?(unsigned)sample->info[3]:(unsigned)scene->info[3];if(draw_count>864)return 0;
 uint32_t*columns[864]={0};int ok=0;HDC dc=NULL;HGLRC old=NULL;
 const void*hud_colors,*hud_metadata,*hud_rows;size_t hn;
 if(!nf_pc_scene_hud_buffer(scene,0,&hud_colors,&hn)||hn!=153600||!nf_pc_scene_hud_buffer(scene,1,&hud_metadata,&hn)||hn!=153600||!nf_pc_scene_hud_buffer(scene,2,&hud_rows,&hn)||hn!=3200){error("Scene HUD preparation");return 0;}
 const void*retained[2][2]={{0}};
 for(unsigned owner=0;owner<scene->info[2];owner++)for(unsigned layer=0;layer<2;layer++){size_t n;if(!nf_pc_scene_retention_buffer(scene,owner,NFPC_ROAD+layer,0,&retained[owner][layer],&n)||n!=153600){error("Scene retention preparation");return 0;}}

 /* Complete width-dependent preparation before touching the framebuffer. */
 for(unsigned i=0;i<draw_count;i++){unsigned source_index=sample?(unsigned)sample->draws[i].trace[0]:i;const NFPCSceneCommand*c=sample?&sample->draws[i].command:scene->commands+i;if(c->info[8]&&c->info[5]){columns[i]=malloc((size_t)aw*4);if(!columns[i]||!nf_pc_scene_command_columns(scene,source_index,aw,columns[i],(size_t)aw*4)){error("Scene shade preparation");goto cleanup;}}}
 dc=wglGetCurrentDC();old=wglGetCurrentContext();if(!wglMakeCurrent(g->dc,g->context)){error("Scene make current");goto cleanup;}
 if(!g->target||g->width!=width||g->height!=height){if(g->fbo)g->del(1,&g->fbo);if(g->target)glDeleteTextures(1,&g->target);g->fbo=g->target=0;g->width=g->height=0;glGenTextures(1,&g->target);glBindTexture(GL_TEXTURE_2D,g->target);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,width,height,0,GL_RGBA,GL_UNSIGNED_BYTE,NULL);g->gen(1,&g->fbo);g->bind(FRAMEBUFFER,g->fbo);g->attach(FRAMEBUFFER,ATTACHMENT,GL_TEXTURE_2D,g->target,0);if(g->check(FRAMEBUFFER)!=COMPLETE){error("Scene framebuffer incomplete");goto done;}g->width=width;g->height=height;}
 g->bind(FRAMEBUFFER,g->fbo);glViewport(0,0,width,height);glDisable(GL_BLEND);glDisable(GL_DEPTH_TEST);glDisable(GL_CULL_FACE);glDisable(GL_SCISSOR_TEST);glDisable(GL_DITHER);glColorMask(GL_TRUE,GL_TRUE,GL_TRUE,GL_TRUE);glClearColor(0,0,0,0);glClear(GL_COLOR_BUFFER_BIT);glPixelStorei(GL_UNPACK_ALIGNMENT,1);
 if(passes&1u){g->active(TEXTURE0);glBindTexture(GL_TEXTURE_2D,g->input);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,240,160,0,GL_RGBA,GL_UNSIGNED_BYTE,sample?sample->background:scene->background);g->use_program(g->background);g->uniform1i(g->uniform(g->background,"image"),0);g->uniform2f(g->uniform(g->background,"viewport"),(float)aw,(float)ah);glViewport(0,0,aw,ah);glBegin(GL_QUADS);glVertex2f(0,0);glVertex2f(240,0);glVertex2f(240,160);glVertex2f(0,160);glEnd();}
 glViewport(0,0,aw,ah);g->use_program(g->program);g->active(TEXTURE0+1);glBindTexture(GL_TEXTURE_2D,g->palette);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,CLAMP_EDGE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,CLAMP_EDGE);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,256,160,0,GL_RGBA,GL_UNSIGNED_BYTE,scene->palette);g->uniform1i(g->uniform(g->program,"rows"),1);g->uniform1i(g->uniform(g->program,"image"),0);g->uniform2f(g->uniform(g->program,"viewport"),(float)aw,(float)ah);g->active(TEXTURE0);glBindTexture(GL_TEXTURE_2D,g->input);
 /* Source-index layers share the target and palette. No readback/compositing. */
 g->use_program(g->retention);g->uniform1i(g->uniform(g->retention,"image"),0);g->uniform1i(g->uniform(g->retention,"rows"),1);g->uniform2f(g->uniform(g->retention,"viewport"),(float)aw,(float)ah);
 if(passes&2u)for(unsigned layer=0;layer<2;layer++)for(unsigned owner=0;owner<scene->info[2];owner++){/* Owner bands were applied to source cells before quad construction. Original edge GPU has no additional scissor: fractional row-boundary coverage belongs to its cell quad. */glDisable(GL_SCISSOR_TEST);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,240,160,0,GL_RGBA,GL_UNSIGNED_BYTE,retained[owner][layer]);glBegin(GL_TRIANGLES);const float*v=scene->retention_vertices[owner][layer];for(size_t j=0;j<scene->retention_vertex_bytes[owner][layer]/sizeof(float);j+=4){glTexCoord2f(v[j+2],v[j+3]);glVertex2f(v[j],v[j+1]);}glEnd();}
 glDisable(GL_SCISSOR_TEST);g->use_program(g->program);
 if(passes&4u)for(unsigned i=0;i<draw_count;i++){unsigned source_index=sample?(unsigned)sample->draws[i].trace[0]:i;const NFPCSceneCommand*c=sample?&sample->draws[i].command:scene->commands+i;const uint64_t*m=c->info;if(!m[5])continue;unsigned top=m[11]>m[13]?(unsigned)m[11]:(unsigned)m[13],bottom=m[12]<m[14]?(unsigned)m[12]:(unsigned)m[14];int left=clip_edge((unsigned)m[9],aw,240),right=clip_edge((unsigned)m[10],aw,240),t=clip_edge(top,ah,160),b=clip_edge(bottom,ah,160);if(top>=bottom||left>=right||t>=b)continue;
 g->uniform1i(g->uniform(g->program,"indexed"),(GLint)m[6]);g->uniform1i(g->uniform(g->program,"wall"),(GLint)m[7]);glEnable(GL_SCISSOR_TEST);
 for(int start=left;start<right;){unsigned level=columns[i]?columns[i][start]:0;int end=right;if(columns[i]){end=start+1;while(end<right&&columns[i][end]==level)end++;}const void*rgba;size_t rn;if(!nf_pc_scene_command_image(scene,source_index,level,&rgba,&rn)||rn!=m[3]*m[4]*4){error("Scene upload binding");goto done;}glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,(GLsizei)m[3],(GLsizei)m[4],0,GL_RGBA,GL_UNSIGNED_BYTE,rgba);glScissor(start,(int)ah-b,end-start,b-t);const float*v=c->vertices;
 for(unsigned triangle=0;triangle<m[5]/3;triangle++){const float*p=c->planes+triangle*11;g->uniform2f(g->uniform(g->program,"origin"),p[0],p[1]);g->uniform3fv(g->uniform(g->program,"planeBase"),1,p+2);g->uniform3fv(g->uniform(g->program,"planeX"),1,p+5);g->uniform3fv(g->uniform(g->program,"planeY"),1,p+8);glBegin(GL_TRIANGLES);for(unsigned k=0;k<3;k++)glVertex2f(v[(triangle*3+k)*5],v[(triangle*3+k)*5+1]);glEnd();}start=end;}}
 glDisable(GL_SCISSOR_TEST);
 if(passes&8u){
 g->use_program(g->hud);g->active(TEXTURE0);glBindTexture(GL_TEXTURE_2D,g->hudcopy);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,CLAMP_EDGE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,CLAMP_EDGE);glCopyTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,0,0,width,height,0);g->uniform1i(g->uniform(g->hud,"nativeBackground"),0);
 g->active(TEXTURE0+1);glBindTexture(GL_TEXTURE_2D,g->input);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,240,160,0,GL_RGBA,GL_UNSIGNED_BYTE,hud_colors);g->uniform1i(g->uniform(g->hud,"candidates"),1);g->active(TEXTURE0+2);glBindTexture(GL_TEXTURE_2D,g->palette);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,240,160,0,GL_RGBA,GL_UNSIGNED_BYTE,hud_metadata);g->uniform1i(g->uniform(g->hud,"metadataImage"),2);g->uniform2f(g->uniform(g->hud,"viewport"),(float)aw,(float)ah);g->uniform2f(g->uniform(g->hud,"target"),(float)width,(float)height);glEnable(GL_SCISSOR_TEST);
 const uint32_t*rows=hud_rows;for(unsigned y=0;y<160;){const uint32_t*p=rows+y*5;unsigned end=y+1;while(end<160&&!memcmp(p,rows+end*5,5*sizeof(uint32_t)))end++;int top=clip_edge(y,ah,160),bottom=clip_edge(end,ah,160);if(top<bottom){uint32_t blend=p[2],alpha=p[3];g->uniform4f(g->uniform(g->hud,"backdropColor"),(float)(p[0]&255),(float)((p[0]>>8)&255),(float)((p[0]>>16)&255),1);g->uniform4f(g->uniform(g->hud,"effectParameters"),(float)((blend>>6)&3),0,0,(float)p[1]);g->uniform4f(g->uniform(g->hud,"firstTargets"),(blend&16)?1:0,(blend&4)?1:0,(blend&32)?1:0,0);g->uniform4f(g->uniform(g->hud,"secondTargets"),(blend&4096)?1:0,(blend&1024)?1:0,(blend&8192)?1:0,0);unsigned ea=alpha&31,eb=(alpha>>8)&31,ey=p[4]&31;g->uniform4f(g->uniform(g->hud,"coefficients"),(float)(ea>16?16:ea),(float)(eb>16?16:eb),(float)(ey>16?16:ey),0);glScissor(0,(int)ah-bottom,(GLsizei)aw,bottom-top);glBegin(GL_QUADS);glVertex2f(0,0);glVertex2f(240,0);glVertex2f(240,160);glVertex2f(0,160);glEnd();}y=end;}
 glDisable(GL_SCISSOR_TEST);g->active(TEXTURE0);
 }
 glPixelStorei(GL_PACK_ALIGNMENT,1);if(readback)glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,out);if(glGetError()!=GL_NO_ERROR){error("Scene draw/readback");goto done;}ok=1;
done:g->bind(FRAMEBUFFER,0);wglMakeCurrent(dc,old);
cleanup:for(unsigned i=0;i<864;i++)free(columns[i]);return ok;}

/* Geometry-only shallow view; materials/retention/HUD remain parent-owned. */
int nf_pc_scene_gpu_draw_pose_meshes(NFPCSceneGPU*g,NFPCScene*s,const NFPCWorldMesh*const*worlds,const NFPCModelMesh*const*models,size_t count,const void*background,size_t bn,unsigned w,unsigned h,unsigned aw,unsigned ah,unsigned passes,void*out,size_t bytes){
 if(!s||s->info[3]>288||count!=s->info[3]||((background&&bn!=153600)||(!background&&bn))){error("Pose command count/background");return 0;}
 NFPCScene*view=malloc(sizeof(*view));float*owned[288]={0};size_t plane_total=0;int ok=0;
 if(!view){error("Pose view allocation");return 0;}memcpy(view,s,sizeof(*view));
 if(background)memcpy(view->background,background,153600);
 for(unsigned i=0;i<count;i++){
  const NFPCWorldMesh*wm=worlds?worlds[i]:NULL;const NFPCModelMesh*mm=models?models[i]:NULL;
  if(!wm&&!mm)continue;
  NFPCSceneCommand*c=view->commands+i;uint64_t original[16],sample[16];size_t n;const void*v;uint64_t vertices;
  if(wm){
   if(mm||c->info[1]||!nf_pc_world_mesh_info(c->world,original)||!nf_pc_world_mesh_info(wm,sample)||memcmp(original,sample,12*sizeof(uint64_t))||sample[12]>186||sample[12]%3||!nf_pc_world_mesh_buffer(wm,0,&v,&n)){error("World sample binding");goto cleanup;}
   vertices=sample[12];
  }else{
   if(!c->info[1]||!nf_pc_model_mesh_info(c->model,original)||!nf_pc_model_mesh_info(mm,sample)||memcmp(original,sample,4*sizeof(uint64_t))||original[5]!=sample[5]||sample[4]>512u*62*3||sample[4]%3||!nf_pc_model_mesh_buffer(mm,0,&v,&n)){error("Model sample binding");goto cleanup;}
   vertices=sample[4];
  }
  if(n!=vertices*20){error("Pose vertex bytes");goto cleanup;}
  size_t pn=(size_t)vertices/3*11*sizeof(float);
  if(pn>16u*1024*1024-plane_total){error("Pose plane budget");goto cleanup;}plane_total+=pn;
  if(pn){owned[i]=malloc(pn);if(!owned[i]){error("Pose plane allocation");goto cleanup;}
   for(unsigned triangle=0;triangle<vertices/3;triangle++){
    float*plane=owned[i]+triangle*11;
    if(!(wm?nf_pc_world_mesh_plane(wm,triangle,plane):nf_pc_model_mesh_plane(mm,triangle,plane))&&!(mm&&nf_pc_empty_model_plane((const float*)v+triangle*15,plane))){error("Pose texture plane");goto cleanup;}
   }
  }
  c->vertices=v;c->vertices_bytes=n;c->planes=owned[i];c->info[5]=vertices;
 }
 ok=render(g,view,w,h,aw,ah,passes,out,bytes,1,NULL);
cleanup:for(unsigned i=0;i<288;i++)free(owned[i]);free(view);return ok;
}
int nf_pc_scene_gpu_draw_world_meshes(NFPCSceneGPU*g,NFPCScene*s,const NFPCWorldMesh*const*meshes,size_t count,unsigned w,unsigned h,unsigned aw,unsigned ah,unsigned passes,void*out,size_t bytes){
 if(!meshes&&count){error("World sample command count");return 0;}
 return nf_pc_scene_gpu_draw_pose_meshes(g,s,meshes,NULL,count,NULL,0,w,h,aw,ah,passes,out,bytes);
}

int nf_pc_scene_gpu_draw(NFPCSceneGPU*g,NFPCScene*s,unsigned w,unsigned h,unsigned aw,unsigned ah,void*out,size_t n){return nf_pc_scene_gpu_draw_passes(g,s,w,h,aw,ah,15,out,n);}

NFPCSceneGPU* nf_pc_scene_gpu_open(void){return nf_pc_scene_gpu_open_window(NULL);}
int nf_pc_scene_gpu_draw_passes(NFPCSceneGPU*g,NFPCScene*s,unsigned w,unsigned h,unsigned aw,unsigned ah,unsigned passes,void*out,size_t n){return render(g,s,w,h,aw,ah,passes,out,n,1,NULL);}
int nf_pc_scene_gpu_render(NFPCSceneGPU*g,NFPCScene*s,unsigned w,unsigned h,unsigned aw,unsigned ah){return render(g,s,w,h,aw,ah,15,NULL,0,0,NULL);}
int nf_pc_scene_gpu_present(NFPCSceneGPU*g,const void*original,size_t bytes,unsigned aw,unsigned ah){
 if(!g||g->owner!=GetCurrentThreadId()||!aw||!ah||(!original&&(aw>g->width||ah>g->height||!g->target))||(original&&bytes<153600)){error("Present target/thread");return 0;}
 RECT r;if(!GetClientRect(g->window,&r)){error("Present window");return 0;}int w=r.right,h=r.bottom;if(w<1||h<1)return 1;HDC dc=wglGetCurrentDC();HGLRC old=wglGetCurrentContext();if(!wglMakeCurrent(g->dc,g->context)){error("Present make current");return 0;}int wanted=IsWindowVisible(g->window)?1:0;swap_observe(g,wanted);
 g->bind(FRAMEBUFFER,0);g->use_program(0);g->active(TEXTURE0);glDisable(GL_BLEND);glDisable(GL_DEPTH_TEST);glDisable(GL_CULL_FACE);glDisable(GL_SCISSOR_TEST);glDisable(GL_ALPHA_TEST);glViewport(0,0,w,h);glClearColor(0,0,0,1);glClear(GL_COLOR_BUFFER_BIT);int vw=w,vh=w*2/3;if(vh>h){vh=h;vw=h*3/2;}glViewport((w-vw)/2,(h-vh)/2,vw,vh);glMatrixMode(GL_PROJECTION);glLoadIdentity();glMatrixMode(GL_MODELVIEW);glLoadIdentity();glEnable(GL_TEXTURE_2D);glColor4f(1,1,1,1);
 float u=original?1:(float)aw/g->width,v=original?1:(float)ah/g->height;GLuint image=g->target;if(original){image=g->input;u=v=1;glBindTexture(GL_TEXTURE_2D,image);glPixelStorei(GL_UNPACK_ALIGNMENT,1);glTexImage2D(GL_TEXTURE_2D,0,GL_RGB,240,160,0,GL_RGBA,GL_UNSIGNED_BYTE,original);}else glBindTexture(GL_TEXTURE_2D,image);
 glBegin(GL_QUADS);glTexCoord2f(0,original?v:0);glVertex2f(-1,-1);glTexCoord2f(u,original?v:0);glVertex2f(1,-1);glTexCoord2f(u,original?0:v);glVertex2f(1,1);glTexCoord2f(0,original?0:v);glVertex2f(-1,1);glEnd();glDisable(GL_TEXTURE_2D);int ok=glGetError()==GL_NO_ERROR;if(ok&&!SwapBuffers(g->dc))ok=0;if(ok){if(wanted)g->visible_swaps++;else g->hidden_swaps++;}if(!ok)error("Present draw/swap");wglMakeCurrent(dc,old);return ok;
}

int nf_pc_scene_gpu_draw_sample(NFPCSceneGPU*g,const NFPCSceneSample*p,unsigned w,unsigned h,unsigned aw,unsigned ah,unsigned passes,void*out,size_t n){if(!p)return 0;return render(g,p->base,w,h,aw,ah,passes,out,n,1,p);}
int nf_pc_scene_gpu_render_sample(NFPCSceneGPU*g,const NFPCSceneSample*p,unsigned w,unsigned h,unsigned aw,unsigned ah){if(!p)return 0;return render(g,p->base,w,h,aw,ah,15,NULL,0,0,p);}

/* Renderer-owned source OBJ/window/effect compositor. Reader expands one
   immutable hardware row at a time; no 16MB full-row staging allocation. */
#include "obj_tile.h"
#include "obj_effect_gpu.h"
#include "obj_candidate_effect_gpu.h"
#ifndef NF_MENU_ROW_READER
#define NF_MENU_ROW_READER
typedef int (*NFMenuRowReader)(void*,unsigned,uint8_t[100480]);
#endif
static struct {HGLRC context;GLuint program,textures[3];uint32_t colors[38400],metadata[38400];unsigned effects[160][5];unsigned initializations,frames;} menu_compositor;
static void menu_compose_destroy(void){
 if(menu_compositor.context&&menu_compositor.context==wglGetCurrentContext()){
  glDeleteTextures(3,menu_compositor.textures);void(APIENTRY*remove)(GLuint)=(void*)wglGetProcAddress("glDeleteProgram");if(remove&&menu_compositor.program)remove(menu_compositor.program);
 }
 memset(&menu_compositor,0,sizeof(menu_compositor));
}
static int menu_compose_gpu_read(NFMenuRowReader read,void*source){
 if(!read||!source||!wglGetCurrentContext())return 0;
 if(menu_compositor.context&&menu_compositor.context!=wglGetCurrentContext())return 0;
 uint8_t row[100480];uint32_t*colors=menu_compositor.colors,*metadata=menu_compositor.metadata;
 for(unsigned y=0;y<160;y++){if(!read(source,y,row))return 0;const uint8_t*r=row;unsigned display=half(r+8);if((display&7)!=4||(display&0x8080)||(half(r+20)&64))return 0;
 uint16_t window[6];for(unsigned i=0;i<6;i++)window[i]=half(r+72+i*2);uint32_t tags[240];uint8_t controls[240],backdrop[240];
 if(!nf_obj_window_scanline_prepared(r+128,0x18000,r+98432,1024,r+99456,1024,display,y,window,half(r+88),half(r+92),colors+y*240,tags,controls,backdrop))return 0;
 unsigned*e=menu_compositor.effects[y];e[0]=half(r+88);e[1]=half(r+90);e[2]=half(r+92);e[3]=half(r+98432);e[4]=half(r+20)&3;
 for(unsigned x=0;x<240;x++){unsigned control=controls[x];if(!(display&0x400))control&=~4u;unsigned flags=128|control|((backdrop[x]&32)?64:0);metadata[y*240+x]=0xff000000u|(flags<<16)|(tags[x]&3)|(((tags[x]>>2)&3)<<8);}}
 void(APIENTRY*active)(GLenum)=(void*)wglGetProcAddress("glActiveTexture");void(APIENTRY*uniform1)(GLint,GLint)=(void*)wglGetProcAddress("glUniform1i");if(!active||!uniform1)return 0;
 if(!menu_compositor.program){if(!obj_shader_create(obj_candidate_effect_fragment))return 0;menu_compositor.program=obj_affine_program;menu_compositor.context=wglGetCurrentContext();menu_compositor.initializations++;glGenTextures(3,menu_compositor.textures);
 for(unsigned i=0;i<3;i++){active(0x84c0+i);glBindTexture(GL_TEXTURE_2D,menu_compositor.textures[i]);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,i==2?3840:240,i==2?2160:160,0,GL_RGBA,GL_UNSIGNED_BYTE,NULL);}}
 for(unsigned i=0;i<3;i++){active(0x84c0+i);glBindTexture(GL_TEXTURE_2D,menu_compositor.textures[i]);if(i==2)glCopyTexSubImage2D(GL_TEXTURE_2D,0,0,0,0,0,3840,2160);else glTexSubImage2D(GL_TEXTURE_2D,0,0,0,240,160,GL_RGBA,GL_UNSIGNED_BYTE,i?metadata:colors);}
 GLuint program=menu_compositor.program;obj_use(program);uniform1(obj_location(program,"candidateColor"),0);uniform1(obj_location(program,"candidateMetadata"),1);uniform1(obj_location(program,"nativeBackground"),2);
 for(unsigned y=0;y<160;y++){unsigned*e=menu_compositor.effects[y];unsigned blend=e[0],alpha=e[1],brightness=e[2],bd=e[3],priority=e[4];
 obj_uniform4(obj_location(program,"backdropColor"),((bd&31)<<3)|((bd&31)>>2),((bd>>5&31)<<3)|((bd>>5&31)>>2),((bd>>10&31)<<3)|((bd>>10&31)>>2),1);
 obj_uniform4(obj_location(program,"effectParameters"),blend>>6&3,0,0,priority);obj_uniform4(obj_location(program,"firstTargets"),!!(blend&16),!!(blend&4),!!(blend&32),0);obj_uniform4(obj_location(program,"secondTargets"),!!(blend&4096),!!(blend&1024),!!(blend&8192),0);
 unsigned ea=alpha&31,eb=alpha>>8&31,ey=brightness&31;obj_uniform4(obj_location(program,"coefficients"),ea>16?16:ea,eb>16?16:eb,ey>16?16:ey,0);
 int top=(int)ceil(y*13.5-.5),bottom=(int)ceil((y+1)*13.5-.5);glScissor(0,2160-bottom,3840,bottom-top);glBegin(GL_QUADS);glVertex2i(0,0);glVertex2i(3840,0);glVertex2i(3840,2160);glVertex2i(0,2160);glEnd();}
 obj_use(0);active(0x84c0);menu_compositor.frames++;return glGetError()==GL_NO_ERROR;
}
static int menu_contiguous_row(void*source,unsigned y,uint8_t out[100480]){if(!source||y>=160)return 0;memcpy(out,(const uint8_t*)source+y*100480,100480);return 1;}
static int menu_compose_gpu(const uint8_t*rows){return menu_compose_gpu_read(menu_contiguous_row,(void*)rows);}

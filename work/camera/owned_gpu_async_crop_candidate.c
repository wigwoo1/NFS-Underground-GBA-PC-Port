/* Isolated bounded asynchronous final-target crop diagnostic. */
#define nf_owned_gpu_close nf_base_gpu_close
#include "owned_gpu_sky_hud_view_candidate.c"
#undef nf_owned_gpu_close
#include <stddef.h>
static GLuint crop_pbo[3];static OwnedPoolSync crop_fence[3];static uint64_t crop_id[3];
static unsigned crop_head,crop_count;
static void(APIENTRY*crop_gen)(GLsizei,GLuint*);
static void(APIENTRY*crop_bind)(GLenum,GLuint);
static void(APIENTRY*crop_data)(GLenum,ptrdiff_t,const void*,GLenum);
static void*(APIENTRY*crop_map)(GLenum,GLenum);
static GLboolean(APIENTRY*crop_unmap)(GLenum);
static void(APIENTRY*crop_delete)(GLsizei,const GLuint*);
static GLenum(APIENTRY*crop_wait)(OwnedPoolSync,GLbitfield,uint64_t);
static int crop_valid(void*p){return (uintptr_t)p>3&&(intptr_t)p!=-1;}
static int crop_load(void){
 crop_gen=(void*)wglGetProcAddress("glGenBuffers");crop_bind=(void*)wglGetProcAddress("glBindBuffer");crop_data=(void*)wglGetProcAddress("glBufferData");crop_map=(void*)wglGetProcAddress("glMapBuffer");crop_unmap=(void*)wglGetProcAddress("glUnmapBuffer");crop_delete=(void*)wglGetProcAddress("glDeleteBuffers");crop_wait=(void*)wglGetProcAddress("glClientWaitSync");
 return crop_valid(crop_gen)&&crop_valid(crop_bind)&&crop_valid(crop_data)&&crop_valid(crop_map)&&crop_valid(crop_unmap)&&crop_valid(crop_delete)&&crop_valid(crop_wait)&&owned_pool_sync_load();
}
/* Capture 64x16 RGB at a caller-selected top-left pixel coordinate.
   Queue-full returns 2; caller must record omitted diagnostic samples. */
__declspec(dllexport) int nf_crop_enqueue(uint64_t id,unsigned x,unsigned y){
 if(gpu_owner!=GetCurrentThreadId()||wglGetCurrentContext()!=preview_context)return 31;
 if(!id||x>3776||y>2144)return 37;if(crop_count==3)return 2;if(!crop_load())return 39;
 unsigned i=(crop_head+crop_count)%3;GLint binding,alignment,row,skipx,skipy;
 glGetIntegerv(0x88ed,&binding);glGetIntegerv(GL_PACK_ALIGNMENT,&alignment);glGetIntegerv(GL_PACK_ROW_LENGTH,&row);glGetIntegerv(GL_PACK_SKIP_PIXELS,&skipx);glGetIntegerv(GL_PACK_SKIP_ROWS,&skipy);
 if(!crop_pbo[i])crop_gen(1,crop_pbo+i);crop_bind(0x88eb,crop_pbo[i]);crop_data(0x88eb,3072,NULL,0x88e1);
 glPixelStorei(GL_PACK_ALIGNMENT,1);glPixelStorei(GL_PACK_ROW_LENGTH,0);glPixelStorei(GL_PACK_SKIP_PIXELS,0);glPixelStorei(GL_PACK_SKIP_ROWS,0);
 glReadPixels(x,2160-y-16,64,16,GL_RGB,GL_UNSIGNED_BYTE,0);GLenum error=glGetError();
 crop_bind(0x88eb,binding);glPixelStorei(GL_PACK_ALIGNMENT,alignment);glPixelStorei(GL_PACK_ROW_LENGTH,row);glPixelStorei(GL_PACK_SKIP_PIXELS,skipx);glPixelStorei(GL_PACK_SKIP_ROWS,skipy);
 if(error)return 8;crop_fence[i]=owned_pool_make(0x9117,0);if(!crop_fence[i])return 8;
 crop_id[i]=id;crop_count++;glFlush();return 0;
}
/* 0=not ready,1=copied,2=empty. Never waits for an unsignaled fence. */
__declspec(dllexport) int nf_crop_poll(uint64_t*id,void*out,size_t bytes){
 if(gpu_owner!=GetCurrentThreadId()||wglGetCurrentContext()!=preview_context)return 31;
 if(!id||!out||bytes!=3072)return 37;if(!crop_count)return 2;
 unsigned i=crop_head;GLenum ready=crop_wait(crop_fence[i],0,0);
 if(ready==0x911b)return 0;if(ready!=0x911a&&ready!=0x911c)return 8;
 GLint binding;glGetIntegerv(0x88ed,&binding);crop_bind(0x88eb,crop_pbo[i]);uint8_t*p=crop_map(0x88eb,0x88b8);
 if(!p){crop_bind(0x88eb,binding);return 8;}
 uint8_t copy[3072];for(unsigned y=0;y<16;y++)memcpy(copy+y*192,p+(15-y)*192,192);
 GLboolean ok=crop_unmap(0x88eb);crop_bind(0x88eb,binding);if(!ok)return 8;
 memcpy(out,copy,3072);*id=crop_id[i];owned_pool_remove(crop_fence[i]);crop_fence[i]=NULL;crop_id[i]=0;crop_head=(crop_head+1)%3;crop_count--;return 1;
}
__declspec(dllexport) int nf_crop_pending(void){if(gpu_owner&&gpu_owner!=GetCurrentThreadId())return -1;return crop_count;}
__declspec(dllexport) int nf_owned_gpu_close(void){
 if(gpu_owner&&gpu_owner!=GetCurrentThreadId())return 0;
 if(preview_context){for(unsigned i=0;i<3;i++){if(crop_fence[i])owned_pool_remove(crop_fence[i]);if(crop_pbo[i])crop_delete(1,crop_pbo+i);}}
 memset(crop_pbo,0,sizeof(crop_pbo));memset(crop_fence,0,sizeof(crop_fence));memset(crop_id,0,sizeof(crop_id));crop_head=crop_count=0;
 return nf_base_gpu_close();
}


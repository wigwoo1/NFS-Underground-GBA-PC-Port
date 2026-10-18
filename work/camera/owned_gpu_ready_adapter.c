#include <windows.h>
#include <GL/gl.h>
#include <stdint.h>
typedef void* Sync;
static Sync(APIENTRY*make)(GLenum,GLbitfield);
static GLenum(APIENTRY*poll)(Sync,GLbitfield,uint64_t);
static void(APIENTRY*remove_sync)(Sync);
static int(*draw_fn)(void*);static Sync fence;static DWORD owner;static HGLRC context;
static uint64_t created,deleted,polls;
static int owns(void){return owner==GetCurrentThreadId()&&context==wglGetCurrentContext();}
__declspec(dllexport) int nf_gpu_ready_set_draw(void*fn){
 if(!fn||!wglGetCurrentContext())return 31;
 if(owner&&!owns())return 31;
 make=(void*)wglGetProcAddress("glFenceSync");poll=(void*)wglGetProcAddress("glClientWaitSync");remove_sync=(void*)wglGetProcAddress("glDeleteSync");
 if((uintptr_t)make<=3||(intptr_t)make==-1||(uintptr_t)poll<=3||(intptr_t)poll==-1||(uintptr_t)remove_sync<=3||(intptr_t)remove_sync==-1)return 39;
 owner=GetCurrentThreadId();context=wglGetCurrentContext();draw_fn=fn;return 0;
}
__declspec(dllexport) int nf_gpu_ready_draw(void*ctx){
 if(!owns()||!draw_fn)return 31;
 if(fence){remove_sync(fence);fence=NULL;deleted++;}
 int result=draw_fn(ctx);if(result)return result;
 fence=make(0x9117,0);if(!fence)return 39;created++;glFlush();return 0;
}
__declspec(dllexport) int nf_gpu_ready_poll(void*ctx){
 (void)ctx;if(!owns())return -1;if(!fence)return 1;
 polls++;GLenum status=poll(fence,0,0);if(status==0x911b)return 0;
 if(status!=0x911a&&status!=0x911c)return -1;
 remove_sync(fence);fence=NULL;deleted++;return 1;
}
__declspec(dllexport) int nf_gpu_ready_close(void){
 if(owner&&!owns())return 31;
 if(fence){remove_sync(fence);fence=NULL;deleted++;}
 owner=0;context=NULL;draw_fn=NULL;return 0;
}
__declspec(dllexport) int nf_gpu_ready_stats(uint64_t*out){if(!out)return 37;out[0]=created;out[1]=deleted;out[2]=polls;out[3]=fence!=NULL;return 0;}

#include <stdint.h>
#include <stddef.h>
#include <windows.h>
#include <GL/gl.h>
typedef struct {int(*present)(void*);void*context;int(*read)(uint64_t*);uint64_t stages[3];int result;int(*completion_read)(uint64_t*);uint64_t completion[3];int completion_result;int fence_enabled;uint64_t fence[8];int(*cpu_read)(uint64_t*);uint64_t cpu[4];int cpu_result;int(*query_read)(uint64_t*);uint64_t queries[104];int query_result;} Profile;

/* Bounded diagnostics. Timeout is always zero; never flush or wait. */
typedef void* Sync;
static Sync(APIENTRY*make_fence)(GLenum,GLbitfield);
static GLenum(APIENTRY*poll_fence)(Sync,GLbitfield,uint64_t);
static void(APIENTRY*delete_fence)(Sync);
static Sync fences[16];static uint64_t submitted[16];static unsigned count;static DWORD owner;
static uint64_t now_ns(void){LARGE_INTEGER t,f;QueryPerformanceCounter(&t);QueryPerformanceFrequency(&f);return(uint64_t)(t.QuadPart*1000000000.0/f.QuadPart);}
__declspec(dllexport) int nf_owned_profile_fences_clear(void){
 if(owner&&owner!=GetCurrentThreadId())return 0;
 for(unsigned i=0;i<count;i++){delete_fence(fences[i]);}
 count=0;owner=0;
 make_fence=NULL;poll_fence=NULL;delete_fence=NULL;return 1;
}
static int fence_init(void){
 if(owner)return owner==GetCurrentThreadId();
 if(!wglGetCurrentContext())return 0;
 make_fence=(void*)wglGetProcAddress("glFenceSync");poll_fence=(void*)wglGetProcAddress("glClientWaitSync");delete_fence=(void*)wglGetProcAddress("glDeleteSync");
 if((uintptr_t)make_fence<=3||(intptr_t)make_fence==-1||(uintptr_t)poll_fence<=3||(intptr_t)poll_fence==-1||(uintptr_t)delete_fence<=3||(intptr_t)delete_fence==-1)return 0;
 owner=GetCurrentThreadId();return 1;
}
static int collect(uint64_t*out){
 while(count){GLenum status=poll_fence(fences[0],0,0);
  if(status==0x911b)return 1; /* TIMEOUT_EXPIRED */
  if(status!=0x911a&&status!=0x911c)return 0;
  uint64_t age=now_ns()-submitted[0];if(age>out[4])out[4]=age;out[2]++;
  delete_fence(fences[0]);count--;for(unsigned i=0;i<count;i++){fences[i]=fences[i+1];submitted[i]=submitted[i+1];}
 }return 1;
}
__declspec(dllexport) int nf_owned_profile_present(void *opaque){
 Profile*p=opaque;if(!p||!p->present||!p->read)return 0;
 memset(p->fence,0,sizeof(p->fence));
 if(p->fence_enabled){uint64_t begin=now_ns();p->fence[0]=count;
  if(!fence_init()||!collect(p->fence))p->fence[6]=1;
  else{if(count)p->fence[3]=now_ns()-submitted[0];
   if(count==16)p->fence[5]=1;
   else{Sync marker=make_fence(0x9117,0);if(!marker)p->fence[6]=2;else{fences[count]=marker;submitted[count]=now_ns();count++;}}
  }p->fence[7]=now_ns()-begin;
 }
 int ok=p->present(p->context);p->result=p->read(p->stages);p->completion_result=p->completion_read?p->completion_read(p->completion):-1;
 if(p->fence_enabled){uint64_t begin=now_ns();if(!p->fence[6]&&!collect(p->fence))p->fence[6]=3;p->fence[1]=count;p->fence[7]+=now_ns()-begin;}
 p->cpu_result=p->cpu_read?p->cpu_read(p->cpu):-1;
 p->query_result=p->query_read?p->query_read(p->queries):-1;
 return ok&&p->result==0&&p->completion_result==0&&p->cpu_result==0&&p->query_result==0;
}

__declspec(dllexport) size_t nf_owned_profile_size(void){return sizeof(Profile);}
__declspec(dllexport) unsigned nf_owned_profile_fences_pending(void){return count;}

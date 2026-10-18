#include <windows.h>
#include <GL/gl.h>
#include <stdint.h>
#include <string.h>
typedef void(APIENTRY *bt_Gen)(GLsizei,GLuint*);
typedef void(APIENTRY *bt_Del)(GLsizei,const GLuint*);
typedef void(APIENTRY *bt_Counter)(GLuint,GLenum);
typedef void(APIENTRY *bt_Available)(GLuint,GLenum,GLint*);
typedef void(APIENTRY *bt_Result)(GLuint,GLenum,uint64_t*);
static bt_Gen bt_gen;static bt_Del bt_del;static bt_Counter bt_counter;static bt_Available bt_available;static bt_Result bt_result;
static DWORD bt_owner;static HGLRC bt_context;static unsigned bt_count,bt_created,bt_deleted,bt_pending;static unsigned bt_pending_indices[4096];
static struct {GLuint q[2];uint64_t row[8];} bt_records[4096];
static int bt_valid(void){return bt_owner==GetCurrentThreadId()&&bt_context&&bt_context==wglGetCurrentContext();}
static int bt_proc_valid(void*p){return p&&p!=(void*)1&&p!=(void*)2&&p!=(void*)3&&p!=(void*)(intptr_t)-1;}
__declspec(dllexport) int nf_blit_timestamp_open(void){
 if(bt_owner||!wglGetCurrentContext())return 1;
 bt_gen=(bt_Gen)wglGetProcAddress("glGenQueries");bt_del=(bt_Del)wglGetProcAddress("glDeleteQueries");bt_counter=(bt_Counter)wglGetProcAddress("glQueryCounter");bt_available=(bt_Available)wglGetProcAddress("glGetQueryObjectiv");bt_result=(bt_Result)wglGetProcAddress("glGetQueryObjectui64v");
 if(!bt_proc_valid(bt_gen)||!bt_proc_valid(bt_del)||!bt_proc_valid(bt_counter)||!bt_proc_valid(bt_available)||!bt_proc_valid(bt_result))return 2;
 bt_owner=GetCurrentThreadId();bt_context=wglGetCurrentContext();bt_count=bt_created=bt_deleted=bt_pending=0;memset(bt_records,0,sizeof(bt_records));return 0;
}
/* Never request a bt_result until BOTH availability flags are true. No flush,
   fence wait, GPU readback, or retained borrowed draw bt_context. */
__declspec(dllexport) int nf_blit_timestamp_poll(void){
 if(!bt_valid())return 1;
 for(unsigned pos=0;pos<bt_pending;){unsigned i=bt_pending_indices[pos];
  GLint a=0,b=0;bt_available(bt_records[i].q[0],0x8867,&a);bt_available(bt_records[i].q[1],0x8867,&b);
  if(a&&b){bt_result(bt_records[i].q[0],0x8866,&bt_records[i].row[3]);bt_result(bt_records[i].q[1],0x8866,&bt_records[i].row[4]);bt_records[i].row[7]=bt_records[i].row[4]>=bt_records[i].row[3]?1:2;bt_del(2,bt_records[i].q);bt_records[i].q[0]=bt_records[i].q[1]=0;bt_deleted+=2;bt_pending_indices[pos]=bt_pending_indices[--bt_pending];}else pos++;
 }
 return 0;
}
__declspec(dllexport) int nf_blit_timestamp_draw(uint64_t epoch,uint64_t generation,uint64_t index,int(*draw)(void*),void*ptr){
 if(!bt_valid()||!epoch||!generation||!draw||bt_count==4096)return 1;
 if(nf_blit_timestamp_poll())return 1;
 unsigned i=bt_count;bt_gen(2,bt_records[i].q);if(!bt_records[i].q[0]||!bt_records[i].q[1]){bt_del(2,bt_records[i].q);memset(bt_records+i,0,sizeof(bt_records[i]));return 3;}
 bt_count++;bt_created+=2;bt_pending_indices[bt_pending++]=i;bt_records[i].row[0]=epoch;bt_records[i].row[1]=generation;bt_records[i].row[2]=index;
 bt_counter(bt_records[i].q[0],0x8e28);LARGE_INTEGER begin,end,f;QueryPerformanceFrequency(&f);QueryPerformanceCounter(&begin);
 int status=draw(ptr);QueryPerformanceCounter(&end);bt_counter(bt_records[i].q[1],0x8e28);
 bt_records[i].row[5]=(uint64_t)((end.QuadPart-begin.QuadPart)*1000000000ull/f.QuadPart);bt_records[i].row[6]=(int64_t)status;return status;
}
__declspec(dllexport) unsigned nf_blit_timestamp_count(void){return bt_count;}
__declspec(dllexport) int nf_blit_timestamp_read(unsigned i,uint64_t*out){if(!out||i>=bt_count)return 1;memcpy(out,bt_records[i].row,sizeof(bt_records[i].row));return 0;}
__declspec(dllexport) int nf_blit_timestamp_stats(uint64_t*out){if(!out)return 1;out[0]=bt_created;out[1]=bt_deleted;out[2]=bt_pending;return 0;}
__declspec(dllexport) int nf_blit_timestamp_close(void){if(!bt_valid())return 1;while(bt_pending){unsigned i=bt_pending_indices[bt_pending-1];bt_del(2,bt_records[i].q);bt_records[i].q[0]=bt_records[i].q[1]=0;bt_deleted+=2;bt_pending--;bt_records[i].row[7]=3;}bt_owner=0;bt_context=NULL;return 0;}

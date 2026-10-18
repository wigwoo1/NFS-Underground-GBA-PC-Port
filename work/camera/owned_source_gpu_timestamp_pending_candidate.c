#include <windows.h>
#include <GL/gl.h>
#include <stdint.h>
#include <string.h>
typedef void(APIENTRY *Gen)(GLsizei,GLuint*);
typedef void(APIENTRY *Del)(GLsizei,const GLuint*);
typedef void(APIENTRY *Counter)(GLuint,GLenum);
typedef void(APIENTRY *Available)(GLuint,GLenum,GLint*);
typedef void(APIENTRY *Result)(GLuint,GLenum,uint64_t*);
static Gen gen;static Del del;static Counter counter;static Available available;static Result result;
static DWORD owner;static HGLRC context;static unsigned count,created,deleted,pending;static unsigned pending_indices[4096];
static struct {GLuint q[2];uint64_t row[8];} records[4096];
static int valid(void){return owner==GetCurrentThreadId()&&context&&context==wglGetCurrentContext();}
static int proc_valid(void*p){return p&&p!=(void*)1&&p!=(void*)2&&p!=(void*)3&&p!=(void*)(intptr_t)-1;}
__declspec(dllexport) int nf_source_timestamp_open(void){
 if(owner||!wglGetCurrentContext())return 1;
 gen=(Gen)wglGetProcAddress("glGenQueries");del=(Del)wglGetProcAddress("glDeleteQueries");counter=(Counter)wglGetProcAddress("glQueryCounter");available=(Available)wglGetProcAddress("glGetQueryObjectiv");result=(Result)wglGetProcAddress("glGetQueryObjectui64v");
 if(!proc_valid(gen)||!proc_valid(del)||!proc_valid(counter)||!proc_valid(available)||!proc_valid(result))return 2;
 owner=GetCurrentThreadId();context=wglGetCurrentContext();count=created=deleted=pending=0;memset(records,0,sizeof(records));return 0;
}
/* Never request a result until BOTH availability flags are true. No flush,
   fence wait, GPU readback, or retained borrowed draw context. */
__declspec(dllexport) int nf_source_timestamp_poll(void){
 if(!valid())return 1;
 for(unsigned pos=0;pos<pending;){unsigned i=pending_indices[pos];
  GLint a=0,b=0;available(records[i].q[0],0x8867,&a);available(records[i].q[1],0x8867,&b);
  if(a&&b){result(records[i].q[0],0x8866,&records[i].row[3]);result(records[i].q[1],0x8866,&records[i].row[4]);records[i].row[7]=records[i].row[4]>=records[i].row[3]?1:2;del(2,records[i].q);records[i].q[0]=records[i].q[1]=0;deleted+=2;pending_indices[pos]=pending_indices[--pending];}else pos++;
 }
 return 0;
}
__declspec(dllexport) int nf_source_timestamp_draw(uint64_t epoch,uint64_t generation,uint64_t index,int(*draw)(void*),void*ptr){
 if(!valid()||!epoch||!generation||!draw||count==4096)return 1;
 if(nf_source_timestamp_poll())return 1;
 unsigned i=count;gen(2,records[i].q);if(!records[i].q[0]||!records[i].q[1]){del(2,records[i].q);memset(records+i,0,sizeof(records[i]));return 3;}
 count++;created+=2;pending_indices[pending++]=i;records[i].row[0]=epoch;records[i].row[1]=generation;records[i].row[2]=index;
 counter(records[i].q[0],0x8e28);LARGE_INTEGER begin,end,f;QueryPerformanceFrequency(&f);QueryPerformanceCounter(&begin);
 int status=draw(ptr);QueryPerformanceCounter(&end);counter(records[i].q[1],0x8e28);
 records[i].row[5]=(uint64_t)((end.QuadPart-begin.QuadPart)*1000000000ull/f.QuadPart);records[i].row[6]=(int64_t)status;return status;
}
__declspec(dllexport) unsigned nf_source_timestamp_count(void){return count;}
__declspec(dllexport) int nf_source_timestamp_read(unsigned i,uint64_t*out){if(!out||i>=count)return 1;memcpy(out,records[i].row,sizeof(records[i].row));return 0;}
__declspec(dllexport) int nf_source_timestamp_stats(uint64_t*out){if(!out)return 1;out[0]=created;out[1]=deleted;out[2]=pending;return 0;}
__declspec(dllexport) int nf_source_timestamp_close(void){if(!valid())return 1;while(pending){unsigned i=pending_indices[pending-1];del(2,records[i].q);records[i].q[0]=records[i].q[1]=0;deleted+=2;pending--;records[i].row[7]=3;}owner=0;context=NULL;return 0;}

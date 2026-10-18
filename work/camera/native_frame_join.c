#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <windows.h>
typedef struct {const unsigned char *data;size_t size;} Span;
/* Validate before writing into caller's unpublished owned output allocation. */
__declspec(dllexport) int nf_frame_join(const Span *spans,size_t count,unsigned char *out,size_t size){
 if(!spans||!out||count>4096||size>64*1024*1024)return 0;
 size_t total=0;
 for(size_t i=0;i<count;i++){if(!spans[i].data||spans[i].size>size-total)return 0;total+=spans[i].size;}
 if(total!=size)return 0;
 size_t at=0;for(size_t i=0;i<count;i++){memcpy(out+at,spans[i].data,spans[i].size);at+=spans[i].size;}return 1;
}

__declspec(dllexport) int nf_frame_join_timed(const Span *spans,size_t count,unsigned char *out,size_t size,uint64_t *timing){
 if(!timing)return 0;
 LARGE_INTEGER begin,end,hz;ULONG64 first=0,last=0;
 QueryPerformanceFrequency(&hz);QueryThreadCycleTime(GetCurrentThread(),&first);QueryPerformanceCounter(&begin);
 int result=nf_frame_join(spans,count,out,size);
 QueryPerformanceCounter(&end);QueryThreadCycleTime(GetCurrentThread(),&last);
 timing[0]=begin.QuadPart;timing[1]=end.QuadPart;timing[2]=hz.QuadPart;timing[3]=first;timing[4]=last;return result;
}

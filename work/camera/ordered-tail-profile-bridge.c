#include <windows.h>
#include <stdint.h>
#include <stddef.h>
typedef int (*tail_fn)(const void*,size_t,unsigned*);
__declspec(dllexport) int nf_profile_ordered_tail(tail_fn fn,const void* job,size_t size,unsigned* failed,uint64_t* out){
 if(!fn||!job||!failed||!out)return -99;
 LARGE_INTEGER a,b;ULONG64 ca=0,cb=0;QueryThreadCycleTime(GetCurrentThread(),&ca);QueryPerformanceCounter(&a);
 int result=fn(job,size,failed);
 QueryPerformanceCounter(&b);QueryThreadCycleTime(GetCurrentThread(),&cb);
 LARGE_INTEGER frequency;QueryPerformanceFrequency(&frequency);
 out[0]=(uint64_t)(a.QuadPart/(double)frequency.QuadPart*1e9);out[1]=(uint64_t)(b.QuadPart/(double)frequency.QuadPart*1e9);out[2]=ca;out[3]=cb;return result;
}

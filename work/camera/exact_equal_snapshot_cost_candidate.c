#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <string.h>
#include "owned_exact_equal_sse2_candidate.h"
__declspec(dllexport) int equal_sse2(const void*a,const void*b,size_t n){return owned_exact_equal_sse2(a,b,n);}
__declspec(dllexport) int equal_original(const void*a,const void*b,size_t n){return !memcmp(a,b,n);}

static void snapshot(void){uint64_t cycles;FILETIME c,e,k,u;LARGE_INTEGER q,f;QueryPerformanceCounter(&q);QueryPerformanceFrequency(&f);QueryThreadCycleTime(GetCurrentThread(),&cycles);GetThreadTimes(GetCurrentThread(),&c,&e,&k,&u);}
__declspec(dllexport) uint64_t measure(const void*a,const void*b,size_t n,unsigned repeat,unsigned mode){LARGE_INTEGER begin,end,f;QueryPerformanceFrequency(&f);QueryPerformanceCounter(&begin);for(unsigned i=0;i<repeat;i++){if(mode)snapshot();if(mode!=2&&!equal_original(a,b,n))return UINT64_MAX;if(mode)snapshot();}QueryPerformanceCounter(&end);return (uint64_t)((end.QuadPart-begin.QuadPart)*1000000000.0/f.QuadPart);}

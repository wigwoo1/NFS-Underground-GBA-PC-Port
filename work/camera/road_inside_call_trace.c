#include <windows.h>
#include <stdint.h>
static void stamp(uint64_t *v){LARGE_INTEGER q;ULONG64 c=0;QueryPerformanceCounter(&q);QueryThreadCycleTime(GetCurrentThread(),&c);v[0]=(uint64_t)q.QuadPart;v[1]=c;}
typedef int (*camera_fn)(void*,unsigned,void*,void*,void*,void*,unsigned,void*);
typedef int (*clip_fn)(void*,unsigned,double,double,void*,void*,unsigned,void*);
__declspec(dllexport) int nf_trace_camera(void*fn,void*a,unsigned b,void*c,void*d,void*e,void*f,unsigned g,void*h,uint64_t*out){LARGE_INTEGER freq;QueryPerformanceFrequency(&freq);stamp(out);int result=((camera_fn)fn)(a,b,c,d,e,f,g,h);stamp(out+2);out[4]=freq.QuadPart;return result;}
__declspec(dllexport) int nf_trace_clip(void*fn,void*a,unsigned b,double c,double d,void*e,void*f,unsigned g,void*h,uint64_t*out){LARGE_INTEGER freq;QueryPerformanceFrequency(&freq);stamp(out);int result=((clip_fn)fn)(a,b,c,d,e,f,g,h);stamp(out+2);out[4]=freq.QuadPart;return result;}

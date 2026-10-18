#include <windows.h>
#undef near
#include "wall_visibility_batch.c"
__declspec(dllexport) int nf_wall_visibility_timed(const In*in,size_t n,int near,uint32_t scale,int cx,int cy,const uint32_t*r,size_t count,Out*out,uint64_t*trace){
 if(!trace)return 0;
 LARGE_INTEGER a,b,f;ULONG64 ca=0,cb=0;
 QueryPerformanceFrequency(&f);QueryPerformanceCounter(&a);QueryThreadCycleTime(GetCurrentThread(),&ca);
 int result=nf_wall_visibility_batch(in,n,near,scale,cx,cy,r,count,out);
 QueryThreadCycleTime(GetCurrentThread(),&cb);QueryPerformanceCounter(&b);
 trace[0]=a.QuadPart;trace[1]=b.QuadPart;trace[2]=f.QuadPart;trace[3]=cb-ca;return result;
}

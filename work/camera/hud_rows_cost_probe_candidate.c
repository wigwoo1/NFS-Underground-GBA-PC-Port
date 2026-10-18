#include <windows.h>
#include <stdint.h>
#include <stddef.h>
typedef int(*Row)(uint64_t,unsigned,unsigned,void*,unsigned);
typedef int(*Bulk)(uint64_t,unsigned,void*,size_t);
__declspec(dllexport) int nf_benchmark_hud(void*function,unsigned bulk,uint64_t epoch,unsigned refresh,void*out,size_t size,unsigned repeats,uint64_t timing[3]){
 if(!function||bulk>1||!epoch||!out||size!=160*34944u||!repeats||repeats>32||!timing)return 0;
 LARGE_INTEGER frequency,begin,end;ULONG64 a,b;QueryPerformanceFrequency(&frequency);QueryPerformanceCounter(&begin);QueryThreadCycleTime(GetCurrentThread(),&a);
 for(unsigned n=0;n<repeats;n++){
  if(bulk){if(!((Bulk)function)(epoch,refresh,out,size))return 0;}
  else for(unsigned y=0;y<160;y++)if(!((Row)function)(epoch,refresh,y,(uint8_t*)out+y*34944,34944))return 0;
 }
 QueryThreadCycleTime(GetCurrentThread(),&b);QueryPerformanceCounter(&end);timing[0]=end.QuadPart-begin.QuadPart;timing[1]=frequency.QuadPart;timing[2]=b-a;return 1;
}

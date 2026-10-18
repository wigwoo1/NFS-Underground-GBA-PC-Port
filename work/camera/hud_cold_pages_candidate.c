#include <windows.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>
typedef int(*Bulk)(uint64_t,unsigned,void*,size_t);
__declspec(dllexport) int nf_cold_hud(void*fn,uint64_t epoch,unsigned refresh,void*out,size_t size,uint64_t timing[5]){
 if(!fn||!epoch||!out||size!=160*34944u||!timing)return 0;
 void*p=VirtualAlloc(NULL,size,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);if(!p)return 0;
 LARGE_INTEGER f,a,b;ULONG64 c,d;QueryPerformanceFrequency(&f);timing[4]=f.QuadPart;
 int ok=1;
 for(unsigned pass=0;pass<2;pass++){
 QueryPerformanceCounter(&a);QueryThreadCycleTime(GetCurrentThread(),&c);
 int result=((Bulk)fn)(epoch,refresh,p,size);
 QueryThreadCycleTime(GetCurrentThread(),&d);QueryPerformanceCounter(&b);
 timing[pass*2]=b.QuadPart-a.QuadPart;timing[pass*2+1]=d-c;
 if(!result){ok=0;break;}
 if(pass==0)memcpy(out,p,size);else if(memcmp(out,p,size)){ok=0;break;}
 }
 VirtualFree(p,0,MEM_RELEASE);return ok;
}

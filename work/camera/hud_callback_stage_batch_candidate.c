#include <windows.h>
#include <stdint.h>
#include <stddef.h>
static uint64_t stamp(void){LARGE_INTEGER c,f;QueryPerformanceCounter(&c);QueryPerformanceFrequency(&f);return (uint64_t)(c.QuadPart/f.QuadPart)*1000000000ull+(uint64_t)(c.QuadPart%f.QuadPart)*1000000000ull/f.QuadPart;}
__declspec(dllexport) uint64_t nf_profile_hud_create(void *f,void *p,size_t n,uint64_t epoch,unsigned refresh,uint64_t *out){
 uint64_t a,b;QueryThreadCycleTime(GetCurrentThread(),&a);out[0]=stamp();uint64_t result=((uint64_t(*)(void*,size_t,uint64_t,unsigned))f)(p,n,epoch,refresh);out[1]=stamp();QueryThreadCycleTime(GetCurrentThread(),&b);out[2]=b-a;return result;
}
__declspec(dllexport) int nf_profile_hud_callback(void *f,void *ctx,size_t prefix,void *tail,size_t bytes,uint64_t token,uint64_t epoch,uint64_t *out){
 uint64_t a,b;QueryThreadCycleTime(GetCurrentThread(),&a);out[0]=stamp();int result=((int(*)(void*,size_t,void*,size_t,uint64_t,uint64_t))f)(ctx,prefix,tail,bytes,token,epoch);out[1]=stamp();QueryThreadCycleTime(GetCurrentThread(),&b);out[2]=b-a;return result;
}

__declspec(dllexport) int nf_profile_hud_callback_stages(void *f,void *getter,void *ctx,size_t prefix,void *tail,size_t bytes,uint64_t token,uint64_t epoch,uint64_t *out,uint64_t *stages,int *getter_status){
 if(!f||!getter||!out||!stages||!getter_status)return -999;
 uint64_t a,b;QueryThreadCycleTime(GetCurrentThread(),&a);out[0]=stamp();
 int result=((int(*)(void*,size_t,void*,size_t,uint64_t,uint64_t))f)(ctx,prefix,tail,bytes,token,epoch);
 out[1]=stamp();QueryThreadCycleTime(GetCurrentThread(),&b);out[2]=b-a;
 *getter_status=((int(*)(uint64_t*))getter)(stages);
 return result;
}

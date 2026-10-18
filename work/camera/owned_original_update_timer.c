#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
static uint64_t ticks(FILETIME a,FILETIME b){ULARGE_INTEGER x,y;x.LowPart=a.dwLowDateTime;x.HighPart=a.dwHighDateTime;y.LowPart=b.dwLowDateTime;y.HighPart=b.dwHighDateTime;return x.QuadPart+y.QuadPart;}
__declspec(dllexport) int nf_original_update_timed(void(*update)(unsigned),unsigned keys,uint64_t*out){
 if(!update||!out)return 0;LARGE_INTEGER a,b,f;FILETIME c,e,k0,u0,k1,u1;
 int cpu0=GetThreadTimes(GetCurrentThread(),&c,&e,&k0,&u0);QueryPerformanceFrequency(&f);QueryPerformanceCounter(&a);
 update(keys);
 QueryPerformanceCounter(&b);int cpu1=GetThreadTimes(GetCurrentThread(),&c,&e,&k1,&u1);
 out[0]=(uint64_t)((b.QuadPart-a.QuadPart)*1000000000.0/f.QuadPart);out[1]=cpu0&&cpu1?(ticks(k1,u1)-ticks(k0,u0))*100:UINT64_MAX;return 1;
}

static uint64_t boundary_now(void){LARGE_INTEGER q,f;QueryPerformanceFrequency(&f);QueryPerformanceCounter(&q);return (uint64_t)(q.QuadPart*1000000000.0/f.QuadPart);}
__declspec(dllexport) int nf_original_update_boundary(void(*update)(unsigned),unsigned keys,uint64_t*out){
 if(!update||!out)return 0;ULONG64 a=0,b=0;
 int ca=QueryThreadCycleTime(GetCurrentThread(),&a);
 out[0]=boundary_now();update(keys);out[1]=boundary_now();
 int cb=QueryThreadCycleTime(GetCurrentThread(),&b);
 out[2]=ca&&cb?b-a:UINT64_MAX;out[3]=GetCurrentThreadId();return 1;
}

__declspec(dllexport) int nf_original_update_boundary_cpu(void(*update)(unsigned),unsigned keys,uint64_t*out){
 if(!update||!out)return 0;FILETIME c,e,k0,u0,k1,u1;ULONG64 a=0,b=0;
 int cpu0=GetThreadTimes(GetCurrentThread(),&c,&e,&k0,&u0);
 int ca=QueryThreadCycleTime(GetCurrentThread(),&a);
 out[0]=boundary_now();update(keys);out[1]=boundary_now();
 int cb=QueryThreadCycleTime(GetCurrentThread(),&b);
 int cpu1=GetThreadTimes(GetCurrentThread(),&c,&e,&k1,&u1);
 out[2]=ca&&cb?b-a:UINT64_MAX;out[3]=GetCurrentThreadId();
 out[4]=cpu0&&cpu1?(ticks(k1,u1)-ticks(k0,u0))*100:UINT64_MAX;
 return 1;
}

/* One bounded wait slice; caller owns pause/quit checks between slices. */
__declspec(dllexport) int nf_original_deadline_wait_slice(uint64_t deadline,uint64_t*out){
 if(!out)return 0;out[0]=boundary_now();out[1]=out[0];out[2]=0;
 if(deadline<=out[0])return 1;
 uint64_t left=deadline-out[0];if(left>10000000)left=10000000;
 HANDLE timer=CreateWaitableTimerExW(NULL,NULL,2,TIMER_ALL_ACCESS);
 if(!timer){timer=CreateWaitableTimerW(NULL,TRUE,NULL);out[2]=1;}
 if(!timer)return 0;
 LARGE_INTEGER due;due.QuadPart=-(LONGLONG)((left+99)/100);
 int ok=SetWaitableTimer(timer,&due,0,NULL,NULL,FALSE)&&WaitForSingleObject(timer,1000)==WAIT_OBJECT_0;
 CloseHandle(timer);out[1]=boundary_now();return ok;
}

__declspec(dllexport) int nf_original_frame_read_boundary(int(*read_frame)(uint64_t,unsigned,void*,size_t,size_t*),uint64_t epoch,unsigned refresh,void*buffer,size_t capacity,size_t*written,uint64_t*out){
 if(!read_frame||!written||!out)return 0;ULONG64 a=0,b=0;
 int ca=QueryThreadCycleTime(GetCurrentThread(),&a);out[0]=boundary_now();
 int result=read_frame(epoch,refresh,buffer,capacity,written);
 out[1]=boundary_now();int cb=QueryThreadCycleTime(GetCurrentThread(),&b);
 out[2]=ca&&cb?b-a:UINT64_MAX;out[3]=GetCurrentThreadId();return result;
}

__declspec(dllexport) int nf_original_frame_read_batch(int(*read_frame)(uint64_t,unsigned,void*,size_t,size_t*),uint64_t epoch,unsigned refresh,void*buffer,size_t capacity,size_t*written,uint64_t*out){
 if(!read_frame||!buffer||!written||!out)return 0;ULONG64 a=0,b=0;size_t needed=0;
 int ca=QueryThreadCycleTime(GetCurrentThread(),&a);out[0]=boundary_now();
 int result=read_frame(epoch,refresh,NULL,0,&needed);
 if(result){*written=needed;result=needed<=capacity&&read_frame(epoch,refresh,buffer,capacity,written);}
 out[1]=boundary_now();int cb=QueryThreadCycleTime(GetCurrentThread(),&b);
 out[2]=ca&&cb?b-a:UINT64_MAX;out[3]=GetCurrentThreadId();return result;
}

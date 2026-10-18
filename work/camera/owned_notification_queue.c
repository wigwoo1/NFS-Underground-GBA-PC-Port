#include <windows.h>
#include <stdint.h>
#include <stdlib.h>
typedef struct {CRITICAL_SECTION lock;HANDLE items,space;unsigned capacity,head,count;uint64_t values[8];} Queue;
static uint64_t now(void){LARGE_INTEGER a,b;QueryPerformanceCounter(&a);QueryPerformanceFrequency(&b);return(uint64_t)(a.QuadPart*1000000000.0/b.QuadPart);}
__declspec(dllexport) void*nf_notification_create(unsigned capacity){
 if(!capacity||capacity>8)return NULL;
 Queue*q=calloc(1,sizeof(*q));if(!q)return NULL;
 InitializeCriticalSection(&q->lock);q->capacity=capacity;q->items=CreateSemaphoreA(NULL,0,capacity,NULL);q->space=CreateSemaphoreA(NULL,capacity,capacity,NULL);
 if(!q->items||!q->space){if(q->items)CloseHandle(q->items);if(q->space)CloseHandle(q->space);DeleteCriticalSection(&q->lock);free(q);return NULL;}return q;
}
__declspec(dllexport) int nf_notification_put(Queue*q,uint64_t value,unsigned timeout){
 if(!q)return -1;
 DWORD result=WaitForSingleObject(q->space,timeout);if(result==WAIT_TIMEOUT)return 0;if(result!=WAIT_OBJECT_0)return -1;
 EnterCriticalSection(&q->lock);q->values[(q->head+q->count)%q->capacity]=value;q->count++;LeaveCriticalSection(&q->lock);return ReleaseSemaphore(q->items,1,NULL)?1:-1;
}
/* Native timestamps bracket kernel wait independently of Python reacquisition. */
__declspec(dllexport) int nf_notification_get(Queue*q,unsigned timeout,uint64_t*out){
 if(!q||!out)return -1;
 out[0]=now();DWORD result=WaitForSingleObject(q->items,timeout);out[1]=now();if(result==WAIT_TIMEOUT){out[2]=now();return 0;}if(result!=WAIT_OBJECT_0)return -1;
 EnterCriticalSection(&q->lock);out[3]=q->values[q->head];q->head=(q->head+1)%q->capacity;q->count--;LeaveCriticalSection(&q->lock);
 if(!ReleaseSemaphore(q->space,1,NULL))return -1;
 out[2]=now();return 1;
}
/* Caller must join all users before destroying handles. */
__declspec(dllexport) void nf_notification_destroy(Queue*q){if(!q)return;CloseHandle(q->items);CloseHandle(q->space);DeleteCriticalSection(&q->lock);free(q);}

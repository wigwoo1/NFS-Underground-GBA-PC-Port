#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <Xinput.h>
#include <stdint.h>
#include "../../outputs/nfsug-research/controller.h"
/* Owner starts/stops service; render thread only requests and copies snapshots.
   Device calls never hold the snapshot lock. Failed join retains all handles. */
static HANDLE stop_event,wake_event,worker;
static SRWLOCK state_lock=SRWLOCK_INIT;
static uint32_t state[2];static uint64_t generation,sample_started_ms;
static DWORD (WINAPI *get_pad)(DWORD,XINPUT_STATE*);
static DWORD WINAPI controller_run(void*unused){
 (void)unused;HANDLE events[2]={stop_event,wake_event};
 for(;;){
  if(WaitForSingleObject(stop_event,0)==WAIT_OBJECT_0)break;
  uint64_t started=GetTickCount64();uint32_t keys=0,connected=0;XINPUT_STATE pad;
  for(DWORD i=0;i<4;i++)if(get_pad(i,&pad)==ERROR_SUCCESS){connected=1;keys=nfs_map_controller(pad.Gamepad.wButtons,pad.Gamepad.sThumbLX,pad.Gamepad.sThumbLY,pad.Gamepad.bLeftTrigger,pad.Gamepad.bRightTrigger);break;}
  AcquireSRWLockExclusive(&state_lock);state[0]=keys;state[1]=connected;sample_started_ms=started;generation++;ReleaseSRWLockExclusive(&state_lock);
  DWORD result=WaitForMultipleObjects(2,events,FALSE,16);
  if(result==WAIT_OBJECT_0||result==WAIT_FAILED)break;
 }
 return 0;
}
__declspec(dllexport) int nf_controller_service_start(void*callback){
 if(worker||!callback)return 0;
 stop_event=CreateEvent(NULL,TRUE,FALSE,NULL);wake_event=CreateEvent(NULL,FALSE,FALSE,NULL);
 if(!stop_event||!wake_event){if(stop_event)CloseHandle(stop_event);if(wake_event)CloseHandle(wake_event);stop_event=wake_event=NULL;return 0;}
 get_pad=callback;state[0]=state[1]=0;generation=0;sample_started_ms=0;
 worker=CreateThread(NULL,0,controller_run,NULL,0,NULL);
 if(!worker){CloseHandle(stop_event);CloseHandle(wake_event);stop_event=wake_event=NULL;get_pad=NULL;return 0;}return 1;
}
__declspec(dllexport) int nf_controller_service_request(void){return worker&&SetEvent(wake_event);}
__declspec(dllexport) int nf_controller_service_snapshot(uint32_t out[2],uint64_t*serial){
 if(!worker||!out||!serial)return 0;
 AcquireSRWLockShared(&state_lock);out[0]=state[0];out[1]=state[1];*serial=generation;ReleaseSRWLockShared(&state_lock);return 1;
}
/* Age starts before the OS call: a delayed response must not revive held keys. */
__declspec(dllexport) int nf_controller_service_fresh_snapshot(uint32_t out[2],uint64_t*serial,unsigned max_age_ms){
 if(!worker||!out||!serial||!max_age_ms||max_age_ms>1000)return 0;
 AcquireSRWLockShared(&state_lock);*serial=generation;
 uint64_t now=GetTickCount64();int fresh=generation&&now-sample_started_ms<=max_age_ms;
 out[0]=fresh?state[0]:0;out[1]=fresh?state[1]:0;ReleaseSRWLockShared(&state_lock);return 1;
}
__declspec(dllexport) int nf_controller_service_close(unsigned timeout_ms){
 if(timeout_ms>5000)return 0;if(!worker)return 1;SetEvent(stop_event);SetEvent(wake_event);
 if(WaitForSingleObject(worker,timeout_ms)!=WAIT_OBJECT_0)return 0;
 CloseHandle(worker);CloseHandle(stop_event);CloseHandle(wake_event);worker=stop_event=wake_event=NULL;get_pad=NULL;state[0]=state[1]=0;return 1;
}

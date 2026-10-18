#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <Xinput.h>
#include <stdint.h>
#include "../../outputs/nfsug-research/controller.h"
extern int nf_controller_service_start(void*);
extern int nf_controller_service_request(void);
extern int nf_controller_service_fresh_snapshot(uint32_t*,uint64_t*,unsigned);
extern int nf_controller_service_close(unsigned);
static int controller_started;
static HWND input_window;static WNDPROC previous_proc;static SRWLOCK input_lock=SRWLOCK_INIT;static uint32_t input_state[4];static unsigned manual_pause,space_down,quit;
static uint64_t input_message_profile[6];
__declspec(dllexport) int nf_owned_input_message_profile(uint64_t*out){if(!out)return 0;memcpy(out,input_message_profile,sizeof(input_message_profile));return 1;}
static int input_stage_timing;static uint64_t input_stage_ns[4];
static uint64_t input_now(void){LARGE_INTEGER t,f;QueryPerformanceFrequency(&f);QueryPerformanceCounter(&t);return (uint64_t)(t.QuadPart*1000000000.0/f.QuadPart);}
__declspec(dllexport) int nf_owned_input_stages(uint64_t out[4]){if(!out)return 0;memcpy(out,input_stage_ns,sizeof(input_stage_ns));return 1;}
static DWORD(WINAPI*pad_get)(DWORD,XINPUT_STATE*);
/* GBA A,B,Select,Start,Right,Left,Up,Down,R,L. Pure mapping for verification. */
__declspec(dllexport) uint32_t nf_owned_pad_keys(unsigned buttons,unsigned lt,unsigned rt,int lx,int ly){
 return nfs_map_controller((uint16_t)buttons,(int16_t)lx,(int16_t)ly,(uint8_t)lt,(uint8_t)rt);
}
static LRESULT CALLBACK input_proc(HWND h,UINT m,WPARAM w,LPARAM l){if(m==WM_CLOSE){quit=1;return 0;}return CallWindowProc(previous_proc,h,m,w,l);}
int nf_owned_input_init(HWND window){if(!window)return 0;input_window=window;manual_pause=space_down=quit=0;previous_proc=(WNDPROC)SetWindowLongPtr(window,GWLP_WNDPROC,(LONG_PTR)input_proc);
 if(!pad_get){const char*names[]={"xinput1_4.dll","xinput1_3.dll","xinput9_1_0.dll"};for(unsigned i=0;i<3&&!pad_get;i++){HMODULE m=LoadLibraryA(names[i]);if(m)pad_get=(void*)GetProcAddress(m,"XInputGetState");}}
 if(!previous_proc)return 0;
 if(pad_get){if(!nf_controller_service_start((void*)pad_get))return 0;controller_started=1;}
 return 1;
}
__declspec(dllexport) int nf_owned_input_poll(void){if(!input_window)return 0;uint64_t a=input_stage_timing?input_now():0,b=0,c=0,d=0;MSG m;if(input_stage_timing)memset(input_message_profile,0,sizeof(input_message_profile));while(PeekMessage(&m,input_window,0,0,PM_REMOVE)){uint64_t begin=input_stage_timing?input_now():0;TranslateMessage(&m);DispatchMessage(&m);if(input_stage_timing){uint64_t end=input_now();input_message_profile[5]++;if(end-begin>=input_message_profile[2]-input_message_profile[1]){input_message_profile[0]=m.message;input_message_profile[1]=begin;input_message_profile[2]=end;input_message_profile[3]=(uint64_t)m.wParam;input_message_profile[4]=(uint64_t)m.lParam;}}}if(input_stage_timing)b=input_now();unsigned focus=GetForegroundWindow()==input_window;uint32_t keys=0;unsigned space=(GetAsyncKeyState(VK_SPACE)&0x8000)!=0;
 if(focus){if(space&&!space_down)manual_pause=!manual_pause;if(GetAsyncKeyState(VK_ESCAPE)&0x8000)quit=1;const unsigned vk[10]={'Z','X',VK_BACK,VK_RETURN,VK_RIGHT,VK_LEFT,VK_UP,VK_DOWN,'S','A'};for(unsigned i=0;i<10;i++)if(GetAsyncKeyState(vk[i])&0x8000)keys|=1u<<i;}space_down=space;
 if(input_stage_timing)c=input_now();unsigned connected=0;uint32_t snapshot[2];uint64_t serial;
 if(controller_started){if(!nf_controller_service_request()||!nf_controller_service_fresh_snapshot(snapshot,&serial,100))return 0;connected=snapshot[1];if(focus)keys|=snapshot[0];}
 if(input_stage_timing)d=input_now();unsigned paused=!focus||manual_pause;AcquireSRWLockExclusive(&input_lock);input_state[0]=paused?0:keys;input_state[1]=paused;input_state[2]=quit;input_state[3]=connected;ReleaseSRWLockExclusive(&input_lock);if(input_stage_timing){uint64_t e=input_now();input_stage_ns[0]=b-a;input_stage_ns[1]=c-b;input_stage_ns[2]=d-c;input_stage_ns[3]=e-d;}return 1;
}
__declspec(dllexport) int nf_owned_input_snapshot(uint32_t out[4]){if(!out)return 0;AcquireSRWLockShared(&input_lock);for(unsigned i=0;i<4;i++)out[i]=input_state[i];ReleaseSRWLockShared(&input_lock);return 1;}

__declspec(dllexport) int nf_owned_input_poll_timed(uint64_t*out){if(!out)return 37;LARGE_INTEGER a,b,f;QueryPerformanceFrequency(&f);QueryPerformanceCounter(&a);input_stage_timing=1;int result=nf_owned_input_poll();input_stage_timing=0;QueryPerformanceCounter(&b);*out=(uint64_t)((b.QuadPart-a.QuadPart)*1000000000.0/f.QuadPart);return result;}

int nf_owned_input_close(void){
 if(controller_started&&!nf_controller_service_close(5000))return 0;
 controller_started=0;
 if(input_window&&previous_proc&&IsWindow(input_window))SetWindowLongPtr(input_window,GWLP_WNDPROC,(LONG_PTR)previous_proc);
 input_window=NULL;previous_proc=NULL;
 AcquireSRWLockExclusive(&input_lock);memset(input_state,0,sizeof(input_state));ReleaseSRWLockExclusive(&input_lock);return 1;
}

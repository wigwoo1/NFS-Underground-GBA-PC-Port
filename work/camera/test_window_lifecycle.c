#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <string.h>
#include <stdio.h>
#include <assert.h>
#include "window_lifecycle.h"
#include "frame_clock.h"
int main(void){
 HWND w=CreateWindowA("STATIC","Lifecycle test",WS_OVERLAPPED,0,0,16,16,NULL,NULL,GetModuleHandle(NULL),NULL);assert(w&&nf_window_attach(w));
 SendMessage(w,WM_SETFOCUS,0,0);assert(nf_window_running());
 SendMessage(w,WM_KEYDOWN,VK_SPACE,0);assert(!nf_window_running());
 SendMessage(w,WM_KEYDOWN,VK_SPACE,1L<<30);assert(!nf_window_running());
 SendMessage(w,WM_KILLFOCUS,0,0);SendMessage(w,WM_SETFOCUS,0,0);assert(!nf_window_running());
 SendMessage(w,WM_KEYDOWN,VK_SPACE,0);assert(nf_window_running());
 SendMessage(w,WM_SIZE,SIZE_MINIMIZED,0);assert(!nf_window_running());
 SendMessage(w,WM_SIZE,SIZE_RESTORED,0);assert(nf_window_running());
 unsigned before_resize=window_lifecycle.generation;
 SendMessage(w,WM_ENTERSIZEMOVE,0,0);assert(!nf_window_running());
 SendMessage(w,WM_EXITSIZEMOVE,0,0);assert(nf_window_running()&&window_lifecycle.generation>before_resize);
 NFFrameClock clock;NFFramePlan plan;assert(nf_frame_clock_start(&clock,0,100,5));
 assert(nf_frame_clock_poll(&clock,100000000,&plan));
 SendMessage(w,WM_KILLFOCUS,0,0);assert(!nf_window_running());
 /* The loop does not poll its clock while paused. Resume rebases wall time. */
 SendMessage(w,WM_SETFOCUS,0,0);assert(nf_window_running());
 assert(nf_frame_clock_start(&clock,30000000000ull,105,5));assert(nf_frame_clock_poll(&clock,30000000000ull,&plan)&&plan.simulation_steps==0);
 SendMessage(w,WM_CLOSE,0,0);assert(window_lifecycle.closed&&!nf_window_running()&&IsWindow(w));
 DestroyWindow(w);puts("result=PASS focus_pause_repeat_minimize_resize_resume_deferred_close=1");return 0;
}

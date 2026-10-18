#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "scene_gpu.h"
static NFPCSceneGPU* shared;
static DWORD WINAPI wrong_thread(void*unused){(void)unused;int64_t state[10];for(unsigned i=0;i<10;i++)state[i]=77;assert(!nf_pc_scene_gpu_swap_info(shared,state,sizeof(state)));for(unsigned i=0;i<10;i++)assert(state[i]==77);return 0;}
static void check(NFPCSceneGPU*g,int desired,int64_t*state){assert(nf_pc_scene_gpu_swap_info(g,state,10*sizeof(*state)));assert(state[2]==desired);if(state[0]){assert(state[3]==desired);assert(state[5]>0&&state[6]==0);}if(state[1]){assert(state[4]==desired);assert(state[7]>0);}}
int main(void){
 WNDCLASSA klass={0};klass.style=CS_OWNDC;klass.lpfnWndProc=DefWindowProcA;klass.hInstance=GetModuleHandle(NULL);klass.lpszClassName="NFSUGSwapObservationFixture";assert(RegisterClassA(&klass));
 /* WS_VISIBLE branch only, deliberately offscreen/no activation. This is not
    a physical scanout, foreground, tearing or presentation cadence test. */
 HWND window=CreateWindowA(klass.lpszClassName,"NFSUG swap state fixture",WS_POPUP,-32000,-32000,64,64,NULL,NULL,klass.hInstance,NULL);assert(window);
 NFPCSceneGPU*g=nf_pc_scene_gpu_open_window(window);if(!g){fprintf(stderr,"GPU: %s\n",nf_pc_scene_gpu_error());return 1;}
 uint32_t pixels[38400];for(unsigned i=0;i<38400;i++)pixels[i]=0xff345678u;
 assert(nf_pc_scene_gpu_present(g,pixels,sizeof(pixels),240,160));int64_t hidden[10],visible[10],again[10];check(g,0,hidden);
 assert(!nf_pc_scene_gpu_swap_info(g,NULL,sizeof(hidden)));int64_t sentinel[10];for(unsigned i=0;i<10;i++)sentinel[i]=77;
 assert(!nf_pc_scene_gpu_swap_info(NULL,sentinel,sizeof(sentinel))&&!nf_pc_scene_gpu_swap_info(g,sentinel,sizeof(sentinel)-1));for(unsigned i=0;i<10;i++)assert(sentinel[i]==77);
 shared=g;HANDLE thread=CreateThread(NULL,0,wrong_thread,NULL,0,NULL);assert(thread&&WaitForSingleObject(thread,5000)==WAIT_OBJECT_0);CloseHandle(thread);
 ShowWindow(window,SW_SHOWNOACTIVATE);assert(IsWindowVisible(window));assert(nf_pc_scene_gpu_present(g,pixels,sizeof(pixels),240,160));check(g,1,visible);
 ShowWindow(window,SW_HIDE);assert(!IsWindowVisible(window));assert(nf_pc_scene_gpu_present(g,pixels,sizeof(pixels),240,160));check(g,0,again);
 assert(again[8]==1&&again[9]==2);assert(again[5]>=hidden[5]&&again[6]==0);
 printf("{\"result\":\"PASS_REAL_WGL_SWAP_OBSERVATION_COMPONENT\",\"setter_available\":%lld,\"getter_available\":%lld,\"hidden_reported_interval\":%lld,\"visible_reported_interval\":%lld,\"hidden_again_reported_interval\":%lld,\"set_attempts\":%lld,\"set_failures\":%lld,\"readbacks\":%lld,\"visible_presents\":%lld,\"hidden_presents\":%lld,\"invalid_buffer_and_thread_guards\":true,\"offscreen_visibility_fixture\":true,\"physical_scanout_verified\":false,\"full_scene_60fps\":false}\n",(long long)again[0],(long long)again[1],(long long)hidden[4],(long long)visible[4],(long long)again[4],(long long)again[5],(long long)again[6],(long long)again[7],(long long)again[8],(long long)again[9]);
 nf_pc_scene_gpu_close(g);DestroyWindow(window);return 0;
}

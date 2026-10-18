#ifndef NF_CONTROLLER_INPUT_H
#define NF_CONTROLLER_INPUT_H
#include <windows.h>
#include <xinput.h>
#include "../../outputs/nfsug-research/controller.h"
typedef DWORD (WINAPI*NFGetPad)(DWORD,XINPUT_STATE*);
/* Fresh polling every simulation step. No cached held buttons survive a
   disconnect or focus loss; the lowest connected slot owns the controls. */
static unsigned nf_input_sample(int focused,unsigned keyboard,NFGetPad getpad,int*connected){
 *connected=0;if(!focused)return 0;
 unsigned keys=keyboard&1023;
 if(getpad)for(DWORD i=0;i<4;i++){
  XINPUT_STATE state={0};
  if(getpad(i,&state)!=ERROR_SUCCESS)continue;
  *connected=1;
  keys|=nfs_map_controller(state.Gamepad.wButtons,state.Gamepad.sThumbLX,state.Gamepad.sThumbLY,state.Gamepad.bLeftTrigger,state.Gamepad.bRightTrigger);break;
 }
 return keys;
}
static unsigned nf_input_keyboard(void){
 const int vk[]={'Z','X',VK_BACK,VK_RETURN,VK_RIGHT,VK_LEFT,VK_UP,VK_DOWN,'S','A'};unsigned keys=0;
 for(unsigned i=0;i<10;i++)if(GetAsyncKeyState(vk[i])&0x8000)keys|=1u<<i;
 return keys;
}
#endif

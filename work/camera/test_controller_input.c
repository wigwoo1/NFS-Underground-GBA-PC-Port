#include <stdio.h>
#include <assert.h>
#include "controller_input.h"
static XINPUT_STATE pads[4];static unsigned available,calls;
static DWORD WINAPI fake_pad(DWORD index,XINPUT_STATE*out){calls++;if(!(available&(1u<<index)))return ERROR_DEVICE_NOT_CONNECTED;*out=pads[index];return ERROR_SUCCESS;}
int main(void){
 int connected;unsigned tests=0;
 /* Retain reference to the real keyboard adapter without polling user input. */
 unsigned(*keyboard_adapter)(void)=nf_input_keyboard;assert(keyboard_adapter);
 const WORD buttons[]={XINPUT_GAMEPAD_A,XINPUT_GAMEPAD_B,XINPUT_GAMEPAD_BACK,XINPUT_GAMEPAD_START,XINPUT_GAMEPAD_DPAD_RIGHT,XINPUT_GAMEPAD_DPAD_LEFT,XINPUT_GAMEPAD_DPAD_UP,XINPUT_GAMEPAD_DPAD_DOWN,XINPUT_GAMEPAD_RIGHT_SHOULDER,XINPUT_GAMEPAD_LEFT_SHOULDER};
 available=1;
 for(unsigned i=0;i<10;i++){pads[0].Gamepad.wButtons=buttons[i];assert(nf_input_sample(1,0,fake_pad,&connected)==(1u<<i)&&connected);tests++;}
 pads[0].Gamepad.wButtons=XINPUT_GAMEPAD_X|XINPUT_GAMEPAD_Y;assert(nf_input_sample(1,0,fake_pad,&connected)==768);tests++;
 pads[0].Gamepad=(XINPUT_GAMEPAD){0};pads[0].Gamepad.bLeftTrigger=40;pads[0].Gamepad.bRightTrigger=40;assert(!nf_input_sample(1,0,fake_pad,&connected));tests++;
 pads[0].Gamepad.bLeftTrigger=41;pads[0].Gamepad.bRightTrigger=41;assert(nf_input_sample(1,0,fake_pad,&connected)==3);tests++;
 pads[0].Gamepad=(XINPUT_GAMEPAD){0};pads[0].Gamepad.sThumbLX=9000;pads[0].Gamepad.sThumbLY=-9000;assert(!nf_input_sample(1,0,fake_pad,&connected));tests++;
 pads[0].Gamepad.sThumbLX=9001;pads[0].Gamepad.sThumbLY=-9001;assert(nf_input_sample(1,0,fake_pad,&connected)==144);tests++;
 pads[0].Gamepad.sThumbLX=-32768;pads[0].Gamepad.sThumbLY=32767;assert(nf_input_sample(1,1,fake_pad,&connected)==97);tests++;
 available=0;assert(nf_input_sample(1,2,fake_pad,&connected)==2&&!connected);tests++;
 available=12;pads[2].Gamepad.wButtons=XINPUT_GAMEPAD_A;pads[3].Gamepad.wButtons=XINPUT_GAMEPAD_B;calls=0;
 assert(nf_input_sample(1,0,fake_pad,&connected)==1&&connected&&calls==3);tests++;
 calls=0;assert(!nf_input_sample(0,1023,fake_pad,&connected)&&!connected&&!calls);tests++;
 assert(nf_input_sample(1,0xFFFF,NULL,&connected)==1023&&!connected);tests++;
 printf("controller_checks=%u result=PASS\n",tests);return 0;
}

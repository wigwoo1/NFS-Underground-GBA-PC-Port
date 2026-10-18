static unsigned checks;
static unsigned char keyboard[256];
static HWND window=(HWND)(uintptr_t)1,foreground;
static int paused;
static DWORD results[4];
static XINPUT_STATE states[4];
static unsigned polls;
static HWND fake_foreground(void){return foreground;}
static SHORT fake_key(int vk){return keyboard[vk]?(SHORT)0x8000:0;}
static DWORD WINAPI fake_pad(DWORD slot,XINPUT_STATE* state){polls++;memset(state,0xff,sizeof(*state));if(results[slot]==ERROR_SUCCESS)*state=states[slot];return results[slot];}
static DWORD (WINAPI *getpad)(DWORD,XINPUT_STATE*)=fake_pad;
#define GetForegroundWindow fake_foreground
#define GetAsyncKeyState fake_key
/* The harness generator inserts the exact current host functions here. */
/* HOST_FUNCTIONS */
static void reset(void){memset(keyboard,0,sizeof(keyboard));memset(states,0,sizeof(states));for(unsigned i=0;i<4;i++)results[i]=ERROR_DEVICE_NOT_CONNECTED;foreground=window;paused=0;polls=0;getpad=fake_pad;}
static void expect(unsigned keys,int connected,unsigned queries){int actual_connected=99;unsigned actual=input(&actual_connected);checks++;if(actual!=keys||actual_connected!=connected||polls!=queries){fprintf(stderr,"case %u: keys %u/%u connected %d/%d polls %u/%u\n",checks,actual,keys,actual_connected,connected,polls,queries);exit(1);}polls=0;}
int main(void){
 reset();if(!controller_check())return 2;checks++;
 /* Manual expectations from the preview's keyboard/help mapping. */
 const int keys[]={'Z','X',VK_BACK,VK_RETURN,VK_RIGHT,VK_LEFT,VK_UP,VK_DOWN,'S','A'};
 const unsigned masks[]={1,2,4,8,16,32,64,128,256,512};
 for(unsigned i=0;i<10;i++){reset();getpad=NULL;keyboard[keys[i]]=1;expect(masks[i],0,0);keyboard[keys[i]]=0;expect(0,0,0);}
 /* A failed XInput call deliberately poisons its output: it must be ignored. */
 reset();expect(0,0,4);keyboard[VK_RETURN]=keyboard[VK_RIGHT]=1;expect(24,0,4);
 for(unsigned slot=0;slot<4;slot++){
  reset();results[slot]=ERROR_SUCCESS;states[slot].Gamepad.wButtons=XINPUT_GAMEPAD_A;states[slot].Gamepad.sThumbLX=-9001;expect(33,1,slot+1);
  results[slot]=ERROR_DEVICE_NOT_CONNECTED;expect(0,0,4);
  results[slot]=ERROR_SUCCESS;memset(&states[slot],0,sizeof(states[slot]));expect(0,1,slot+1);
 }
 /* First connected controller is the current documented polling policy. */
 reset();results[0]=results[1]=ERROR_SUCCESS;states[1].Gamepad.wButtons=XINPUT_GAMEPAD_A;expect(0,1,1);
 reset();results[0]=ERROR_SUCCESS;states[0].Gamepad.wButtons=XINPUT_GAMEPAD_A;keyboard['X']=1;expect(3,1,1);
 foreground=(HWND)(uintptr_t)2;expect(0,0,0);foreground=window;expect(3,1,1);
 paused=1;expect(0,0,0);paused=0;expect(3,1,1);
 keyboard['X']=0;results[0]=ERROR_DEVICE_NOT_CONNECTED;expect(0,0,4);
 /* Analog threshold edges and aliases through the actual polling function. */
 reset();results[0]=ERROR_SUCCESS;states[0].Gamepad.sThumbLX=9000;states[0].Gamepad.sThumbLY=-9000;states[0].Gamepad.bLeftTrigger=states[0].Gamepad.bRightTrigger=40;expect(0,1,1);
 states[0].Gamepad.sThumbLX=9001;states[0].Gamepad.sThumbLY=-9001;states[0].Gamepad.bLeftTrigger=states[0].Gamepad.bRightTrigger=41;expect(147,1,1);
 states[0].Gamepad.sThumbLX=-32768;states[0].Gamepad.sThumbLY=32767;expect(99,1,1);
 memset(&states[0],0,sizeof(states[0]));states[0].Gamepad.wButtons=XINPUT_GAMEPAD_X|XINPUT_GAMEPAD_Y|XINPUT_GAMEPAD_BACK|XINPUT_GAMEPAD_START;expect(780,1,1);
 states[0].Gamepad.wButtons=XINPUT_GAMEPAD_LEFT_SHOULDER|XINPUT_GAMEPAD_RIGHT_SHOULDER;expect(768,1,1);
 printf("{\"result\":\"PASS_CURRENT_HOST_XBOX_POLLING\",\"checks\":%u,\"physical_controller_exercised\":false,\"foreground_and_pause\":true,\"failed_slot_poison_ignored\":true,\"four_slot_disconnect_reconnect\":true}\n",checks);return 0;
}

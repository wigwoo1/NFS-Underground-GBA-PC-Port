#include <assert.h>
#include <stdio.h>
#include "../outputs/nfsug-research/controller.h"
int main(void){
 assert(nfs_map_controller(0,0,0,0,0)==0);
 unsigned buttons[]={0x1000,0x2000,0x20,0x10,8,4,1,2,0x200,0x100};
 for(unsigned i=0;i<10;i++)assert(nfs_map_controller(buttons[i],0,0,0,0)==(1u<<i));
 assert(nfs_map_controller(0,9000,-9000,40,40)==0);
 assert(nfs_map_controller(0,9001,0,0,0)==16);
 assert(nfs_map_controller(0,-9001,0,0,0)==32);
 assert(nfs_map_controller(0,0,9001,0,0)==64);
 assert(nfs_map_controller(0,0,-9001,0,0)==128);
 assert(nfs_map_controller(0,0,0,41,0)==2);
 assert(nfs_map_controller(0,0,0,0,41)==1);
 assert(nfs_map_controller(0x1000,-32768,0,0,255)==33);
 assert(nfs_map_controller(0x4000,0,0,0,0)==512);
 assert(nfs_map_controller(0x8000,0,0,0,0)==256);
 puts("PASS: 21 controller mapping cases. Physical controller not exercised.");return 0;
}

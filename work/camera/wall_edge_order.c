#include <stdint.h>
/* Original03001EC8..03001EF4: only horizontal endpoints swap here. */
__declspec(dllexport) int nf_wall_edge_order(int left,int right,unsigned flags,int out[3]){
 if(!out||left<-32768||left>32767||right<-32768||right>32767||flags>65535)return 0;
 if((flags&0x2000u)&&right<left)flags|=2u;
 if(flags&2u){int t=left;left=right;right=t;}
 out[0]=left;out[1]=right;out[2]=(int)flags;return 1;
}

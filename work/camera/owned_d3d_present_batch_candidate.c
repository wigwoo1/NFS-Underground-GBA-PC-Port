#include "owned_d3d_present_phase_candidate.c"
/* Same pump -> synchronized present -> statistics order, one foreign call. */
__declspec(dllexport) int nf_d3d_present_batch(HWND window,uint64_t*out,size_t bytes){
 if(!valid()||!out||bytes!=27*sizeof(uint64_t))return 37;
 memset(out,0,bytes);out[17]=draw_profile_ns();
 if(nf_d3d_window_pump(window,out+1))return 38;out[18]=draw_profile_ns();
 int status=nf_d3d_present();out[19]=draw_profile_ns();if(status!=0&&status!=3)return 39;out[0]=status;
 if(nf_d3d_display_stats(out+8))return 40;out[20]=draw_profile_ns();
 memcpy(out+21,present_ticks,sizeof(present_ticks));return 0;
}

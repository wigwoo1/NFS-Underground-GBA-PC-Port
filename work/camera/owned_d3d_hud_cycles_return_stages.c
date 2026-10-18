#include "owned_d3d_hud_cycles_return_base.c"
static uint64_t measured_stages[12];
__declspec(dllexport) int nf_d3d_open(void){int result=nf_d3d_open_measured_original();if(!result)memset(measured_stages,0,sizeof(measured_stages));return result;}
__declspec(dllexport) int nf_d3d_window_pump(HWND window,uint64_t*out){
 ULONG64 a=0,b=0;QueryThreadCycleTime(GetCurrentThread(),&a);uint64_t start=draw_profile_ns();
 int result=nf_d3d_window_pump_measured_original(window,out);uint64_t end=draw_profile_ns();QueryThreadCycleTime(GetCurrentThread(),&b);
 if(!result){measured_stages[0]=start;measured_stages[1]=end;measured_stages[2]=a;measured_stages[3]=b;measured_stages[4]=out[0];measured_stages[5]++;}return result;
}
__declspec(dllexport) int nf_d3d_world_batch(const float*v,unsigned n,size_t vb,const unsigned*o,size_t ob,const unsigned*i,size_t ib,const void*s,unsigned nd,size_t sb){
 ULONG64 a=0,b=0;QueryThreadCycleTime(GetCurrentThread(),&a);uint64_t start=draw_profile_ns();
 int result=nf_d3d_world_batch_measured_original(v,n,vb,o,ob,i,ib,s,nd,sb);uint64_t end=draw_profile_ns();QueryThreadCycleTime(GetCurrentThread(),&b);
 if(!result){measured_stages[6]=start;measured_stages[7]=end;measured_stages[8]=a;measured_stages[9]=b;measured_stages[10]=nd;measured_stages[11]++;}return result;
}
__declspec(dllexport) int nf_d3d_measured_stages(uint64_t*out,size_t bytes){if(!valid()||!out||bytes!=sizeof(measured_stages))return 37;memcpy(out,measured_stages,sizeof(measured_stages));return 0;}

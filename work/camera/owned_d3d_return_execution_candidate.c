#define nf_d3d_native_transaction nf_d3d_native_transaction_return_original
#define nf_d3d_open nf_d3d_open_return_original
#include "owned_d3d_stage_cycles_transaction_candidate.c"
#undef nf_d3d_open
#undef nf_d3d_native_transaction
static uint64_t return_execution[4];
__declspec(dllexport) int nf_d3d_open(void){int result=nf_d3d_open_return_original();if(!result)memset(return_execution,0,sizeof(return_execution));return result;}
__declspec(dllexport) int nf_d3d_native_transaction(NFTransaction authority,void*owner,HWND window,uint64_t epoch,uint64_t generation,uint64_t older,uint64_t newer,uint64_t index,double alpha,uint64_t deadline,uint64_t*out,size_t bytes){
 int result=nf_d3d_native_transaction_return_original(authority,owner,window,epoch,generation,older,newer,index,alpha,deadline,out,bytes);
 if(result!=-2){ULONG64 cycles=0;FILETIME creation,exit,kernel,user;QueryThreadCycleTime(GetCurrentThread(),&cycles);
 GetThreadTimes(GetCurrentThread(),&creation,&exit,&kernel,&user);
 return_execution[0]=draw_profile_ns();return_execution[1]=cycles;
 return_execution[2]=(((uint64_t)kernel.dwHighDateTime<<32)|kernel.dwLowDateTime)+(((uint64_t)user.dwHighDateTime<<32)|user.dwLowDateTime);return_execution[3]++;}
 return result;
}
__declspec(dllexport) int nf_d3d_return_execution(uint64_t*out,size_t bytes){if(!valid()||!out||bytes!=sizeof(return_execution))return 37;memcpy(out,return_execution,sizeof(return_execution));return 0;}

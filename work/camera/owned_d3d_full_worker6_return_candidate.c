/* D3D calls stay on owner. Dedicated worker reads mapped staging bytes only. */
#define nf_d3d_close nf_d3d_full_close_original
#include "owned_d3d_return_execution_candidate.c"
#undef nf_d3d_close
#define FULL_SLOT_COUNT 6
static ID3D11Texture2D*full_slots[FULL_SLOT_COUNT];
static uint64_t full_ids[FULL_SLOT_COUNT],full_profiles[FULL_SLOT_COUNT][8];
static volatile LONG full_state[FULL_SLOT_COUNT],full_stop;
static D3D11_MAPPED_SUBRESOURCE full_maps[FULL_SLOT_COUNT];
static void*full_dest[FULL_SLOT_COUNT];
static HANDLE full_event,full_thread;
static int full_last_slot=-1;
static DWORD WINAPI full_copy_worker(void*unused){
 for(;;){WaitForSingleObject(full_event,INFINITE);
  for(unsigned i=0;i<FULL_SLOT_COUNT;i++)if(InterlockedCompareExchange(&full_state[i],0,0)==2){
   full_profiles[i][2]=draw_profile_ns();full_profiles[i][6]=GetCurrentThreadId();
   for(unsigned y=0;y<2160;y++)memcpy((uint8_t*)full_dest[i]+y*15360,(uint8_t*)full_maps[i].pData+y*full_maps[i].RowPitch,15360);
   full_profiles[i][3]=draw_profile_ns();InterlockedExchange(&full_state[i],3);
  }
  if(InterlockedCompareExchange(&full_stop,0,0))return 0;
 }
}
static int full_start(void){
 if(full_thread)return 0;
 full_event=CreateEventW(NULL,FALSE,FALSE,NULL);if(!full_event)return 2;
 full_thread=CreateThread(NULL,0,full_copy_worker,NULL,0,NULL);
 if(!full_thread){CloseHandle(full_event);full_event=NULL;return 2;}return 0;
}
__declspec(dllexport) int nf_d3d_full_async_capture(unsigned slot,uint64_t id){
 if(!valid()||slot>=FULL_SLOT_COUNT||!id||InterlockedCompareExchange(&full_state[slot],0,0)||full_stop)return 1;
 if(full_start())return 2;
 if(!full_slots[slot]){D3D11_TEXTURE2D_DESC td;ID3D11Texture2D_GetDesc(readback,&td);
  if(td.Width!=3840||td.Height!=2160||td.Format!=DXGI_FORMAT_R8G8B8A8_UNORM)return 2;
  if(FAILED(ID3D11Device_CreateTexture2D(dev,&td,NULL,&full_slots[slot])))return 2;}
 memset(full_profiles[slot],0,sizeof(full_profiles[slot]));full_dest[slot]=NULL;
 ID3D11DeviceContext_CopyResource(ctx,(ID3D11Resource*)full_slots[slot],(ID3D11Resource*)target);
 full_ids[slot]=id;InterlockedExchange(&full_state[slot],1);return 0;
}
__declspec(dllexport) int nf_d3d_full_async_poll(unsigned slot,uint64_t id,void*rgba,size_t bytes){
 if(!valid()||slot>=FULL_SLOT_COUNT||full_ids[slot]!=id||!rgba||bytes!=3840u*2160u*4u)return 1;
 LONG state=InterlockedCompareExchange(&full_state[slot],0,0);if(!state)return 1;
 if(full_dest[slot]&&full_dest[slot]!=rgba)return 1;
 if(state==1){
  full_profiles[slot][0]=draw_profile_ns();HRESULT hr=ID3D11DeviceContext_Map(ctx,(ID3D11Resource*)full_slots[slot],0,D3D11_MAP_READ,D3D11_MAP_FLAG_DO_NOT_WAIT,&full_maps[slot]);
  full_profiles[slot][1]=draw_profile_ns();if(hr==DXGI_ERROR_WAS_STILL_DRAWING)return 3;if(FAILED(hr))return 2;
  full_dest[slot]=rgba;full_profiles[slot][7]=GetCurrentThreadId();InterlockedExchange(&full_state[slot],2);SetEvent(full_event);return 3;
 }
 if(state==2)return 3;
 ID3D11DeviceContext_Unmap(ctx,(ID3D11Resource*)full_slots[slot],0);full_profiles[slot][4]=draw_profile_ns();
 InterlockedExchange(&full_state[slot],0);full_profiles[slot][5]=draw_profile_ns();full_last_slot=slot;return 0;
}
__declspec(dllexport) int nf_d3d_full_worker_profile(unsigned slot,uint64_t id,uint64_t*out,size_t bytes){
 if(!valid()||slot>=FULL_SLOT_COUNT||!id||full_ids[slot]!=id||!out||bytes!=sizeof(full_profiles[slot])||InterlockedCompareExchange(&full_state[slot],0,0))return 1;
 memcpy(out,full_profiles[slot],sizeof(full_profiles[slot]));return 0;
}
__declspec(dllexport) int nf_d3d_full_async_poll_profile(uint64_t*out,size_t bytes){
 if(!valid()||!out||bytes!=4*sizeof(uint64_t))return 1;
 if(full_last_slot<0)return 1;unsigned i=(unsigned)full_last_slot;out[0]=full_profiles[i][0];out[1]=full_profiles[i][1];out[2]=full_profiles[i][3];out[3]=full_profiles[i][5];return 0;
}
__declspec(dllexport) int nf_d3d_full_async_stats(uint64_t*out,size_t bytes){
 if(!out||bytes!=3*sizeof(uint64_t)||(dev&&owner!=GetCurrentThreadId()))return 1;
 out[0]=out[1]=0;for(unsigned i=0;i<FULL_SLOT_COUNT;i++){out[0]+=full_slots[i]!=NULL;out[1]+=InterlockedCompareExchange(&full_state[i],0,0)!=0;}
 out[2]=out[0]*3840u*2160u*4u;return 0;
}
__declspec(dllexport) int nf_d3d_close(void){
 if(dev&&owner!=GetCurrentThreadId())return 1;
 if(full_thread){InterlockedExchange(&full_stop,1);SetEvent(full_event);if(WaitForSingleObject(full_thread,5000)!=WAIT_OBJECT_0)return 4;CloseHandle(full_thread);CloseHandle(full_event);full_thread=full_event=NULL;}
 for(unsigned i=0;i<FULL_SLOT_COUNT;i++){LONG state=InterlockedCompareExchange(&full_state[i],0,0);if(state==2||state==3)ID3D11DeviceContext_Unmap(ctx,(ID3D11Resource*)full_slots[i],0);if(full_slots[i])ID3D11Texture2D_Release(full_slots[i]);full_slots[i]=NULL;full_ids[i]=0;full_dest[i]=NULL;InterlockedExchange(&full_state[i],0);memset(full_profiles[i],0,sizeof(full_profiles[i]));}
 InterlockedExchange(&full_stop,0);full_last_slot=-1;return nf_d3d_full_close_original();
}

__declspec(dllexport) int nf_d3d_full_worker_state(unsigned slot,uint64_t id){if(!valid()||slot>=FULL_SLOT_COUNT||!id||full_ids[slot]!=id)return -1;return InterlockedCompareExchange(&full_state[slot],0,0);}
__declspec(dllexport) int nf_d3d_full_worker_lifecycle(uint64_t*out,size_t bytes){if(!out||bytes!=3*sizeof(uint64_t)||(dev&&owner!=GetCurrentThreadId()))return 1;out[0]=full_thread!=NULL;out[1]=0;for(unsigned i=0;i<FULL_SLOT_COUNT;i++){LONG state=InterlockedCompareExchange(&full_state[i],0,0);out[1]+=state==2||state==3;}out[2]=InterlockedCompareExchange(&full_stop,0,0);return 0;}

/* Full-frame asynchronous diagnostics layered over the unchanged transaction. */
#define nf_d3d_close nf_d3d_full_close_original
#include "owned_d3d_return_execution_candidate.c"
#undef nf_d3d_close
static ID3D11Texture2D*full_slots[3];
static uint64_t full_ids[3];
static unsigned full_pending[3];
static uint64_t full_poll_profile[4];
__declspec(dllexport) int nf_d3d_full_async_capture(unsigned slot,uint64_t id){
 if(!valid()||slot>=3||!id||full_pending[slot])return 1;
 if(!full_slots[slot]){D3D11_TEXTURE2D_DESC td;ID3D11Texture2D_GetDesc(readback,&td);
  if(td.Width!=3840||td.Height!=2160||td.Format!=DXGI_FORMAT_R8G8B8A8_UNORM)return 2;
  if(FAILED(ID3D11Device_CreateTexture2D(dev,&td,NULL,&full_slots[slot])))return 2;}
 ID3D11DeviceContext_CopyResource(ctx,(ID3D11Resource*)full_slots[slot],(ID3D11Resource*)target);
 full_ids[slot]=id;full_pending[slot]=1;return 0;
}
__declspec(dllexport) int nf_d3d_full_async_poll(unsigned slot,uint64_t id,void*rgba,size_t bytes){
 if(!valid()||slot>=3||!full_pending[slot]||full_ids[slot]!=id||!rgba||bytes!=3840u*2160u*4u)return 1;
 full_poll_profile[0]=draw_profile_ns();
 D3D11_MAPPED_SUBRESOURCE map;HRESULT hr=ID3D11DeviceContext_Map(ctx,(ID3D11Resource*)full_slots[slot],0,D3D11_MAP_READ,D3D11_MAP_FLAG_DO_NOT_WAIT,&map);
 full_poll_profile[1]=draw_profile_ns();
 if(hr==DXGI_ERROR_WAS_STILL_DRAWING)return 3;if(FAILED(hr))return 2;
 for(unsigned y=0;y<2160;y++)memcpy((uint8_t*)rgba+y*15360,(uint8_t*)map.pData+y*map.RowPitch,15360);
 full_poll_profile[2]=draw_profile_ns();
 ID3D11DeviceContext_Unmap(ctx,(ID3D11Resource*)full_slots[slot],0);full_pending[slot]=0;full_poll_profile[3]=draw_profile_ns();return 0;
}
__declspec(dllexport) int nf_d3d_full_async_stats(uint64_t*out,size_t bytes){
 if(!out||bytes!=3*sizeof(uint64_t)||(dev&&owner!=GetCurrentThreadId()))return 1;
 out[0]=out[1]=0;for(unsigned i=0;i<3;i++){out[0]+=full_slots[i]!=NULL;out[1]+=full_pending[i]!=0;}
 out[2]=out[0]*3840u*2160u*4u;return 0;
}
__declspec(dllexport) int nf_d3d_close(void){
 if(dev&&owner!=GetCurrentThreadId())return 1;
 for(unsigned i=0;i<3;i++){if(full_slots[i])ID3D11Texture2D_Release(full_slots[i]);full_slots[i]=NULL;full_ids[i]=0;full_pending[i]=0;}
 return nf_d3d_full_close_original();
}

__declspec(dllexport) int nf_d3d_full_async_poll_profile(uint64_t*out,size_t bytes){if(!valid()||!out||bytes!=sizeof(full_poll_profile))return 1;memcpy(out,full_poll_profile,sizeof(full_poll_profile));return 0;}

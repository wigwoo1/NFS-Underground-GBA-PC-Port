/* Diagnostic-only wrapper around the current renderer, no device selection change. */
#define nf_d3d_open nf_d3d_open_original
#include "owned_d3d_world_stream_linear_transaction_candidate.c"
#undef nf_d3d_open
static DXGI_ADAPTER_DESC1 adapter_identity;
static int adapter_identity_status=-1;
static uint64_t adapter_feature_level;
__declspec(dllexport) int nf_d3d_open(void){
 int result=nf_d3d_open_original();
 if(result)return result;
 adapter_feature_level=ID3D11Device_GetFeatureLevel(dev);
 IDXGIDevice *device=NULL;IDXGIAdapter *adapter=NULL;IDXGIAdapter1 *adapter1=NULL;
 adapter_identity_status=-2;
 if(SUCCEEDED(ID3D11Device_QueryInterface(dev,&IID_IDXGIDevice,(void**)&device)) &&
    SUCCEEDED(IDXGIDevice_GetAdapter(device,&adapter)) &&
    SUCCEEDED(IDXGIAdapter_QueryInterface(adapter,&IID_IDXGIAdapter1,(void**)&adapter1)) &&
    SUCCEEDED(IDXGIAdapter1_GetDesc1(adapter1,&adapter_identity)))adapter_identity_status=0;
 if(adapter1)IDXGIAdapter1_Release(adapter1);
 if(adapter)IDXGIAdapter_Release(adapter);
 if(device)IDXGIDevice_Release(device);
 return result;
}
__declspec(dllexport) int nf_d3d_adapter_identity(uint64_t*out,size_t bytes,wchar_t*name,size_t chars){
 if(!out||bytes!=12*sizeof(uint64_t)||!name||chars!=128||!dev)return -3;
 if(adapter_identity_status)return adapter_identity_status;
 out[0]=adapter_identity.VendorId;out[1]=adapter_identity.DeviceId;
 out[2]=adapter_identity.SubSysId;out[3]=adapter_identity.Revision;
 out[4]=adapter_identity.DedicatedVideoMemory;out[5]=adapter_identity.DedicatedSystemMemory;
 out[6]=adapter_identity.SharedSystemMemory;out[7]=adapter_identity.AdapterLuid.LowPart;
 out[8]=(uint32_t)adapter_identity.AdapterLuid.HighPart;
 out[9]=adapter_feature_level;out[10]=adapter_identity.Flags;out[11]=owner;
 memcpy(name,adapter_identity.Description,128*sizeof(wchar_t));return 0;
}

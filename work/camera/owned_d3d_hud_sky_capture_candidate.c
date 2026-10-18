#include "owned_d3d_hud_target_reuse_candidate.c"
__declspec(dllexport) int nf_d3d_read_region(unsigned x,unsigned y,unsigned w,unsigned h,void*out,size_t bytes){
 if(!valid()||!out||!w||!h||x>=3840||y>=2160||w>3840-x||h>2160-y||bytes!=(size_t)w*h*4)return 37;
 D3D11_TEXTURE2D_DESC td;memset(&td,0,sizeof(td));td.Width=w;td.Height=h;td.MipLevels=td.ArraySize=td.SampleDesc.Count=1;td.Format=DXGI_FORMAT_R8G8B8A8_UNORM;td.Usage=D3D11_USAGE_STAGING;td.CPUAccessFlags=D3D11_CPU_ACCESS_READ;
 ID3D11Texture2D*region=NULL;HRESULT hr=ID3D11Device_CreateTexture2D(dev,&td,NULL,&region);if(FAILED(hr))return 38;
 D3D11_BOX box={x,y,0,x+w,y+h,1};ID3D11DeviceContext_CopySubresourceRegion(ctx,(ID3D11Resource*)region,0,0,0,0,(ID3D11Resource*)target,0,&box);
 D3D11_MAPPED_SUBRESOURCE mapped;hr=ID3D11DeviceContext_Map(ctx,(ID3D11Resource*)region,0,D3D11_MAP_READ,0,&mapped);
 if(FAILED(hr)){ID3D11Texture2D_Release(region);return 39;}
 for(unsigned row=0;row<h;row++)memcpy((char*)out+(size_t)row*w*4,(char*)mapped.pData+(size_t)row*mapped.RowPitch,(size_t)w*4);
 ID3D11DeviceContext_Unmap(ctx,(ID3D11Resource*)region,0);ID3D11Texture2D_Release(region);return 0;
}

static unsigned sky_diag_enabled,sky_diag_ready,phase_ready;
static unsigned phase_valid[2];static double phase_weights[2];static unsigned char phase_planes[2][153600];
static unsigned char sky_diag_pixels[3840*16*4];
__declspec(dllexport) int nf_d3d_sky_diag_enable(unsigned enabled){if(!valid()||enabled>1)return 37;sky_diag_enabled=enabled;sky_diag_ready=0;phase_ready=0;return 0;}
__declspec(dllexport) int nf_d3d_source_sky_diag_batch(void*info,void*copy){sky_diag_ready=0;phase_ready=0;if(sky_diag_enabled){if(!valid()||!info||!copy)return 37;if(((SkyInfo)info)(phase_valid,phase_weights))return 37;for(unsigned i=0;i<2;i++){if(phase_valid[i]!=1||((PlaneCopy)copy)(i,phase_planes[i],153600))return 37;}phase_ready=1;}int rc=nf_d3d_source_sky_pan_batch(info,copy);if(rc||!sky_diag_enabled)return rc;rc=nf_d3d_read_region(0,600,3840,16,sky_diag_pixels,sizeof(sky_diag_pixels));if(!rc)sky_diag_ready=1;return rc;}
__declspec(dllexport) int nf_d3d_sky_diag_copy(void*out,size_t bytes){if(!valid()||!sky_diag_ready||!out||bytes!=sizeof(sky_diag_pixels))return 37;memcpy(out,sky_diag_pixels,bytes);sky_diag_ready=0;return 0;}

__declspec(dllexport) int nf_d3d_sky_phase_copy(unsigned slot,void*out,size_t bytes,double*weight){if(!valid()||!phase_ready||slot>1||!out||!weight||bytes!=153600)return 37;memcpy(out,phase_planes[slot],bytes);*weight=phase_weights[slot];return 0;}

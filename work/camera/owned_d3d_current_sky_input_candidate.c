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

__declspec(dllexport) int nf_d3d_sky_input_copy(unsigned slot,void*out,size_t bytes){
 unsigned id=1001+slot;if(!valid()||slot>1||!out||bytes!=240*160*4||cache_sizes[id]!=bytes||cache_w[id]!=240||cache_h[id]!=160||!cache_pixels[id])return 37;
 memcpy(out,cache_pixels[id],bytes);return 0;
}

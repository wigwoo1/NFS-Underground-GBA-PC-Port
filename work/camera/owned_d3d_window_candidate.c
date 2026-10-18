#define COBJMACROS
#define INITGUID
#include <windows.h>
#include <d3d11.h>
#include <dxgi.h>
#include <d3dcompiler.h>
#include <stdint.h>
#include <string.h>
static ID3D11Device*dev;static ID3D11DeviceContext*ctx;static ID3D11Texture2D*target,*readback;static ID3D11RenderTargetView*rt;static ID3D11VertexShader*vs;static ID3D11PixelShader*ps;static ID3D11InputLayout*layout;static ID3D11Buffer*constants;static ID3D11RasterizerState*rs;static ID3D11BlendState*blend[2];static ID3D11SamplerState*samplers[4];static DWORD owner;
static ID3D11Texture2D*textures[4096];static ID3D11ShaderResourceView*views[4096];
static ID3D11PixelShader*hud_ps;static ID3D11Buffer*hud_constants;static int hud_active;static unsigned hud_ids[4];
static IDXGISwapChain*chain;
static uint64_t draws,uploads,live_textures;static char compile_error[4096];
static const char*shader="cbuffer Config:register(b0){float4 ortho;float4 flags;}struct In{float2 p:POSITION;float4 uv:TEXCOORD;float4 color:COLOR;};struct Out{float4 p:SV_POSITION;float4 uv:TEXCOORD;float4 color:COLOR;};Out vertex(In i){Out o;o.p=float4(i.p.x*ortho.x+ortho.y,i.p.y*ortho.z+ortho.w,.5,1);o.uv=i.uv;o.color=i.color;return o;}Texture2D asset:register(t0);SamplerState sampling:register(s0);float4 pixel(Out i):SV_TARGET{float4 c=i.color;if(flags.x>0){uint w,h;asset.GetDimensions(w,h);float2 uv=i.uv.xy/i.uv.w;int2 t=(int2)floor(uv*float2(w,h));int mode=(int)flags.w;t.x=(mode&1)?((t.x%(int)w+(int)w)%(int)w):clamp(t.x,0,(int)w-1);t.y=(mode&2)?((t.y%(int)h+(int)h)%(int)h):clamp(t.y,0,(int)h-1);c*=asset.Load(int3(t,0));}if(flags.y>0&&c.a<=flags.z)discard;return c;}";
static int valid(void){return dev&&owner==GetCurrentThreadId();}
__declspec(dllexport) const char*nf_d3d_compile_error(void){return compile_error;}
__declspec(dllexport) int nf_d3d_close(void){if(dev&&owner!=GetCurrentThreadId())return 1;if(ctx){ID3D11DeviceContext_ClearState(ctx);ID3D11DeviceContext_Flush(ctx);}for(unsigned i=0;i<4096;i++){if(views[i])ID3D11ShaderResourceView_Release(views[i]);if(textures[i])ID3D11Texture2D_Release(textures[i]);views[i]=NULL;textures[i]=NULL;}live_textures=0;
#define DROP(type,x) if(x){type##_Release(x);x=NULL;}
 DROP(ID3D11PixelShader,hud_ps);DROP(ID3D11Buffer,hud_constants);hud_active=0;DROP(IDXGISwapChain,chain);DROP(ID3D11Buffer,constants);DROP(ID3D11InputLayout,layout);DROP(ID3D11PixelShader,ps);DROP(ID3D11VertexShader,vs);DROP(ID3D11RasterizerState,rs);for(unsigned i=0;i<2;i++){DROP(ID3D11BlendState,blend[i]);}for(unsigned i=0;i<4;i++){DROP(ID3D11SamplerState,samplers[i]);}DROP(ID3D11RenderTargetView,rt);DROP(ID3D11Texture2D,readback);DROP(ID3D11Texture2D,target);DROP(ID3D11DeviceContext,ctx);DROP(ID3D11Device,dev);owner=0;return 0;}
__declspec(dllexport) int nf_d3d_open(void){if(dev)return 1;HRESULT h;owner=GetCurrentThreadId();draws=uploads=0;compile_error[0]=0;
#define CHECK(expr,code) if(FAILED(h=(expr))){nf_d3d_close();return code;}
 CHECK(D3D11CreateDevice(NULL,D3D_DRIVER_TYPE_HARDWARE,NULL,0,NULL,0,D3D11_SDK_VERSION,&dev,NULL,&ctx),2);
 D3D11_TEXTURE2D_DESC td;memset(&td,0,sizeof(td));td.Width=3840;td.Height=2160;td.MipLevels=td.ArraySize=td.SampleDesc.Count=1;td.Format=DXGI_FORMAT_R8G8B8A8_UNORM;td.BindFlags=D3D11_BIND_RENDER_TARGET;CHECK(ID3D11Device_CreateTexture2D(dev,&td,NULL,&target),3);CHECK(ID3D11Device_CreateRenderTargetView(dev,(ID3D11Resource*)target,NULL,&rt),4);td.BindFlags=0;td.Usage=D3D11_USAGE_STAGING;td.CPUAccessFlags=D3D11_CPU_ACCESS_READ;CHECK(ID3D11Device_CreateTexture2D(dev,&td,NULL,&readback),5);
 ID3DBlob*v=NULL,*p=NULL,*err=NULL;h=D3DCompile(shader,strlen(shader),NULL,NULL,NULL,"vertex","vs_4_0",D3DCOMPILE_ENABLE_STRICTNESS,0,&v,&err);if(FAILED(h)){if(err){strncpy(compile_error,ID3D10Blob_GetBufferPointer(err),4095);ID3D10Blob_Release(err);}nf_d3d_close();return 6;}if(err)ID3D10Blob_Release(err);err=NULL;
 h=D3DCompile(shader,strlen(shader),NULL,NULL,NULL,"pixel","ps_4_0",D3DCOMPILE_ENABLE_STRICTNESS,0,&p,&err);if(FAILED(h)){if(err){strncpy(compile_error,ID3D10Blob_GetBufferPointer(err),4095);ID3D10Blob_Release(err);}ID3D10Blob_Release(v);nf_d3d_close();return 7;}if(err)ID3D10Blob_Release(err);
 h=ID3D11Device_CreateVertexShader(dev,ID3D10Blob_GetBufferPointer(v),ID3D10Blob_GetBufferSize(v),NULL,&vs);if(SUCCEEDED(h))h=ID3D11Device_CreatePixelShader(dev,ID3D10Blob_GetBufferPointer(p),ID3D10Blob_GetBufferSize(p),NULL,&ps);
 D3D11_INPUT_ELEMENT_DESC elements[3]={{"POSITION",0,DXGI_FORMAT_R32G32_FLOAT,0,0,D3D11_INPUT_PER_VERTEX_DATA,0},{"TEXCOORD",0,DXGI_FORMAT_R32G32B32A32_FLOAT,0,8,D3D11_INPUT_PER_VERTEX_DATA,0},{"COLOR",0,DXGI_FORMAT_R32G32B32A32_FLOAT,0,24,D3D11_INPUT_PER_VERTEX_DATA,0}};if(SUCCEEDED(h))h=ID3D11Device_CreateInputLayout(dev,elements,3,ID3D10Blob_GetBufferPointer(v),ID3D10Blob_GetBufferSize(v),&layout);ID3D10Blob_Release(v);ID3D10Blob_Release(p);if(FAILED(h)){nf_d3d_close();return 8;}
 D3D11_BUFFER_DESC bd;memset(&bd,0,sizeof(bd));bd.ByteWidth=32;bd.BindFlags=D3D11_BIND_CONSTANT_BUFFER;CHECK(ID3D11Device_CreateBuffer(dev,&bd,NULL,&constants),9);
 D3D11_RASTERIZER_DESC rd;memset(&rd,0,sizeof(rd));rd.FillMode=D3D11_FILL_SOLID;rd.CullMode=D3D11_CULL_NONE;rd.DepthClipEnable=TRUE;rd.ScissorEnable=TRUE;CHECK(ID3D11Device_CreateRasterizerState(dev,&rd,&rs),10);
 for(unsigned i=0;i<2;i++){D3D11_BLEND_DESC b;memset(&b,0,sizeof(b));b.RenderTarget[0].RenderTargetWriteMask=15;b.RenderTarget[0].BlendEnable=i;b.RenderTarget[0].SrcBlend=b.RenderTarget[0].SrcBlendAlpha=D3D11_BLEND_SRC_ALPHA;b.RenderTarget[0].DestBlend=b.RenderTarget[0].DestBlendAlpha=D3D11_BLEND_INV_SRC_ALPHA;b.RenderTarget[0].BlendOp=b.RenderTarget[0].BlendOpAlpha=D3D11_BLEND_OP_ADD;CHECK(ID3D11Device_CreateBlendState(dev,&b,&blend[i]),11);}
 for(unsigned i=0;i<4;i++){D3D11_SAMPLER_DESC s;memset(&s,0,sizeof(s));s.Filter=D3D11_FILTER_MIN_MAG_MIP_POINT;s.AddressU=i&1?D3D11_TEXTURE_ADDRESS_WRAP:D3D11_TEXTURE_ADDRESS_CLAMP;s.AddressV=i&2?D3D11_TEXTURE_ADDRESS_WRAP:D3D11_TEXTURE_ADDRESS_CLAMP;s.AddressW=D3D11_TEXTURE_ADDRESS_CLAMP;s.MaxLOD=D3D11_FLOAT32_MAX;CHECK(ID3D11Device_CreateSamplerState(dev,&s,&samplers[i]),12);}return 0;}
__declspec(dllexport) int nf_d3d_texture(unsigned id,unsigned w,unsigned h,const void*rgba,size_t bytes){if(!valid()||!id||id>=4096||!w||!h||w>4096||h>4096||!rgba||bytes!=(size_t)w*h*4)return 1;if(views[id])ID3D11ShaderResourceView_Release(views[id]);if(textures[id]){ID3D11Texture2D_Release(textures[id]);live_textures--;}views[id]=NULL;textures[id]=NULL;D3D11_TEXTURE2D_DESC td;memset(&td,0,sizeof(td));td.Width=w;td.Height=h;td.MipLevels=td.ArraySize=td.SampleDesc.Count=1;td.Format=DXGI_FORMAT_R8G8B8A8_UNORM;td.BindFlags=D3D11_BIND_SHADER_RESOURCE;D3D11_SUBRESOURCE_DATA data={rgba,w*4,0};HRESULT hresult=ID3D11Device_CreateTexture2D(dev,&td,&data,&textures[id]);if(FAILED(hresult))return 2;live_textures++;if(FAILED(ID3D11Device_CreateShaderResourceView(dev,(ID3D11Resource*)textures[id],NULL,&views[id])))return 3;uploads++;return 0;}
__declspec(dllexport) int nf_d3d_clear(const float*color){if(!valid()||!color)return 1;ID3D11DeviceContext_ClearRenderTargetView(ctx,rt,color);return 0;}
/* Ten floats/vertex: raw source XY, projective STRQ, RGBA. No CPU image. */
__declspec(dllexport) int nf_d3d_draw(const float*vertices,unsigned count,unsigned texture,unsigned sampling,unsigned blending,const float*config,const int*scissor){if(!valid()||!vertices||!count||count>65536||count%3||texture>=4096||sampling>3||blending>1||!config||!scissor||(config[4]>0&&!views[texture]))return 1;D3D11_BUFFER_DESC bd;memset(&bd,0,sizeof(bd));bd.ByteWidth=count*40;bd.BindFlags=D3D11_BIND_VERTEX_BUFFER;bd.Usage=D3D11_USAGE_IMMUTABLE;D3D11_SUBRESOURCE_DATA data={vertices,0,0};ID3D11Buffer*vb=NULL;if(FAILED(ID3D11Device_CreateBuffer(dev,&bd,&data,&vb)))return 2;float load_config[8];memcpy(load_config,config,32);load_config[7]=(float)sampling;load_config[0]=(float)(2.0/((double)config[1]-config[0]));load_config[1]=(float)(-((double)config[1]+config[0])/((double)config[1]-config[0]));load_config[2]=(float)(2.0/((double)config[3]-config[2]));load_config[3]=(float)(-((double)config[3]+config[2])/((double)config[3]-config[2]));ID3D11DeviceContext_UpdateSubresource(ctx,(ID3D11Resource*)constants,0,NULL,load_config,0,0);UINT stride=40,offset=0;ID3D11DeviceContext_IASetVertexBuffers(ctx,0,1,&vb,&stride,&offset);ID3D11DeviceContext_IASetInputLayout(ctx,layout);ID3D11DeviceContext_IASetPrimitiveTopology(ctx,D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);ID3D11DeviceContext_VSSetShader(ctx,vs,NULL,0);ID3D11DeviceContext_PSSetShader(ctx,ps,NULL,0);ID3D11DeviceContext_VSSetConstantBuffers(ctx,0,1,&constants);ID3D11DeviceContext_PSSetConstantBuffers(ctx,0,1,&constants);ID3D11DeviceContext_PSSetShaderResources(ctx,0,1,&views[texture]);ID3D11DeviceContext_PSSetSamplers(ctx,0,1,&samplers[sampling]);ID3D11DeviceContext_OMSetRenderTargets(ctx,1,&rt,NULL);ID3D11DeviceContext_OMSetBlendState(ctx,blend[blending],NULL,0xffffffff);ID3D11DeviceContext_RSSetState(ctx,rs);D3D11_VIEWPORT vp={(float)scissor[4],(float)(2160-scissor[5]-scissor[7]),(float)scissor[6],(float)scissor[7],0,1};ID3D11DeviceContext_RSSetViewports(ctx,1,&vp);D3D11_RECT rect={scissor[0],scissor[1],scissor[2],scissor[3]};ID3D11DeviceContext_RSSetScissorRects(ctx,1,&rect);if(hud_active){ID3D11ShaderResourceView*inputs[4];for(unsigned j=0;j<4;j++)inputs[j]=views[hud_ids[j]];ID3D11DeviceContext_PSSetShader(ctx,hud_ps,NULL,0);ID3D11DeviceContext_PSSetConstantBuffers(ctx,0,1,&hud_constants);ID3D11DeviceContext_PSSetShaderResources(ctx,0,4,inputs);}ID3D11DeviceContext_Draw(ctx,count,0);ID3D11Buffer_Release(vb);draws++;return 0;}
__declspec(dllexport) int nf_d3d_read(void*rgba,size_t bytes){if(!valid()||!rgba||bytes!=3840u*2160u*4u)return 1;ID3D11DeviceContext_CopyResource(ctx,(ID3D11Resource*)readback,(ID3D11Resource*)target);D3D11_MAPPED_SUBRESOURCE map;if(FAILED(ID3D11DeviceContext_Map(ctx,(ID3D11Resource*)readback,0,D3D11_MAP_READ,0,&map)))return 2;for(unsigned y=0;y<2160;y++)memcpy((uint8_t*)rgba+y*15360,(uint8_t*)map.pData+y*map.RowPitch,15360);ID3D11DeviceContext_Unmap(ctx,(ID3D11Resource*)readback,0);return 0;}
__declspec(dllexport) int nf_d3d_stats(uint64_t*out){if(!out)return 1;out[0]=draws;out[1]=uploads;out[2]=live_textures;out[3]=dev!=NULL;return 0;}

/* HUD background snapshot: native GPU copy, with top-down D3D coordinates. */
__declspec(dllexport) int nf_d3d_copy_target(unsigned id){
 if(!valid()||!id||id>=4096)return 1;
 D3D11_TEXTURE2D_DESC td;ID3D11Texture2D_GetDesc(target,&td);td.BindFlags=D3D11_BIND_SHADER_RESOURCE;
 ID3D11Texture2D*next=NULL;ID3D11ShaderResourceView*view=NULL;
 if(FAILED(ID3D11Device_CreateTexture2D(dev,&td,NULL,&next)))return 2;
 if(FAILED(ID3D11Device_CreateShaderResourceView(dev,(ID3D11Resource*)next,NULL,&view))){ID3D11Texture2D_Release(next);return 3;}
 ID3D11DeviceContext_CopyResource(ctx,(ID3D11Resource*)next,(ID3D11Resource*)target);
 if(views[id])ID3D11ShaderResourceView_Release(views[id]);
 if(textures[id]){ID3D11Texture2D_Release(textures[id]);live_textures--;}
 textures[id]=next;views[id]=view;live_textures++;return 0;
}

__declspec(dllexport) int nf_d3d_hud_shader(const void*code,size_t bytes){
 if(!valid()||!code||!bytes||hud_ps)return 1;
 if(FAILED(ID3D11Device_CreatePixelShader(dev,code,bytes,NULL,&hud_ps)))return 2;
 D3D11_BUFFER_DESC bd;memset(&bd,0,sizeof(bd));bd.ByteWidth=96;bd.BindFlags=D3D11_BIND_CONSTANT_BUFFER;
 if(FAILED(ID3D11Device_CreateBuffer(dev,&bd,NULL,&hud_constants))){ID3D11PixelShader_Release(hud_ps);hud_ps=NULL;return 3;}return 0;
}
__declspec(dllexport) int nf_d3d_hud_draw(const float*vertices,unsigned count,const unsigned*ids,const void*parameters,const float*config,const int*rect){
 if(!valid()||!hud_ps||!ids||!parameters||hud_active)return 1;
 for(unsigned j=0;j<4;j++){if(ids[j]>=4096||!views[ids[j]])return 1;hud_ids[j]=ids[j];}
 ID3D11DeviceContext_UpdateSubresource(ctx,(ID3D11Resource*)hud_constants,0,NULL,parameters,0,0);
 hud_active=1;int result=nf_d3d_draw(vertices,count,0,0,0,config,rect);hud_active=0;return result;
}

__declspec(dllexport) int nf_d3d_window(HWND window){
 if(!valid()||!IsWindow(window)||chain)return 1;
 IDXGIDevice*dx=NULL;IDXGIAdapter*adapter=NULL;IDXGIFactory*factory=NULL;
 HRESULT h=ID3D11Device_QueryInterface(dev,&IID_IDXGIDevice,(void**)&dx);
 if(SUCCEEDED(h))h=IDXGIDevice_GetAdapter(dx,&adapter);
 if(SUCCEEDED(h))h=IDXGIAdapter_GetParent(adapter,&IID_IDXGIFactory,(void**)&factory);
 if(SUCCEEDED(h)){
 DXGI_SWAP_CHAIN_DESC d;memset(&d,0,sizeof(d));d.BufferDesc.Width=3840;d.BufferDesc.Height=2160;d.BufferDesc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;d.SampleDesc.Count=1;d.BufferUsage=DXGI_USAGE_RENDER_TARGET_OUTPUT;d.BufferCount=2;d.OutputWindow=window;d.Windowed=TRUE;d.SwapEffect=DXGI_SWAP_EFFECT_DISCARD;
 h=IDXGIFactory_CreateSwapChain(factory,(IUnknown*)dev,&d,&chain);
 if(SUCCEEDED(h))IDXGIFactory_MakeWindowAssociation(factory,window,DXGI_MWA_NO_ALT_ENTER);
 }
 if(factory)IDXGIFactory_Release(factory);if(adapter)IDXGIAdapter_Release(adapter);if(dx)IDXGIDevice_Release(dx);
 return FAILED(h)?2:0;
}
__declspec(dllexport) int nf_d3d_present(void){
 if(!valid()||!chain)return 1;ID3D11Texture2D*back=NULL;
 if(FAILED(IDXGISwapChain_GetBuffer(chain,0,&IID_ID3D11Texture2D,(void**)&back)))return 2;
 ID3D11DeviceContext_CopyResource(ctx,(ID3D11Resource*)back,(ID3D11Resource*)target);ID3D11Texture2D_Release(back);
 HRESULT h=IDXGISwapChain_Present(chain,1,0);return h==S_OK?0:(h==DXGI_STATUS_OCCLUDED?3:4);
}

/* Endpoint-anchored one-sided reconstruction; filter width bounded by source boundary distance.
   Explicit experimental convention, not proof of original spatial fidelity. */
/* Isolated horizontal translation coverage: phase shifts a source pixel boundary.
   Original alpha-boundary selection retained until separately verified. */
#define COBJMACROS
#define INITGUID
#include <windows.h>
#include <d3d11.h>
#include <dxgi.h>
#include <d3dcompiler.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
static ID3D11Device*dev;static ID3D11DeviceContext*ctx;static ID3D11Texture2D*target,*readback;static ID3D11RenderTargetView*rt;static ID3D11VertexShader*vs;static ID3D11PixelShader*ps;static ID3D11InputLayout*layout;static ID3D11Buffer*constants;static ID3D11RasterizerState*rs;static ID3D11BlendState*blend[2];static ID3D11SamplerState*samplers[4];static DWORD owner;
static ID3D11Buffer*world_buffer;static const float*world_vertices;static uint64_t world_buffer_creates;
static ID3D11Buffer*quad_buffers[8];static unsigned char quad_bytes[8][240];static unsigned quad_next;static uint64_t quad_creates,quad_reuses;
static uint8_t*cache_pixels[4096];static size_t cache_sizes[4096],cache_total;static unsigned cache_w[4096],cache_h[4096];static uint64_t cache_hits,cache_uploads;
static void invalidate_cache(unsigned id){if(cache_pixels[id]){cache_total-=cache_sizes[id];free(cache_pixels[id]);}cache_pixels[id]=NULL;cache_sizes[id]=0;cache_w[id]=cache_h[id]=0;}
static ID3D11Texture2D*textures[4096];static ID3D11ShaderResourceView*views[4096];
static ID3D11PixelShader*hud_ps;static ID3D11Buffer*hud_constants;static int hud_active;static unsigned hud_ids[4];
static IDXGISwapChain*chain;static ID3D11PixelShader*sky_pan_ps;static ID3D11Buffer*sky_pan_constants;static int sky_pan_active;
static ID3D11Texture2D*async_readbacks[3];static uint64_t async_ids[3];static unsigned async_pending[3];
static uint64_t draws,uploads,live_textures;static char compile_error[4096];
static const char*shader="cbuffer Config:register(b0){float4 ortho;float4 flags;}struct In{float2 p:POSITION;float4 uv:TEXCOORD;float4 color:COLOR;};struct Out{float4 p:SV_POSITION;float4 uv:TEXCOORD;float4 color:COLOR;};Out vertex(In i){Out o;o.p=float4(i.p.x*ortho.x+ortho.y,i.p.y*ortho.z+ortho.w,.5,1);o.uv=i.uv;o.color=i.color;return o;}Texture2D asset:register(t0);SamplerState sampling:register(s0);float4 pixel(Out i):SV_TARGET{float4 c=i.color;if(flags.x>0){uint w,h;asset.GetDimensions(w,h);float2 uv=i.uv.xy/i.uv.w;int2 t=(int2)floor(uv*float2(w,h));int mode=(int)flags.w;t.x=(mode&1)?((t.x%(int)w+(int)w)%(int)w):clamp(t.x,0,(int)w-1);t.y=(mode&2)?((t.y%(int)h+(int)h)%(int)h):clamp(t.y,0,(int)h-1);c*=asset.Load(int3(t,0));}if(flags.y>0&&c.a<=flags.z)discard;return c;}";
static int valid(void){return dev&&owner==GetCurrentThreadId();}
__declspec(dllexport) const char*nf_d3d_compile_error(void){return compile_error;}
__declspec(dllexport) int nf_d3d_close(void){if(dev&&owner!=GetCurrentThreadId())return 1;if(ctx){ID3D11DeviceContext_ClearState(ctx);ID3D11DeviceContext_Flush(ctx);}for(unsigned i=0;i<4096;i++){if(views[i])ID3D11ShaderResourceView_Release(views[i]);if(textures[i])ID3D11Texture2D_Release(textures[i]);views[i]=NULL;textures[i]=NULL;}live_textures=0;for(unsigned j=0;j<4096;j++)invalidate_cache(j);
#define DROP(type,x) if(x){type##_Release(x);x=NULL;}
 for(unsigned i=0;i<3;i++){if(async_readbacks[i])ID3D11Texture2D_Release(async_readbacks[i]);async_readbacks[i]=NULL;async_pending[i]=0;async_ids[i]=0;}
 for(unsigned i=0;i<8;i++){if(quad_buffers[i])ID3D11Buffer_Release(quad_buffers[i]);quad_buffers[i]=NULL;}quad_next=0;
 DROP(ID3D11PixelShader,sky_pan_ps);DROP(ID3D11Buffer,sky_pan_constants);sky_pan_active=0;DROP(ID3D11PixelShader,hud_ps);DROP(ID3D11Buffer,hud_constants);hud_active=0;DROP(IDXGISwapChain,chain);DROP(ID3D11Buffer,constants);DROP(ID3D11InputLayout,layout);DROP(ID3D11PixelShader,ps);DROP(ID3D11VertexShader,vs);DROP(ID3D11RasterizerState,rs);for(unsigned i=0;i<2;i++){DROP(ID3D11BlendState,blend[i]);}for(unsigned i=0;i<4;i++){DROP(ID3D11SamplerState,samplers[i]);}DROP(ID3D11RenderTargetView,rt);DROP(ID3D11Texture2D,readback);DROP(ID3D11Texture2D,target);DROP(ID3D11DeviceContext,ctx);DROP(ID3D11Device,dev);owner=0;return 0;}
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
__declspec(dllexport) int nf_d3d_texture(unsigned id,unsigned w,unsigned h,const void*rgba,size_t bytes){if(!valid()||!id||id>=4096||!w||!h||w>4096||h>4096||!rgba||bytes!=(size_t)w*h*4)return 1;invalidate_cache(id);if(views[id])ID3D11ShaderResourceView_Release(views[id]);if(textures[id]){ID3D11Texture2D_Release(textures[id]);live_textures--;}views[id]=NULL;textures[id]=NULL;D3D11_TEXTURE2D_DESC td;memset(&td,0,sizeof(td));td.Width=w;td.Height=h;td.MipLevels=td.ArraySize=td.SampleDesc.Count=1;td.Format=DXGI_FORMAT_R8G8B8A8_UNORM;td.BindFlags=D3D11_BIND_SHADER_RESOURCE;D3D11_SUBRESOURCE_DATA data={rgba,w*4,0};HRESULT hresult=ID3D11Device_CreateTexture2D(dev,&td,&data,&textures[id]);if(FAILED(hresult))return 2;live_textures++;if(FAILED(ID3D11Device_CreateShaderResourceView(dev,(ID3D11Resource*)textures[id],NULL,&views[id])))return 3;uploads++;return 0;}
__declspec(dllexport) int nf_d3d_clear(const float*color){if(!valid()||!color)return 1;ID3D11DeviceContext_ClearRenderTargetView(ctx,rt,color);return 0;}
/* Ten floats/vertex: raw source XY, projective STRQ, RGBA. No CPU image. */
__declspec(dllexport) int nf_d3d_draw(const float*vertices,unsigned count,unsigned texture,unsigned sampling,unsigned blending,const float*config,const int*scissor){if(!valid()||!vertices||!count||count>65536||count%3||texture>=4096||sampling>3||blending>1||!config||!scissor||(config[4]>0&&!views[texture]))return 1;ID3D11Buffer*vb=NULL;UINT first_vertex=0;int cached=-1;if(world_buffer){vb=world_buffer;ID3D11Buffer_AddRef(vb);first_vertex=(UINT)((vertices-world_vertices)/10);}if(count==6&&!vb){for(unsigned i=0;i<8;i++)if(quad_buffers[i]&&!memcmp(quad_bytes[i],vertices,240)){vb=quad_buffers[i];ID3D11Buffer_AddRef(vb);quad_reuses++;break;}}if(!vb){D3D11_BUFFER_DESC bd;memset(&bd,0,sizeof(bd));bd.ByteWidth=count*40;bd.BindFlags=D3D11_BIND_VERTEX_BUFFER;bd.Usage=D3D11_USAGE_IMMUTABLE;D3D11_SUBRESOURCE_DATA data={vertices,0,0};if(FAILED(ID3D11Device_CreateBuffer(dev,&bd,&data,&vb)))return 2;if(count==6){cached=quad_next;quad_next=(quad_next+1)%8;if(quad_buffers[cached])ID3D11Buffer_Release(quad_buffers[cached]);quad_buffers[cached]=vb;ID3D11Buffer_AddRef(vb);memcpy(quad_bytes[cached],vertices,240);quad_creates++;}}float load_config[8];memcpy(load_config,config,32);load_config[7]=(float)sampling;load_config[0]=(float)(2.0/((double)config[1]-config[0]));load_config[1]=(float)(-((double)config[1]+config[0])/((double)config[1]-config[0]));load_config[2]=(float)(2.0/((double)config[3]-config[2]));load_config[3]=(float)(-((double)config[3]+config[2])/((double)config[3]-config[2]));ID3D11DeviceContext_UpdateSubresource(ctx,(ID3D11Resource*)constants,0,NULL,load_config,0,0);UINT stride=40,offset=0;ID3D11DeviceContext_IASetVertexBuffers(ctx,0,1,&vb,&stride,&offset);ID3D11DeviceContext_IASetInputLayout(ctx,layout);ID3D11DeviceContext_IASetPrimitiveTopology(ctx,D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);ID3D11DeviceContext_VSSetShader(ctx,vs,NULL,0);ID3D11DeviceContext_PSSetShader(ctx,ps,NULL,0);ID3D11DeviceContext_VSSetConstantBuffers(ctx,0,1,&constants);ID3D11DeviceContext_PSSetConstantBuffers(ctx,0,1,&constants);ID3D11DeviceContext_PSSetShaderResources(ctx,0,1,&views[texture]);ID3D11DeviceContext_PSSetSamplers(ctx,0,1,&samplers[sampling]);ID3D11DeviceContext_OMSetRenderTargets(ctx,1,&rt,NULL);ID3D11DeviceContext_OMSetBlendState(ctx,blend[blending],NULL,0xffffffff);ID3D11DeviceContext_RSSetState(ctx,rs);D3D11_VIEWPORT vp={(float)scissor[4],(float)(2160-scissor[5]-scissor[7]),(float)scissor[6],(float)scissor[7],0,1};ID3D11DeviceContext_RSSetViewports(ctx,1,&vp);D3D11_RECT rect={scissor[0],scissor[1],scissor[2],scissor[3]};ID3D11DeviceContext_RSSetScissorRects(ctx,1,&rect);if(hud_active){ID3D11ShaderResourceView*inputs[4];for(unsigned j=0;j<4;j++)inputs[j]=views[hud_ids[j]];ID3D11DeviceContext_PSSetShader(ctx,hud_ps,NULL,0);ID3D11DeviceContext_PSSetConstantBuffers(ctx,0,1,&hud_constants);ID3D11DeviceContext_PSSetShaderResources(ctx,0,4,inputs);}if(sky_pan_active){ID3D11ShaderResourceView*inputs[2]={views[1001],views[1002]};ID3D11DeviceContext_PSSetShader(ctx,sky_pan_ps,NULL,0);ID3D11DeviceContext_PSSetShaderResources(ctx,0,2,inputs);ID3D11DeviceContext_PSSetConstantBuffers(ctx,1,1,&sky_pan_constants);}ID3D11DeviceContext_Draw(ctx,count,first_vertex);ID3D11Buffer_Release(vb);draws++;return 0;}
__declspec(dllexport) int nf_d3d_read(void*rgba,size_t bytes){if(!valid()||!rgba||bytes!=3840u*2160u*4u)return 1;ID3D11DeviceContext_CopyResource(ctx,(ID3D11Resource*)readback,(ID3D11Resource*)target);D3D11_MAPPED_SUBRESOURCE map;if(FAILED(ID3D11DeviceContext_Map(ctx,(ID3D11Resource*)readback,0,D3D11_MAP_READ,0,&map)))return 2;for(unsigned y=0;y<2160;y++)memcpy((uint8_t*)rgba+y*15360,(uint8_t*)map.pData+y*map.RowPitch,15360);ID3D11DeviceContext_Unmap(ctx,(ID3D11Resource*)readback,0);return 0;}
__declspec(dllexport) int nf_d3d_stats(uint64_t*out){if(!out)return 1;out[0]=draws;out[1]=uploads;out[2]=live_textures;out[3]=dev!=NULL;return 0;}

/* HUD background snapshot: native GPU copy, with top-down D3D coordinates. */
static uint64_t hud_target_creates,hud_target_reuses;
__declspec(dllexport) int nf_d3d_hud_target_stats(uint64_t*out){if(!valid()||!out)return 1;out[0]=hud_target_creates;out[1]=hud_target_reuses;return 0;}
__declspec(dllexport) int nf_d3d_copy_target(unsigned id){
 if(!valid()||!id||id>=4096)return 1;invalidate_cache(id);
 D3D11_TEXTURE2D_DESC td;ID3D11Texture2D_GetDesc(target,&td);td.BindFlags=D3D11_BIND_SHADER_RESOURCE;
 if(id==1004&&textures[id]&&views[id]){
  D3D11_TEXTURE2D_DESC previous;ID3D11Texture2D_GetDesc(textures[id],&previous);
  if(!memcmp(&previous,&td,sizeof(td))){
   ID3D11ShaderResourceView*empty[4]={NULL,NULL,NULL,NULL};
   ID3D11DeviceContext_PSSetShaderResources(ctx,0,4,empty);
   ID3D11DeviceContext_CopyResource(ctx,(ID3D11Resource*)textures[id],(ID3D11Resource*)target);
   hud_target_reuses++;return 0;
  }
 }

 ID3D11Texture2D*next=NULL;ID3D11ShaderResourceView*view=NULL;
 if(FAILED(ID3D11Device_CreateTexture2D(dev,&td,NULL,&next)))return 2;
 if(FAILED(ID3D11Device_CreateShaderResourceView(dev,(ID3D11Resource*)next,NULL,&view))){ID3D11Texture2D_Release(next);return 3;}
 ID3D11DeviceContext_CopyResource(ctx,(ID3D11Resource*)next,(ID3D11Resource*)target);
 if(views[id])ID3D11ShaderResourceView_Release(views[id]);
 if(textures[id]){ID3D11Texture2D_Release(textures[id]);live_textures--;}
 textures[id]=next;views[id]=view;live_textures++;if(id==1004)hud_target_creates++;return 0;
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
 DXGI_SWAP_CHAIN_DESC d;memset(&d,0,sizeof(d));d.BufferDesc.Width=3840;d.BufferDesc.Height=2160;d.BufferDesc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;d.SampleDesc.Count=1;d.BufferUsage=DXGI_USAGE_RENDER_TARGET_OUTPUT;d.BufferCount=2;d.OutputWindow=window;d.Windowed=TRUE;d.SwapEffect=(DXGI_SWAP_EFFECT)4;
 h=IDXGIFactory_CreateSwapChain(factory,(IUnknown*)dev,&d,&chain);
 if(SUCCEEDED(h))IDXGIFactory_MakeWindowAssociation(factory,window,DXGI_MWA_NO_ALT_ENTER);
 }
 if(factory)IDXGIFactory_Release(factory);if(adapter)IDXGIAdapter_Release(adapter);if(dx)IDXGIDevice_Release(dx);
 return FAILED(h)?2:0;
}
static uint64_t present_ticks[6];
static uint64_t present_qpc(void){LARGE_INTEGER t;QueryPerformanceCounter(&t);return (uint64_t)t.QuadPart;}
__declspec(dllexport) int nf_d3d_present_phase_ticks(uint64_t*out,size_t bytes){if(!valid()||!out||bytes!=sizeof(present_ticks))return 1;memcpy(out,present_ticks,bytes);return 0;}
__declspec(dllexport) int nf_d3d_present(void){
 memset(present_ticks,0,sizeof(present_ticks));
 if(!valid()||!chain)return 1;ID3D11Texture2D*back=NULL;
 LARGE_INTEGER f;QueryPerformanceFrequency(&f);present_ticks[0]=f.QuadPart;present_ticks[1]=present_qpc();
 if(FAILED(IDXGISwapChain_GetBuffer(chain,0,&IID_ID3D11Texture2D,(void**)&back)))return 2;
 present_ticks[2]=present_qpc();
 ID3D11DeviceContext_CopyResource(ctx,(ID3D11Resource*)back,(ID3D11Resource*)target);present_ticks[3]=present_qpc();
 ID3D11Texture2D_Release(back);present_ticks[4]=present_qpc();
 HRESULT h=IDXGISwapChain_Present(chain,1,0);present_ticks[5]=present_qpc();return h==S_OK?0:(h==DXGI_STATUS_OCCLUDED?3:4);
}

__declspec(dllexport) int nf_d3d_window_pump(HWND window,uint64_t*out){
 if(!valid()||!IsWindow(window)||!out||GetWindowThreadProcessId(window,NULL)!=owner)return 1;
 MSG m;unsigned count=0;while(PeekMessageW(&m,NULL,0,0,PM_REMOVE)){if(m.message==WM_QUIT)break;TranslateMessage(&m);DispatchMessageW(&m);count++;}
 RECT r;memset(&r,0,sizeof(r));if(!GetClientRect(window,&r))return 2;
 out[0]=count;out[1]=IsWindowVisible(window);out[2]=IsIconic(window);out[3]=r.right-r.left;out[4]=r.bottom-r.top;out[5]=(uint64_t)(uintptr_t)GetForegroundWindow();out[6]=(uint64_t)(uintptr_t)window;return 0;
}

__declspec(dllexport) int nf_d3d_quad_cache_stats(uint64_t out[3]){if(!out)return 1;out[0]=quad_creates;out[1]=quad_reuses;out[2]=0;for(unsigned i=0;i<8;i++)out[2]+=quad_buffers[i]!=NULL;return 0;}

__declspec(dllexport) int nf_d3d_hud_batch(const float*vertices,unsigned count,const unsigned*ids,const void*records,unsigned n,size_t bytes,const float*config){
 if(!valid()||!hud_ps||hud_active||!vertices||!count||count>65536||count%3||!ids||!records||!config||!n||n>160||bytes!=(size_t)n*112)return 1;
 for(unsigned j=0;j<4;j++)if(ids[j]>=4096||!views[ids[j]])return 1;
 const unsigned char*raw=(const unsigned char*)records;
 for(unsigned i=0;i<n;i++){int clip[4];memcpy(clip,raw+i*112+96,16);if(clip[0]<0||clip[1]<0||clip[2]>3840||clip[3]>2160||clip[0]>=clip[2]||clip[1]>=clip[3])return 1;}
 for(unsigned i=0;i<n;i++){int rect[8]={0,0,0,0,0,0,3840,2160};memcpy(rect,raw+i*112+96,16);int result=nf_d3d_hud_draw(vertices,count,ids,raw+i*112,config,rect);if(result)return result;}
 return 0;
}

__declspec(dllexport) int nf_d3d_world_batch(const float*vertices,unsigned nv,size_t vertex_bytes,const unsigned*offsets,size_t offset_bytes,const unsigned*ids,size_t id_bytes,const void*states,unsigned nd,size_t state_bytes){
 if(!valid()||!vertices||!offsets||!ids||!states||nv>65536||nd>4096||vertex_bytes!=(size_t)nv*40||offset_bytes!=((size_t)nd+1)*4||id_bytes!=(size_t)nd*4||state_bytes!=(size_t)nd*72||offsets[0]!=0||offsets[nd]!=nv)return 1;
 const unsigned char*raw=(const unsigned char*)states;
 for(unsigned i=0;i<nd;i++){float config[8];unsigned mode[2];memcpy(config,raw+i*72,32);memcpy(mode,raw+i*72+64,8);if(offsets[i]>=offsets[i+1]||offsets[i+1]>nv||(offsets[i+1]-offsets[i])%3||ids[i]>=4096||mode[0]>3||mode[1]>1||(config[4]>0&&!views[ids[i]]))return 1;}
 if(!nd)return 0;if(world_buffer)return 1;D3D11_BUFFER_DESC bd;memset(&bd,0,sizeof(bd));bd.ByteWidth=nv*40;bd.BindFlags=D3D11_BIND_VERTEX_BUFFER;bd.Usage=D3D11_USAGE_IMMUTABLE;D3D11_SUBRESOURCE_DATA data={vertices,0,0};if(FAILED(ID3D11Device_CreateBuffer(dev,&bd,&data,&world_buffer)))return 2;world_buffer_creates++;world_vertices=vertices;int status=0;
 for(unsigned i=0;i<nd;i++){float config[8];int rect[8];unsigned mode[2];memcpy(config,raw+i*72,32);memcpy(rect,raw+i*72+32,32);memcpy(mode,raw+i*72+64,8);status=nf_d3d_draw(vertices+offsets[i]*10,offsets[i+1]-offsets[i],ids[i],mode[0],mode[1],config,rect);if(status)break;}
 ID3D11Buffer_Release(world_buffer);world_buffer=NULL;world_vertices=NULL;return status;
}

__declspec(dllexport) int nf_d3d_world_upload_stats(uint64_t out[2]){if(!out)return 1;out[0]=world_buffer_creates;out[1]=world_buffer!=NULL;return 0;}

__declspec(dllexport) int nf_d3d_backdrop(const uint8_t*rgba,size_t bytes){
 if(!valid()||!rgba||bytes!=640)return 1;
 float vertices[9600];unsigned count=0;
 const unsigned corner[6][2]={{0,0},{1,0},{0,1},{1,0},{1,1},{0,1}};
 for(unsigned y=0;y<160;){unsigned end=y+1;while(end<160&&!memcmp(rgba+y*4,rgba+end*4,4))end++;
  for(unsigned j=0;j<6;j++){float*v=vertices+count*10;v[0]=corner[j][0]?240:0;v[1]=(float)(corner[j][1]?end:y);v[2]=(float)corner[j][0];v[3]=(float)corner[j][1];v[4]=0;v[5]=1;for(unsigned k=0;k<4;k++)v[6+k]=(float)rgba[y*4+k]/255.0f;count++;}y=end;
 }
 const float config[8]={0,240,160,0,0,0,0,0};const int rect[8]={0,0,3840,2160,300,0,3240,2160};return nf_d3d_draw(vertices,count,0,0,0,config,rect);
}

static void fixed_quad(float*v,float w,float h,float alpha){const unsigned corner[6][2]={{0,0},{1,0},{0,1},{1,0},{1,1},{0,1}};for(unsigned j=0;j<6;j++){float*x=v+j*10;x[0]=corner[j][0]?w:0;x[1]=corner[j][1]?h:0;x[2]=(float)corner[j][0];x[3]=(float)corner[j][1];x[4]=0;x[5]=1;x[6]=x[7]=x[8]=1;x[9]=alpha;}}
__declspec(dllexport) int nf_d3d_sky_quad(unsigned layer,float alpha){if(!valid()||layer>1||!(alpha>=0&&alpha<=1))return 1;float v[60];fixed_quad(v,240,160,alpha);float config[8]={0,240,160,0,1,layer==0,.5,0};int rect[8]={0,0,3840,2160,300,0,3240,2160};return nf_d3d_draw(v,6,1001+layer,3,layer,config,rect);}
__declspec(dllexport) int nf_d3d_hud_fixed_quad(const unsigned*ids,const void*records,unsigned n,size_t bytes){float v[60];fixed_quad(v,3840,2160,1);const float config[8]={0,3840,2160,0,0,0,0,0};return nf_d3d_hud_batch(v,6,ids,records,n,bytes,config);}

__declspec(dllexport) int nf_d3d_texture_cached(unsigned id,unsigned w,unsigned h,const void*rgba,size_t bytes){
 if(!valid()||!id||id>=4096||!w||!h||w>4096||h>4096||!rgba||bytes!=(size_t)w*h*4)return 1;
 if(cache_pixels[id]&&cache_w[id]==w&&cache_h[id]==h&&cache_sizes[id]==bytes&&!memcmp(cache_pixels[id],rgba,bytes)){cache_hits++;return 0;}
 int status=nf_d3d_texture(id,w,h,rgba,bytes);if(status)return status;cache_uploads++;
 if(bytes<=16u*1024u*1024u-cache_total){uint8_t*owned=malloc(bytes);if(owned){memcpy(owned,rgba,bytes);cache_pixels[id]=owned;cache_sizes[id]=bytes;cache_w[id]=w;cache_h[id]=h;cache_total+=bytes;}}
 return 0;
}
__declspec(dllexport) int nf_d3d_texture_cache_stats(uint64_t*out){if(!out)return 1;out[0]=cache_uploads;out[1]=cache_hits;out[2]=cache_total;return 0;}

/* Validate the entire source material packet before uploading any record. */
__declspec(dllexport) int nf_d3d_material_packet_cached(const void*rgba,size_t bytes,const unsigned*records,unsigned count,size_t record_bytes){
 if(!valid()||!rgba||!records||count>64||bytes>16u*1024u*1024u||record_bytes!=(size_t)count*16)return 1;
 for(unsigned i=0;i<count;i++){const unsigned*r=records+4*i;if(!r[0]||!r[1]||r[0]>4096||r[1]>4096||r[3]!=(size_t)r[0]*r[1]*4||r[2]>bytes||r[3]>bytes-r[2])return 1;}
 for(unsigned i=0;i<count;i++){const unsigned*r=records+4*i;int status=nf_d3d_texture_cached(i+1,r[0],r[1],(const uint8_t*)rgba+r[2],r[3]);if(status)return status;}
 return 0;
}

static uint8_t auxiliary_pixels[153600],auxiliary_hud_records[160*112];
typedef int(*SkyInfo)(unsigned*,double*);typedef int(*PlaneCopy)(unsigned,void*,size_t);typedef int(*HUDInfo)(unsigned*);typedef unsigned(*HUDCount)(void);typedef int(*HUDCopy)(void*,size_t);
__declspec(dllexport) int nf_d3d_source_sky_batch(SkyInfo info,PlaneCopy copy){
 if(!valid()||!info||!copy)return 1;unsigned enabled[2];double alpha[2];if(info(enabled,alpha))return 1;
 for(unsigned i=0;i<2;i++)if(enabled[i]>1||(enabled[i]&&!(alpha[i]>=0&&alpha[i]<=1)))return 1;
 for(unsigned i=0;i<2;i++)if(enabled[i]){if(copy(i,auxiliary_pixels,sizeof(auxiliary_pixels)))return 1;int result=nf_d3d_texture_cached(1001+i,240,160,auxiliary_pixels,sizeof(auxiliary_pixels));if(result)return result;result=nf_d3d_sky_quad(i,(float)alpha[i]);if(result)return result;}
 return 0;
}
static uint64_t hud_phase_ticks[12];
static void hud_tick(unsigned i){LARGE_INTEGER t;QueryPerformanceCounter(&t);hud_phase_ticks[i]=(uint64_t)t.QuadPart;}
__declspec(dllexport) int nf_d3d_hud_phase_ticks(uint64_t*out,size_t bytes){if(!valid()||!out||bytes!=sizeof(hud_phase_ticks))return 1;memcpy(out,hud_phase_ticks,sizeof(hud_phase_ticks));return 0;}
__declspec(dllexport) int nf_d3d_source_hud_batch(HUDInfo info,PlaneCopy copy,HUDCount count,HUDCopy records){
 memset(hud_phase_ticks,0,sizeof(hud_phase_ticks));LARGE_INTEGER f;QueryPerformanceFrequency(&f);hud_phase_ticks[0]=(uint64_t)f.QuadPart;hud_tick(1);
 if(!valid()||!info||!copy||!count||!records)return 1;unsigned enabled[2];if(info(enabled)||enabled[0]>1)return 1;if(!enabled[0])return 0;unsigned n=count();if(n>160)return 1;hud_tick(2);
 int result=nf_d3d_copy_target(1004);hud_tick(3);if(result)return result;
 for(unsigned i=0;i<3;i++){if(copy(i,auxiliary_pixels,sizeof(auxiliary_pixels)))return 1;hud_tick(4+i*2);result=nf_d3d_texture_cached(1010+i,240,160,auxiliary_pixels,sizeof(auxiliary_pixels));hud_tick(5+i*2);if(result)return result;}
 if(records(auxiliary_hud_records,n*112))return 1;hud_tick(10);const unsigned ids[4]={1010,1011,1004,1012};result=nf_d3d_hud_fixed_quad(ids,auxiliary_hud_records,n,n*112);hud_tick(11);return result;
}

__declspec(dllexport) int nf_d3d_backdrop_rows(const unsigned char*rows,size_t bytes){
 if(!valid()||!rows||bytes!=640)return 1;
 static float vertices[160*6*10];unsigned n=0;
 const float xyuv[6][4]={{0,0,0,0},{240,0,1,0},{0,1,0,1},{240,0,1,0},{240,1,1,1},{0,1,0,1}};
 for(unsigned start=0;start<160;){unsigned end=start+1;while(end<160&&!memcmp(rows+start*4,rows+end*4,4))end++;
  for(unsigned v=0;v<6;v++){float*q=vertices+n++*10;q[0]=xyuv[v][0];q[1]=xyuv[v][1]*(end-start)+start;q[2]=xyuv[v][2];q[3]=xyuv[v][3];q[4]=0;q[5]=1;for(unsigned c=0;c<4;c++)q[6+c]=(float)rows[start*4+c]/255.0f;}
  start=end;
 }
 const float config[8]={0,240,160,0,0,0,0,0};const int rect[8]={0,0,3840,2160,300,0,3240,2160};
 return nf_d3d_draw(vertices,n,0,0,0,config,rect);
}

__declspec(dllexport) int nf_d3d_async_capture(unsigned slot,uint64_t id){
 if(!valid()||slot>=3||async_pending[slot])return 1;
 if(!async_readbacks[slot]){D3D11_TEXTURE2D_DESC td;ID3D11Texture2D_GetDesc(readback,&td);td.Width=512;td.Height=64;if(FAILED(ID3D11Device_CreateTexture2D(dev,&td,NULL,&async_readbacks[slot])))return 2;}
 D3D11_BOX box={300,594,0,812,658,1};ID3D11DeviceContext_CopySubresourceRegion(ctx,(ID3D11Resource*)async_readbacks[slot],0,0,0,0,(ID3D11Resource*)target,0,&box);async_ids[slot]=id;async_pending[slot]=1;return 0;
}
__declspec(dllexport) int nf_d3d_async_poll(unsigned slot,uint64_t id,void*rgba,size_t bytes){
 if(!valid()||slot>=3||!async_pending[slot]||async_ids[slot]!=id||!rgba||bytes!=512u*64u*4u)return 1;
 D3D11_MAPPED_SUBRESOURCE map;HRESULT hr=ID3D11DeviceContext_Map(ctx,(ID3D11Resource*)async_readbacks[slot],0,D3D11_MAP_READ,D3D11_MAP_FLAG_DO_NOT_WAIT,&map);
 if(hr==DXGI_ERROR_WAS_STILL_DRAWING)return 3;if(FAILED(hr))return 2;
 for(unsigned y=0;y<64;y++)memcpy((uint8_t*)rgba+y*2048,(uint8_t*)map.pData+y*map.RowPitch,2048);
 ID3D11DeviceContext_Unmap(ctx,(ID3D11Resource*)async_readbacks[slot],0);async_pending[slot]=0;return 0;
}
__declspec(dllexport) int nf_d3d_async_stats(unsigned out[2]){if(!out)return 1;out[0]=out[1]=0;for(unsigned i=0;i<3;i++){out[0]+=async_readbacks[i]!=NULL;out[1]+=async_pending[i]!=0;}return 0;}

__declspec(dllexport) int nf_d3d_display_stats(uint64_t out[9]){
 if(!valid()||!chain||!out)return 1;memset(out,0,9*sizeof(uint64_t));DXGI_FRAME_STATISTICS stats;memset(&stats,0,sizeof(stats));UINT count=0;HRESULT a=IDXGISwapChain_GetFrameStatistics(chain,&stats);HRESULT b=IDXGISwapChain_GetLastPresentCount(chain,&count);out[0]=(uint32_t)a;out[1]=(uint32_t)b;if(SUCCEEDED(b))out[2]=count;if(SUCCEEDED(a)){out[3]=stats.PresentCount;out[4]=stats.PresentRefreshCount;out[5]=stats.SyncRefreshCount;out[6]=stats.SyncQPCTime.QuadPart;out[7]=stats.SyncGPUTime.QuadPart;}LARGE_INTEGER f;QueryPerformanceFrequency(&f);out[8]=f.QuadPart;return 0;
}

__declspec(dllexport) int nf_d3d_sky_pan(float phase){
 if(!valid()||!(phase>=0&&phase<=1)||!views[1001]||!views[1002])return 1;
 if(!sky_pan_ps){const char*code="cbuffer SkyPan:register(b1){float phase;float3 padding;}struct Out{float4 p:SV_POSITION;float4 uv:TEXCOORD;float4 color:COLOR;};Texture2D lower:register(t0);Texture2D upper:register(t1);float4 pixel(Out i):SV_TARGET{float2 source=float2((i.p.x-300)*2/27,i.p.y*2/27);int2 t=(int2)floor(source);t=clamp(t,int2(0,0),int2(239,159));float4 c=lower.Load(int3(t,0));float4 next=upper.Load(int3(t,0));if(c.a>.5&&next.a>.5){float boundary=1-frac(source.x);float width=min(2.0/27.0,boundary);float coverage=saturate((phase-boundary)/width+1);c=lerp(c,next,coverage);}else if(floor(source.x+phase)>floor(source.x))c=next;if(c.a<=.5)discard;return c*i.color;}";ID3DBlob*b=NULL,*err=NULL;HRESULT h=D3DCompile(code,strlen(code),NULL,NULL,NULL,"pixel","ps_4_0",D3DCOMPILE_ENABLE_STRICTNESS,0,&b,&err);if(err)ID3D10Blob_Release(err);if(FAILED(h))return 2;h=ID3D11Device_CreatePixelShader(dev,ID3D10Blob_GetBufferPointer(b),ID3D10Blob_GetBufferSize(b),NULL,&sky_pan_ps);ID3D10Blob_Release(b);if(FAILED(h))return 2;}
 if(!sky_pan_constants){D3D11_BUFFER_DESC bd;memset(&bd,0,sizeof(bd));bd.ByteWidth=16;bd.BindFlags=D3D11_BIND_CONSTANT_BUFFER;if(FAILED(ID3D11Device_CreateBuffer(dev,&bd,NULL,&sky_pan_constants)))return 2;}
 float params[4]={phase,0,0,0};ID3D11DeviceContext_UpdateSubresource(ctx,(ID3D11Resource*)sky_pan_constants,0,NULL,params,0,0);float v[60];fixed_quad(v,240,160,1);float config[8]={0,240,160,0,1,1,.5,0};int rect[8]={0,0,3840,2160,300,0,3240,2160};sky_pan_active=1;int result=nf_d3d_draw(v,6,1001,3,0,config,rect);sky_pan_active=0;return result;
}

__declspec(dllexport) int nf_d3d_source_sky_pan_batch(SkyInfo info,PlaneCopy copy){
 if(!valid()||!info||!copy)return 1;unsigned enabled[2];double alpha[2];if(info(enabled,alpha))return 1;
 for(unsigned i=0;i<2;i++)if(enabled[i]>1||(enabled[i]&&!(alpha[i]>=0&&alpha[i]<=1)))return 1;
 if(!enabled[0])return enabled[1]?1:0;
 for(unsigned i=0;i<2;i++)if(enabled[i]){if(copy(i,auxiliary_pixels,sizeof(auxiliary_pixels)))return 1;int r=nf_d3d_texture_cached(1001+i,240,160,auxiliary_pixels,sizeof(auxiliary_pixels));if(r)return r;}
 if(!enabled[1]){int r=nf_d3d_texture_cached(1002,240,160,auxiliary_pixels,sizeof(auxiliary_pixels));if(r)return r;return nf_d3d_sky_pan(0);}
 return nf_d3d_sky_pan((float)alpha[1]);
}



static uint64_t draw_profile_ns(void){LARGE_INTEGER t,f;QueryPerformanceCounter(&t);QueryPerformanceFrequency(&f);return (uint64_t)(t.QuadPart/f.QuadPart)*1000000000ull+(uint64_t)(t.QuadPart%f.QuadPart)*1000000000ull/f.QuadPart;}

__declspec(dllexport) int nf_d3d_material_packet_cached_profiled(const void*rgba,size_t bytes,const unsigned*records,unsigned count,size_t record_bytes,uint64_t*timings,size_t timingc){
 if(!timings||timingc<32)return 1;ULONG64 c0=0,c1=0;QueryThreadCycleTime(GetCurrentThread(),&c0);uint64_t w0=draw_profile_ns();int result=nf_d3d_material_packet_cached(rgba,bytes,records,count,record_bytes);uint64_t w1=draw_profile_ns();QueryThreadCycleTime(GetCurrentThread(),&c1);timings[0]=w0;timings[1]=w1;timings[2]=c0;timings[3]=c1;return result;
}

__declspec(dllexport) int nf_d3d_world_batch_profiled(const float*vertices,unsigned nv,size_t vertex_bytes,const unsigned*offsets,size_t offset_bytes,const unsigned*ids,size_t id_bytes,const void*states,unsigned nd,size_t state_bytes,uint64_t*timings,size_t timingc){
 if(!timings||timingc<32)return 1;ULONG64 c0=0,c1=0;QueryThreadCycleTime(GetCurrentThread(),&c0);uint64_t w0=draw_profile_ns();int result=nf_d3d_world_batch(vertices,nv,vertex_bytes,offsets,offset_bytes,ids,id_bytes,states,nd,state_bytes);uint64_t w1=draw_profile_ns();QueryThreadCycleTime(GetCurrentThread(),&c1);timings[0]=w0;timings[1]=w1;timings[2]=c0;timings[3]=c1;return result;
}

__declspec(dllexport) int nf_d3d_source_hud_batch_profiled(HUDInfo info,PlaneCopy copy,HUDCount count,HUDCopy records,uint64_t*timings,size_t timingc){
 if(!timings||timingc<32)return 1;ULONG64 c0=0,c1=0;QueryThreadCycleTime(GetCurrentThread(),&c0);uint64_t w0=draw_profile_ns();int result=nf_d3d_source_hud_batch(info,copy,count,records);uint64_t w1=draw_profile_ns();QueryThreadCycleTime(GetCurrentThread(),&c1);timings[0]=w0;timings[1]=w1;timings[2]=c0;timings[3]=c1;return result;
}

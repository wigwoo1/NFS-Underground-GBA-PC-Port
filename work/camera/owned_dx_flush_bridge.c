#define INITGUID
#define COBJMACROS
#include <windows.h>
#include <GL/gl.h>
#include <d3d11.h>
#include <dxgi1_2.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
/* Standalone diagnostic: readback verifies cross-API pixels, never a live path. */
static IDXGIFactory2*factory;static IDXGISwapChain1*swap;
static ID3D11Device*device;static ID3D11DeviceContext*context;static ID3D11Texture2D*texture,*staging;
static HANDLE interop,object;static GLuint rb,fbo;static DWORD owner;static HGLRC owner_context;static uint64_t presents,readbacks;
__declspec(dllexport) unsigned nf_dx_bridge_active(void){return device!=NULL;}
static uint64_t phase_rows[8192][18],phase_count,phase_dropped;
static void phase_mark(uint64_t*p,unsigned i){LARGE_INTEGER t;ULONG64 cycles=0;QueryPerformanceCounter(&t);QueryThreadCycleTime(GetCurrentThread(),&cycles);p[i]=t.QuadPart;p[9+i]=cycles;}
__declspec(dllexport) unsigned nf_dx_phase_count(void){return (unsigned)phase_count;}
__declspec(dllexport) uint64_t nf_dx_phase_dropped(void){return phase_dropped;}
__declspec(dllexport) int nf_dx_phase_read(unsigned i,uint64_t*out){if(!out||i>=phase_count)return 0;memcpy(out,phase_rows[i],18*sizeof(uint64_t));return 1;}

static GLuint gpu_queries[16][3];static unsigned gpu_busy[16];static uint64_t gpu_identity[16],gpu_results[8192][4],gpu_count,gpu_skipped,gpu_deleted,gpu_unresolved;
static void(APIENTRY*q_gen)(GLsizei,GLuint*);static void(APIENTRY*q_delete)(GLsizei,const GLuint*);static void(APIENTRY*q_counter)(GLuint,GLenum);static void(APIENTRY*q_available)(GLuint,GLenum,GLint*);static void(APIENTRY*q_result)(GLuint,GLenum,uint64_t*);
static int gpu_init(void){if(q_gen)return 1;q_gen=(void*)wglGetProcAddress("glGenQueries");q_delete=(void*)wglGetProcAddress("glDeleteQueries");q_counter=(void*)wglGetProcAddress("glQueryCounter");q_available=(void*)wglGetProcAddress("glGetQueryObjectiv");q_result=(void*)wglGetProcAddress("glGetQueryObjectui64v");int valid=(uintptr_t)q_gen>3&&(intptr_t)q_gen!=-1&&(uintptr_t)q_delete>3&&(intptr_t)q_delete!=-1&&(uintptr_t)q_counter>3&&(intptr_t)q_counter!=-1&&(uintptr_t)q_available>3&&(intptr_t)q_available!=-1&&(uintptr_t)q_result>3&&(intptr_t)q_result!=-1;if(!valid){q_gen=NULL;q_delete=NULL;q_counter=NULL;q_available=NULL;q_result=NULL;}return valid;}
static void gpu_collect(void){for(unsigned i=0;i<16;i++)if(gpu_busy[i]){GLint a=0,b=0,c=0;q_available(gpu_queries[i][0],0x8867,&a);q_available(gpu_queries[i][1],0x8867,&b);q_available(gpu_queries[i][2],0x8867,&c);if(a&&b&&c){uint64_t x,y,z;q_result(gpu_queries[i][0],0x8866,&x);q_result(gpu_queries[i][1],0x8866,&y);q_result(gpu_queries[i][2],0x8866,&z);if(gpu_count<8192){gpu_results[gpu_count][0]=gpu_identity[i];gpu_results[gpu_count][1]=x;gpu_results[gpu_count][2]=y;gpu_results[gpu_count++][3]=z;}gpu_busy[i]=0;}}}
static void gpu_ready(int slot,uint64_t *phase,unsigned bit){if(slot>=0){GLint ready=0;q_available(gpu_queries[slot][0],0x8867,&ready);if(ready)phase[17]|=bit;}}
static int gpu_begin(uint64_t identity){gpu_collect();for(unsigned i=0;i<16;i++)if(!gpu_busy[i]){if(!gpu_queries[i][0])q_gen(3,gpu_queries[i]);if(!gpu_queries[i][0]||!gpu_queries[i][1]||!gpu_queries[i][2]){gpu_skipped++;return -1;}gpu_identity[i]=identity;q_counter(gpu_queries[i][0],0x8e28);return (int)i;}gpu_skipped++;return -1;}
static void gpu_close(void){if(q_gen){gpu_collect();for(unsigned i=0;i<16;i++){if(gpu_busy[i])gpu_unresolved++;if(gpu_queries[i][0]){q_delete(3,gpu_queries[i]);gpu_deleted+=3;}gpu_queries[i][0]=gpu_queries[i][1]=gpu_queries[i][2]=gpu_busy[i]=0;}q_gen=NULL;}}
__declspec(dllexport) unsigned nf_dx_gpu_count(void){return (unsigned)gpu_count;}
__declspec(dllexport) int nf_dx_gpu_read(unsigned i,uint64_t*out){if(!out||i>=gpu_count)return 0;memcpy(out,gpu_results[i],32);return 1;}
__declspec(dllexport) int nf_dx_gpu_cleanup(uint64_t*out){if(!out)return 0;unsigned pending=0,allocated=0;for(unsigned i=0;i<16;i++){pending+=gpu_busy[i];allocated+=!!gpu_queries[i][0]+!!gpu_queries[i][1]+!!gpu_queries[i][2];}out[0]=allocated;out[1]=pending;out[2]=gpu_deleted;out[3]=gpu_unresolved;return 1;}
__declspec(dllexport) uint64_t nf_dx_gpu_skipped(void){return gpu_skipped;}


/* Optional native wrapper: timestamps encompass the original complete draw callback.
   Available-only reads; exhaustion skips telemetry, never a gameplay sample. */
static int(*scene_draw)(void*);static DWORD scene_owner;static HGLRC scene_context;
static GLuint scene_queries[16][2];static unsigned scene_busy[16];
static uint64_t scene_identity[16],scene_results[8192][3],scene_count,scene_skipped,scene_deleted,scene_unresolved;
static void scene_collect(void){if(!q_gen)return;for(unsigned i=0;i<16;i++)if(scene_busy[i]){GLint a=0,b=0;q_available(scene_queries[i][0],0x8867,&a);q_available(scene_queries[i][1],0x8867,&b);if(a&&b){uint64_t x,y;q_result(scene_queries[i][0],0x8866,&x);q_result(scene_queries[i][1],0x8866,&y);if(scene_count<8192){scene_results[scene_count][0]=scene_identity[i];scene_results[scene_count][1]=x;scene_results[scene_count++][2]=y;}else scene_skipped++;scene_busy[i]=0;}}}
static void scene_close(void){if(q_gen){scene_collect();for(unsigned i=0;i<16;i++){if(scene_busy[i])scene_unresolved++;if(scene_queries[i][0]||scene_queries[i][1]){q_delete(2,scene_queries[i]);scene_deleted+=!!scene_queries[i][0]+!!scene_queries[i][1];}scene_queries[i][0]=scene_queries[i][1]=scene_busy[i]=0;}}scene_draw=NULL;scene_owner=0;scene_context=NULL;}
__declspec(dllexport) int nf_dx_scene_set_draw(void*callback){if(!callback||!wglGetCurrentContext())return 31;if(scene_owner&&(scene_owner!=GetCurrentThreadId()||scene_context!=wglGetCurrentContext()))return 45;scene_owner=GetCurrentThreadId();scene_context=wglGetCurrentContext();scene_draw=callback;return 0;}
__declspec(dllexport) int nf_dx_scene_draw_callback(void*opaque){if(!opaque||!scene_draw)return 37;if(scene_owner!=GetCurrentThreadId()||scene_context!=wglGetCurrentContext())return 31;int slot=-1;if(gpu_init()){scene_collect();for(unsigned i=0;i<16;i++)if(!scene_busy[i]){if(!scene_queries[i][0])q_gen(2,scene_queries[i]);if(scene_queries[i][0]&&scene_queries[i][1]){slot=i;scene_identity[i]=phase_count;q_counter(scene_queries[i][0],0x8e28);}break;}}if(slot<0)scene_skipped++;int result=scene_draw(opaque);if(slot>=0){q_counter(scene_queries[slot][1],0x8e28);scene_busy[slot]=1;}return result;}
__declspec(dllexport) unsigned nf_dx_scene_count(void){return (unsigned)scene_count;}
__declspec(dllexport) int nf_dx_scene_read(unsigned i,uint64_t*out){if(!out||i>=scene_count)return 0;memcpy(out,scene_results[i],24);return 1;}
__declspec(dllexport) int nf_dx_scene_cleanup(uint64_t*out){if(!out)return 0;unsigned a=0,b=0;for(unsigned i=0;i<16;i++){a+=!!scene_queries[i][0]+!!scene_queries[i][1];b+=scene_busy[i];}out[0]=a;out[1]=b;out[2]=scene_deleted;out[3]=scene_unresolved;out[4]=scene_skipped;return 1;}

static int bridge_frame(uint64_t*out,int diagnostic){
 if(!wglGetCurrentContext())return 31;
 if(owner&&(owner!=GetCurrentThreadId()||owner_context!=wglGetCurrentContext()))return 45;
 uint64_t scratch[16];int closing=!out;if(closing)out=scratch;
 memset(out,0,16*sizeof(*out));int status=0,locked=0,pushed=0;HRESULT hr=0;GLint oldfbo=0,oldread=0,oldrb=0,oldpack=0;
 ID3D11Texture2D*back=NULL;uint8_t*expected=NULL;
 HANDLE(WINAPI*open_device)(void*)=(void*)wglGetProcAddress("wglDXOpenDeviceNV");BOOL(WINAPI*close_device)(HANDLE)=(void*)wglGetProcAddress("wglDXCloseDeviceNV");
 HANDLE(WINAPI*register_object)(HANDLE,void*,GLuint,GLenum,GLenum)=(void*)wglGetProcAddress("wglDXRegisterObjectNV");BOOL(WINAPI*unregister_object)(HANDLE,HANDLE)=(void*)wglGetProcAddress("wglDXUnregisterObjectNV");
 BOOL(WINAPI*lock_objects)(HANDLE,GLint,HANDLE*)=(void*)wglGetProcAddress("wglDXLockObjectsNV");BOOL(WINAPI*unlock_objects)(HANDLE,GLint,HANDLE*)=(void*)wglGetProcAddress("wglDXUnlockObjectsNV");
 void(APIENTRY*gen_rb)(GLsizei,GLuint*)=(void*)wglGetProcAddress("glGenRenderbuffers");void(APIENTRY*delete_rb)(GLsizei,const GLuint*)=(void*)wglGetProcAddress("glDeleteRenderbuffers");void(APIENTRY*bind_rb)(GLenum,GLuint)=(void*)wglGetProcAddress("glBindRenderbuffer");
 void(APIENTRY*gen_fbo)(GLsizei,GLuint*)=(void*)wglGetProcAddress("glGenFramebuffers");void(APIENTRY*delete_fbo)(GLsizei,const GLuint*)=(void*)wglGetProcAddress("glDeleteFramebuffers");void(APIENTRY*bind_fbo)(GLenum,GLuint)=(void*)wglGetProcAddress("glBindFramebuffer");void(APIENTRY*attach)(GLenum,GLenum,GLenum,GLuint)=(void*)wglGetProcAddress("glFramebufferRenderbuffer");GLenum(APIENTRY*check)(GLenum)=(void*)wglGetProcAddress("glCheckFramebufferStatus");
 void(APIENTRY*blit)(GLint,GLint,GLint,GLint,GLint,GLint,GLint,GLint,GLbitfield,GLenum)=(void*)wglGetProcAddress("glBlitFramebuffer");
 if(!blit)return 40;
 if(!open_device||!close_device||!register_object||!unregister_object||!lock_objects||!unlock_objects||!gen_rb||!delete_rb||!bind_rb||!gen_fbo||!delete_fbo||!bind_fbo||!attach||!check)return 39;
 uint64_t phase[18]={0};LARGE_INTEGER phase_freq;QueryPerformanceFrequency(&phase_freq);phase[8]=phase_freq.QuadPart;phase_mark(phase,0);
 if(closing)goto cleanup;
 glGetIntegerv(0x8ca6,&oldfbo);glGetIntegerv(0x8caa,&oldread);glGetIntegerv(0x8ca7,&oldrb);glGetIntegerv(GL_PACK_ALIGNMENT,&oldpack);glPushAttrib(GL_ALL_ATTRIB_BITS);pushed=1;
 if(!device){owner=GetCurrentThreadId();owner_context=wglGetCurrentContext();
 hr=D3D11CreateDevice(NULL,D3D_DRIVER_TYPE_HARDWARE,NULL,D3D11_CREATE_DEVICE_BGRA_SUPPORT,NULL,0,D3D11_SDK_VERSION,&device,NULL,&context);if(FAILED(hr)){status=1;goto cleanup;}out[0]=1;
 hr=CreateDXGIFactory1(&IID_IDXGIFactory2,(void**)&factory);if(FAILED(hr)){status=41;goto cleanup;}
 DXGI_SWAP_CHAIN_DESC1 sc;memset(&sc,0,sizeof(sc));sc.Width=3840;sc.Height=2160;sc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;sc.SampleDesc.Count=1;sc.BufferUsage=DXGI_USAGE_RENDER_TARGET_OUTPUT;sc.BufferCount=2;sc.Scaling=DXGI_SCALING_STRETCH;sc.SwapEffect=DXGI_SWAP_EFFECT_FLIP_SEQUENTIAL;
 hr=IDXGIFactory2_CreateSwapChainForHwnd(factory,(IUnknown*)device,WindowFromDC(wglGetCurrentDC()),&sc,NULL,NULL,&swap);if(FAILED(hr)){status=42;goto cleanup;}
 D3D11_TEXTURE2D_DESC desc;memset(&desc,0,sizeof(desc));desc.Width=3840;desc.Height=2160;desc.MipLevels=desc.ArraySize=1;desc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;desc.SampleDesc.Count=1;desc.Usage=D3D11_USAGE_DEFAULT;desc.BindFlags=D3D11_BIND_RENDER_TARGET|D3D11_BIND_SHADER_RESOURCE;
 hr=ID3D11Device_CreateTexture2D(device,&desc,NULL,&texture);if(FAILED(hr)){status=2;goto cleanup;}out[1]=1;
 interop=open_device(device);if(!interop){status=4;goto cleanup;}out[2]=1;
 gen_rb(1,&rb);object=register_object(interop,texture,rb,0x8d41,1);if(!object){status=5;goto cleanup;}out[3]=1;
 }
 out[0]=out[1]=out[2]=out[3]=1;
 hr=IDXGISwapChain1_GetBuffer(swap,0,&IID_ID3D11Texture2D,(void**)&back);if(FAILED(hr)){status=43;goto cleanup;}
 int gpu_slot=-1;if(!diagnostic){if(!gpu_init()){status=49;goto cleanup;}gpu_slot=gpu_begin(phase_count);}
 gpu_ready(gpu_slot,phase,1);phase_mark(phase,1);
 if(!lock_objects(interop,1,&object)){status=6;goto cleanup;}locked=1;out[4]=1;phase_mark(phase,2);gpu_ready(gpu_slot,phase,2);
 if(!fbo){gen_fbo(1,&fbo);}bind_fbo(0x8d40,fbo);attach(0x8d40,0x8ce0,0x8d41,rb);if(check(0x8d40)!=0x8cd5){status=7;goto cleanup;}
 bind_fbo(0x8ca8,(GLuint)oldfbo);
 if(diagnostic){
 expected=malloc(3840u*2160u*4u);if(!expected){status=8;goto cleanup;}
 glPixelStorei(GL_PACK_ALIGNMENT,1);glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,expected);
 }
 glDisable(GL_SCISSOR_TEST);bind_fbo(0x8ca9,fbo);
 if(gpu_slot>=0)q_counter(gpu_queries[gpu_slot][1],0x8e28);
 /* D3D top row receives GL top row; retain native 4K pixels entirely on GPU. */
 blit(0,2160,3840,0,0,0,3840,2160,GL_COLOR_BUFFER_BIT,GL_NEAREST);
 if(gpu_slot>=0){q_counter(gpu_queries[gpu_slot][2],0x8e28);gpu_busy[gpu_slot]=1;}
 if(glGetError()){status=9;goto cleanup;}
 /* Submit GL work explicitly before transferring interop ownership. No finish/readback. */
 glFlush();gpu_ready(gpu_slot,phase,4);phase_mark(phase,3);
 if(!unlock_objects(interop,1,&object)){status=10;goto cleanup;}locked=0;out[5]=1;phase_mark(phase,4);gpu_ready(gpu_slot,phase,8);
 ID3D11DeviceContext_CopyResource(context,(ID3D11Resource*)back,(ID3D11Resource*)texture);
 if(diagnostic){
 if(!staging){D3D11_TEXTURE2D_DESC desc;ID3D11Texture2D_GetDesc(texture,&desc);desc.Usage=D3D11_USAGE_STAGING;desc.BindFlags=0;desc.CPUAccessFlags=D3D11_CPU_ACCESS_READ;
 hr=ID3D11Device_CreateTexture2D(device,&desc,NULL,&staging);if(FAILED(hr)){status=3;goto cleanup;}}
 ID3D11DeviceContext_CopyResource(context,(ID3D11Resource*)staging,(ID3D11Resource*)back);
 D3D11_MAPPED_SUBRESOURCE mapped;hr=ID3D11DeviceContext_Map(context,(ID3D11Resource*)staging,0,D3D11_MAP_READ,0,&mapped);if(FAILED(hr)){status=11;goto cleanup;}
 out[6]=mapped.RowPitch;out[7]=3840u*2160u*4u;int direct=1,flipped=1;
 for(unsigned y=0;y<2160;y++){const uint8_t*row=(uint8_t*)mapped.pData+y*mapped.RowPitch;if(memcmp(row,expected+y*3840*4,3840*4))direct=0;if(memcmp(row,expected+(2159-y)*3840*4,3840*4))flipped=0;}
 ID3D11DeviceContext_Unmap(context,(ID3D11Resource*)staging,0);out[8]=direct;out[9]=flipped;if(!flipped)status=12;
 readbacks++;
 }
 phase_mark(phase,5);
 if(!status){hr=IDXGISwapChain1_Present(swap,0,0);if(FAILED(hr))status=44;else presents++;}
phase_mark(phase,6);
cleanup:
 out[10]=(uint32_t)hr;out[11]=presents;free(expected);
 if(locked&&!unlock_objects(interop,1,&object))status=status?status:13;
 if(pushed){bind_fbo(0x8ca9,(GLuint)oldfbo);bind_fbo(0x8ca8,(GLuint)oldread);glPixelStorei(GL_PACK_ALIGNMENT,oldpack);bind_rb(0x8d41,(GLuint)oldrb);glPopAttrib();}
 if(back)ID3D11Texture2D_Release(back);
 if(status||closing){scene_close();gpu_close();
 if(fbo)delete_fbo(1,&fbo);
 if(object){out[12]=unregister_object(interop,object);if(!out[12])status=status?status:14;}
 if(rb)delete_rb(1,&rb);
 if(interop){out[13]=close_device(interop);if(!out[13])status=status?status:15;}
 if(swap)IDXGISwapChain1_Release(swap);
 if(context){ID3D11DeviceContext_ClearState(context);ID3D11DeviceContext_Flush(context);}
 if(factory)IDXGIFactory2_Release(factory);
 if(staging)ID3D11Texture2D_Release(staging);
 if(texture)ID3D11Texture2D_Release(texture);
 if(context)ID3D11DeviceContext_Release(context);
 if(device)ID3D11Device_Release(device);
 factory=NULL;swap=NULL;device=NULL;context=NULL;texture=NULL;staging=NULL;interop=object=NULL;rb=fbo=0;owner=0;owner_context=NULL;presents=readbacks=0;
 }
 if(pushed){GLint restored[4];glGetIntegerv(0x8ca6,&restored[0]);glGetIntegerv(0x8caa,&restored[1]);glGetIntegerv(0x8ca7,&restored[2]);glGetIntegerv(GL_PACK_ALIGNMENT,&restored[3]);if(restored[0]!=oldfbo||restored[1]!=oldread||restored[2]!=oldrb||restored[3]!=oldpack)status=status?status:17;}
 out[14]=glGetError();if(out[14])status=status?status:16;out[15]=status;
 if(!closing&&!diagnostic&&!status){phase_mark(phase,7);if(phase_count<8192)memcpy(phase_rows[phase_count++],phase,sizeof(phase));else phase_dropped++;}
 return status;
}


__declspec(dllexport) int nf_dx_bridge_diagnostic(uint64_t*out){return bridge_frame(out,1);}
__declspec(dllexport) int nf_dx_bridge_close(void){return bridge_frame(NULL,0);}
__declspec(dllexport) int nf_dx_bridge_present_callback(void*unused){(void)unused;uint64_t out[16];return bridge_frame(out,0)==0;}
__declspec(dllexport) int nf_dx_bridge_stats(uint64_t*out){if(!out)return 1;if(owner&&owner!=GetCurrentThreadId())return 45;out[0]=presents;out[1]=readbacks;out[2]=staging!=NULL;out[3]=device!=NULL;return 0;}

typedef struct {uint64_t epoch;uint32_t timed;int32_t result;uint64_t elapsed_ns;} NFPresentContext;
__declspec(dllexport) int nf_dx_bridge_present_context_callback(void*context_ptr){
 NFPresentContext*c=context_ptr;if(!c||c->timed>1)return 0;
 LARGE_INTEGER begin,end,freq;QueryPerformanceCounter(&begin);
 uint64_t out[16];c->result=bridge_frame(out,0);
 QueryPerformanceCounter(&end);QueryPerformanceFrequency(&freq);
 c->elapsed_ns=c->timed?(uint64_t)((end.QuadPart-begin.QuadPart)*1000000000.0/freq.QuadPart):0;
 return c->result==0;
}

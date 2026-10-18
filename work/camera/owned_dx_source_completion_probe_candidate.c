#define INITGUID
#define COBJMACROS
#include <windows.h>
#include <GL/gl.h>
#include <d3d11.h>
#include <dxgi1_3.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
/* Standalone diagnostic: readback verifies cross-API pixels, never a live path. */
static IDXGIFactory2*factory;static IDXGISwapChain1*swap;static DWORD owner;static HANDLE availability;static uint64_t availability_stats[7];
__declspec(dllexport) int nf_dx_availability_stats(uint64_t*out){if(!out||(owner&&owner!=GetCurrentThreadId()))return 45;memcpy(out,availability_stats,sizeof(availability_stats));return 0;}
static ID3D11Device*device;static ID3D11DeviceContext*context;static ID3D11Texture2D*texture,*staging;
static HANDLE interop,object;static GLuint rb,fbo;static HGLRC owner_context;static uint64_t presents,readbacks;
__declspec(dllexport) unsigned nf_dx_bridge_active(void){return device!=NULL;}
static uint64_t phase_rows[10000][18],phase_times[8],phase_cycles[8];static unsigned phase_count,phase_enabled;static uint64_t phase_frequency;
static void phase_stamp(unsigned index){if(!phase_enabled)return;LARGE_INTEGER t,f;QueryPerformanceCounter(&t);if(!phase_frequency){QueryPerformanceFrequency(&f);phase_frequency=f.QuadPart;}phase_times[index]=(uint64_t)((long double)t.QuadPart*1000000000.0L/phase_frequency);ULONG64 c=0;phase_cycles[index]=QueryThreadCycleTime(GetCurrentThread(),&c)?c:UINT64_MAX;}
__declspec(dllexport) unsigned nf_dx_phase_count(void){return phase_count;}
__declspec(dllexport) int nf_dx_phase_read(unsigned index,uint64_t*out){if(!out||index>=phase_count)return 1;memcpy(out,phase_rows[index],sizeof(phase_rows[index]));return 0;}
static uint64_t display_rows[10000][14];static unsigned display_count,display_dropped;
__declspec(dllexport) unsigned nf_dx_display_count(void){return display_count;}
__declspec(dllexport) unsigned nf_dx_display_dropped(void){return display_dropped;}
__declspec(dllexport) int nf_dx_display_read(unsigned i,uint64_t*out){if(!out||i>=display_count)return 1;memcpy(out,display_rows[i],sizeof(display_rows[i]));return 0;}
static uint64_t display_stats[10];
__declspec(dllexport) int nf_dx_display_stats(uint64_t*out){if(!out||!swap||owner!=GetCurrentThreadId())return 45;memcpy(out,display_stats,sizeof(display_stats));return 0;}
static unsigned availability_credit,prepared_frame;static uint64_t prepared_identity[3];
static uint64_t completion_probe[12],completion_rows[10000][15];static unsigned completion_count,completion_dropped;
static void probe_sync(void*sync,unsigned slot,GLenum(APIENTRY*wait_sync)(void*,GLbitfield,uint64_t)){LARGE_INTEGER a,b,f;QueryPerformanceCounter(&a);GLenum result=wait_sync(sync,0,0);QueryPerformanceCounter(&b);QueryPerformanceFrequency(&f);completion_probe[slot]=result;completion_probe[6+slot]=(uint64_t)((b.QuadPart-a.QuadPart)*1000000000.0/f.QuadPart);}
__declspec(dllexport) unsigned nf_dx_completion_count(void){return completion_count;}
__declspec(dllexport) unsigned nf_dx_completion_dropped(void){return completion_dropped;}
__declspec(dllexport) int nf_dx_completion_read(unsigned i,uint64_t*out){if(!out||i>=completion_count)return 1;memcpy(out,completion_rows[i],sizeof(completion_rows[i]));return 0;}
static HWND presentation_window;
static uint64_t window_created,window_destroyed,window_resized;
__declspec(dllexport) int nf_dx_window_stats(uint64_t*out){if(!out)return 1;out[0]=window_created;out[1]=window_destroyed;out[2]=window_resized;out[3]=presentation_window&&IsWindow(presentation_window);return 0;}
static uint64_t creation_diagnostic[5];
__declspec(dllexport) int nf_dx_creation_diagnostic(uint64_t*out){if(!out)return 1;memcpy(out,creation_diagnostic,sizeof(creation_diagnostic));return 0;}
static int bridge_frame(uint64_t*out,int diagnostic){
 if(!wglGetCurrentContext())return 31;
 if(owner&&(owner!=GetCurrentThreadId()||owner_context!=wglGetCurrentContext()))return 45;
 phase_stamp(0);uint64_t scratch[16];int closing=!out;if(closing)out=scratch;
 memset(out,0,16*sizeof(*out));int status=0,locked=0,pushed=0;HRESULT hr=0;GLint oldfbo=0,oldread=0,oldrb=0,oldpack=0;
 void*world_sync=NULL,*blit_sync=NULL;int probe_transfer=diagnostic==3||diagnostic==4;
 void*(APIENTRY*fence_sync)(GLenum,GLbitfield)=(void*)wglGetProcAddress("glFenceSync");
 GLenum(APIENTRY*wait_sync)(void*,GLbitfield,uint64_t)=(void*)wglGetProcAddress("glClientWaitSync");
 void(APIENTRY*delete_sync)(void*)=(void*)wglGetProcAddress("glDeleteSync");
 ID3D11Texture2D*back=NULL;uint8_t*expected=NULL;
 HANDLE(WINAPI*open_device)(void*)=(void*)wglGetProcAddress("wglDXOpenDeviceNV");BOOL(WINAPI*close_device)(HANDLE)=(void*)wglGetProcAddress("wglDXCloseDeviceNV");
 HANDLE(WINAPI*register_object)(HANDLE,void*,GLuint,GLenum,GLenum)=(void*)wglGetProcAddress("wglDXRegisterObjectNV");BOOL(WINAPI*unregister_object)(HANDLE,HANDLE)=(void*)wglGetProcAddress("wglDXUnregisterObjectNV");
 BOOL(WINAPI*lock_objects)(HANDLE,GLint,HANDLE*)=(void*)wglGetProcAddress("wglDXLockObjectsNV");BOOL(WINAPI*unlock_objects)(HANDLE,GLint,HANDLE*)=(void*)wglGetProcAddress("wglDXUnlockObjectsNV");
 void(APIENTRY*gen_rb)(GLsizei,GLuint*)=(void*)wglGetProcAddress("glGenRenderbuffers");void(APIENTRY*delete_rb)(GLsizei,const GLuint*)=(void*)wglGetProcAddress("glDeleteRenderbuffers");void(APIENTRY*bind_rb)(GLenum,GLuint)=(void*)wglGetProcAddress("glBindRenderbuffer");
 void(APIENTRY*gen_fbo)(GLsizei,GLuint*)=(void*)wglGetProcAddress("glGenFramebuffers");void(APIENTRY*delete_fbo)(GLsizei,const GLuint*)=(void*)wglGetProcAddress("glDeleteFramebuffers");void(APIENTRY*bind_fbo)(GLenum,GLuint)=(void*)wglGetProcAddress("glBindFramebuffer");void(APIENTRY*attach)(GLenum,GLenum,GLenum,GLuint)=(void*)wglGetProcAddress("glFramebufferRenderbuffer");GLenum(APIENTRY*check)(GLenum)=(void*)wglGetProcAddress("glCheckFramebufferStatus");
 void(APIENTRY*blit)(GLint,GLint,GLint,GLint,GLint,GLint,GLint,GLint,GLbitfield,GLenum)=(void*)wglGetProcAddress("glBlitFramebuffer");
 if(!blit)return 40;
 if(!open_device||!close_device||!register_object||!unregister_object||!lock_objects||!unlock_objects||!gen_rb||!delete_rb||!bind_rb||!gen_fbo||!delete_fbo||!bind_fbo||!attach||!check)return 39;
 if(closing)goto cleanup;
 glGetIntegerv(0x8ca6,&oldfbo);glGetIntegerv(0x8caa,&oldread);glGetIntegerv(0x8ca7,&oldrb);glGetIntegerv(GL_PACK_ALIGNMENT,&oldpack);glPushAttrib(GL_ALL_ATTRIB_BITS);pushed=1;
 if(!device){owner=GetCurrentThreadId();owner_context=wglGetCurrentContext();
 hr=D3D11CreateDevice(NULL,D3D_DRIVER_TYPE_HARDWARE,NULL,D3D11_CREATE_DEVICE_BGRA_SUPPORT,NULL,0,D3D11_SDK_VERSION,&device,NULL,&context);if(FAILED(hr)){status=1;goto cleanup;}out[0]=1;
 hr=CreateDXGIFactory1(&IID_IDXGIFactory2,(void**)&factory);if(FAILED(hr)){status=41;goto cleanup;}
 DXGI_SWAP_CHAIN_DESC1 sc;memset(&sc,0,sizeof(sc));sc.Width=3840;sc.Height=2160;sc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;sc.SampleDesc.Count=1;sc.BufferUsage=DXGI_USAGE_RENDER_TARGET_OUTPUT;sc.BufferCount=2;sc.Scaling=DXGI_SCALING_STRETCH;sc.SwapEffect=DXGI_SWAP_EFFECT_FLIP_SEQUENTIAL;sc.Flags=DXGI_SWAP_CHAIN_FLAG_FRAME_LATENCY_WAITABLE_OBJECT;
 HWND parent=WindowFromDC(wglGetCurrentDC());RECT client;if(!GetClientRect(parent,&client)){status=46;goto cleanup;}
 presentation_window=CreateWindowExA(0,"STATIC","NFSUG native DXGI surface",WS_CHILD|WS_VISIBLE,0,0,client.right,client.bottom,parent,NULL,GetModuleHandleA(NULL),NULL);
 if(!presentation_window){status=47;goto cleanup;}window_created++;
 HWND target=presentation_window;creation_diagnostic[1]=(uintptr_t)target;creation_diagnostic[2]=IsWindow(target);creation_diagnostic[3]=GetPixelFormat(wglGetCurrentDC());creation_diagnostic[4]=(uintptr_t)wglGetCurrentDC();
 hr=IDXGIFactory2_CreateSwapChainForHwnd(factory,(IUnknown*)device,target,&sc,NULL,NULL,&swap);creation_diagnostic[0]=(uint32_t)hr;if(FAILED(hr)){status=42;goto cleanup;}
 IDXGISwapChain2*swap2=NULL;hr=IDXGISwapChain1_QueryInterface(swap,&IID_IDXGISwapChain2,(void**)&swap2);availability_stats[0]=(uint32_t)hr;availability_stats[3]=2;if(FAILED(hr)){status=50;goto cleanup;}
 HRESULT a=IDXGISwapChain2_SetMaximumFrameLatency(swap2,2);UINT observed=0;HRESULT b=IDXGISwapChain2_GetMaximumFrameLatency(swap2,&observed);availability_stats[1]=(uint32_t)a;availability_stats[2]=(uint32_t)b;availability_stats[4]=observed;availability=IDXGISwapChain2_GetFrameLatencyWaitableObject(swap2);IDXGISwapChain2_Release(swap2);if(availability)availability_stats[5]++;if(FAILED(a)||FAILED(b)||observed!=2||!availability){status=50;goto cleanup;}
 D3D11_TEXTURE2D_DESC desc;memset(&desc,0,sizeof(desc));desc.Width=3840;desc.Height=2160;desc.MipLevels=desc.ArraySize=1;desc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;desc.SampleDesc.Count=1;desc.Usage=D3D11_USAGE_DEFAULT;desc.BindFlags=D3D11_BIND_RENDER_TARGET|D3D11_BIND_SHADER_RESOURCE;
 hr=ID3D11Device_CreateTexture2D(device,&desc,NULL,&texture);if(FAILED(hr)){status=2;goto cleanup;}out[1]=1;
 interop=open_device(device);if(!interop){status=4;goto cleanup;}out[2]=1;
 gen_rb(1,&rb);object=register_object(interop,texture,rb,0x8d41,1);if(!object){status=5;goto cleanup;}out[3]=1;
 }
 if(presentation_window){RECT client,current;HWND parent=GetParent(presentation_window);if(!GetClientRect(parent,&client)||!GetClientRect(presentation_window,&current)){status=46;goto cleanup;}
 if(client.right!=current.right||client.bottom!=current.bottom){if(!MoveWindow(presentation_window,0,0,client.right,client.bottom,FALSE)){status=46;goto cleanup;}window_resized++;}}
 out[0]=out[1]=out[2]=out[3]=1;
 /* Initialization restores GL state without drawing, copying or presenting. */
 if(diagnostic==2)goto cleanup;
 if(diagnostic==5){for(unsigned i=1;i<=5;i++)phase_stamp(i);goto present_prepared;}
 hr=IDXGISwapChain1_GetBuffer(swap,0,&IID_ID3D11Texture2D,(void**)&back);if(FAILED(hr)){status=43;goto cleanup;}
 if(probe_transfer){memset(completion_probe,0,sizeof(completion_probe));if(!fence_sync||!wait_sync||!delete_sync){status=52;goto cleanup;}world_sync=fence_sync(0x9117,0);if(!world_sync){status=53;goto cleanup;}completion_probe[4]++;glFlush();probe_sync(world_sync,0,wait_sync);}
 phase_stamp(1);if(!lock_objects(interop,1,&object)){status=6;goto cleanup;}locked=1;out[4]=1;phase_stamp(2);if(world_sync)probe_sync(world_sync,1,wait_sync);
 if(!fbo){gen_fbo(1,&fbo);}bind_fbo(0x8d40,fbo);attach(0x8d40,0x8ce0,0x8d41,rb);if(check(0x8d40)!=0x8cd5){status=7;goto cleanup;}
 bind_fbo(0x8ca8,(GLuint)oldfbo);
 if(diagnostic==1||diagnostic==4){
 expected=malloc(3840u*2160u*4u);if(!expected){status=8;goto cleanup;}
 glPixelStorei(GL_PACK_ALIGNMENT,1);glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,expected);
 }
 glDisable(GL_SCISSOR_TEST);bind_fbo(0x8ca9,fbo);
 /* D3D top row receives GL top row; retain native 4K pixels entirely on GPU. */
 blit(0,2160,3840,0,0,0,3840,2160,GL_COLOR_BUFFER_BIT,GL_NEAREST);
 if(glGetError()){status=9;goto cleanup;}
 if(probe_transfer){blit_sync=fence_sync(0x9117,0);if(!blit_sync){status=53;goto cleanup;}completion_probe[4]++;glFlush();probe_sync(blit_sync,2,wait_sync);}
 phase_stamp(3);if(!unlock_objects(interop,1,&object)){status=10;goto cleanup;}locked=0;out[5]=1;phase_stamp(4);if(blit_sync)probe_sync(blit_sync,3,wait_sync);
 ID3D11DeviceContext_CopyResource(context,(ID3D11Resource*)back,(ID3D11Resource*)texture);
 phase_stamp(5);if(diagnostic==1||diagnostic==4){
 if(!staging){D3D11_TEXTURE2D_DESC desc;ID3D11Texture2D_GetDesc(texture,&desc);desc.Usage=D3D11_USAGE_STAGING;desc.BindFlags=0;desc.CPUAccessFlags=D3D11_CPU_ACCESS_READ;
 hr=ID3D11Device_CreateTexture2D(device,&desc,NULL,&staging);if(FAILED(hr)){status=3;goto cleanup;}}
 ID3D11DeviceContext_CopyResource(context,(ID3D11Resource*)staging,(ID3D11Resource*)back);
 D3D11_MAPPED_SUBRESOURCE mapped;hr=ID3D11DeviceContext_Map(context,(ID3D11Resource*)staging,0,D3D11_MAP_READ,0,&mapped);if(FAILED(hr)){status=11;goto cleanup;}
 out[6]=mapped.RowPitch;out[7]=3840u*2160u*4u;int direct=1,flipped=1;
 for(unsigned y=0;y<2160;y++){const uint8_t*row=(uint8_t*)mapped.pData+y*mapped.RowPitch;if(memcmp(row,expected+y*3840*4,3840*4))direct=0;if(memcmp(row,expected+(2159-y)*3840*4,3840*4))flipped=0;}
 ID3D11DeviceContext_Unmap(context,(ID3D11Resource*)staging,0);out[8]=direct;out[9]=flipped;if(!flipped)status=12;
 readbacks++;
 }
 if(diagnostic==3||diagnostic==4){phase_stamp(6);goto cleanup;}
 present_prepared:
 if(!status){hr=IDXGISwapChain1_Present(swap,1,0);if(FAILED(hr))status=44;else {availability_credit=0;presents++;UINT last=0;DXGI_FRAME_STATISTICS stats;memset(&stats,0,sizeof(stats));HRESULT a=IDXGISwapChain1_GetLastPresentCount(swap,&last),b=IDXGISwapChain1_GetFrameStatistics(swap,&stats);display_stats[0]=presents;display_stats[1]=(uint32_t)a;display_stats[2]=last;display_stats[3]=(uint32_t)b;display_stats[4]=stats.PresentCount;display_stats[5]=stats.PresentRefreshCount;display_stats[6]=stats.SyncRefreshCount;display_stats[7]=stats.SyncQPCTime.QuadPart;display_stats[8]=stats.SyncGPUTime.QuadPart;display_stats[9]=(uintptr_t)swap;}}
phase_stamp(6);cleanup:
 if(world_sync){delete_sync(world_sync);completion_probe[5]++;}if(blit_sync){delete_sync(blit_sync);completion_probe[5]++;}if(probe_transfer){completion_probe[10]=glGetError();if(completion_probe[10])status=status?status:54;completion_probe[11]=status;}
 out[10]=(uint32_t)hr;out[11]=presents;free(expected);
 if(locked&&!unlock_objects(interop,1,&object))status=status?status:13;
 if(pushed){bind_fbo(0x8ca9,(GLuint)oldfbo);bind_fbo(0x8ca8,(GLuint)oldread);glPixelStorei(GL_PACK_ALIGNMENT,oldpack);bind_rb(0x8d41,(GLuint)oldrb);glPopAttrib();}
 if(back)ID3D11Texture2D_Release(back);
 if(status||closing){
 if(fbo)delete_fbo(1,&fbo);
 if(object){out[12]=unregister_object(interop,object);if(!out[12])status=status?status:14;}
 if(rb)delete_rb(1,&rb);
 if(interop){out[13]=close_device(interop);if(!out[13])status=status?status:15;}
 availability_credit=prepared_frame=0;memset(prepared_identity,0,sizeof(prepared_identity));
 if(availability){if(CloseHandle(availability))availability_stats[6]++;availability=NULL;}
 if(swap)IDXGISwapChain1_Release(swap);
 if(presentation_window){if(DestroyWindow(presentation_window)){window_destroyed++;presentation_window=NULL;}else status=status?status:48;}
 if(context){ID3D11DeviceContext_ClearState(context);ID3D11DeviceContext_Flush(context);}
 if(factory)IDXGIFactory2_Release(factory);
 if(staging)ID3D11Texture2D_Release(staging);
 if(texture)ID3D11Texture2D_Release(texture);
 if(context)ID3D11DeviceContext_Release(context);
 if(device)ID3D11Device_Release(device);
 factory=NULL;swap=NULL;device=NULL;context=NULL;texture=NULL;staging=NULL;interop=object=NULL;rb=fbo=0;owner=0;owner_context=NULL;presents=readbacks=0;
 }
 if(pushed){GLint restored[4];glGetIntegerv(0x8ca6,&restored[0]);glGetIntegerv(0x8caa,&restored[1]);glGetIntegerv(0x8ca7,&restored[2]);glGetIntegerv(GL_PACK_ALIGNMENT,&restored[3]);if(restored[0]!=oldfbo||restored[1]!=oldread||restored[2]!=oldrb||restored[3]!=oldpack)status=status?status:17;}
 out[14]=glGetError();if(out[14])status=status?status:16;out[15]=status;phase_stamp(7);return status;
}


/* Immutable identity owns a single prepared backbuffer until present/abort.
   Rejections never consume or destroy the pending prepared frame. */
__declspec(dllexport) int nf_dx_prepare(uint64_t epoch,uint64_t generation,uint64_t index,unsigned diagnostic,uint64_t*out){
 if(!out||!epoch||!generation||diagnostic>1||prepared_frame)return 51;
 if(owner&&owner!=GetCurrentThreadId())return 45;
 int result=bridge_frame(out,diagnostic?4:3);if(!result){prepared_frame=1;prepared_identity[0]=epoch;prepared_identity[1]=generation;prepared_identity[2]=index;}return result;
}
__declspec(dllexport) int nf_dx_present_prepared(uint64_t epoch,uint64_t generation,uint64_t index,uint64_t*out){
 if(!out||!prepared_frame||prepared_identity[0]!=epoch||prepared_identity[1]!=generation||prepared_identity[2]!=index)return 51;
 if(owner!=GetCurrentThreadId())return 45;
 int result=bridge_frame(out,5);if(!result){prepared_frame=0;memset(prepared_identity,0,sizeof(prepared_identity));}return result;
}
__declspec(dllexport) int nf_dx_abort_prepared(uint64_t epoch,uint64_t generation,uint64_t index){
 if(!prepared_frame||prepared_identity[0]!=epoch||prepared_identity[1]!=generation||prepared_identity[2]!=index)return 51;
 if(owner!=GetCurrentThreadId())return 45;
 prepared_frame=0;memset(prepared_identity,0,sizeof(prepared_identity));return 0;
}
__declspec(dllexport) int nf_dx_bridge_initialize_callback(void){uint64_t out[16];return bridge_frame(out,2);}
__declspec(dllexport) int nf_dx_bridge_initialize(uint64_t*out){if(!out)return 45;return bridge_frame(out,2);}
__declspec(dllexport) int nf_dx_bridge_diagnostic(uint64_t*out){return prepared_frame?51:bridge_frame(out,1);}
__declspec(dllexport) int nf_dx_bridge_close(void){return bridge_frame(NULL,0);}
__declspec(dllexport) int nf_dx_bridge_present_callback(void*unused){(void)unused;if(prepared_frame)return 0;uint64_t out[16];return bridge_frame(out,0)==0;}
__declspec(dllexport) int nf_dx_bridge_stats(uint64_t*out){if(!out)return 1;if(owner&&owner!=GetCurrentThreadId())return 45;out[0]=presents;out[1]=readbacks;out[2]=staging!=NULL;out[3]=device!=NULL;return 0;}

typedef struct {uint64_t epoch;uint32_t timed;int32_t result;uint64_t elapsed_ns;} NFPresentContext;
__declspec(dllexport) int nf_dx_bridge_present_context_callback(void*context_ptr){
 NFPresentContext*c=context_ptr;if(!c||c->timed>1||prepared_frame)return 0;
 LARGE_INTEGER begin,end,freq;QueryPerformanceCounter(&begin);
 memset(phase_times,0,sizeof(phase_times));memset(phase_cycles,0,sizeof(phase_cycles));phase_enabled=1;
 uint64_t out[16];c->result=bridge_frame(out,0);phase_enabled=0;
 if(phase_count<10000){memcpy(phase_rows[phase_count],phase_times,sizeof(phase_times));memcpy(phase_rows[phase_count]+8,phase_cycles,sizeof(phase_cycles));phase_rows[phase_count][16]=(uint32_t)c->result;phase_rows[phase_count][17]=GetCurrentThreadId();phase_count++;}
 QueryPerformanceCounter(&end);QueryPerformanceFrequency(&freq);
 if(!c->result){if(display_count<10000){uint64_t*row=display_rows[display_count++];row[0]=c->epoch;row[1]=begin.QuadPart;row[2]=end.QuadPart;row[3]=freq.QuadPart;memcpy(row+4,display_stats,sizeof(display_stats));}else display_dropped++;}
 c->elapsed_ns=c->timed?(uint64_t)((end.QuadPart-begin.QuadPart)*1000000000.0/freq.QuadPart):0;
 return c->result==0;
}





static uint64_t poll_stats[8];
__declspec(dllexport) int nf_dx_availability_poll_stats(uint64_t*out){if(!out)return 45;memcpy(out,poll_stats,sizeof(poll_stats));return 0;}
__declspec(dllexport) int nf_dx_availability_poll(unsigned timeout_ms){if(!availability||owner!=GetCurrentThreadId()||timeout_ms>2)return -45;DWORD result=availability_credit?WAIT_OBJECT_0:WaitForSingleObjectEx(availability,timeout_ms,FALSE);if(result==WAIT_OBJECT_0)availability_credit=1;poll_stats[0]++;poll_stats[1]+=result==WAIT_OBJECT_0;poll_stats[2]+=result==WAIT_TIMEOUT;poll_stats[3]+=result!=WAIT_OBJECT_0&&result!=WAIT_TIMEOUT;poll_stats[4]=presents;poll_stats[5]=result;LARGE_INTEGER t;QueryPerformanceCounter(&t);poll_stats[6]=t.QuadPart;poll_stats[7]=GetCurrentThreadId();return result==WAIT_OBJECT_0?1:result==WAIT_TIMEOUT?0:-50;}

static unsigned observation_enabled=1;
__declspec(dllexport) int nf_dx_observation_configure(unsigned enabled){if(device||enabled>1)return 45;observation_enabled=enabled;return 0;}
static uint64_t observation_rows[30000][16];static unsigned observation_count,observation_dropped;
__declspec(dllexport) int nf_dx_observe(uint64_t epoch,uint64_t generation,uint64_t index,unsigned point,uint64_t*out){
 if(!out||!swap||owner!=GetCurrentThreadId()||point>3)return 45;
 if(!observation_enabled){memset(out,0,16*sizeof(*out));return 0;}
 LARGE_INTEGER begin,end,freq;QueryPerformanceCounter(&begin);QueryPerformanceFrequency(&freq);
 UINT last=0;DXGI_FRAME_STATISTICS stats;memset(&stats,0,sizeof(stats));HRESULT a=IDXGISwapChain1_GetLastPresentCount(swap,&last),b=IDXGISwapChain1_GetFrameStatistics(swap,&stats);QueryPerformanceCounter(&end);
 uint64_t row[16]={epoch,generation,index,point,begin.QuadPart,end.QuadPart,freq.QuadPart,presents,(uint32_t)a,last,(uint32_t)b,stats.PresentCount,stats.PresentRefreshCount,stats.SyncRefreshCount,stats.SyncQPCTime.QuadPart,(uintptr_t)swap};memcpy(out,row,sizeof(row));
 if(observation_count<30000)memcpy(observation_rows[observation_count++],row,sizeof(row));else observation_dropped++;return 0;
}
__declspec(dllexport) unsigned nf_dx_observation_count(void){return observation_count;}
__declspec(dllexport) unsigned nf_dx_observation_dropped(void){return observation_dropped;}
__declspec(dllexport) int nf_dx_observation_read(unsigned i,uint64_t*out){if(!out||i>=observation_count)return 1;memcpy(out,observation_rows[i],sizeof(observation_rows[i]));return 0;}
static uint64_t prepare_rows[10000][21];static unsigned prepare_count,prepare_dropped;
__declspec(dllexport) unsigned nf_dx_prepare_count(void){return prepare_count;}
__declspec(dllexport) unsigned nf_dx_prepare_dropped(void){return prepare_dropped;}
__declspec(dllexport) int nf_dx_prepare_read(unsigned i,uint64_t*out){if(!out||i>=prepare_count)return 1;memcpy(out,prepare_rows[i],sizeof(prepare_rows[i]));return 0;}
__declspec(dllexport) int nf_dx_prepare_callback(uint64_t epoch,uint64_t generation,uint64_t index){
 memset(phase_times,0,sizeof(phase_times));memset(phase_cycles,0,sizeof(phase_cycles));phase_enabled=1;
 uint64_t out[16];int result=nf_dx_prepare(epoch,generation,index,0,out);phase_enabled=0;if(!result){uint64_t observed[16];nf_dx_observe(epoch,generation,index,0,observed);}
 if(prepare_count<10000){uint64_t*row=prepare_rows[prepare_count++];row[0]=epoch;row[1]=generation;row[2]=index;memcpy(row+3,phase_times,sizeof(phase_times));memcpy(row+11,phase_cycles,sizeof(phase_cycles));row[19]=(uint32_t)result;row[20]=GetCurrentThreadId();}else prepare_dropped++;
 if(completion_count<10000){uint64_t*row=completion_rows[completion_count++];row[0]=epoch;row[1]=generation;row[2]=index;memcpy(row+3,completion_probe,sizeof(completion_probe));}else completion_dropped++;
 return result;
}
__declspec(dllexport) int nf_dx_present_prepared_callback(uint64_t epoch,uint64_t generation,uint64_t index,void*ptr){
 NFPresentContext*c=ptr;if(!c||c->timed>1||c->epoch!=epoch)return 0;
 uint64_t observed[16];nf_dx_observe(epoch,generation,index,1,observed);
 LARGE_INTEGER begin,end,freq;QueryPerformanceCounter(&begin);
 memset(phase_times,0,sizeof(phase_times));memset(phase_cycles,0,sizeof(phase_cycles));phase_enabled=1;
 uint64_t out[16];c->result=nf_dx_present_prepared(epoch,generation,index,out);phase_enabled=0;nf_dx_observe(epoch,generation,index,2,observed);
 if(phase_count<10000){memcpy(phase_rows[phase_count],phase_times,sizeof(phase_times));memcpy(phase_rows[phase_count]+8,phase_cycles,sizeof(phase_cycles));phase_rows[phase_count][16]=(uint32_t)c->result;phase_rows[phase_count][17]=GetCurrentThreadId();phase_count++;}
 QueryPerformanceCounter(&end);QueryPerformanceFrequency(&freq);
 if(!c->result){if(display_count<10000){uint64_t*row=display_rows[display_count++];row[0]=epoch;row[1]=begin.QuadPart;row[2]=end.QuadPart;row[3]=freq.QuadPart;memcpy(row+4,display_stats,sizeof(display_stats));}else display_dropped++;}
 c->elapsed_ns=c->timed?(uint64_t)((end.QuadPart-begin.QuadPart)*1000000000.0/freq.QuadPart):0;return c->result==0;
}


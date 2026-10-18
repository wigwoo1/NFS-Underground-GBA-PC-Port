#include <windows.h>
#include <GL/gl.h>
#include <dwmapi.h>
#include <stdint.h>
#include <string.h>
static int valid(void*p){return(uintptr_t)p>3&&(intptr_t)p!=-1;}
static int extension(const char*all,const char*name){if(!all)return 0;size_t n=strlen(name);const char*p=all;while((p=strstr(p,name))){if((p==all||p[-1]==' ')&&(p[n]==0||p[n]==' '))return 1;p+=n;}return 0;}
__declspec(dllexport) int nf_present_capabilities(uint64_t*out){
 if(!out||!wglGetCurrentContext())return 31;
 memset(out,0,32*sizeof(*out));HDC dc=wglGetCurrentDC();HWND window=WindowFromDC(dc);out[0]=1;out[1]=dc!=NULL;out[2]=window&&GetWindowThreadProcessId(window,NULL)==GetCurrentThreadId();
 const char*(WINAPI*extensions)(HDC)=(void*)wglGetProcAddress("wglGetExtensionsStringARB");const char*names=valid((void*)extensions)?extensions(dc):NULL;
 out[3]=extension(names,"WGL_NV_DX_interop");out[4]=extension(names,"WGL_NV_DX_interop2");
 const char*functions[7]={"wglDXOpenDeviceNV","wglDXCloseDeviceNV","wglDXRegisterObjectNV","wglDXUnregisterObjectNV","wglDXLockObjectsNV","wglDXUnlockObjectsNV","wglDXSetResourceShareHandleNV"};
 for(unsigned i=0;i<7;i++)out[5+i]=valid((void*)wglGetProcAddress(functions[i]));
 int(WINAPI*interval)(void)=(void*)wglGetProcAddress("wglGetSwapIntervalEXT");out[12]=valid((void*)interval);if(out[12])out[13]=(uint64_t)((int64_t)interval()+1);
 HMODULE dwm=LoadLibraryA("dwmapi.dll");if(!dwm)return 0;
 HRESULT(WINAPI*enabled)(BOOL*)=(void*)GetProcAddress(dwm,"DwmIsCompositionEnabled");HRESULT(WINAPI*timing)(HWND,DWM_TIMING_INFO*)=(void*)GetProcAddress(dwm,"DwmGetCompositionTimingInfo");
 BOOL composition=FALSE;out[14]=enabled!=NULL;if(enabled){out[15]=(uint32_t)enabled(&composition);out[16]=composition;}
 if(timing){DWM_TIMING_INFO info;memset(&info,0,sizeof(info));info.cbSize=sizeof(info);HRESULT status=timing(NULL,&info);out[17]=1;out[18]=(uint32_t)status;if(SUCCEEDED(status)){out[19]=info.rateRefresh.uiNumerator;out[20]=info.rateRefresh.uiDenominator;out[21]=info.qpcRefreshPeriod;out[22]=info.qpcVBlank;out[23]=info.cRefresh;out[24]=info.cFrame;out[25]=info.cFramesLate;out[26]=info.cFramesOutstanding;}}
 FreeLibrary(dwm);return 0;
}

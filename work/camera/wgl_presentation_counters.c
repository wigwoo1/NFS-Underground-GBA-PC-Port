#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <stdint.h>
__declspec(dllexport) int nf_wgl_presentation_counters(int64_t*out){
 if(!out)return -1;for(int i=0;i<5;i++)out[i]=0;
 HDC dc=wglGetCurrentDC();if(!dc||!wglGetCurrentContext())return -2;
 BOOL(WINAPI*sync)(HDC,int64_t*,int64_t*,int64_t*)=(void*)wglGetProcAddress("wglGetSyncValuesOML");
 BOOL(WINAPI*rate)(HDC,int32_t*,int32_t*)=(void*)wglGetProcAddress("wglGetMscRateOML");
 if((uintptr_t)sync<=3||(intptr_t)sync==-1)return 0;
 if(!sync(dc,out,out+1,out+2))return -3;
 int32_t numerator=0,denominator=0;
 if((uintptr_t)rate>3&&(intptr_t)rate!=-1&&rate(dc,&numerator,&denominator)){out[3]=numerator;out[4]=denominator;}
 return 1;
}


#include <dwmapi.h>
static uint64_t cadence_rows[10000][22];static unsigned cadence_count,cadence_dropped;static uint64_t cadence_serial;
/* DWM values describe composition, not this application's physical scanout.
   Optional OML values are valid only when the current driver supplies them. */
static int cadence_probe(uint64_t epoch,unsigned point,HDC dc){
 if(!dc||!wglGetCurrentContext()||gpu_owner!=GetCurrentThreadId())return 31;
 LARGE_INTEGER begin,end,f;QueryPerformanceCounter(&begin);QueryPerformanceFrequency(&f);
 DWM_TIMING_INFO info;memset(&info,0,sizeof(info));info.cbSize=sizeof(info);
 HRESULT hr=DwmGetCompositionTimingInfo(NULL,&info);
 BOOL(WINAPI*sync)(HDC,int64_t*,int64_t*,int64_t*)=(void*)wglGetProcAddress("wglGetSyncValuesOML");
 int valid=sync&&(uintptr_t)sync>3&&(intptr_t)sync!=-1;int64_t ust=0,msc=0,sbc=0;int success=valid?sync(dc,&ust,&msc,&sbc):0;
 int(WINAPI*interval)(void)=(void*)wglGetProcAddress("wglGetSwapIntervalEXT");int iv=interval&&(uintptr_t)interval>3&&(intptr_t)interval!=-1?interval():-99;
 QueryPerformanceCounter(&end);
 uint64_t row[22]={epoch,cadence_serial,point,begin.QuadPart,end.QuadPart,f.QuadPart,(uint32_t)hr,info.qpcRefreshPeriod,info.rateRefresh.uiNumerator,info.rateRefresh.uiDenominator,info.qpcVBlank,info.cRefresh,info.cFrame,info.cFramesDisplayed,info.cFramesDropped,info.cFramesMissed,valid,success,ust,msc,sbc,(int64_t)iv};
 if(cadence_count<10000)memcpy(cadence_rows[cadence_count++],row,sizeof(row));else cadence_dropped++;return 0;
}
__declspec(dllexport) unsigned nf_owned_gpu_cadence_count(void){return cadence_count;}
__declspec(dllexport) unsigned nf_owned_gpu_cadence_dropped(void){return cadence_dropped;}
__declspec(dllexport) int nf_owned_gpu_cadence_read(unsigned i,uint64_t*out){if(!out||i>=cadence_count)return 1;memcpy(out,cadence_rows[i],sizeof(cadence_rows[i]));return 0;}
__declspec(dllexport) int nf_owned_gpu_cadence_probe(void){return cadence_probe(0,2,wglGetCurrentDC());}

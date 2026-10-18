#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <commdlg.h>
#include <mmsystem.h>
#include <xinput.h>
#include <GL/gl.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <mgba/core/core.h>
#include <mgba/core/blip_buf.h>
#include "../outputs/nfsug-research/controller.h"
#include "v2/scene.h"
#include "v2/gpu.h"
#include "v2/texture_pack.h"
int nf_init(const char*,const char*);void nf_frame(unsigned);void* nf_pixels(void);
unsigned nf_reg(int);unsigned nf_read(unsigned,int);void nf_native(int);unsigned nf_native_calls(void);unsigned nf_native_rejected(void);
void nf_60(int);unsigned nf_scene_version(void);
int nf_gpu_motion_legacy_forced(void);
void nf_close(void);int nf_state(const char*,int);struct mCore* nf_core(void);
static HWND window;static HDC dc;static HGLRC glcontext;static GLuint texture;
static int running=1,native_mode=0,paused=0,fullscreen=0,ready=0,hidden=0;
static int gpu_mode=1,gpu_ready,mode60=0;
static FILE* diagnostic;
static FILE* frame_audit;
static FILE* layer_audit;
static int focus_paused;
static int smooth_motion=1;
static HMENU texture_menu;
enum {ID_TEXTURE_ORIGINAL=42001,ID_TEXTURE_UPSCALED=42002};
static int texture_pack_preference,texture_pack_available;
static char settings_path[MAX_PATH];
static int scene_available(void){int n=0;nf_scene(&n);return n>0;}
static const char* capture_path;
static RECT window_rect;static char folder[MAX_PATH],rom[MAX_PATH],savepath[MAX_PATH],notice[160];
static LARGE_INTEGER freq;static double notice_until;
static double metric_update_s,metric_draw_s,metric_audit_s,metric_wait_s,metric_update_max_s,metric_draw_max_s,metric_audit_max_s,metric_wait_max_s;
static unsigned metric_max_update_batch;
static DWORD (WINAPI* getpad)(DWORD,XINPUT_STATE*);
static HWAVEOUT audio;static WAVEHDR wave[8];static short samples[8][4096];
static double now(void){LARGE_INTEGER q;QueryPerformanceCounter(&q);return (double)q.QuadPart/freq.QuadPart;}
static void status(const char* s){snprintf(notice,sizeof(notice),"%s",s);notice_until=now()+3;}
static void audio_reset(void){if(audio)waveOutReset(audio);if(ready){struct mCore*c=nf_core();if(c){blip_clear(c->getAudioChannel(c,0));blip_clear(c->getAudioChannel(c,1));}}}
static void audio_init(void){
 WAVEFORMATEX f={WAVE_FORMAT_PCM,2,44100,44100*4,4,16,0};
 if(waveOutOpen(&audio,WAVE_MAPPER,&f,0,0,CALLBACK_NULL)!=MMSYSERR_NOERROR){audio=0;return;}
 for(int i=0;i<8;i++){wave[i].lpData=(char*)samples[i];wave[i].dwBufferLength=sizeof(samples[i]);waveOutPrepareHeader(audio,&wave[i],sizeof(WAVEHDR));}
}
static void audio_push(void){
 struct mCore* c=nf_core();blip_t* l=c->getAudioChannel(c,0);blip_t*r=c->getAudioChannel(c,1);
 int n=blip_samples_avail(l);if(n>2048)n=2048;if(n<=0)return;
 for(int i=0;i<8;i++)if(!(wave[i].dwFlags&WHDR_INQUEUE)){
  blip_read_samples(l,samples[i],n,1);blip_read_samples(r,samples[i]+1,n,1);
  if(audio){wave[i].dwBufferLength=n*4;waveOutWrite(audio,&wave[i],sizeof(WAVEHDR));}return;
 }
 /* Keep game timing independent of a stalled audio device. */
 short discard[4096];blip_read_samples(l,discard,n,1);blip_read_samples(r,discard+1,n,1);
}
static void toggle_fullscreen(void){
 if(!fullscreen){GetWindowRect(window,&window_rect);MONITORINFO m={sizeof(m)};GetMonitorInfo(MonitorFromWindow(window,MONITOR_DEFAULTTONEAREST),&m);SetWindowLongPtr(window,GWL_STYLE,WS_POPUP|WS_VISIBLE);SetWindowPos(window,HWND_TOP,m.rcMonitor.left,m.rcMonitor.top,m.rcMonitor.right-m.rcMonitor.left,m.rcMonitor.bottom-m.rcMonitor.top,SWP_FRAMECHANGED);}
 else{SetWindowLongPtr(window,GWL_STYLE,WS_OVERLAPPEDWINDOW|WS_VISIBLE);SetWindowPos(window,NULL,window_rect.left,window_rect.top,window_rect.right-window_rect.left,window_rect.bottom-window_rect.top,SWP_FRAMECHANGED|SWP_NOZORDER);}fullscreen=!fullscreen;
}
static void texture_pack_select(int upscaled,int persist){
 if(upscaled&&!nf_gpu_texture_pack_available()){
  upscaled=0;
  status("4K upscaled pack not installed; using original textures");
 }else status(upscaled?"4K upscaled textures enabled":"Original textures enabled");
 texture_pack_preference=upscaled;
 if(texture_menu){
  CheckMenuRadioItem(texture_menu,ID_TEXTURE_ORIGINAL,ID_TEXTURE_UPSCALED,
   upscaled?ID_TEXTURE_UPSCALED:ID_TEXTURE_ORIGINAL,MF_BYCOMMAND);
  if(!texture_pack_available)EnableMenuItem(texture_menu,ID_TEXTURE_UPSCALED,MF_BYCOMMAND|MF_GRAYED);
 }
 if(gpu_ready)nf_gpu_texture_pack(upscaled);
 if(persist&&settings_path[0]&&!nf_texture_pack_preference_save(settings_path,upscaled))
  status("Texture mode changed for this run, but settings.ini could not be saved");
}
static void texture_menu_init(void){
 HMENU root=CreateMenu(),graphics=CreatePopupMenu();texture_menu=CreatePopupMenu();
 if(!root||!graphics||!texture_menu){if(root)DestroyMenu(root);if(graphics)DestroyMenu(graphics);if(texture_menu)DestroyMenu(texture_menu);texture_menu=NULL;return;}
 texture_pack_available=nf_gpu_texture_pack_available();
 AppendMenuA(texture_menu,MF_STRING,ID_TEXTURE_ORIGINAL,"Original textures");
 AppendMenuA(texture_menu,MF_STRING|(texture_pack_available?0:MF_GRAYED),ID_TEXTURE_UPSCALED,
  texture_pack_available?"4K Upscaled textures":"4K Upscaled textures (pack not installed)");
 CheckMenuRadioItem(texture_menu,ID_TEXTURE_ORIGINAL,ID_TEXTURE_UPSCALED,
  texture_pack_preference&&texture_pack_available?ID_TEXTURE_UPSCALED:ID_TEXTURE_ORIGINAL,MF_BYCOMMAND);
 AppendMenuA(graphics,MF_POPUP,(UINT_PTR)texture_menu,"Texture set");
 AppendMenuA(root,MF_POPUP,(UINT_PTR)graphics,"Graphics");
 if(!SetMenu(window,root)){DestroyMenu(root);texture_menu=NULL;return;}
 DrawMenuBar(window);
}
static LRESULT CALLBACK proc(HWND h,UINT m,WPARAM w,LPARAM l){
 if(m==WM_CLOSE){running=0;return 0;}
 if(m==WM_COMMAND){
  switch(LOWORD(w)){
   case ID_TEXTURE_ORIGINAL:texture_pack_select(0,1);return 0;
   case ID_TEXTURE_UPSCALED:texture_pack_select(1,1);return 0;
  }
 }
 if(m==WM_SETFOCUS && focus_paused){focus_paused=0;paused=0;audio_reset();status("Resumed");}
 if(m==WM_KILLFOCUS && ready){if(!paused)focus_paused=1;paused=1;audio_reset();status("Paused - click the window and press Space to resume");}
 if(m==WM_KEYDOWN && !(l&(1L<<30))){
  if(w==VK_ESCAPE && fullscreen)toggle_fullscreen();
  if(w==VK_F11)toggle_fullscreen();
  if(w==VK_SPACE){focus_paused=0;paused=!paused;audio_reset();status(paused?"Paused":"Resumed");}
  if(w==VK_F2 && ready){native_mode=!native_mode;nf_native(native_mode);status(native_mode?"Experimental native span routine enabled":"Reference renderer enabled");}
  if(w==VK_F4 && ready){smooth_motion=!smooth_motion;nf_gpu_motion(smooth_motion);status(smooth_motion?"Geometry interpolation ON; original simulation timing":"Geometry interpolation OFF; original simulation timing");}
  if(w==VK_F3 && ready){gpu_mode=!gpu_mode;status(gpu_mode?"4K GPU polygons enabled (experimental)":"Original GBA rendering");}
  if(w==VK_F5 && ready)status(nf_state(savepath,1)?"Snapshot saved":"Save failed");
  if(w==VK_F8 && ready){status(nf_state(savepath,0)?"Snapshot loaded":"No compatible snapshot found");audio_reset();}
  if(w==VK_F1){paused=1;audio_reset();MessageBoxA(h,"Xbox: RT/A = accelerate/confirm; LT/B = brake/back\nLeft stick or D-pad = steer/navigate\nLB/X = GBA L; RB/Y = GBA R\nMenu = Start; View = Select\n\nKeyboard: Arrows, Z=A, X=B, A=L, S=R\nEnter=Start; Backspace=Select\n\nGraphics menu: choose Original or 4K Upscaled textures\nF3: 4K geometry / original image\nF4: geometry interpolation (simulation stays original)\nF2: experimental native span routine\nF5/F8: save/load snapshot; Space: pause\nF11: fullscreen; Escape: leave fullscreen\n\nThis research build still uses mGBA for the game.\nRoad, car and scenery use a 3840x2160 GPU render target.\nHUD and unsupported effects retain original resolution.\nGame logic still runs in mGBA at original timing.\n60-fps gameplay and a fully native port remain in development.","NFSUG Port Lab - controls and status",MB_OK);status("Paused - Space to resume");}
 }
 return DefWindowProc(h,m,w,l);
}
static unsigned input(int* controller){
 *controller=0;if(GetForegroundWindow()!=window || paused)return 0;
 unsigned k=0;int vk[]={ 'Z','X',VK_BACK,VK_RETURN,VK_RIGHT,VK_LEFT,VK_UP,VK_DOWN,'S','A'};
 for(int i=0;i<10;i++)if(GetAsyncKeyState(vk[i])&0x8000)k|=1<<i;
 if(getpad)for(DWORD i=0;i<4;i++){XINPUT_STATE s;if(getpad(i,&s)==ERROR_SUCCESS){*controller=1;k|=nfs_map_controller(s.Gamepad.wButtons,s.Gamepad.sThumbLX,s.Gamepad.sThumbLY,s.Gamepad.bLeftTrigger,s.Gamepad.bRightTrigger);break;}}
 return k;
}
static int draw(void){
 RECT rc;GetClientRect(window,&rc);int w=rc.right,h=rc.bottom;if(w<1||h<1)return 1;
 if(gpu_ready && gpu_mode){int native_view=scene_available();nf_gpu_draw(w,h,native_view);GLenum e=glGetError();if(e!=GL_NO_ERROR&&diagnostic)fprintf(diagnostic,"OpenGL draw error=0x%04x native_view=%d scene_version=%u polygons=%d\n",(unsigned)e,native_view,nf_scene_version(),nf_gpu_polygon_count());SwapBuffers(dc);return e==GL_NO_ERROR;}
 glDisable(GL_ALPHA_TEST);glDisable(GL_BLEND);glDisable(GL_DEPTH_TEST);
 glViewport(0,0,w,h);glClearColor(0,0,0,1);glClear(GL_COLOR_BUFFER_BIT);
 int vw=w,vh=(int)(w/1.5);if(vh>h){vh=h;vw=(int)(h*1.5);}glViewport((w-vw)/2,(h-vh)/2,vw,vh);
 glMatrixMode(GL_PROJECTION);glLoadIdentity();glOrtho(0,1,1,0,-1,1);glMatrixMode(GL_MODELVIEW);glLoadIdentity();
 glEnable(GL_TEXTURE_2D);glBindTexture(GL_TEXTURE_2D,texture);glTexSubImage2D(GL_TEXTURE_2D,0,0,0,240,160,GL_RGBA,GL_UNSIGNED_BYTE,nf_pixels());
 glColor3f(1,1,1);glBegin(GL_QUADS);glTexCoord2f(0,0);glVertex2f(0,0);glTexCoord2f(1,0);glVertex2f(1,0);glTexCoord2f(1,1);glVertex2f(1,1);glTexCoord2f(0,1);glVertex2f(0,1);glEnd();
 GLenum err=glGetError();SwapBuffers(dc);return err==GL_NO_ERROR;
}
int main(int argc,char** argv){
 QueryPerformanceFrequency(&freq);SetProcessDPIAware();
 GetModuleFileNameA(NULL,folder,MAX_PATH);char*p=strrchr(folder,'\\');if(p)*p=0;
 snprintf(settings_path,sizeof(settings_path),"%s\\settings.ini",folder);
 texture_pack_preference=nf_texture_pack_preference_load(settings_path);
 snprintf(savepath,sizeof(savepath),"%s\\progress.state",folder);
 char logpath[MAX_PATH];snprintf(logpath,sizeof(logpath),"%s\\startup-diagnostic.log",folder);diagnostic=fopen(logpath,"w");if(diagnostic){setvbuf(diagnostic,NULL,_IONBF,0);fprintf(diagnostic,"NFSUG fresh scene renderer build 4\n");}
 snprintf(rom,sizeof(rom),"G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba");
 int testframes=0,test_startup=0,test_audio=0,test_realtime=0,test_foreground=0;char* loadstate=NULL;char* exitstate=NULL;
 for(int i=1;i<argc;i++){if(!strcmp(argv[i],"--test-startup")){test_startup=1;testframes=2400;hidden=1;}else if(!strcmp(argv[i],"--audit-frames")&&i+1<argc){frame_audit=fopen(argv[++i],"w");if(frame_audit)fprintf(frame_audit,"seconds,emuframe,hash,mode60,polygons\n");}else if(!strcmp(argv[i],"--audit-layers")&&i+1<argc){layer_audit=fopen(argv[++i],"w");if(layer_audit)fprintf(layer_audit,"seconds,emuframe,source_frame_hash,masked_backdrop_hash,differential_overlay_hash,overlay_opaque_pixels,overlay_active,sky_candidate_roi_hash,top_band_hash,scene_version,polygons\n");}else if(!strcmp(argv[i],"--test-realtime")){test_realtime=1;}else if(!strcmp(argv[i],"--test-audio")){test_audio=1;}else if(!strcmp(argv[i],"--test-visible")&&i+1<argc){testframes=atoi(argv[++i]);}else if(!strcmp(argv[i],"--test-foreground")&&i+1<argc){testframes=atoi(argv[++i]);test_foreground=1;}else if(!strcmp(argv[i],"--test")&&i+1<argc){testframes=atoi(argv[++i]);hidden=1;}else if(!strcmp(argv[i],"--original-timing"))mode60=0;else if(!strcmp(argv[i],"--no-smoothing"))smooth_motion=0;else if(!strcmp(argv[i],"--native"))native_mode=1;else if(!strcmp(argv[i],"--reference"))gpu_mode=0;else if(!strcmp(argv[i],"--capture")&&i+1<argc)capture_path=argv[++i];else if(!strcmp(argv[i],"--save-exit")&&i+1<argc)exitstate=argv[++i];else if(!strcmp(argv[i],"--state")&&i+1<argc)loadstate=argv[++i];else if(!strcmp(argv[i],"--rom")&&i+1<argc)snprintf(rom,sizeof(rom),"%s",argv[++i]);}
 if(GetFileAttributesA(rom)==INVALID_FILE_ATTRIBUTES){
  if(hidden)return 2;rom[0]=0;OPENFILENAMEA ofn={sizeof(ofn)};ofn.lpstrFilter="GBA ROM\0*.gba\0";ofn.lpstrFile=rom;ofn.nMaxFile=MAX_PATH;ofn.Flags=OFN_FILEMUSTEXIST|OFN_NOCHANGEDIR;ofn.lpstrTitle="Choose your Need for Speed Underground GBA ROM";if(!GetOpenFileNameA(&ofn))return 2;
 }
 if(!nf_init(rom,"")){if(!hidden)MessageBoxA(NULL,"This build requires the inspected NFSUG BNSE revision 0 ROM (CRC32 828020E9).","ROM could not be loaded",MB_ICONERROR);return 3;}
 ready=1;nf_native(native_mode);nf_60(0);
 struct mCore* core=nf_core();blip_set_rates(core->getAudioChannel(core,0),core->frequency(core),44100);blip_set_rates(core->getAudioChannel(core,1),core->frequency(core),44100);
 if(loadstate && !nf_state(loadstate,0))return 4;
 nf_scene_enable(1);
 WNDCLASSA wc={0};wc.lpfnWndProc=proc;wc.hInstance=GetModuleHandle(NULL);wc.lpszClassName="NFSUGPortLab";wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.style=CS_OWNDC;RegisterClassA(&wc);
 window=CreateWindowA(wc.lpszClassName,"NFSUG Native Renderer | 4K geometry experiment | F1 controls",WS_OVERLAPPEDWINDOW,CW_USEDEFAULT,CW_USEDEFAULT,1216,839,NULL,NULL,wc.hInstance,NULL);
 if(!window)return 5;dc=GetDC(window);PIXELFORMATDESCRIPTOR pf={sizeof(pf),1,PFD_DRAW_TO_WINDOW|PFD_SUPPORT_OPENGL|PFD_DOUBLEBUFFER,PFD_TYPE_RGBA,32,0,0,0,0,0,0,0,0,0,0,0,0,24,8,0,PFD_MAIN_PLANE,0,0,0,0};
 int fmt=ChoosePixelFormat(dc,&pf);if(!fmt||!SetPixelFormat(dc,fmt,&pf))return 6;glcontext=wglCreateContext(dc);if(!glcontext||!wglMakeCurrent(dc,glcontext))return 7;
 BOOL(WINAPI* interval)(int)=(void*)wglGetProcAddress("wglSwapIntervalEXT");if(interval)interval(0);
 glGenTextures(1,&texture);glBindTexture(GL_TEXTURE_2D,texture);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,240,160,0,GL_RGBA,GL_UNSIGNED_BYTE,nf_pixels());
 gpu_ready=nf_gpu_init();nf_gpu_motion(smooth_motion);nf_gpu_audit_layers(frame_audit!=NULL||layer_audit!=NULL);
 texture_menu_init();texture_pack_select(texture_pack_preference,0);
 HMODULE xi=LoadLibraryA("xinput1_4.dll");if(!xi)xi=LoadLibraryA("xinput9_1_0.dll");if(xi)getpad=(void*)GetProcAddress(xi,"XInputGetState");
 if(!hidden){ShowWindow(window,SW_SHOW);if(test_foreground)SetForegroundWindow(window);}if(!hidden||test_audio)audio_init();timeBeginPeriod(1);
 double last=now(),loop_start=last,acc=0,title_time=last,deadline=last,loop_interval_max=0;uint64_t loop_over_16667=0,loop_over_20000=0,loop_over_25000=0,loop_over_30000=0,loop_over_33333=0;unsigned version=nf_scene_version();int motionframes=0,displayframes=0,motionframes_total=0,displayframes_total=0,scenes=0,emuframes=0,errors=0,pad=0;unsigned page=nf_read(0x04000000,2)&16;
 double step=(double)core->frameCycles(core)/core->frequency(core);
 while(running){
  MSG msg;while(PeekMessage(&msg,NULL,0,0,PM_REMOVE)){TranslateMessage(&msg);DispatchMessage(&msg);}
  double t=now(),dt=t-last;last=t;if(dt>loop_interval_max)loop_interval_max=dt;if(dt*1000.0>16.667)loop_over_16667++;if(dt*1000.0>20.0)loop_over_20000++;if(dt*1000.0>25.0)loop_over_25000++;if(dt*1000.0>30.0)loop_over_30000++;if(dt*1000.0>33.333)loop_over_33333++;if(dt>0.25)dt=0.25;
  if(testframes&&!test_realtime)acc=step;else if(!paused)acc+=dt;else acc=0;
  unsigned keys=testframes?1:input(&pad);
  if(test_startup){keys=0;int starts[]={500,692,944,1196,1448,1700,1952,2204};for(int j=0;j<8;j++)if(emuframes>=starts[j]&&emuframes<starts[j]+12)keys=j==1?8:1;}
  double update_begin=now();unsigned update_batch=0;
  while(acc>=step&&(!testframes||emuframes<testframes)){nf_frame(keys);audio_push();acc-=step;emuframes++;update_batch++;unsigned q=nf_read(0x04000000,2)&16;if(q!=page){scenes++;page=q;}}
  double update_cost=now()-update_begin;metric_update_s+=update_cost;if(update_cost>metric_update_max_s)metric_update_max_s=update_cost;if(update_batch>metric_max_update_batch)metric_max_update_batch=update_batch;
  if(frame_audit||layer_audit)nf_gpu_audit_frame_begin();
  double draw_begin=now();if(!draw())errors++;displayframes++;displayframes_total++;double draw_cost=now()-draw_begin;metric_draw_s+=draw_cost;if(draw_cost>metric_draw_max_s)metric_draw_max_s=draw_cost;
  unsigned latest=nf_scene_version();if(latest!=version&&scene_available()){motionframes++;motionframes_total++;}version=latest;
  double audit_begin=now();
  if(frame_audit)fprintf(frame_audit,"%.6f,%d,%08x,%d,%d\n",now(),emuframes,nf_gpu_frame_hash(),mode60,nf_gpu_polygon_count());
  if(layer_audit)fprintf(layer_audit,"%.6f,%d,%08x,%08x,%08x,%u,%d,%08x,%08x,%u,%d\n",now(),emuframes,nf_gpu_reference_hash(),nf_gpu_background_hash(),nf_gpu_overlay_hash(),nf_gpu_overlay_pixel_count(),nf_gpu_overlay_active(),nf_gpu_source_region_hash(70,12,21,19),nf_gpu_source_region_hash(0,0,240,34),nf_scene_version(),nf_gpu_polygon_count());
  double audit_cost=now()-audit_begin;metric_audit_s+=audit_cost;if(audit_cost>metric_audit_max_s)metric_audit_max_s=audit_cost;
  if(t-title_time>=1 && diagnostic && !hidden)fprintf(diagnostic,"frames=%d paused=%d focus_pause=%d foreground=%d state=%u pc=%08x display=%04x errors=%d audio=%d mode60=%d motion_fps=%.2f present_fps=%.2f\n",emuframes,paused,focus_paused,GetForegroundWindow()==window,nf_read(0x03005f14,4),nf_reg(15),nf_read(0x04000000,2),errors,audio!=0,mode60,motionframes/(t-title_time),displayframes/(t-title_time));
  if(t-title_time>=1 && !hidden){char title[512];snprintf(title,sizeof(title),"NFSUG Motion Interpolation | %s | source %.1f fps | display %.1f fps | %s | %s",gpu_ready&&gpu_mode&&scene_available()?smooth_motion?"4K interpolation / original logic":"4K / original timing":"original display",motionframes/(t-title_time),displayframes/(t-title_time),pad?"Xbox connected":"keyboard / no active Xbox",t<notice_until?notice:paused?"PAUSED - Space resumes":"F1 controls  F3 compare  F4 timing  F5 save  F8 load  F11 fullscreen");SetWindowTextA(window,title);title_time=t;scenes=0;displayframes=0;motionframes=0;}
  if(testframes && emuframes>=testframes)break;
  if(!testframes||test_realtime){deadline+=1.0/60.0;double left=deadline-now();if(left>0)Sleep((DWORD)(left*1000));else if(left<-.1)deadline=now();}
  double wait_cost=now()-t;if(wait_cost>draw_cost+audit_cost+update_cost){wait_cost-=draw_cost+audit_cost+update_cost;}else wait_cost=0;metric_wait_s+=wait_cost;if(wait_cost>metric_wait_max_s)metric_wait_max_s=wait_cost;
  if(diagnostic&&(dt>0.033333||update_cost>0.033333||draw_cost>0.033333||audit_cost>0.033333||wait_cost>0.033333))fprintf(diagnostic,"slow-loop frame=%d foreground=%d loop_ms=%.3f update_ms=%.3f draw_swap_ms=%.3f audit_ms=%.3f wait_ms=%.3f polygons=%d\n",emuframes,GetForegroundWindow()==window,dt*1000.0,update_cost*1000.0,draw_cost*1000.0,audit_cost*1000.0,wait_cost*1000.0,nf_gpu_polygon_count());
 }
 if(testframes){
  char phase_report[MAX_PATH];snprintf(phase_report,sizeof(phase_report),"%s\\host-phase-metrics.json",folder);FILE*phase_file=fopen(phase_report,"w");if(phase_file){fprintf(phase_file,"{\"emulation_total_ms\":%.3f,\"emulation_max_ms\":%.3f,\"draw_and_swap_total_ms\":%.3f,\"draw_and_swap_max_ms\":%.3f,\"audit_io_total_ms\":%.3f,\"audit_io_max_ms\":%.3f,\"wait_and_other_total_ms\":%.3f,\"wait_and_other_max_ms\":%.3f,\"max_updates_per_loop\":%u}\n",metric_update_s*1000.0,metric_update_max_s*1000.0,metric_draw_s*1000.0,metric_draw_max_s*1000.0,metric_audit_s*1000.0,metric_audit_max_s*1000.0,metric_wait_s*1000.0,metric_wait_max_s*1000.0,metric_max_update_batch);fclose(phase_file);}
  uint64_t match_calls=0,match_ns=0,match_max_ns=0,match_candidates=0,legacy_cost_calls=0,verify_pairs=0,verify_mismatches=0;nf_gpu_motion_profile(&match_calls,&match_ns,&match_max_ns,&match_candidates,&legacy_cost_calls);nf_gpu_motion_verification(&verify_pairs,&verify_mismatches);
  char report[MAX_PATH];snprintf(report,sizeof(report),"%s\\host-test.json",folder);FILE*f=fopen(report,"w");if(f){double elapsed=now()-loop_start;if(elapsed<=0)elapsed=1e-9;fprintf(f,"{\"frames\":%d,\"elapsed_seconds\":%.6f,\"display_iterations\":%d,\"scene_version_updates\":%d,\"loop_intervals_over_16_667_ms\":%llu,\"loop_intervals_over_20_ms\":%llu,\"loop_intervals_over_25_ms\":%llu,\"loop_intervals_over_30_ms\":%llu,\"loop_intervals_over_33_333_ms\":%llu,\"loop_interval_max_ms\":%.3f,\"native_calls\":%u,\"native_rejected\":%u,\"opengl_errors\":%d,\"render_target_width\":%d,\"render_target_height\":%d,\"native_geometry\":%s,\"captured_polygons\":%d,\"motion_profile_calls\":%llu,\"motion_profile_total_ns\":%llu,\"motion_profile_max_ns\":%llu,\"motion_candidate_comparisons\":%llu,\"motion_legacy_cost_calls\":%llu,\"motion_verify_scene_pairs\":%llu,\"motion_verify_mismatches\":%llu,\"motion_legacy_forced\":%s,\"xinput_available\":%s,\"renderer\":\"%s\"}\n",emuframes,elapsed,displayframes_total,motionframes_total,(unsigned long long)loop_over_16667,(unsigned long long)loop_over_20000,(unsigned long long)loop_over_25000,(unsigned long long)loop_over_30000,(unsigned long long)loop_over_33333,loop_interval_max*1000.0,nf_native_calls(),nf_native_rejected(),errors,gpu_ready?3840:240,gpu_ready?2160:160,gpu_ready&&gpu_mode?"true":"false",gpu_ready?nf_gpu_polygon_count():0,(unsigned long long)match_calls,(unsigned long long)match_ns,(unsigned long long)match_max_ns,(unsigned long long)match_candidates,(unsigned long long)legacy_cost_calls,(unsigned long long)verify_pairs,(unsigned long long)verify_mismatches,nf_gpu_motion_legacy_forced()?"true":"false",getpad?"true":"false",glGetString(GL_RENDERER));fclose(f);}
 }
 if(audio){waveOutReset(audio);for(int i=0;i<8;i++)waveOutUnprepareHeader(audio,&wave[i],sizeof(WAVEHDR));waveOutClose(audio);}timeEndPeriod(1);
 if(exitstate)nf_state(exitstate,1);
 if(capture_path&&gpu_ready){RECT rc;GetClientRect(window,&rc);nf_gpu_draw(rc.right,rc.bottom,scene_available());nf_gpu_capture(capture_path);}
 if(diagnostic){fprintf(diagnostic,"Clean exit frames=%d errors=%d\n",emuframes,errors);fclose(diagnostic);}
 if(frame_audit)fclose(frame_audit);
 if(layer_audit)fclose(layer_audit);
 ready=0;running=0;if(xi)FreeLibrary(xi);nf_close();if(gpu_ready)nf_gpu_close();glDeleteTextures(1,&texture);wglMakeCurrent(NULL,NULL);wglDeleteContext(glcontext);ReleaseDC(window,dc);DestroyWindow(window);return errors?8:0;
}

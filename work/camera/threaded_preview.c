/* Separate opt-in integration host. Only worker touches renderer globals/GL;
   only producer touches bridge, snapshot history and original updates. */
#define NF_PACED_NO_MAIN
#include "paced_preview.c"
#include "render_handoff.h"
#include "road_split_hud_gpu.h"
#include "prepared_motion_gpu.h"
#include "ordered_capture.h"
#include "prepared_motion_capture.h"
#include "menu_renderer_gpu.h"
#include "gpu_frame_timer.h"
typedef struct {NFRenderHandoff*queue;NFHardwareSubmission*warm_menu;NFPresentationSubmission*warm_native;HANDLE stop,ready,inflight,release,wake;FILE*log;char**args;DWORD producer,consumer,window_owner;unsigned rendered,verified,motion_verified,stable_verified,ordered_verified,stale,cleared,cancelled;int result,test_cut,scheduled,interactive;uint64_t clock_origin,lag_ns;uint32_t source_base;volatile LONG pause_flags,quit;HWND window;WNDPROC previous_proc;} NFThreadedRun;
typedef struct {uint64_t wall,cpu,cycles;unsigned valid;} NFThreadCPU;
static NFThreadCPU threaded_cpu_mark(FILE*f){NFThreadCPU m={0};if(!f)return m;FILETIME created,exit,kernel,user;ULONG64 cycles=0;
 m.wall=elapsed_ns();if(GetThreadTimes(GetCurrentThread(),&created,&exit,&kernel,&user)&&QueryThreadCycleTime(GetCurrentThread(),&cycles)){ULARGE_INTEGER k,u;k.LowPart=kernel.dwLowDateTime;k.HighPart=kernel.dwHighDateTime;u.LowPart=user.dwLowDateTime;u.HighPart=user.dwHighDateTime;m.cpu=(k.QuadPart+u.QuadPart)*100;m.cycles=cycles;m.valid=1;}return m;}
static FILE*threaded_cpu_open(const char*prefix,const char*owner){if(!getenv("NF_TEST_THREAD_CPU_PROFILE"))return NULL;char path[1500];snprintf(path,sizeof(path),"%s-%s-cpu.csv",prefix,owner);FILE*f=fopen(path,"wb");if(f)fprintf(f,"kind,target,begin_ns,end_ns,cpu_begin_ns,cpu_end_ns,cycle_begin,cycle_end,valid\n");return f;}
static void threaded_cpu_record(FILE*f,const char*kind,double target,NFThreadCPU start){if(!f)return;NFThreadCPU end=threaded_cpu_mark(f);fprintf(f,"%s,%.12f,%llu,%llu,%llu,%llu,%llu,%llu,%u\n",kind,target,(unsigned long long)start.wall,(unsigned long long)end.wall,(unsigned long long)start.cpu,(unsigned long long)end.cpu,(unsigned long long)start.cycles,(unsigned long long)end.cycles,start.valid&&end.valid);}
static int threaded_complete_file(const char*base,const char*suffix,const void*data,size_t size){char path[1600];if(snprintf(path,sizeof(path),"%s-%s.bin",base,suffix)>=(int)sizeof(path))return 0;FILE*f=fopen(path,"wb");if(!f)return 0;int ok=fwrite(data,1,size,f)==size;return fclose(f)==0&&ok;}
static int threaded_complete_export(const char*prefix,const NFStableSceneSubmission*s,const NFOrderedSceneSubmission*o,const void*pixels,size_t pixel_size){char base[1500];if(snprintf(base,sizeof(base),"%s-complete-%s",prefix,s?"stable":"ordered")>=(int)sizeof(base))return 0;
 if(!threaded_complete_file(base,"rgb",pixels,pixel_size))return 0;
 const uint8_t*h=s?s->hud:o->hud,*t=s?s->text:o->text;size_t hn=s?s->hud_size:o->hud_size,tn=s?s->text_size:o->text_size;
 if(!threaded_complete_file(base,"hud",h,hn)||!threaded_complete_file(base,"text",t,tn))return 0;
 if(s)return threaded_complete_file(base,"bundle",s->bundle,s->bundle_size)&&threaded_complete_file(base,"proof",&s->proof,sizeof(s->proof));
 uint16_t palette[160][256];for(unsigned y=0;y<160;y++)memcpy(palette[y],h+y*sizeof(NFHudLayerRow)+32896,512);
 return threaded_complete_file(base,"older",o->older,o->older_size)&&threaded_complete_file(base,"newer",o->newer,o->newer_size)&&threaded_complete_file(base,"palette",palette,sizeof(palette))&&threaded_complete_file(base,"cut",&o->cut,sizeof(o->cut));
}
static unsigned threaded_test_input_index;
static int(*threaded_text_read)(uint64_t,unsigned,unsigned,void*,void*,unsigned);
static int threaded_capture_text(void*ctx,uint64_t epoch,uint32_t refresh,unsigned row,uint8_t indices[240],uint8_t coverage[240]){
 (void)ctx;return threaded_text_read&&threaded_text_read(epoch,refresh,row,indices,coverage,240);
}
static unsigned threaded_route_keys(unsigned step){return 1u|((step>=180&&step<500)?32u:((step>=500&&step<720)?16u:0u));}
static DWORD WINAPI threaded_fake_pad(DWORD slot,XINPUT_STATE*out){unsigned phase=threaded_test_input_index%8;memset(out,0,sizeof(*out));if(phase==3||phase==5||(phase==6?slot!=1:slot!=0))return ERROR_DEVICE_NOT_CONNECTED;if(phase==0||phase==6)out->Gamepad.wButtons=XINPUT_GAMEPAD_A;if(phase==1)out->Gamepad.bLeftTrigger=100;if(phase==2)out->Gamepad.sThumbLX=-18000;if(phase==7){out->Gamepad.sThumbLX=18000;out->Gamepad.bRightTrigger=41;}return ERROR_SUCCESS;}
static LRESULT CALLBACK threaded_window_proc(HWND window,UINT message,WPARAM wp,LPARAM lp){
 NFThreadedRun*r=(void*)GetWindowLongPtr(window,GWLP_USERDATA);if(!r)return DefWindowProc(window,message,wp,lp);
 LONG flags=InterlockedCompareExchange(&r->pause_flags,0,0),next=flags;
 if(message==WM_APP+41&&getenv("NF_TEST_THREADED_ACTUAL_WINDOW")){
  ShowWindow(window,wp?SW_SHOWNOACTIVATE:SW_SHOWMINNOACTIVE);
  printf("threaded_actual_iconic=%d resume=%d\n",IsIconic(window)!=0,wp!=0);
  return 0;
 }
 if(message==WM_APP+42&&getenv("NF_TEST_THREADED_ACTUAL_WINDOW")){
  RECT size={0,0,wp?1280:640,wp?720:480},client;
  AdjustWindowRectEx(&size,(DWORD)GetWindowLongPtr(window,GWL_STYLE),FALSE,(DWORD)GetWindowLongPtr(window,GWL_EXSTYLE));
  int ok=SetWindowPos(window,NULL,0,0,size.right-size.left,size.bottom-size.top,SWP_NOMOVE|SWP_NOZORDER|SWP_NOACTIVATE);
  if(!GetClientRect(window,&client))ok=0;
  printf("threaded_actual_resize_ok=%d width=%ld height=%ld resume=%d\n",ok,(long)client.right,(long)client.bottom,wp!=0);
  return 0;
 }
 if(message==WM_KEYDOWN&&wp==VK_SPACE&&!(lp&(1L<<30)))next^=1;
 if(message==WM_SIZE){if(wp==SIZE_MINIMIZED)next|=2;else next&=~2;}
 if(message==WM_ENTERSIZEMOVE)next|=4;if(message==WM_EXITSIZEMOVE)next&=~4;
 if(message==WM_ACTIVATEAPP){if(wp)next&=~8;else next|=8;}
 if(message==WM_CLOSE||(message==WM_KEYDOWN&&wp==VK_ESCAPE)){nf_render_handoff_invalidate(r->queue);InterlockedExchange(&r->quit,1);return 0;}
 if(next!=flags){if(next)nf_render_handoff_invalidate(r->queue);InterlockedExchange(&r->pause_flags,next);printf("threaded_window_flags=%ld event_ns=%llu\n",(long)next,(unsigned long long)elapsed_ns());}
 return CallWindowProc(r->previous_proc,window,message,wp,lp);
}
static void threaded_test_message(NFThreadedRun*r,unsigned stage,int resume){
 if(stage==0)SendMessage(r->window,WM_KEYDOWN,VK_SPACE,0);
 if(stage==1){if(getenv("NF_TEST_THREADED_ACTUAL_WINDOW"))SendMessage(r->window,WM_APP+41,resume,0);else SendMessage(r->window,WM_SIZE,resume?SIZE_RESTORED:SIZE_MINIMIZED,MAKELPARAM(1280,720));}
 if(stage==2){if(!resume)SendMessage(r->window,WM_ENTERSIZEMOVE,0,0);if(getenv("NF_TEST_THREADED_ACTUAL_WINDOW"))SendMessage(r->window,WM_APP+42,resume,0);if(resume)SendMessage(r->window,WM_EXITSIZEMOVE,0,0);}
 if(stage==3)SendMessage(r->window,WM_ACTIVATEAPP,resume?TRUE:FALSE,0);
}
static int threaded_present(void*unused){(void)unused;return preview_window_stage(1)&&preview_window_finish();}
static int threaded_clear(void*unused){(void)unused;return preview_window_stage(0)&&preview_window_finish();}
static int threaded_export_scene(const char*prefix,NFPresentationSubmission*s){
 const void*packet;size_t bytes;uint32_t sources[2];NFScenePacket view;
 if(!nf_submission_packet(s,&packet,&bytes)||!nf_submission_sources(s,sources)||!nf_scene_packet_view(packet,bytes,&view))return 0;
 char path[1400];snprintf(path,sizeof(path),"%s-native-scene.bin",prefix);FILE*f=fopen(path,"wb");if(!f)return 0;
 int ok=fwrite(packet,1,bytes,f)==bytes;if(fclose(f))ok=0;if(!ok)return 0;
 snprintf(path,sizeof(path),"%s-native-source.json",prefix);f=fopen(path,"wb");if(!f)return 0;
 const NFTimelineSample*t=nf_submission_time(s);
 ok=fprintf(f,"{\"target\":%.12f,\"alpha\":%.12f,\"epoch\":%llu,\"older_handle\":%llu,\"newer_handle\":%llu,\"source_refreshes\":[%u,%u],\"packet_begin\":%u,\"packet_end\":%u,\"packet_bytes\":%llu}\n",t->target,t->alpha,(unsigned long long)t->epoch,(unsigned long long)t->older,(unsigned long long)t->newer,sources[0],sources[1],view.begin_refresh,view.end_refresh,(unsigned long long)bytes)>0;
 if(fclose(f))ok=0;if(!ok)return 0;
 const NFRigidPose*endpoint_cameras=nf_submission_cameras(s),*command_cameras=NULL;unsigned command_count=0;nf_submission_command_cameras(s,&command_cameras,&command_count);
 snprintf(path,sizeof(path),"%s-owned-cameras.bin",prefix);f=fopen(path,"wb");if(!f)return 0;uint32_t camera_header[4]={0x5043464e,1,endpoint_cameras?2:0,command_count};
 ok=fwrite(camera_header,1,sizeof(camera_header),f)==sizeof(camera_header)&&fwrite(&t->alpha,1,sizeof(t->alpha),f)==sizeof(t->alpha);
 if(ok&&endpoint_cameras)ok=fwrite(endpoint_cameras,sizeof(*endpoint_cameras),2,f)==2;
 if(ok&&command_count)ok=fwrite(command_cameras,sizeof(*command_cameras),command_count,f)==command_count;
 if(fclose(f))ok=0;if(!ok)return 0;
 snprintf(path,sizeof(path),"%s-owned-hud.bin",prefix);f=fopen(path,"wb");if(!f)return 0;
 NFHudLayerRow row;for(unsigned y=0;y<160;y++){if(!nf_submission_row(s,t->epoch,(unsigned)floor(t->target),y,&row)||fwrite(&row,1,sizeof(row),f)!=sizeof(row)){ok=0;break;}}
 if(fclose(f))ok=0;if(!ok)return 0;
 uint8_t indices[240],coverage[240];
 if(nf_submission_text_row(s,t->epoch,(unsigned)floor(t->target),0,indices,coverage)){
  snprintf(path,sizeof(path),"%s-owned-text.bin",prefix);f=fopen(path,"wb");if(!f)return 0;
  for(unsigned y=0;y<160;y++)if(!nf_submission_text_row(s,t->epoch,(unsigned)floor(t->target),y,indices,coverage)||fwrite(indices,1,240,f)!=240||fwrite(coverage,1,240,f)!=240){ok=0;break;}
  if(fclose(f))ok=0;
 }
 return ok;
}
/* Compose two native GPU scene renders; original bitmap data never uploaded. */
static int threaded_render_split(NFPresentationSubmission*older,NFPresentationSubmission*newer,unsigned row,char**args){
 int previous_hud=hud_preview;hud_preview=0;int result=render_owned_submission(newer,args);GLuint texture=0;
 void(APIENTRY*active)(GLenum)=(void*)wglGetProcAddress("glActiveTexture");
 if(!result&&!active)result=19;
 if(!result){active(0x84c0);glGenTextures(1,&texture);glBindTexture(GL_TEXTURE_2D,texture);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glCopyTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,0,0,3840,2160,0);result=render_owned_submission(older,args);}
 if(!result){int top=(int)ceil(row*13.5-.5);active(0x84c0);glBindTexture(GL_TEXTURE_2D,texture);glCopyTexSubImage2D(GL_TEXTURE_2D,0,0,2160-top,0,2160-top,3840,top);
  glPushAttrib(GL_ALL_ATTRIB_BITS);obj_use(0);glDisable(GL_DEPTH_TEST);glDisable(GL_BLEND);glDisable(GL_SCISSOR_TEST);glDisable(GL_ALPHA_TEST);glEnable(GL_TEXTURE_2D);glTexEnvi(GL_TEXTURE_ENV,GL_TEXTURE_ENV_MODE,GL_REPLACE);glViewport(0,0,3840,2160);
  glMatrixMode(GL_PROJECTION);glPushMatrix();glLoadIdentity();glOrtho(0,3840,2160,0,-1,1);glMatrixMode(GL_MODELVIEW);glPushMatrix();glLoadIdentity();
  glBegin(GL_QUADS);glTexCoord2f(0,1);glVertex2i(0,0);glTexCoord2f(1,1);glVertex2i(3840,0);glTexCoord2f(1,0);glVertex2i(3840,2160);glTexCoord2f(0,0);glVertex2i(0,2160);glEnd();glMatrixMode(GL_MODELVIEW);glPopMatrix();glMatrixMode(GL_PROJECTION);glPopMatrix();glPopAttrib();if(glGetError()!=GL_NO_ERROR)result=19;
 }
 if(texture)glDeleteTextures(1,&texture);hud_preview=previous_hud;
 if(!result){NFPresentationSubmission*prior=owned_submission;owned_submission=newer;if(!endpoint_hud())result=19;owned_submission=prior;}
 return result;
}
static int threaded_verify_split(NFPresentationSubmission*older,NFPresentationSubmission*newer,unsigned row,char**args){
 size_t n=(size_t)3840*2160*3;uint8_t*mixed=malloc(n),*old=malloc(n),*next=malloc(n);int ok=mixed&&old&&next;
 if(ok){glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,mixed);ok=!render_owned_submission(older,args);}
 if(ok){glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,old);ok=!render_owned_submission(newer,args);}
 if(ok){glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,next);size_t top=(size_t)ceil(row*13.5-.5),bottom_bytes=(2160-top)*3840*3;ok=!memcmp(mixed,next,bottom_bytes)&&!memcmp(mixed+bottom_bytes,old+bottom_bytes,n-bottom_bytes)&&glGetError()==GL_NO_ERROR;}
 if(ok){char path[1500],prefix[1400];snprintf(prefix,sizeof(prefix),"%s-split-older",args[4]);ok=threaded_export_scene(prefix,older);snprintf(prefix,sizeof(prefix),"%s-split-newer",args[4]);if(ok)ok=threaded_export_scene(prefix,newer);snprintf(path,sizeof(path),"%s-split-native.ppm",args[4]);FILE*f=ok?fopen(path,"wb"):NULL;if(!f)ok=0;else{fprintf(f,"P6\n3840 2160\n255\n");for(int y=2159;y>=0;y--)if(fwrite(mixed+(size_t)y*3840*3,3,3840,f)!=3840)ok=0;if(fclose(f))ok=0;}}
 if(ok)ok=!threaded_render_split(older,newer,row,args);
 printf("selection_split_gpu_exact=%d row=%u pixels=%u\n",ok,row,3840*2160);free(mixed);free(old);free(next);return ok;
}
static int threaded_priority_apply(const char*owner){
 if(!getenv("NF_TEST_ABOVE_NORMAL_THREADS"))return 1;
 int before=GetThreadPriority(GetCurrentThread());if(before==THREAD_PRIORITY_ERROR_RETURN)return 0;
 if(!SetThreadPriority(GetCurrentThread(),THREAD_PRIORITY_ABOVE_NORMAL))return 0;
 int after=GetThreadPriority(GetCurrentThread());printf("%s_priority_before=%d %s_priority_after=%d\n",owner,before,owner,after);
 return after==THREAD_PRIORITY_ABOVE_NORMAL;
}
typedef struct {uint64_t now,origin,due,simulated,latest,next_display;unsigned steps,present,skipped;} NFClockPollTrace;
static DWORD WINAPI threaded_render(void*opaque){
 NFThreadedRun*r=opaque;r->consumer=GetCurrentThreadId();r->result=preview_context_open();
 if(!threaded_priority_apply("worker"))r->result=19;
 if(!r->result){r->window_owner=GetWindowThreadProcessId(preview_window,NULL);if(r->window_owner!=r->consumer||r->consumer==r->producer)r->result=19;}
 if(!r->result){r->window=preview_window;SetWindowLongPtr(preview_window,GWLP_USERDATA,(LONG_PTR)r);r->previous_proc=(WNDPROC)SetWindowLongPtr(preview_window,GWLP_WNDPROC,(LONG_PTR)threaded_window_proc);if(!r->previous_proc)r->result=19;}
 if(!r->result&&!endpoint_hud_warmup())r->result=19;
 if(r->warm_native){if(!r->result){r->result=render_owned_submission(r->warm_native,r->args);printf("native_warmup_renderer_result=%d\n",r->result);}glFinish();nf_submission_destroy(r->warm_native);r->warm_native=NULL;}
 if(r->warm_menu){if(!r->result&&!nf_menu_render_hardware(r->warm_menu,1))r->result=19;nf_hardware_submission_destroy(r->warm_menu);r->warm_menu=NULL;}
 if(!r->result&&r->interactive){SetWindowText(preview_window,"NFS Underground Prototype");ShowWindow(preview_window,SW_SHOW);}
 FILE*cpu_profile=threaded_cpu_open(r->args[4],"worker");if(getenv("NF_TEST_THREAD_CPU_PROFILE")&&!cpu_profile)r->result=19;
 SetEvent(r->ready);
 unsigned image_checks=getenv("NF_THREADED_NO_READBACK")?0:12;
 const char*capture_start=getenv("NF_THREADED_CAPTURE_REFRESH");double capture_refresh=capture_start?strtod(capture_start,NULL):0;
 if(capture_start&&(!isfinite(capture_refresh)||capture_refresh<0))r->result=19;
 /* Opt-in bounded immutable retention; disk export/readback occurs after the
    timed live loop. Clone cost remains visible in subsequent live deadlines. */
 NFPresentationSubmission*dense[60]={0};unsigned dense_count=0,dense_limit=0;
 const char*dense_env=getenv("NF_THREADED_DENSE_COUNT");
 if(dense_env){char*end;unsigned long count=strtoul(dense_env,&end,10);if(!*dense_env||*end||!count||count>60||!capture_start)r->result=19;else dense_limit=(unsigned)count;}
 FILE*dense_cost=NULL;if(dense_limit&&!r->result){char path[1400];snprintf(path,sizeof(path),"%s-dense-cost.csv",r->args[4]);dense_cost=fopen(path,"wb");if(!dense_cost)r->result=19;else fprintf(dense_cost,"epoch,target,begin_ns,end_ns,packet_bytes\n");}
 size_t n=(size_t)3840*2160*3;uint8_t*a=image_checks?malloc(n):NULL,*b=image_checks?malloc(n):NULL;if(image_checks&&(!a||!b))r->result=19;
 uint64_t front_epoch=0;
 char stage_path[1400];snprintf(stage_path,sizeof(stage_path),"%s-stages.csv",r->args[4]);FILE*stages=fopen(stage_path,"wb");if(!stages)r->result=19;
 if(stages)fprintf(stages,"epoch,target,begin_ns,renderer_begin_ns,setup_end_ns,scene_end_ns,hud_end_ns,finish_end_ns\n");
 char component_path[1400];snprintf(component_path,sizeof(component_path),"%s-components.csv",r->args[4]);FILE*components=fopen(component_path,"wb");if(!components)r->result=19;
 if(components)fprintf(components,"epoch,target,kind,begin_ns,end_ns,hud_wall_ms,hud_prepare_ms,hud_calls,finish_wall_ms,finish_calls,async_finish\n");
 NFGpuTimer gpu_timer;if(!nf_gpu_timer_open(&gpu_timer,r->args[4]))r->result=19;
 while(!r->result&&WaitForSingleObject(r->stop,0)!=WAIT_OBJECT_0){
  double hud_wall_before=owned_hud_total_ms,hud_prepare_before=hud_prepare_ms;unsigned hud_calls_before=owned_hud_calls;
  double finish_wall_before=preview_finish_wall_ms;unsigned finish_calls_before=preview_finish_calls;
  MSG msg;while(PeekMessage(&msg,NULL,0,0,PM_REMOVE)){TranslateMessage(&msg);DispatchMessage(&msg);}
  /* A minimized window can have no drawable client area. Retain the front
     epoch so restoration clears it before accepting another scene. */
  RECT drawable;
  if(IsIconic(r->window)||(GetClientRect(r->window,&drawable)&&
     (drawable.right<=0||drawable.bottom<=0))){Sleep(1);continue;}
  uint64_t current=nf_render_handoff_current_epoch(r->queue);if(front_epoch&&!current){int blank=nf_render_handoff_blank(r->queue,threaded_clear,NULL);if(blank<0){r->result=19;break;}if(blank){front_epoch=0;r->cleared++;printf("worker_pause_clear_ns=%llu\n",(unsigned long long)elapsed_ns());}}if(front_epoch&&current&&front_epoch!=current){int clear=nf_render_handoff_commit(r->queue,current,threaded_clear,NULL);if(clear<0){r->result=19;break;}if(clear){front_epoch=current;r->cleared++;printf("worker_epoch_clear=%llu\n",(unsigned long long)current);}}
  NFRenderSubmission*frame=nf_render_handoff_pop(r->queue);if(!frame){if(getenv("NF_THREADED_POLLING"))Sleep(1);else{HANDLE events[2]={r->stop,r->wake};if(MsgWaitForMultipleObjects(2,events,FALSE,20,QS_ALLINPUT)==WAIT_FAILED){r->result=19;break;}}continue;}
  const NFPreparedMotionSubmission*motion=nf_render_submission_prepared_motion_view(frame);const NFStableSceneSubmission*stable=nf_render_submission_stable_view(frame);const NFOrderedSceneSubmission*ordered=nf_render_submission_ordered_view(frame);NFPresentationSubmission*s=nf_render_submission_native_view(frame);NFHardwareSubmission*hardware=nf_render_submission_hardware_view(frame);NFPresentationSubmission*split_old=NULL,*split_new=NULL;unsigned split_row=0;int is_split=nf_render_submission_split_view(frame,&split_old,&split_new,&split_row);const NFTimelineSample*time=nf_render_submission_time(frame);NFSubmissionSchedule schedule={0};NFTimelineSample hardware_time;if(!time||(!s&&!hardware&&!is_split&&!ordered&&!stable&&!motion)){nf_render_submission_destroy(frame);r->result=19;break;}NFThreadCPU cpu_begin=threaded_cpu_mark(cpu_profile);uint64_t begin=elapsed_ns();int gpu_slot=nf_gpu_timer_begin(&gpu_timer,time->epoch,time->target,nf_render_submission_kind(frame));if(gpu_slot==-2){nf_render_submission_destroy(frame);r->result=19;break;}if(ordered||stable||motion){if(!nf_render_submission_ordered_schedule(frame,&schedule))r->result=19;else r->result=motion?render_prepared_motion_hud_diagnostic(motion,r->args):stable?render_stable_scene_submission(stable,r->args):render_ordered_scene_submission(ordered,r->args);uint64_t finish=elapsed_ns();renderer_marks[0]=begin;renderer_marks[1]=begin;renderer_marks[2]=finish;renderer_marks[3]=finish;renderer_marks[4]=finish;}else if(is_split){r->result=threaded_render_split(split_old,split_new,split_row,r->args);if(!r->result&&getenv("NF_THREADED_EXPORT_FRAME")&&!threaded_verify_split(split_old,split_new,split_row,r->args))r->result=19;if(!nf_submission_schedule_get(split_new,&schedule))r->result=19;}else if(s){r->result=render_owned_submission(s,r->args);if(!nf_submission_schedule_get(s,&schedule))r->result=19;}else{if(!nf_hardware_submission_metadata(hardware,&hardware_time,&schedule)||preview_context_open()||!nf_menu_render_hardware(hardware,1))r->result=19;uint64_t finish=elapsed_ns();renderer_marks[0]=begin;renderer_marks[1]=begin;renderer_marks[2]=finish;renderer_marks[3]=finish;renderer_marks[4]=finish;}
  if(!nf_gpu_timer_end(&gpu_timer,gpu_slot))r->result=19;
  if(!r->result)fprintf(components,"%llu,%.12f,%u,%llu,%llu,%.9f,%.9f,%u,%.9f,%u,%u\n",(unsigned long long)time->epoch,time->target,nf_render_submission_kind(frame),(unsigned long long)begin,(unsigned long long)elapsed_ns(),owned_hud_total_ms-hud_wall_before,hud_prepare_ms-hud_prepare_before,owned_hud_calls-hud_calls_before,preview_finish_wall_ms-finish_wall_before,preview_finish_calls-finish_calls_before,getenv("NF_TEST_ASYNC_RENDER_FINISH")!=NULL);
  if(!r->result)fprintf(stages,"%llu,%.12f,%llu,%llu,%llu,%llu,%llu,%llu\n",(unsigned long long)time->epoch,time->target,(unsigned long long)begin,(unsigned long long)renderer_marks[0],(unsigned long long)renderer_marks[1],(unsigned long long)renderer_marks[2],(unsigned long long)renderer_marks[3],(unsigned long long)renderer_marks[4]);
  if(motion&&!r->result&&image_checks&&r->motion_verified<6){
   glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,a);int binding=preview_force_context_rebind;preview_force_context_rebind=1;
   NFPreparedMotionSubmission reference=*motion;void*full_hud=NULL;int paired=getenv("NF_VERIFY_OWNED_HUD_POOL")!=NULL;
   if(paired){
    size_t bytes=160*sizeof(NFHudLayerRow);full_hud=malloc(bytes);if(!full_hud||!motion->hud_pool||!nf_prepared_motion_export_hud(motion,time->epoch,full_hud,bytes))r->result=19;
    if(!r->result){NFHudRowPool*bad=malloc(motion->hud_pool->bytes);if(!bad)r->result=19;else{
     size_t extent=motion->hud_pool->bytes;memcpy(bad,motion->hud_pool,extent);NFPreparedMotionSubmission forged=*motion;forged.hud_pool=bad;NFHudSubmissionView rejected={0};bad->epoch++;if(nf_prepared_motion_display_view(&forged,&rejected))r->result=19;
     memcpy(bad,motion->hud_pool,extent);bad->payload[0]^=1;if(nf_prepared_motion_display_view(&forged,&rejected))r->result=19;free(bad);
    }}
    if(!r->result){reference.hud_pool=NULL;reference.hud=full_hud;}
   }
   if(!r->result)r->result=render_prepared_motion_hud_diagnostic(paired?&reference:motion,r->args);
   preview_force_context_rebind=binding;glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,b);
   if(glGetError()!=GL_NO_ERROR||memcmp(a,b,n))r->result=19;else if(!r->result){r->verified++;r->motion_verified++;if(paired)printf("owned_hud_pool_pixels_exact=8294400 pool_epoch_negative=1 pool_payload_negative=1\n");}free(full_hud);
  }
  if((stable||ordered)&&!r->result&&image_checks&&time->target>=capture_refresh){
   unsigned limit=image_checks/2;unsigned *count=stable?&r->stable_verified:&r->ordered_verified;
   if(*count<limit){glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,a);int binding=preview_force_context_rebind;preview_force_context_rebind=1;
    r->result=stable?render_stable_scene_submission(stable,r->args):render_ordered_scene_submission(ordered,r->args);preview_force_context_rebind=binding;
    glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,b);if(glGetError()!=GL_NO_ERROR||memcmp(a,b,n))r->result=19;else{if(!*count&&getenv("NF_TEST_COMPLETE_EXPORT")&&!threaded_complete_export(r->args[4],stable,ordered,a,n))r->result=19;(*count)++;r->verified++;}}
  }
  if(s&&!r->result&&r->verified<image_checks&&time->target>=capture_refresh){glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,a);int prior_binding=preview_force_context_rebind;preview_force_context_rebind=1;r->result=render_owned_submission(s,r->args);preview_force_context_rebind=prior_binding;glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,b);if(glGetError()!=GL_NO_ERROR||memcmp(a,b,n))r->result=19;else{r->verified++;if((capture_start||r->verified==12)&&getenv("NF_THREADED_EXPORT_FRAME")){char export_prefix[1400];if(capture_start)snprintf(export_prefix,sizeof(export_prefix),"%s-capture-%02u",r->args[4],r->verified);else snprintf(export_prefix,sizeof(export_prefix),"%s",r->args[4]);if(!threaded_export_scene(export_prefix,s))r->result=19;char image_path[1500];snprintf(image_path,sizeof(image_path),"%s-native.ppm",export_prefix);FILE*image=fopen(image_path,"wb");if(!image)r->result=19;else{fprintf(image,"P6\n3840 2160\n255\n");for(int y=2159;y>=0;y--)if(fwrite(a+(size_t)y*3840*3,3,3840,image)!=3840)r->result=19;if(fclose(image))r->result=19;}}}}
  if(hardware&&!r->result&&r->rendered<6&&getenv("NF_TEST_THREADED_HARDWARE_EXPORT")){uint8_t*pixels=malloc(3840*2160*4);if(!pixels)r->result=19;else{glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,pixels);char path[1500];snprintf(path,sizeof(path),"%s-hardware-%02u.rgba",r->args[4],r->rendered);FILE*f=fopen(path,"wb");if(!f)r->result=19;else{for(int y=2159;y>=0;y--)if(fwrite(pixels+y*3840*4,4,3840,f)!=3840)r->result=19;if(fclose(f))r->result=19;}free(pixels);}}
  threaded_cpu_record(cpu_profile,"draw",time->target,cpu_begin);
  uint64_t draw_end=elapsed_ns(),deadline=0;
  if(r->scheduled){double index=(time->target-schedule.source_base+schedule.delay_refreshes)*(280896.0*60/16777216);if(!isfinite(index)||index<0||fabs(index-round(index))>1e-6)r->result=19;else{uint64_t slot=(uint64_t)llround(index);deadline=schedule.origin_ns+slot/60*1000000000ull+(slot%60*1000000000ull+59)/60+schedule.lag_ns;}}
  if(r->test_cut&&!r->stale&&(getenv("NF_TEST_SHARED_SOURCE_EPOCH")?(motion&&motion->shared_older&&r->rendered>=20):r->rendered==20)){printf("shared_epoch_inflight kind=%u epoch=%llu shared=%u\n",nf_render_submission_kind(frame),(unsigned long long)time->epoch,motion&&motion->shared_older?1:0);SetEvent(r->inflight);HANDLE events[2]={r->stop,r->release};if(WaitForMultipleObjects(2,events,FALSE,INFINITE)!=WAIT_OBJECT_0+1)r->result=19;}
  while(!r->result&&deadline&&WaitForSingleObject(r->stop,0)!=WAIT_OBJECT_0){uint64_t now=elapsed_ns();if(now>=deadline)break;uint64_t remaining=deadline-now;if(remaining>2000000)WaitForSingleObject(r->stop,1);else SwitchToThread();}
  uint64_t commit_begin=elapsed_ns();
  int committed=0;if(!r->result){if(WaitForSingleObject(r->stop,0)==WAIT_OBJECT_0){committed=-2;r->cancelled++;}else{committed=nf_render_handoff_commit(r->queue,time->epoch,threaded_present,NULL);if(committed<0)r->result=19;else if(!committed)r->stale++;}}
  fprintf(r->log,"%llu,%llu,%.12f,%llu,%llu,%d,%d,%llu,%llu,%llu,%u,%llu,%llu,%u\n",(unsigned long long)time->epoch,(unsigned long long)time->newer,time->target,(unsigned long long)begin,(unsigned long long)elapsed_ns(),r->result,committed,(unsigned long long)draw_end,(unsigned long long)deadline,(unsigned long long)schedule.origin_ns,schedule.source_base,(unsigned long long)schedule.lag_ns,(unsigned long long)commit_begin,nf_render_submission_kind(frame));
  if(!r->result&&committed==1){front_epoch=time->epoch;r->rendered++;
   if(s&&dense_count<dense_limit&&time->target>=capture_refresh){uint64_t clone_begin=elapsed_ns();dense[dense_count]=nf_submission_clone(s);uint64_t clone_end=elapsed_ns();if(!dense[dense_count])r->result=19;else{const void*packet;size_t bytes;if(!nf_submission_packet(dense[dense_count],&packet,&bytes))r->result=19;else fprintf(dense_cost,"%llu,%.12f,%llu,%llu,%llu\n",(unsigned long long)time->epoch,time->target,(unsigned long long)clone_begin,(unsigned long long)clone_end,(unsigned long long)bytes);dense_count++;}}
  }nf_render_submission_destroy(frame);
 }
 if(!nf_gpu_timer_close(&gpu_timer))r->result=19;
 if(dense_cost&&fclose(dense_cost))r->result=19;
 if(!r->result&&dense_limit&&dense_count!=dense_limit)r->result=19;
 if(!r->result&&dense_count){
  uint8_t*first=malloc(n),*second=malloc(n);if(!first||!second)r->result=19;
  for(unsigned i=0;!r->result&&i<dense_count;i++){
   r->result=render_owned_submission(dense[i],r->args);if(!r->result)glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,first);
   if(!r->result)r->result=render_owned_submission(dense[i],r->args);if(!r->result)glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,second);
   if(!r->result&&(glGetError()!=GL_NO_ERROR||memcmp(first,second,n)))r->result=19;
   if(!r->result){char prefix[1400],path[1500];snprintf(prefix,sizeof(prefix),"%s-dense-%02u",r->args[4],i+1);if(!threaded_export_scene(prefix,dense[i]))r->result=19;
    snprintf(path,sizeof(path),"%s-native.ppm",prefix);FILE*f=fopen(path,"wb");if(!f)r->result=19;else{fprintf(f,"P6\n3840 2160\n255\n");for(int y=2159;y>=0;y--)if(fwrite(first+(size_t)y*3840*3,3,3840,f)!=3840)r->result=19;if(fclose(f))r->result=19;}
   }
  }free(first);free(second);
 }
 if(cpu_profile&&fclose(cpu_profile))r->result=19;
 for(unsigned i=0;i<dense_count;i++)nf_submission_destroy(dense[i]);
 printf("dense_retained=%u dense_exported_after_live=%d\n",dense_count,dense_count&&!r->result);
 printf("hud_pool_draws=%u hud_pool_verified_rows=%u hud_pool_full_bytes=%llu hud_pool_stored_bytes=%llu\n",hud_pool_draws,hud_pool_verified_rows,(unsigned long long)hud_pool_full_bytes,(unsigned long long)hud_pool_stored_bytes);if(components)fclose(components);if(stages)fclose(stages);free(a);free(b);nf_menu_renderer_destroy();preview_shutdown();return r->result;
}
static const char*selection_trace_prefix;
static HMODULE selection_trace_bridge;
static uint64_t selection_latest_epoch;static uint32_t selection_latest_serial,selection_latest_begin,selection_latest_end;
static int(*threaded_page_generation)(uint64_t[2]);
static int(*threaded_display_generation)(uint64_t,unsigned,unsigned,uint64_t*);
static uint64_t(*threaded_observer_version)(void);static uint64_t threaded_owner_version;
static NFPagePersistenceProof threaded_page_owners[64];static unsigned threaded_page_owner_cursor;
static int threaded_motion_frame(HMODULE dll,NFSnapshotStore*store,uint64_t epoch,unsigned display,double target,const NFSubmissionSchedule*schedule,NFRenderSubmission**out){
 if(!threaded_observer_version||threaded_owner_version!=threaded_observer_version()||!threaded_display_generation)return 0;
 NFSnapshotPair pair={0};int ready=nf_snapshot_acquire(store,target,0,&pair),ok=0;NFScenePacket older,newer;
 if(ready==NF_TIME_READY&&nf_scene_packet_view(pair.older,pair.older_size,&older)&&nf_scene_packet_view(pair.newer,pair.newer_size,&newer)&&older.serial<newer.serial){
  for(unsigned i=0;i<64;i++){NFPagePersistenceProof proof=threaded_page_owners[i];uint64_t generation;
   if(proof.epoch!=epoch||proof.serial!=older.serial||proof.completion_refresh>display||!threaded_display_generation(epoch,display,proof.page,&generation)||generation!=proof.completion_generation)continue;
   proof.display_refresh=display;proof.display_generation=generation;NFPreparedMotionSubmission*motion=NULL;
   if(nf_prepared_motion_capture(dll,&pair.time,&proof,&motion)&&nf_render_submission_prepared_motion_live(&motion,&pair.time,schedule,out))ok=1;
   nf_prepared_motion_destroy(motion);break;
  }
 }
 nf_snapshot_release(store);return ok;
}
static int threaded_stable_frame(HMODULE dll,uint64_t epoch,unsigned display,double target,const NFSubmissionSchedule*schedule,NFRenderSubmission**out){
 if(!threaded_page_generation||!threaded_display_generation||!threaded_observer_version)return 0;if(threaded_owner_version!=threaded_observer_version()){memset(threaded_page_owners,0,sizeof(threaded_page_owners));threaded_owner_version=threaded_observer_version();return 0;}uint64_t generation;
 const NFPagePersistenceProof*best[2]={0};for(unsigned i=0;i<64;i++){const NFPagePersistenceProof*p=threaded_page_owners+i;if(p->epoch==epoch&&p->page<2&&p->completion_refresh<=display&&(!best[p->page]||p->completion_refresh>best[p->page]->completion_refresh))best[p->page]=p;}
 if(getenv("NF_TEST_ORDERED_CAPTURE")&&best[0]&&best[1]){const NFPagePersistenceProof*a=best[0],*b=best[1];if(a->completion_refresh>b->completion_refresh){const NFPagePersistenceProof*swap=a;a=b;b=swap;}unsigned cut=0;int(*split)(uint64_t,unsigned,unsigned,uint64_t,unsigned,uint64_t,unsigned*)=(void*)GetProcAddress(dll,"nf_layer_queue_split_generations");if(b->completion_refresh==display&&split&&split(epoch,display,a->page,a->completion_generation,b->page,b->completion_generation,&cut)){NFOrderedSceneSubmission*s=NULL;NFTimelineSample time={epoch,a->serial,b->serial,1,target};if(nf_ordered_capture(dll,epoch,a->serial,b->serial,display,cut,&s)&&nf_render_submission_ordered(&s,&time,schedule,out))return 1;nf_ordered_scene_submission_destroy(s);}}
 for(unsigned page=0;page<2;page++)if(best[page]&&threaded_display_generation(epoch,display,page,&generation)&&best[page]->completion_generation==generation){NFPagePersistenceProof proof=*best[page];proof.display_refresh=display;proof.display_generation=generation;NFStableSceneSubmission*s=NULL;NFTimelineSample time={epoch,proof.serial,proof.serial,0,target};if(nf_stable_capture(dll,&proof,&s)&&nf_render_submission_stable(&s,&time,schedule,out))return 1;nf_stable_scene_destroy(s);}return 0;
}
static int threaded_sink(void*ctx,uint64_t epoch,const void*data,size_t size){NFScenePacket latest;if(nf_scene_packet_view(data,size,&latest)){selection_latest_epoch=epoch;selection_latest_serial=latest.serial;selection_latest_begin=latest.begin_refresh;selection_latest_end=latest.end_refresh;if(threaded_page_generation&&latest.page<2){if(threaded_observer_version&&threaded_owner_version!=threaded_observer_version()){memset(threaded_page_owners,0,sizeof(threaded_page_owners));threaded_owner_version=threaded_observer_version();}uint64_t generation[2];if(threaded_page_generation(generation)){NFPagePersistenceProof proof={epoch,generation[latest.page],generation[latest.page],latest.serial,latest.end_refresh,latest.end_refresh,latest.page};threaded_page_owners[threaded_page_owner_cursor++%64]=proof;}}}if(selection_trace_prefix){NFScenePacket p;if(nf_scene_packet_view(data,size,&p)&&p.serial>=21&&p.serial<=23){if(p.serial==22){int(*view_read)(uint64_t,uint32_t,unsigned,uint32_t*)=(void*)GetProcAddress(selection_trace_bridge,"nf_live_completed_draw_view");for(unsigned i=0;i<nf_scene_packet_model_count(&p);i++){uint32_t view[12];NFSceneSection model;NFRigidPose camera;int exact=0;if(view_read&&view_read(epoch,p.serial,i,view)&&nf_scene_packet_model(&p,i,&model)){NFPoint3 position={-(double)(int32_t)view[9],-(double)(int32_t)view[10],-(double)(int32_t)view[11]};exact=nf_pose_decode((const int32_t*)view,&position,&camera)&&!memcmp(&camera,model.data+48,sizeof(camera));}printf("selection_owned_view serial=%u ordinal=%u camera_exact=%d\n",p.serial,i,exact);}}
char path[1500];snprintf(path,sizeof(path),"%s-source-%u.bin",selection_trace_prefix,p.serial);FILE*f=fopen(path,"wb");if(f){fwrite(data,1,size,f);fclose(f);}}}return nf_scene_packet_push(ctx,epoch,data,size);}
#ifndef NF_THREADED_NO_MAIN
int main(int argc,char**argv){
 if(argc!=6)return 1; /* bridge ROM state output-prefix duration-seconds */
 unsigned seconds=(unsigned)atoi(argv[5]);if(!seconds||seconds>3600)return 1;
 uint64_t presentation_lag=16666667;const char*lag_setting=getenv("NF_THREADED_LAG_NS");if(lag_setting){char*lag_end;unsigned long long lag=strtoull(lag_setting,&lag_end,10);if(!*lag_setting||*lag_end||lag>100000000ull)return 1;presentation_lag=lag;}
 double source_delay=8;const char*delay_setting=getenv("NF_TEST_SOURCE_DELAY_REFRESHES");if(delay_setting){char*end;double value=strtod(delay_setting,&end);if(!*delay_setting||*end||!isfinite(value)||value<8||value>32)return 1;source_delay=value;}
 QueryPerformanceFrequency(&timer_frequency);QueryPerformanceCounter(&timer_origin);
 if(!threaded_priority_apply("producer"))return 19;
 HMODULE dll=LoadLibraryA(argv[1]);if(!dll)return 2;
 int(*init)(const char*,const char*)=(void*)GetProcAddress(dll,"nf_init");int(*state)(const char*,int)=(void*)GetProcAddress(dll,"nf_state");void(*frame)(unsigned)=(void*)GetProcAddress(dll,"nf_frame");void(*close_game)(void)=(void*)GetProcAddress(dll,"nf_close");
 uint64_t(*epoch)(void)=(void*)GetProcAddress(dll,"nf_native_scene_epoch");uint32_t(*refresh)(void)=(void*)GetProcAddress(dll,"nf_native_scene_refresh");int(*sink)(PacedSink,void*)=(void*)GetProcAddress(dll,"nf_native_scene_sink");int(*models)(int)=(void*)GetProcAddress(dll,"nf_native_scene_multimodel");
 int(*enable)(const void*,size_t,size_t)=(void*)GetProcAddress(dll,"nf_live_visibility_enable");void(*audit)(int)=(void*)GetProcAddress(dll,"nf_live_surface_audit_enable");int(*layers)(unsigned)=(void*)GetProcAddress(dll,"nf_layer_queue_enable");
 int(*extract)(const NFVisibilityIdentity*,const NFVisibilityIdentity*,double,void**,size_t*,unsigned*)=(void*)GetProcAddress(dll,"nf_live_completed_native_multimodel_world_classified_pair_packet");void(*release)(void*)=(void*)GetProcAddress(dll,"nf_scene_packet_free");void(*dump)(const char*,unsigned,unsigned)=(void*)GetProcAddress(dll,"nf_dump");
 unsigned(*hardware_latest)(void)=(void*)GetProcAddress(dll,"nf_layer_queue_latest");int(*hardware_context)(uint64_t,unsigned,uint32_t[3])=(void*)GetProcAddress(dll,"nf_layer_queue_context");NFLayerSnapshot*(*hardware_clone)(uint64_t,unsigned)=(void*)GetProcAddress(dll,"nf_layer_queue_clone");void(*hardware_release)(NFLayerSnapshot*)=(void*)GetProcAddress(dll,"nf_layer_snapshot_destroy");void(*scene_cut)(void)=(void*)GetProcAddress(dll,"nf_native_scene_discontinuity");
 bridge_layer_read=(void*)GetProcAddress(dll,"nf_layer_queue_hud_row");layer_zero_read=(void*)GetProcAddress(dll,"nf_layer_queue_zero_colors");
 if(!init||!state||!frame||!close_game||!epoch||!refresh||!sink||!models||!enable||!audit||!layers||!extract||!release||!dump||!bridge_layer_read||!layer_zero_read||!hardware_latest||!hardware_context||!hardware_clone||!hardware_release||!scene_cut)return 3;
 if(getenv("NF_TEST_THREADED_CAR_SELECTION")){selection_trace_prefix=argv[4];selection_trace_bridge=dll;}
 NFSnapshotStore*store=nf_snapshot_create(32*1024*1024);if(!store||!init(argv[2],"")||!state(argv[3],0)||!sink(threaded_sink,store)||!models(1))return 4;
 FILE*rom=fopen(argv[2],"rb");if(!rom)return 5;fseek(rom,0,SEEK_END);long bytes=ftell(rom);rewind(rom);void*data=bytes>0?malloc(bytes):NULL;
 int enabled=data&&fread(data,1,bytes,rom)==(size_t)bytes&&enable(data,bytes,16*1024*1024);free(data);fclose(rom);if(!enabled||!layers(1))return 5;audit(1);
 if(getenv("NF_TEST_NATIVE_BITMAP_TEXT")){
  int(*text_enable)(int)=(void*)GetProcAddress(dll,"nf_bitmap_text_enable");
  threaded_text_read=(void*)GetProcAddress(dll,"nf_layer_queue_text_row");
  if(!text_enable||!threaded_text_read||!text_enable(1))return 5;
 }
 if(getenv("NF_TEST_STABLE_CAPTURE")){void(*observer)(unsigned)=(void*)GetProcAddress(dll,"nf_page_write_audit_enable");void(*reset)(void)=(void*)GetProcAddress(dll,"nf_page_write_audit_generation_reset");threaded_page_generation=(void*)GetProcAddress(dll,"nf_page_write_audit_generation_copy");threaded_display_generation=(void*)GetProcAddress(dll,"nf_layer_queue_page_generation");threaded_observer_version=(void*)GetProcAddress(dll,"nf_page_write_audit_version");if(!observer||!reset||!threaded_page_generation||!threaded_display_generation||!threaded_observer_version||!threaded_text_read)return 5;memset(threaded_page_owners,0,sizeof(threaded_page_owners));threaded_page_owner_cursor=0;reset();observer(1);threaded_owner_version=threaded_observer_version();}
 char path[1400];snprintf(path,sizeof(path),"%s-input.csv",argv[4]);FILE*inputs=fopen(path,"wb");snprintf(path,sizeof(path),"%s-worker.csv",argv[4]);FILE*log=fopen(path,"wb");if(!inputs||!log)return 6;
 snprintf(path,sizeof(path),"%s-producer.csv",argv[4]);FILE*producer_log=fopen(path,"wb");if(!producer_log)return 6;
 fprintf(producer_log,"epoch,target,begin_ns,extract_end_ns,copy_end_ns,push_begin_ns,push_end_ns,pushed\n");
 FILE*attempt_log=NULL;if(getenv("NF_TEST_PRESENT_ATTEMPT_PROFILE")){snprintf(path,sizeof(path),"%s-attempts.csv",argv[4]);attempt_log=fopen(path,"wb");if(!attempt_log)return 6;fprintf(attempt_log,"epoch,target,begin_ns,end_ns,context_found,acquisition,outcome\n");}
 snprintf(path,sizeof(path),"%s-context.csv",argv[4]);FILE*contexts=fopen(path,"wb");if(!contexts)return 6;fprintf(contexts,"epoch,target,refresh,mode,frontend,kind,found\n");
 FILE*cpu_profile=threaded_cpu_open(argv[4],"producer");if(getenv("NF_TEST_THREAD_CPU_PROFILE")&&!cpu_profile)return 6;
 int interactive=getenv("NF_THREADED_INTERACTIVE")!=NULL,input_enabled=interactive||getenv("NF_THREADED_CONTROLLER")!=NULL,test_input=getenv("NF_TEST_THREADED_INPUT")!=NULL;
 int route=getenv("NF_THREADED_STEERING_ROUTE")!=NULL,menu_start=getenv("NF_TEST_THREADED_MENU_START")!=NULL,neutral=getenv("NF_TEST_THREADED_NEUTRAL")!=NULL;
 if(route&&(input_enabled||test_input||menu_start||neutral)){fprintf(stderr,"Steering replay conflicts with physical or synthetic controller input.\n");return 1;}
 HMODULE input_module=NULL;NFGetPad getpad=NULL;if(input_enabled){input_module=LoadLibrary("xinput1_4.dll");if(!input_module)input_module=LoadLibrary("xinput9_1_0.dll");if(input_module)getpad=(void*)GetProcAddress(input_module,"XInputGetState");}
 unsigned input_polls=0,connected_polls=0;
 fprintf(inputs,"index,keys,before,after,start_ns,end_ns,focused,connected\n");fprintf(log,"epoch,newer,target,start_ns,end_ns,result,committed,draw_end_ns,deadline_ns,clock_origin,source_base,lag_ns,commit_begin_ns,frame_kind\n");unsigned steps=0;
 uint64_t warm_origin=elapsed_ns();for(unsigned i=0;i<40;i++){if(input_enabled){uint64_t due=warm_origin+(uint64_t)(i+1)*280896*1000000000ull/16777216;while(elapsed_ns()<due)Sleep(1);}unsigned keys=route?threaded_route_keys(steps):(input_enabled||menu_start||neutral?0:1),before=refresh();NFThreadCPU tick_cpu=threaded_cpu_mark(cpu_profile);uint64_t tick_start=elapsed_ns();frame(keys);threaded_cpu_record(cpu_profile,"original_tick",steps,tick_cpu);fprintf(inputs,"%u,%u,%u,%u,%llu,%llu,0,0\n",steps++,keys,before,refresh(),(unsigned long long)tick_start,(unsigned long long)elapsed_ns());}
 /* Immutable renderer configuration is established before thread publication. */
 /* A queued presentation renders once; packet alpha supplies the pose.
    The legacy default sweeps five diagnostic phases, not game passes. */
 _putenv("NF_PREVIEW_PHASE=0");
 preview_window_output=preview_keep_context=preview_measure_only=1;hud_preview=layer_sync=preview_zero_background=1;layer_read=submission_layer_read;
 NFThreadedRun run={0};run.producer=GetCurrentThreadId();run.args=argv;run.log=log;run.queue=nf_render_handoff_create(epoch());run.stop=CreateEvent(NULL,TRUE,FALSE,NULL);run.ready=CreateEvent(NULL,TRUE,FALSE,NULL);run.wake=CreateEvent(NULL,FALSE,FALSE,NULL);if(!run.queue||!run.stop||!run.ready||!run.wake)return 7;
 uint32_t warm_context[3];unsigned warm_refresh=hardware_latest();if(hardware_context(epoch(),warm_refresh,warm_context)&&warm_context[2]==2){NFLayerSnapshot*snapshot=hardware_clone(epoch(),warm_refresh);if(snapshot){NFTimelineSample time={0};time.epoch=epoch();time.target=warm_refresh;NFSubmissionSchedule schedule={0};nf_hardware_submission_create(snapshot,&time,&schedule,&run.warm_menu);hardware_release(snapshot);}}
 if(getenv("NF_TEST_NATIVE_WARMUP")){
  unsigned before=refresh();double target=before-source_delay;NFSnapshotPair pair={0};NFScenePacket a,b;int valid=0;
  if(nf_snapshot_acquire(store,target,0,&pair)==NF_TIME_READY&&nf_scene_packet_view(pair.older,pair.older_size,&a)&&nf_scene_packet_view(pair.newer,pair.newer_size,&b)){
   NFVisibilityIdentity left={pair.time.epoch,a.serial,a.begin_refresh,a.end_refresh,0,0},right={pair.time.epoch,b.serial,b.begin_refresh,b.end_refresh,0,0};NFSceneSection ma,mb;NFRigidPose cameras[2];uint16_t zero[160];void*packet=NULL;size_t bytes=0;unsigned stage=0;
   if(nf_scene_packet_model(&a,0,&ma)&&nf_scene_packet_model(&b,0,&mb)){
    memcpy(cameras,ma.data+48,sizeof(*cameras));memcpy(cameras+1,mb.data+48,sizeof(*cameras));
    NFRigidPose command_cameras[144];unsigned command_count=0;int sampled=getenv("NF_TEST_SAMPLED_DRAW_SCENE")||getenv("NF_TEST_TRANSITION_DRAW_SCENE");
    int(*sample_scene)(uint64_t,uint32_t,uint32_t,double,void**,size_t*,NFRigidPose*,unsigned,unsigned*)=(void*)GetProcAddress(dll,getenv("NF_TEST_TRANSITION_DRAW_SCENE")?"nf_live_completed_draw_scene_packet_transition":"nf_live_completed_draw_scene_packet_sample");
    valid=layer_zero_read(pair.time.epoch,(unsigned)floor(target),zero,sizeof(zero));
    if(valid)valid=sampled?(sample_scene&&sample_scene(pair.time.epoch,a.serial,b.serial,pair.time.alpha,&packet,&bytes,command_cameras,144,&command_count)):extract(&left,&right,pair.time.alpha,&packet,&bytes,&stage);
    if(valid)valid=nf_submission_take(&packet,bytes,&pair.time,a.end_refresh,b.end_refresh,command_count?NULL:cameras,zero,submission_capture_row,NULL,release,&run.warm_native);
    if(valid&&command_count)valid=nf_submission_command_cameras_set(run.warm_native,command_cameras,command_count);
    if(valid&&threaded_text_read)valid=nf_submission_text_capture(run.warm_native,threaded_capture_text,NULL);
   }if(packet)release(packet);
  }nf_snapshot_release(store);
  if(!valid||refresh()!=before){nf_submission_destroy(run.warm_native);run.warm_native=NULL;fprintf(stderr,"Native warmup source unavailable or refresh changed.\n");return 19;}
  printf("native_warmup_target=%.12f original_refresh_before=%u original_refresh_after=%u\n",target,before,refresh());
 }
 run.interactive=interactive;
 run.test_cut=getenv("NF_TEST_THREADED_EPOCH")!=NULL;run.inflight=CreateEvent(NULL,TRUE,FALSE,NULL);run.release=CreateEvent(NULL,TRUE,FALSE,NULL);if(!run.inflight||!run.release)return 7;
 HANDLE worker=CreateThread(NULL,0,threaded_render,&run,0,NULL);if(!worker)return 7;HANDLE starts[2]={run.ready,worker};if(WaitForMultipleObjects(2,starts,FALSE,INFINITE)!=WAIT_OBJECT_0)return 7;
 /* Immutable schedule published by the first queue push (queue lock release).
    Worker reads these fields only after acquiring a submitted frame. */
 if(getenv("NF_TEST_CAPTURE_EVENT_PROFILE")){void(*profile_enable)(unsigned)=(void*)GetProcAddress(dll,"nf_capture_profile_enable");if(!profile_enable)return 19;profile_enable(1);}
 NFFrameClock clock;uint64_t start=elapsed_ns();run.clock_origin=start;run.source_base=refresh();run.lag_ns=presentation_lag;run.scheduled=getenv("NF_THREADED_ARRIVAL")==NULL;nf_frame_clock_start(&clock,start,run.source_base,source_delay);unsigned submitted=0,full=0,unavailable=0,cuts=0,hardware_submitted=0,native_submitted=0,last_kind=0,kind_blocked=0,kind_cuts=0;uint64_t last_kind_epoch=epoch();uint64_t skipped=0,cut_time=0,cut_epoch=0,inflight_since=0;unsigned pauses=0;int result=0;
 int backlog_profile=getenv("NF_TEST_CLOCK_BACKLOG_PROFILE")!=NULL;
 int poll_trace=getenv("NF_TEST_CLOCK_POLL_TRACE")!=NULL;unsigned poll_count=0;NFClockPollTrace*poll_records=poll_trace?malloc(16384*sizeof(*poll_records)):NULL;
 uint64_t backlog_polls=0,backlog_suppressed=0,backlog_max=0,backlog_span_begin=0,backlog_longest_ns=0;
 while(elapsed_ns()-start<(uint64_t)seconds*1000000000ull&&WaitForSingleObject(worker,0)!=WAIT_OBJECT_0){
  if(InterlockedCompareExchange(&run.quit,0,0))break;
  static unsigned test_stage;static int test_active,window_paused;static uint64_t frozen_start;static unsigned frozen_refresh,frozen_steps;static LONG frozen_flags;
  int test_window=getenv("NF_TEST_THREADED_WINDOW")!=NULL;
  if(test_window&&test_stage==4&&steps>=420&&getenv("NF_TEST_THREADED_CLOSE")){SendMessage(run.window,WM_CLOSE,0,0);continue;}
  if(test_window&&!test_active&&test_stage<4&&steps>=100+test_stage*80){threaded_test_message(&run,test_stage,0);test_active=1;}
  LONG flags=InterlockedCompareExchange(&run.pause_flags,0,0);
  if(flags){if(!window_paused){nf_render_handoff_invalidate(run.queue);window_paused=1;frozen_start=elapsed_ns();frozen_refresh=refresh();frozen_steps=steps;frozen_flags=flags;}
   if(refresh()!=frozen_refresh||steps!=frozen_steps){result=19;break;}
   if(test_window&&test_active&&elapsed_ns()-frozen_start>=200000000ull){threaded_test_message(&run,test_stage,1);test_active=0;test_stage++;}
   Sleep(1);continue;
  }
  if(window_paused){void(*cut)(void)=(void*)GetProcAddress(dll,"nf_native_scene_discontinuity");if(!cut){result=19;break;}uint64_t old=epoch();cut();if(epoch()<=old||!nf_render_handoff_epoch(run.queue,epoch())){result=19;break;}run.clock_origin=elapsed_ns();run.source_base=refresh();if(!nf_frame_clock_start(&clock,run.clock_origin,run.source_base,source_delay)){result=19;break;}printf("threaded_window_resume=%ld before=%u after=%u steps=%u start_ns=%llu end_ns=%llu\n",(long)frozen_flags,frozen_refresh,refresh(),steps,(unsigned long long)frozen_start,(unsigned long long)elapsed_ns());pauses++;window_paused=0;continue;}
  if(poll_trace&&(!poll_records||poll_count==16384)){result=19;break;}
  NFFramePlan plan;uint64_t poll_now=elapsed_ns(),poll_elapsed=poll_now-clock.origin;
  uint64_t poll_due=((poll_elapsed/1000000000ull)*16777216+(poll_elapsed%1000000000ull)*16777216/1000000000ull)/280896;
  uint64_t poll_latest=(poll_elapsed/1000000000ull)*60+(poll_elapsed%1000000000ull)*60/1000000000ull,poll_next_display=clock.next_display;
  if(!nf_frame_clock_poll(&clock,poll_now,&plan)){result=18;break;}
  if(poll_trace)poll_records[poll_count++]=(NFClockPollTrace){poll_now,clock.origin,poll_due,clock.simulated,poll_latest,poll_next_display,plan.simulation_steps,plan.present,plan.skipped_displays};
  if(backlog_profile){uint64_t debt=poll_due-clock.simulated;backlog_polls++;if(debt>backlog_max)backlog_max=debt;
   if(debt&&poll_latest>=poll_next_display){backlog_suppressed++;if(!backlog_span_begin)backlog_span_begin=poll_now;uint64_t span=poll_now-backlog_span_begin;if(span>backlog_longest_ns)backlog_longest_ns=span;}
   else backlog_span_begin=0;
  }
  for(unsigned i=0;i<plan.simulation_steps;i++){unsigned keys=route?threaded_route_keys(steps):((menu_start||neutral)?(menu_start&&steps>=90&&steps<92?8:0):1);if(getenv("NF_TEST_THREADED_CAR_SELECTION")&&!route){keys=((steps>=90&&steps<92)||(steps>=180&&steps<182))?16:(steps>=270&&steps<272)?32:0;}int focused=0,connected=0;if(input_enabled){focused=GetForegroundWindow()==run.window&&!InterlockedCompareExchange(&run.pause_flags,0,0);keys=nf_input_sample(focused,nf_input_keyboard(),getpad,&connected);input_polls++;connected_polls+=connected;}else if(test_input){threaded_test_input_index=steps-40;unsigned phase=threaded_test_input_index%8;focused=phase!=4;keys=nf_input_sample(focused,phase==5?32:0,threaded_fake_pad,&connected);input_polls++;connected_polls+=connected;}unsigned before=refresh();NFThreadCPU tick_cpu=threaded_cpu_mark(cpu_profile);uint64_t tick_start=elapsed_ns();frame(keys);threaded_cpu_record(cpu_profile,"original_tick",steps,tick_cpu);fprintf(inputs,"%u,%u,%u,%u,%llu,%llu,%d,%d\n",steps++,keys,before,refresh(),(unsigned long long)tick_start,(unsigned long long)elapsed_ns(),focused,connected);}
  if(getenv("NF_TEST_EXACT_SCENE_PREFILL")){
   static uint64_t prepared_epoch;static uint32_t prepared_serial;
   if(selection_latest_epoch==epoch()&&(prepared_epoch!=epoch()||prepared_serial!=selection_latest_serial)){
    int(*owned_scene)(uint64_t,uint32_t,void**,size_t*,NFRigidPose*,unsigned,unsigned*)=(void*)GetProcAddress(dll,"nf_live_completed_draw_scene_packet");void*packet=NULL;size_t bytes=0;NFRigidPose cameras[144];unsigned count=0,before=refresh();NFThreadCPU prefill_cpu=threaded_cpu_mark(cpu_profile);
    int ok=owned_scene&&owned_scene(epoch(),selection_latest_serial,&packet,&bytes,cameras,144,&count);if(packet)release(packet);threaded_cpu_record(cpu_profile,"scene_prefill",selection_latest_serial,prefill_cpu);
    if(refresh()!=before){result=19;break;}prepared_epoch=epoch();prepared_serial=selection_latest_serial;printf("exact_scene_prefill serial=%u refresh=%u success=%d\n",prepared_serial,before,ok);
   }
  }
  if(getenv("NF_TEST_THREADED_PAUSE")&&!pauses&&steps>=180){
   unsigned before=refresh(),before_steps=steps;uint64_t pause_begin=elapsed_ns();nf_render_handoff_invalidate(run.queue);Sleep(200);
   if(refresh()!=before||steps!=before_steps){result=19;break;}
   void(*cut)(void)=(void*)GetProcAddress(dll,"nf_native_scene_discontinuity");if(!cut){result=19;break;}uint64_t old=epoch();cut();if(epoch()<=old||!nf_render_handoff_epoch(run.queue,epoch())){result=19;break;}
   run.clock_origin=elapsed_ns();run.source_base=refresh();if(!nf_frame_clock_start(&clock,run.clock_origin,run.source_base,source_delay)){result=19;break;}
   printf("pause_before=%u pause_after=%u pause_steps=%u pause_start_ns=%llu pause_end_ns=%llu\n",before,refresh(),steps,(unsigned long long)pause_begin,(unsigned long long)elapsed_ns());pauses++;continue;
  }
  if(run.test_cut&&!cuts&&WaitForSingleObject(run.inflight,0)==WAIT_OBJECT_0){if(!inflight_since)inflight_since=elapsed_ns();if(elapsed_ns()-inflight_since>=100000000ull){void(*cut)(void)=(void*)GetProcAddress(dll,"nf_native_scene_discontinuity");if(!cut){result=19;break;}uint64_t old=epoch();nf_render_handoff_invalidate(run.queue);cut();cut_epoch=epoch();if(cut_epoch<=old||!nf_render_handoff_epoch(run.queue,cut_epoch)){result=19;break;}cut_time=elapsed_ns();cuts++;SetEvent(run.release);}}
  if(plan.present){int attempt_outcome=0;NFThreadCPU source_cpu=threaded_cpu_mark(cpu_profile);uint64_t capture_begin=elapsed_ns(),extract_end=0,copy_end=0;skipped+=plan.skipped_displays;NFSnapshotPair pair;NFScenePacket a,b;NFPresentationSubmission*submission=NULL;NFRenderSubmission*owned_frame=NULL;uint64_t source_epoch=epoch();if(!kind_blocked&&source_epoch!=nf_render_handoff_current_epoch(run.queue))nf_render_handoff_epoch(run.queue,source_epoch);uint32_t context[3]={0};unsigned discrete=(unsigned)floor(plan.source_target);int context_found=hardware_context(source_epoch,discrete,context);fprintf(contexts,"%llu,%.12f,%u,%u,%u,%u,%d\n",(unsigned long long)source_epoch,plan.source_target,discrete,context[0],context[1],context[2],context_found);
   if(context_found&&(!context[2]||(last_kind&&last_kind!=context[2]&&source_epoch==last_kind_epoch))&&!kind_blocked){nf_render_handoff_invalidate(run.queue);scene_cut();last_kind_epoch=epoch();last_kind=context[2];kind_blocked=1;kind_cuts++;cuts++;printf("threaded_scene_kind_cut=%u mode=%u frontend=%u target=%.12f old_epoch=%llu new_epoch=%llu event_ns=%llu\n",context[2],context[0],context[1],plan.source_target,(unsigned long long)source_epoch,(unsigned long long)last_kind_epoch,(unsigned long long)elapsed_ns());unavailable++;continue;}
   if(context_found&&context[2]){last_kind=context[2];last_kind_epoch=source_epoch;if(kind_blocked){if(!nf_render_handoff_epoch(run.queue,source_epoch)){result=19;break;}kind_blocked=0;}}
   if(context_found&&context[2]==2){NFLayerSnapshot*snapshot=hardware_clone(source_epoch,discrete);extract_end=elapsed_ns();NFTimelineSample time={0};time.epoch=source_epoch;time.target=plan.source_target;time.alpha=plan.source_target-floor(plan.source_target);NFSubmissionSchedule schedule={clock.origin,run.lag_ns,clock.base,source_delay};NFHardwareSubmission*hardware=NULL;if(snapshot){nf_hardware_submission_create(snapshot,&time,&schedule,&hardware);hardware_release(snapshot);}if(hardware&&!nf_render_submission_hardware(&hardware,&owned_frame)){nf_hardware_submission_destroy(hardware);result=19;break;}if(submission&&threaded_text_read&&!nf_submission_text_capture(submission,threaded_capture_text,NULL)){nf_submission_destroy(submission);submission=NULL;}copy_end=elapsed_ns();}

   if(context_found&&context[2]==1&&getenv("NF_TEST_PREPARED_MOTION_CAPTURE")){NFSubmissionSchedule timing={clock.origin,run.lag_ns,clock.base,source_delay};if(threaded_motion_frame(dll,store,source_epoch,discrete,plan.source_target,&timing,&owned_frame))printf("prepared_motion_capture target=%.12f display=%u\n",plan.source_target,discrete);extract_end=copy_end=elapsed_ns();}
   if(context_found&&context[2]==1&&!owned_frame&&getenv("NF_TEST_STABLE_CAPTURE")){NFSubmissionSchedule timing={clock.origin,run.lag_ns,clock.base,source_delay};if(threaded_stable_frame(dll,source_epoch,discrete,plan.source_target,&timing,&owned_frame))printf("stable_complete_capture target=%.12f display=%u\n",plan.source_target,discrete);extract_end=copy_end=elapsed_ns();}
   int acquisition=(context_found&&context[2]==1&&!owned_frame&&!getenv("NF_TEST_COMPLETE_STABLE_ONLY"))?nf_snapshot_acquire(store,plan.source_target,0,&pair):NF_TIME_EMPTY;
   if(context_found&&context[2]==1&&!owned_frame&&acquisition!=NF_TIME_READY&&getenv("NF_TEST_THREADED_CAR_SELECTION"))printf("selection_source_unavailable target=%.12f status=%d current_refresh=%u latest_epoch=%llu latest_serial=%u latest_begin=%u latest_end=%u\n",plan.source_target,acquisition,refresh(),(unsigned long long)selection_latest_epoch,selection_latest_serial,selection_latest_begin,selection_latest_end);
   int held_page=0;
   if(context_found&&context[2]==1&&acquisition==NF_TIME_AFTER&&getenv("NF_TEST_OWNED_ROOT_ENDPOINT")&&nf_scene_packet_view(pair.older,pair.older_size,&a)){
    int(*page_equal)(uint64_t,unsigned,unsigned,unsigned)=(void*)GetProcAddress(dll,"nf_layer_queue_selection_scene_hold");
    held_page=page_equal&&page_equal(pair.time.epoch,a.end_refresh,a.page,(unsigned)floor(pair.time.target));
   }
   if(context_found&&context[2]==1&&(acquisition==NF_TIME_READY||held_page)&&nf_scene_packet_view(pair.older,pair.older_size,&a)&&nf_scene_packet_view(pair.newer,pair.newer_size,&b)){
    NFVisibilityIdentity left={pair.time.epoch,a.serial,a.begin_refresh,a.end_refresh,0,0},right={pair.time.epoch,b.serial,b.begin_refresh,b.end_refresh,0,0};NFSceneSection ma,mb;NFRigidPose cameras[2],command_cameras[144];unsigned command_camera_count=0;uint16_t zero[160];void*packet=NULL;size_t size=0;unsigned stage=0;
    if(nf_scene_packet_model(&a,0,&ma)&&nf_scene_packet_model(&b,0,&mb)){memcpy(cameras,ma.data+48,sizeof(*cameras));memcpy(cameras+1,mb.data+48,sizeof(*cameras));
     int layer_ok=layer_zero_read(pair.time.epoch,(unsigned)floor(pair.time.target),zero,sizeof(zero));int packet_ok=0;int sampled_requested=getenv("NF_TEST_SAMPLED_DRAW_SCENE")!=NULL||getenv("NF_TEST_TRANSITION_DRAW_SCENE")!=NULL;
     if(layer_ok&&!held_page&&sampled_requested){int(*sample_scene)(uint64_t,uint32_t,uint32_t,double,void**,size_t*,NFRigidPose*,unsigned,unsigned*)=(void*)GetProcAddress(dll,getenv("NF_TEST_TRANSITION_DRAW_SCENE")?"nf_live_completed_draw_scene_packet_transition":"nf_live_completed_draw_scene_packet_sample");packet_ok=sample_scene&&sample_scene(pair.time.epoch,a.serial,b.serial,pair.time.alpha,&packet,&size,command_cameras,144,&command_camera_count);printf("selection_sampled_root target=%.12f older=%u newer=%u alpha=%.12f accepted=%d commands=%u\n",pair.time.target,a.serial,b.serial,pair.time.alpha,packet_ok,command_camera_count);if(!packet_ok){uint32_t reason[8]={0};void(*detail)(uint32_t*)=(void*)GetProcAddress(dll,"nf_live_completed_draw_sample_detail");if(detail)detail(reason);printf("selection_sampled_reject target=%.12f stage=%u pass=%u command=%u kind=%u source=%u reason=%u\n",pair.time.target,reason[2],reason[3],reason[4],reason[5],reason[6],reason[7]);}}
     if(!packet_ok&&!sampled_requested)packet_ok=layer_ok&&!held_page&&extract(&left,&right,pair.time.alpha,&packet,&size,&stage);if(!packet_ok&&layer_ok&&getenv("NF_TEST_OWNED_ROOT_ENDPOINT")){
      int(*owned_scene)(uint64_t,uint32_t,void**,size_t*,NFRigidPose*,unsigned,unsigned*)=(void*)GetProcAddress(dll,"nf_live_completed_draw_scene_packet");
      if(owned_scene&&owned_scene(pair.time.epoch,a.serial,&packet,&size,command_cameras,144,&command_camera_count)){packet_ok=1;printf("selection_exact_root target=%.12f serial=%u commands=%u alpha=%.12f diagnostic_endpoint=1 held_page=%d\n",pair.time.target,a.serial,command_camera_count,pair.time.alpha,held_page);}
     }if(!packet_ok&&getenv("NF_TEST_THREADED_CAR_SELECTION")){uint32_t missing[6]={0};void(*detail)(uint32_t*)=(void*)GetProcAddress(dll,"nf_live_paired_model_inputs_missing");if(detail)detail(missing);if(stage==17){uint32_t publication[6]={0};int(*pub)(uint32_t,uint32_t*)=(void*)GetProcAddress(dll,"nf_live_model_publish_detail");for(unsigned k=0;k<2;k++){unsigned serial=k?b.serial:a.serial;if(pub&&pub(serial,publication)&&publication[4]==2){uint32_t duplicate[8];int(*dup)(uint32_t,uint32_t*)=(void*)GetProcAddress(dll,"nf_live_model_duplicate_detail");if(dup&&dup(serial,duplicate))printf("selection_duplicate serial=%u first=%u second=%u size_equal=%u packet_equal=%u rotation_equal=%u palette_equal=%u object=%u\n",duplicate[0],duplicate[1],duplicate[2],duplicate[3],duplicate[4],duplicate[5],duplicate[6],duplicate[7]);}if(pub&&pub(serial,publication))printf("selection_model_publication serial=%u count=%u captured=%u failed=%u reason=%u index=%u\n",publication[0],publication[1],publication[2],publication[3],publication[4],publication[5]);}}printf("selection_native_failure target=%.12f older=%u newer=%u layer=%d stage=%u missing=%u,%u,%u,%u,%u,%u\n",pair.time.target,a.serial,b.serial,layer_ok,stage,missing[0],missing[1],missing[2],missing[3],missing[4],missing[5]);}if(packet_ok){extract_end=elapsed_ns();nf_submission_take(&packet,size,&pair.time,a.end_refresh,b.end_refresh,command_camera_count?NULL:cameras,zero,submission_capture_row,NULL,release,&submission);if(submission&&command_camera_count&&!nf_submission_command_cameras_set(submission,command_cameras,command_camera_count)){nf_submission_destroy(submission);submission=NULL;}if(submission&&threaded_text_read&&!nf_submission_text_capture(submission,threaded_capture_text,NULL)){nf_submission_destroy(submission);submission=NULL;}copy_end=elapsed_ns();}
    }if(packet)release(packet);
   }nf_snapshot_release(store);
   if(!submission&&!owned_frame&&context_found&&context[2]==1&&acquisition==NF_TIME_AFTER&&!held_page&&getenv("NF_TEST_OWNED_ROOT_ENDPOINT")&&nf_scene_packet_view(pair.older,pair.older_size,&a)&&(unsigned)floor(plan.source_target)==a.end_refresh){
    NFSnapshotPair boundary={0};int status=nf_snapshot_acquire(store,a.end_refresh-.25,0,&boundary);NFScenePacket old_view,new_view;unsigned split_row=0;
    int(*split_guard)(uint64_t,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned*)=(void*)GetProcAddress(dll,"nf_layer_queue_selection_split");
    if(status==NF_TIME_READY&&nf_scene_packet_view(boundary.older,boundary.older_size,&old_view)&&nf_scene_packet_view(boundary.newer,boundary.newer_size,&new_view)&&split_guard&&split_guard(source_epoch,old_view.end_refresh,old_view.page,new_view.end_refresh,new_view.page,discrete,&split_row)){
     int(*owned_scene)(uint64_t,uint32_t,void**,size_t*,NFRigidPose*,unsigned,unsigned*)=(void*)GetProcAddress(dll,"nf_live_completed_draw_scene_packet");NFPresentationSubmission*parts[2]={0};uint16_t zero[160];NFSubmissionSchedule schedule={clock.origin,run.lag_ns,clock.base,source_delay};
     int valid=owned_scene&&layer_zero_read(source_epoch,discrete,zero,sizeof(zero));
     for(unsigned k=0;valid&&k<2;k++){NFScenePacket*v=k?&new_view:&old_view;void*packet=NULL;size_t bytes=0;NFRigidPose cameras[144];unsigned count=0;NFTimelineSample time={source_epoch,v->serial,v->serial,0,plan.source_target};
      NFThreadCPU extract_cpu=threaded_cpu_mark(cpu_profile);valid=owned_scene(source_epoch,v->serial,&packet,&bytes,cameras,144,&count);threaded_cpu_record(cpu_profile,k?"split_new_extract":"split_old_extract",plan.source_target,extract_cpu);
      NFThreadCPU copy_cpu=threaded_cpu_mark(cpu_profile);if(valid)valid=nf_submission_take(&packet,bytes,&time,v->end_refresh,v->end_refresh,NULL,zero,submission_capture_row,NULL,release,parts+k);
      if(packet)release(packet);if(valid)valid=nf_submission_command_cameras_set(parts[k],cameras,count)&&nf_submission_schedule_set(parts[k],&schedule)&&(!threaded_text_read||nf_submission_text_capture(parts[k],threaded_capture_text,NULL));threaded_cpu_record(cpu_profile,k?"split_new_copy":"split_old_copy",plan.source_target,copy_cpu);
     }
     if(valid&&getenv("NF_TEST_ORDERED_CAPTURE")&&plan.source_target==(double)discrete){NFOrderedSceneSubmission*complete=NULL;NFTimelineSample exact={source_epoch,old_view.serial,new_view.serial,1.0,plan.source_target};if(nf_ordered_capture(dll,source_epoch,old_view.serial,new_view.serial,discrete,split_row,&complete)&&nf_render_submission_ordered(&complete,&exact,&schedule,&owned_frame))printf("selection_ordered_capture target=%.12f older=%u newer=%u row=%u\n",plan.source_target,old_view.serial,new_view.serial,split_row);nf_ordered_scene_submission_destroy(complete);}
     if(valid&&!owned_frame&&nf_render_submission_split(parts,parts+1,split_row,&owned_frame))printf("selection_native_split target=%.12f older=%u newer=%u row=%u\n",plan.source_target,old_view.serial,new_view.serial,split_row);
     nf_submission_destroy(parts[0]);nf_submission_destroy(parts[1]);extract_end=copy_end=elapsed_ns();
    }nf_snapshot_release(store);
   }
   if(submission&&!owned_frame){NFSubmissionSchedule schedule={clock.origin,run.lag_ns,clock.base,source_delay};if(!nf_submission_schedule_set(submission,&schedule)){nf_submission_destroy(submission);result=19;break;}if(!nf_render_submission_native(&submission,&owned_frame)){nf_submission_destroy(submission);result=19;break;}}if(owned_frame){uint64_t frame_epoch=nf_render_submission_time(owned_frame)->epoch;unsigned frame_kind=nf_render_submission_kind(owned_frame);nf_render_handoff_epoch(run.queue,frame_epoch);uint64_t push_begin=elapsed_ns();int pushed=nf_render_handoff_push(run.queue,&owned_frame);uint64_t push_end=elapsed_ns();attempt_outcome=pushed?2:1;if(pushed){submitted++;if(frame_kind==NF_RENDER_HARDWARE)hardware_submitted++;else native_submitted++;SetEvent(run.wake);}else full++;fprintf(producer_log,"%llu,%.12f,%llu,%llu,%llu,%llu,%llu,%d\n",(unsigned long long)frame_epoch,plan.source_target,(unsigned long long)capture_begin,(unsigned long long)extract_end,(unsigned long long)copy_end,(unsigned long long)push_begin,(unsigned long long)push_end,pushed);nf_render_submission_destroy(owned_frame);}else unavailable++;if(attempt_log)fprintf(attempt_log,"%llu,%.12f,%llu,%llu,%d,%d,%d\n",(unsigned long long)source_epoch,plan.source_target,(unsigned long long)capture_begin,(unsigned long long)elapsed_ns(),context_found,acquisition,attempt_outcome);threaded_cpu_record(cpu_profile,"submission",plan.source_target,source_cpu);
  }else Sleep(1);
 }
 SetEvent(run.stop);SetEvent(run.release);WaitForSingleObject(worker,INFINITE);DWORD exitcode=19;GetExitCodeThread(worker,&exitcode);if(exitcode)result=19;CloseHandle(worker);unsigned discarded=0;NFRenderSubmission*pending;while((pending=nf_render_handoff_pop(run.queue))!=NULL){discarded++;nf_render_submission_destroy(pending);}nf_render_handoff_close(run.queue);uint64_t qs[4];nf_render_handoff_stats(run.queue,qs);nf_render_handoff_destroy(run.queue);CloseHandle(run.stop);CloseHandle(run.wake);CloseHandle(run.ready);CloseHandle(run.inflight);CloseHandle(run.release);
 if(getenv("NF_TEST_CAPTURE_EVENT_PROFILE")){int(*profile_read)(uint64_t*)=(void*)GetProcAddress(dll,"nf_capture_profile_read");int(*event_read)(unsigned,uint64_t*)=(void*)GetProcAddress(dll,"nf_capture_event_profile_read");uint64_t totals[6];if(!profile_read||!event_read||!profile_read(totals))result=19;else{printf("capture_cost hooks_ns=%llu hooks_calls=%llu layers_ns=%llu layers_calls=%llu scanline_ns=%llu scanline_calls=%llu\n",(unsigned long long)totals[0],(unsigned long long)totals[1],(unsigned long long)totals[2],(unsigned long long)totals[3],(unsigned long long)totals[4],(unsigned long long)totals[5]);for(unsigned i=0;i<64;i++){uint64_t event[3];if(!event_read(i,event))break;printf("capture_event pc=%llu calls=%llu ns=%llu\n",(unsigned long long)event[0],(unsigned long long)event[1],(unsigned long long)event[2]);}}}
 if(cpu_profile&&fclose(cpu_profile))result=19;
 if(getenv("NF_TEST_SURFACE_READ_REUSE")){
  void(*read_stats)(uint64_t*)=(void*)GetProcAddress(dll,"nf_live_surface_read_reuse_stats");uint64_t stats[3]={0};
  if(!read_stats)result=19;else{read_stats(stats);printf("surface_read_reused=%llu surface_read_verified=%llu surface_read_mismatches=%llu\n",(unsigned long long)stats[0],(unsigned long long)stats[1],(unsigned long long)stats[2]);if(!stats[0]||stats[2]||(getenv("NF_VERIFY_SURFACE_READ_REUSE")&&stats[1]!=stats[0]))result=19;}
 }
 unsigned cache_stats[4]={0};void(*cache_report)(unsigned*)=(void*)GetProcAddress(dll,"nf_live_exact_scene_cache_stats");if(cache_report){cache_report(cache_stats);printf("exact_scene_cache_hits=%u stores=%u verified=%u mismatches=%u\n",cache_stats[0],cache_stats[1],cache_stats[2],cache_stats[3]);if(cache_stats[3])result=19;}
 if(poll_trace){snprintf(path,sizeof(path),"%s-clock-polls.csv",argv[4]);FILE*f=fopen(path,"wb");if(!f)result=19;else{fprintf(f,"now_ns,origin_ns,due,scheduled_simulated,latest_display,next_display_before,simulation_steps,present,skipped\n");for(unsigned i=0;i<poll_count;i++){NFClockPollTrace*x=poll_records+i;if(fprintf(f,"%llu,%llu,%llu,%llu,%llu,%llu,%u,%u,%u\n",(unsigned long long)x->now,(unsigned long long)x->origin,(unsigned long long)x->due,(unsigned long long)x->simulated,(unsigned long long)x->latest,(unsigned long long)x->next_display,x->steps,x->present,x->skipped)<0)result=19;}if(fclose(f))result=19;}printf("clock_poll_trace_rows=%u\n",poll_count);}free(poll_records);
 if(attempt_log&&fclose(attempt_log))result=19;fclose(contexts);fclose(producer_log);fclose(inputs);fclose(log);snprintf(path,sizeof(path),"%s-ewram.bin",argv[4]);dump(path,0x02000000,0x40000);snprintf(path,sizeof(path),"%s-iwram.bin",argv[4]);dump(path,0x03000000,0x8000);
 if(!run.result&&(submitted!=run.rendered+run.stale+run.cancelled+discarded+qs[2]||qs[0]!=submitted||qs[0]!=qs[1]+qs[2]||qs[3]!=full))result=19;
 printf("complete_stable_verified=%u complete_ordered_verified=%u complete_motion_verified=%u\n",run.stable_verified,run.ordered_verified,run.motion_verified);
 printf("result=%d original_steps=%u submitted=%u queue_full=%u unavailable=%u skipped=%llu rendered=%u verified=%u producer=%lu consumer=%lu window_owner=%lu discarded=%u\n",result,steps,submitted,full,unavailable,(unsigned long long)skipped,run.rendered,run.verified,(unsigned long)run.producer,(unsigned long)run.consumer,(unsigned long)run.window_owner,discarded);
 printf("stale=%u retired_pending=%llu epoch_cuts=%u cut_ns=%llu cut_epoch=%llu\n",run.stale,(unsigned long long)qs[2],cuts,(unsigned long long)cut_time,(unsigned long long)cut_epoch);
 printf("hardware_submitted=%u native_submitted=%u scene_kind_cuts=%u\n",hardware_submitted,native_submitted,kind_cuts);
 printf("epoch_clears=%u pauses=%u\n",run.cleared,pauses);
 printf("window_quit=%ld\n",(long)InterlockedCompareExchange(&run.quit,0,0));
 printf("steering_route=%d capture_refresh_configured=%d\n",route,getenv("NF_THREADED_CAPTURE_REFRESH")!=NULL);
 printf("interactive=%d input_enabled=%d input_test=%d input_polls=%u connected_polls=%u xinput_available=%d\n",interactive,input_enabled,test_input,input_polls,connected_polls,getpad!=NULL);
 printf("cancelled=%u scheduled=%d clock_origin=%llu source_base=%u presentation_lag_ns=%llu\n",run.cancelled,run.scheduled,(unsigned long long)run.clock_origin,run.source_base,(unsigned long long)run.lag_ns);
 if(backlog_profile)printf("clock_backlog_polls=%llu clock_backlog_suppressed=%llu clock_backlog_max=%llu clock_backlog_longest_ns=%llu\n",(unsigned long long)backlog_polls,(unsigned long long)backlog_suppressed,(unsigned long long)backlog_max,(unsigned long long)backlog_longest_ns);
 printf("complete_road_cache_hits=%llu misses=%llu\n",(unsigned long long)nf_complete_road_cache.hits,(unsigned long long)nf_complete_road_cache.misses);printf("shared_source_cache_hits=%llu shared_source_cache_misses=%llu shared_source_cache_clears=%llu\n",(unsigned long long)nf_shared_road_cache.hits,(unsigned long long)nf_shared_road_cache.misses,(unsigned long long)nf_shared_road_cache.clears);nf_shared_road_cache_clear();nf_complete_road_cache_clear();if(input_module)FreeLibrary(input_module);close_game();nf_snapshot_destroy(store);FreeLibrary(dll);return result;
}




#endif



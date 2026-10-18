#define NF_LIVE_PREVIEW_NO_MAIN
#include "live_preview.c"
#undef main
#include "window_present.h"
#include "controller.h"
#include <Xinput.h>
#include <mmsystem.h>
#include <mgba/core/core.h>
#include "live_hud_adapter.h"
#include "live_sky_adapter.h"
#include "live_pose_adapter.h"

typedef struct { int (WINAPI *get_state)(DWORD, XINPUT_STATE*); } LiveXInput;
/* CPU wall costs include bridge capture and GPU synchronization where applicable. */
typedef struct {const char* name;unsigned count,over8,over16;double total,max;} LiveStage;
static LiveStage live_stages[]={{"core_capture"},{"hud_select"},{"sky_select"},{"geometry"},{"hud_draw"},{"present"}};
static uint64_t live_capture_profile[6];
static int (*live_capture_read)(uint64_t*);
static int (*live_capture_events)(unsigned,uint64_t*);
static int (*live_arm_read)(uint64_t*);
static int live_profile_enabled;
static LARGE_INTEGER live_stage_begin(void){LARGE_INTEGER stamp;QueryPerformanceCounter(&stamp);return stamp;}
static void live_stage_end(unsigned index,LARGE_INTEGER begin){
 LARGE_INTEGER end;QueryPerformanceCounter(&end);
 double ms=(end.QuadPart-begin.QuadPart)*1000.0/rebuild_frequency.QuadPart;
 LiveStage* stage=&live_stages[index];stage->count++;stage->total+=ms;
 if(ms>stage->max)stage->max=ms;if(ms>8)stage->over8++;if(ms>1000.0/60)stage->over16++;
}
static void live_profile_enable(HMODULE bridge){
 if(!getenv("NF_CAPTURE_PROFILE"))return;
 void(*enable)(unsigned)=(void*)GetProcAddress(bridge,"nf_capture_profile_enable");
 live_capture_read=(void*)GetProcAddress(bridge,"nf_capture_profile_read");
 live_capture_events=(void*)GetProcAddress(bridge,"nf_capture_event_profile_read");
 live_arm_read=(void*)GetProcAddress(bridge,"nf_arm_stage_profile_read");
 void(*arm_enable)(unsigned)=(void*)GetProcAddress(bridge,"nf_arm_stage_profile_enable");
 if(enable&&live_capture_read){enable(1);live_profile_enabled=1;}
 /* Per-ARM-call timers are highly intrusive; opt in separately. */
 if(getenv("NF_ARM_STAGE_PROFILE")&&arm_enable&&live_arm_read)arm_enable(1);else live_arm_read=NULL;
}
static void live_profile_sample(void){
 uint64_t values[6];if(live_profile_enabled&&live_capture_read(values))
  for(unsigned i=0;i<6;i++)live_capture_profile[i]+=values[i];
}
static void live_profile_write(FILE* file){
 fprintf(file,",\"stage_profile\":[");
 for(unsigned i=0;i<sizeof(live_stages)/sizeof(live_stages[0]);i++){
  LiveStage* stage=&live_stages[i];
  fprintf(file,"%s{\"name\":\"%s\",\"calls\":%u,\"mean_ms\":%.6f,\"max_ms\":%.6f,\"over8_ms\":%u,\"over16_ms\":%u}",
   i?",":"",stage->name,stage->count,stage->count?stage->total/stage->count:0,stage->max,stage->over8,stage->over16);
 }
 fprintf(file,"],\"bridge_profile_enabled\":%s,\"capture_profile_totals\":[",live_profile_enabled?"true":"false");
 for(unsigned i=0;i<6;i++)fprintf(file,"%s%llu",i?",":"",(unsigned long long)live_capture_profile[i]);
 fprintf(file,"],\"capture_events\":[");
 if(live_profile_enabled&&live_capture_events)for(unsigned i=0;i<64;i++){
  uint64_t values[3];if(!live_capture_events(i,values))break;
  fprintf(file,"%s{\"pc\":%u,\"calls\":%llu,\"ns\":%llu}",i?",":"",(unsigned)values[0],(unsigned long long)values[1],(unsigned long long)values[2]);
 }
 uint64_t arm[6]={0};int arm_ok=live_arm_read&&live_arm_read(arm);
 fprintf(file,"],\"arm_profile_available\":%s,\"arm_stage_totals\":[",arm_ok?"true":"false");
 for(unsigned i=0;i<6;i++)fprintf(file,"%s%llu",i?",":"",(unsigned long long)arm[i]);
 fprintf(file,"]");live_pose_write(file);fprintf(file,"}\n");
}
static unsigned live_presented,live_warm_intervals,live_warm_over20;
static LARGE_INTEGER live_last_swap,live_clock_start;
static double live_warm_interval_ms,live_warm_max_ms;
static int present_packet(void) {
    int ok=preview_window_stage(1) && preview_window_finish();
    if(ok){
        LARGE_INTEGER stamp;QueryPerformanceCounter(&stamp);live_presented++;
        if(live_last_swap.QuadPart&&(stamp.QuadPart-live_clock_start.QuadPart)/(double)rebuild_frequency.QuadPart>=2){
            double interval=(stamp.QuadPart-live_last_swap.QuadPart)*1000.0/rebuild_frequency.QuadPart;
            live_warm_intervals++;live_warm_interval_ms+=interval;
            if(interval>live_warm_max_ms)live_warm_max_ms=interval;
            if(interval>20)live_warm_over20++;
        }
        live_last_swap=stamp;
    }
    return ok;
}
/* Capture the renderer-owned target, without reading the desktop. */
static int live_capture(const char* path) {
    if(!path||!*path||!preview_context)return 0;
    unsigned char* pixels=malloc(3840u*2160u*3u);
    if(!pixels)return 0;
    glReadBuffer(0x8ce0);glPixelStorei(GL_PACK_ALIGNMENT,1);
    glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,pixels);
    int ok=glGetError()==GL_NO_ERROR;FILE* file=ok?fopen(path,"wb"):NULL;
    if(!file){free(pixels);return 0;}
    ok=fprintf(file,"P6\n3840 2160\n255\n")>0;
    for(int y=2159;y>=0&&ok;y--)ok=fwrite(pixels+(size_t)y*3840*3,3,3840,file)==3840;
    if(fclose(file))ok=0;free(pixels);return ok;
}
static unsigned live_packet_gap_max,live_packet_last,live_packet_epoch_changes;
static uint64_t live_packet_epoch;
static uint32_t live_packet_serial;
static int(*live_timing_read)(uint64_t,uint32_t,uint64_t*);
static unsigned live_time_status[4],live_epoch_mismatch,live_warm_unready;
static int live_retain_scene(void* context,uint64_t epoch,const void* data,size_t size){
    NFScenePacket packet;
    if(nf_scene_packet_view(data,size,&packet)){
        if(live_packet_last&&epoch==live_packet_epoch&&packet.end_refresh>live_packet_last){
            unsigned gap=packet.end_refresh-live_packet_last;
            if(gap>live_packet_gap_max)live_packet_gap_max=gap;
        }
        if(live_packet_last&&epoch!=live_packet_epoch)live_packet_epoch_changes++;
        live_packet_last=packet.end_refresh;live_packet_epoch=epoch;live_packet_serial=packet.serial;
        live_pose_scene(epoch,&packet);
        if(!live_sky_retain_boundary(epoch,&packet))return 0;
    }
    return retain_scene(context,epoch,data,size);
}
static unsigned live_keys(LiveXInput* x) {
    unsigned keys = 0;
    int foreground = preview_window && GetForegroundWindow() == preview_window;
    if (foreground) {
        int vk[10] = {'Z','X',VK_BACK,VK_RETURN,VK_RIGHT,VK_LEFT,VK_UP,VK_DOWN,'S','A'};
        for (int i=0; i<10; i++) if (GetAsyncKeyState(vk[i]) & 0x8000) keys |= 1u << i;
    }
    if (x && x->get_state) {
        for (DWORD i=0; i<4; i++) {
            XINPUT_STATE state;
            if (x->get_state(i,&state) == ERROR_SUCCESS) {
                keys |= nfs_map_controller(state.Gamepad.wButtons,state.Gamepad.sThumbLX,
                    state.Gamepad.sThumbLY,state.Gamepad.bLeftTrigger,state.Gamepad.bRightTrigger);
                break;
            }
        }
    }
    return keys;
}
int main(int argc, char** argv) {
    if (argc < 3 || argc > 4) {
        fprintf(stderr,"Usage: live_game_window.exe <nfsprobe.dll> <game.gba> [race-checkpoint.state]\n");
        return 1;
    }
    LARGE_INTEGER frequency,last,now;
    QueryPerformanceFrequency(&frequency);
    QueryPerformanceCounter(&last);
    rebuild_frequency = frequency;
    HMODULE bridge = LoadLibraryA(argv[1]);
    if (!bridge) { fprintf(stderr,"Could not load bridge DLL: %s\n",argv[1]); return 2; }
    int (*init)(const char*,const char*) = (void*)GetProcAddress(bridge,"nf_init");
    int (*state_load)(const char*,int) = (void*)GetProcAddress(bridge,"nf_state");
    int (*sink)(LiveSink,void*) = (void*)GetProcAddress(bridge,"nf_native_scene_sink");
    int (*multimodel)(int) = (void*)GetProcAddress(bridge,"nf_native_scene_multimodel");
    void (*frame)(unsigned) = (void*)GetProcAddress(bridge,"nf_frame");
    void (*pace)(int) = (void*)GetProcAddress(bridge,"nf_60");
    void (*close_game)(void) = (void*)GetProcAddress(bridge,"nf_close");
    uint64_t (*epoch)(void) = (void*)GetProcAddress(bridge,"nf_native_scene_epoch");
    uint32_t (*refresh)(void) = (void*)GetProcAddress(bridge,"nf_native_scene_refresh");
    struct mCore* (*get_core)(void) = (void*)GetProcAddress(bridge,"nf_core");
    if (!init || !sink || !multimodel || !frame || !pace || !close_game ||
        !epoch || !refresh || !get_core) {
        fprintf(stderr,"The bridge is missing a required live-scene function.\n");
        FreeLibrary(bridge); return 3;
    }
    if(getenv("NF_LIVE_SKY_CONTINUOUS")){_putenv("NF_LIVE_SKY=1");_putenv("NF_LIVE_SKY_BOUNDARIES=1");}
    if(getenv("NF_LIVE_SKY"))_putenv("NF_LIVE_HUD=1");
    if(getenv("NF_LIVE_HUD")){_putenv("NF_LAYER_DIRTY=1");_putenv("NF_TEST_RACING_OWNED_CAPTURE=1");}
    if (!init(argv[2],"")) { fprintf(stderr,"Could not load the supplied game ROM.\n"); FreeLibrary(bridge); return 4; }
    pace(0);
    if (argc == 4 && strcmp(argv[3],"-") && (!state_load || !state_load(argv[3],0))) {
        fprintf(stderr,"Could not load race checkpoint: %s\n",argv[3]);
        close_game(); FreeLibrary(bridge); return 5;
    }
    NFSnapshotStore* store = nf_snapshot_create(32u*1024u*1024u);
    if (!store || !sink(live_retain_scene,store) || !multimodel(1)) {
        fprintf(stderr,"Could not initialize live scene capture.\n");
        if (store) nf_snapshot_destroy(store);
        close_game(); FreeLibrary(bridge); return 6;
    }
    /* Diagnostic only: retain original cycles, without retiming any scene. */
    if(getenv("NF_LIVE_AVAILABILITY_TRACE")){
        int(*enable)(int)=(void*)GetProcAddress(bridge,"nf_native_scene_timing_enable");
        live_timing_read=(void*)GetProcAddress(bridge,"nf_native_scene_timing_read");
        if(!enable||!live_timing_read||!enable(1)){
            fprintf(stderr,"Precise scene timing diagnostic unavailable.\n");
            close_game();nf_snapshot_destroy(store);FreeLibrary(bridge);return 14;
        }
    }
    if(!live_pose_enable(bridge)){
        fprintf(stderr,"Early source-pose setup failed.\n");
        close_game();nf_snapshot_destroy(store);FreeLibrary(bridge);return 15;
    }
    if(!live_hud_enable(bridge)){fprintf(stderr,"HUD capture setup failed.\n");close_game();nf_snapshot_destroy(store);FreeLibrary(bridge);return 9;}
    if(!live_sky_enable(bridge,epoch(),argv[2])){fprintf(stderr,"Source sky capture setup failed; check NF_LIVE_SOURCE_TABLE.\n");close_game();nf_snapshot_destroy(store);FreeLibrary(bridge);return 11;}
    preview_window_output=1;
    preview_keep_context=1;
    preview_measure_only=1;
    /* Present only after all scene and overlay drawing has completed. */
    _putenv("NF_PREVIEW_PHASE=0");
    HMODULE xi=LoadLibraryA("xinput1_4.dll");
    if (!xi) xi=LoadLibraryA("xinput9_1_0.dll");
    LiveXInput x={(void*)(xi?GetProcAddress(xi,"XInputGetState"):NULL)};
    struct mCore* core=get_core();
    double step=core&&core->frequency(core)
        ? (double)core->frameCycles(core)/core->frequency(core)
        : 280896.0/16777216.0;
    if (step<=0 || step>.05) step=280896.0/16777216.0;
    /* Allocate the GPU target before starting the simulation clock. */
    int prepare_error=preview_context_open();
    if(prepare_error){fprintf(stderr,"OpenGL setup failed (stage %d).\n",prepare_error);
        live_sky_close();
    live_hud_close();
    preview_shutdown();close_game();nf_snapshot_destroy(store);if(xi)FreeLibrary(xi);FreeLibrary(bridge);return 8;}
    if(hud_preview&&!endpoint_hud_warmup()){fprintf(stderr,"HUD GPU setup failed.\n");live_hud_close();preview_shutdown();close_game();nf_snapshot_destroy(store);if(xi)FreeLibrary(xi);FreeLibrary(bridge);return 10;}
    if(!live_sky_warmup()){fprintf(stderr,"Continuous sky GPU setup failed.\n");live_sky_close();live_hud_close();preview_shutdown();close_game();nf_snapshot_destroy(store);if(xi)FreeLibrary(xi);FreeLibrary(bridge);return 13;}
    live_profile_enable(bridge);
    uint32_t core_start=core->frameCounter(core);
    timeBeginPeriod(1);
    QueryPerformanceCounter(&last);
    double accumulator=0,elapsed=0,render_ms=0,render_max_ms=0;
    LARGE_INTEGER started=last;live_clock_start=last;
    double next_display=0,last_render_target=0;unsigned display_slots_missed=0;
    const char* availability_path=getenv("NF_LIVE_AVAILABILITY_TRACE");
    FILE* availability=availability_path?fopen(availability_path,"w"):NULL;
    if(availability_path&&!availability){fprintf(stderr,"Could not open availability trace.\n");timeEndPeriod(1);live_sky_close();live_hud_close();preview_shutdown();close_game();nf_snapshot_destroy(store);if(xi)FreeLibrary(xi);FreeLibrary(bridge);return 12;}
    void(*capture_stats)(uint32_t*)=(void*)GetProcAddress(bridge,"nf_native_scene_stats");
    if(availability)fprintf(availability,"elapsed,core_refresh,target,status,latest_packet_end,older_end,newer_end,serial,published,rejected,write_failed,latest_serial,timing_valid,flip_cycles,flip_phase,last_geometry_cycles,last_geometry_refresh\n");
    const char* limit_text=getenv("NF_LIVE_TEST_SECONDS");
    double limit=limit_text?strtod(limit_text,NULL):0;
    if(limit<0||limit>3600)limit=0;
    double render_delay=6;
    const char* delay_text=getenv("NF_LIVE_RENDER_DELAY");
    if(delay_text){char* end;double requested=strtod(delay_text,&end);
        if(*delay_text&&!*end&&isfinite(requested)&&requested>=1&&requested<=16)render_delay=requested;
        else fprintf(stderr,"Invalid NF_LIVE_RENDER_DELAY; using six original core frames.\n");}
    int scripted=getenv("NF_LIVE_TEST_INPUT")!=NULL;
    unsigned over_budget=0,refresh_changes=0,last_refresh=0;
    double max_backlog=0;
    unsigned emulated=0,rendered=0,failures=0;
    int shown=0,running=1,last_error=0;
    char* args[]={argv[0],"unused","unused","live-window","unused","unused","unused"};
    while (running) {
        MSG msg;
        while (PeekMessageA(&msg,NULL,0,0,PM_REMOVE)) {
            if (msg.message==WM_QUIT) running=0;
            TranslateMessage(&msg); DispatchMessageA(&msg);
        }
        if (!running) break;
        if (preview_window && !IsWindow(preview_window)) break;
        if (GetAsyncKeyState(VK_ESCAPE)&0x8000) break;
        QueryPerformanceCounter(&now);
        double dt=(double)(now.QuadPart-last.QuadPart)/frequency.QuadPart;
        last=now; if(dt<0)dt=0;
        elapsed=(double)(now.QuadPart-started.QuadPart)/frequency.QuadPart;
        if(limit>0&&elapsed>=limit)break;
        /* Keep elapsed time after slow draws: the core frame period is unchanged. */
        accumulator+=dt;
        if(accumulator>max_backlog)max_backlog=accumulator;
        unsigned keys=live_keys(&x),steps=0;
        if(scripted){
            keys=1u;
            if(getenv("NF_LIVE_TEST_STEER")){
                if((elapsed>=1&&elapsed<2)||(elapsed>=15&&elapsed<16))keys|=16u;
                if(elapsed>=8&&elapsed<9)keys|=32u;
            }
        }
        while (accumulator>=step && steps<8) {
            if(!live_sky_before_frame(epoch())){last_error=47;failures++;running=0;break;}
            LARGE_INTEGER core_begin=live_stage_begin();frame(keys);live_stage_end(0,core_begin);live_profile_sample();live_pose_poll(epoch(),refresh()); accumulator-=step; steps++; emulated++;
        }
        /* Display at 60 Hz independently of the original 59.7275 Hz core. */
        if (elapsed>=next_display) {
            unsigned due=(unsigned)floor((elapsed-next_display)*60.0)+1;
            if(due>1)display_slots_missed+=due-1;
            next_display+=due/60.0;
            uint32_t current=refresh(); uint64_t current_epoch=epoch();
            if (current>5) {
                double target=(double)current-render_delay+fmin(accumulator/step,1.0);
                NFSnapshotPair pair={0};
                int status=nf_snapshot_acquire(store,target,0,&pair);
                if(status>=0&&status<4)live_time_status[status]++;
                int ready=status==NF_TIME_READY;
                if(ready&&pair.time.epoch!=current_epoch)live_epoch_mismatch++;
                if (ready) ready=pair.time.epoch==current_epoch;
                if(!ready&&elapsed>=2)live_warm_unready++;
                if(availability&&!ready){
                    uint32_t stats[4]={0};if(capture_stats)capture_stats(stats);
                    NFScenePacket old={0},new={0};
                    if(pair.older)nf_scene_packet_view(pair.older,pair.older_size,&old);
                    if(pair.newer)nf_scene_packet_view(pair.newer,pair.newer_size,&new);
                    uint64_t timing[20]={0};
                    int timing_ok=live_timing_read&&live_timing_read(live_packet_epoch,live_packet_serial,timing);
                    /* vcount/next event encode position relative to original VBlank.
                       This is logged evidence only; interpolation remains unchanged. */
                    double phase=timing_ok?(((timing[9]+228-160)%228)*1232.0+
                        ((timing[10]&2)?1232:1008)-(int64_t)timing[11])/280896.0:0;
                    fprintf(availability,"%.9f,%u,%.9f,%d,%u,%u,%u,%u,%u,%u,%u,%u,%d,%llu,%.12f,%llu,%llu\n",elapsed,current,target,status,live_packet_last,old.end_refresh,new.end_refresh,stats[0],stats[1],stats[2],stats[3],live_packet_serial,timing_ok,(unsigned long long)timing[4],phase,(unsigned long long)timing[6],(unsigned long long)timing[18]);
                }
                nf_snapshot_release(store);
                if (ready) {
                    LARGE_INTEGER begin,finish;
                    QueryPerformanceCounter(&begin);
                    LARGE_INTEGER stage_begin=live_stage_begin();
                    int hud_ok=live_hud_select(current_epoch,(unsigned)floor(target));live_stage_end(1,stage_begin);
                    if(!hud_ok){last_error=45;failures++;running=0;break;}
                    stage_begin=live_stage_begin();int sky_ok=live_sky_select(current_epoch,(unsigned)floor(target));live_stage_end(2,stage_begin);
                    if(!sky_ok)continue;
                    stage_begin=live_stage_begin();int result=render_packet_at(store,target,args);live_stage_end(3,stage_begin);
                    if(!result){stage_begin=live_stage_begin();if(!live_hud_draw())result=46;live_stage_end(4,stage_begin);}
                    if(!result){stage_begin=live_stage_begin();if(!present_packet())result=44;live_stage_end(5,stage_begin);}
                    QueryPerformanceCounter(&finish);
                    double cost=(double)(finish.QuadPart-begin.QuadPart)*1000.0/frequency.QuadPart;
                    render_ms+=cost; if(cost>render_max_ms)render_max_ms=cost;
                    if(cost>1000.0/60.0)over_budget++;
                    if (result) {
                        last_error=result; failures++;
                        fprintf(stderr,"Live packet render failed (stage %d).\n",result);
                        running=0;
                    } else {
                        rendered++;last_render_target=target;
                        if(current!=last_refresh){refresh_changes++;last_refresh=current;}
                        if (!shown && preview_window) {
                            ShowWindow(preview_window,SW_SHOW);
                            SetForegroundWindow(preview_window);
                            SetWindowTextA(preview_window,
                                "NFSUG live packet renderer preview | mGBA core | ESC exits");
                            shown=1;
                        }
                    }
                }
            }
        }
        if (!steps) Sleep(1);
    }
    QueryPerformanceCounter(&now);
    elapsed=(double)(now.QuadPart-started.QuadPart)/frequency.QuadPart;
    const char* capture=getenv("NF_LIVE_TEST_CAPTURE");
    int capture_ok=capture?live_capture(capture):0;
    const char* base_capture=getenv("NF_LIVE_HUD_BASE_CAPTURE");
    int base_capture_ok=0;
    if(base_capture&&hud_preview&&rendered&&!render_packet_at(store,last_render_target,args))base_capture_ok=live_capture(base_capture);
    uint32_t core_frames=core->frameCounter(core)-core_start;
    const char* report=getenv("NF_LIVE_TEST_REPORT");
    if(report){FILE* f=fopen(report,"w");if(f){
        fprintf(f,"{\"frames\":%u,\"core_frames\":%u,\"model_endpoint_fallbacks\":%u,\"presented\":%u,\"rendered\":%u,\"wall_seconds\":%.9f,\"core_frame_seconds\":%.12f,\"render_delay_frames\":%.6f,\"simulation_seconds\":%.9f,\"backlog_seconds\":%.9f,\"max_backlog_seconds\":%.9f,\"render_mean_ms\":%.6f,\"render_max_ms\":%.6f,\"renders_over_60hz_budget\":%u,\"refresh_changes\":%u,\"last_refresh\":%u,\"display_slots_missed\":%u,\"continuous_camera\":%s,\"warm_intervals\":%u,\"warm_present_mean_ms\":%.6f,\"warm_present_max_ms\":%.6f,\"warm_present_over20_ms\":%u,\"time_status\":[%u,%u,%u,%u],\"warm_unready\":%u,\"epoch_mismatch\":%u,\"source_packets\":%u,\"source_gap_max_frames\":%u,\"last_packet_refresh\":%u,\"sky_enabled\":%s,\"sky_draw_calls\":%u,\"sky_snapshot_misses\":%u,\"sky_refresh\":%u,\"sky_source_updates\":%u,\"sky_image_changes\":%u,\"scripted_steering\":%s,\"hud_enabled\":%s,\"hud_drawn\":%u,\"hud_select_misses\":%u,\"hud_text_missing\":%u,\"hud_refresh\":%u,\"hud_base_capture_ok\":%s,\"capture_ok\":%s,\"scripted_input\":%s,\"failures\":%u,\"error\":%d",
            emulated,core_frames,packet_model_endpoint_fallbacks,live_presented,rendered,elapsed,step,render_delay,emulated*step,accumulator,max_backlog,
            rendered?render_ms/rendered:0,render_max_ms,over_budget,refresh_changes,last_refresh,display_slots_missed,packet_continuous_camera?"true":"false",live_warm_intervals,live_warm_intervals?live_warm_interval_ms/live_warm_intervals:0,live_warm_max_ms,live_warm_over20,
            live_time_status[0],live_time_status[1],live_time_status[2],live_time_status[3],live_warm_unready,live_epoch_mismatch,received,live_packet_gap_max,live_packet_last,
            live_sky_enabled?"true":"false",live_sky_draw_calls,live_sky_snapshot_misses,live_sky_refresh,live_sky_source_updates,live_sky_image_changes,getenv("NF_LIVE_TEST_STEER")?"true":"false",
            hud_preview?"true":"false",hud_drawn,live_hud_select_misses,live_hud_text_missing,hud_refresh,base_capture_ok?"true":"false",
            capture_ok?"true":"false",scripted?"true":"false",failures,last_error);
        fprintf(f,",\"background_capture_only\":%s",live_sky_background_only?"true":"false");
        fprintf(f,",\"model_subset_frames\":%u,\"model_local_holds\":%u,\"subset_camera_moving_frames\":%u",
            packet_model_subset_frames,packet_model_local_holds,packet_subset_camera_moving);
        fprintf(f,",\"sky_boundary_enabled\":%s,\"sky_boundaries_retained\":%u,\"sky_boundary_failures\":%u,\"sky_boundary_last_serial\":%u",
            live_sky_boundary_enabled?"true":"false",live_sky_boundaries_retained,live_sky_boundary_failures,live_sky_boundary_last_serial);
        fprintf(f,",\"sky_continuous\":%s,\"sky_continuous_frames\":%u,\"sky_phase_changes\":%u,\"sky_subpixel_frames\":%u,\"sky_continuous_fallbacks\":%u",
            live_sky_continuous?"true":"false",live_sky_continuous_frames,live_sky_phase_changes,live_sky_subpixel_frames,live_sky_continuous_fallbacks);
        live_profile_write(f);fclose(f);
    }}
    if(availability)fclose(availability);
    timeEndPeriod(1);
    live_sky_close();
    live_hud_close();
    preview_shutdown();
    close_game();
    nf_snapshot_release(store);
    nf_snapshot_destroy(store);
    if(xi)FreeLibrary(xi);
    FreeLibrary(bridge);
    fprintf(stderr,"frames=%u rendered_packets=%u seconds=%.2f render_mean_ms=%.3f render_max_ms=%.3f failures=%u error=%d\n",
        emulated,rendered,elapsed,rendered?render_ms/rendered:0,render_max_ms,failures,last_error);
    return failures?7:0;
}



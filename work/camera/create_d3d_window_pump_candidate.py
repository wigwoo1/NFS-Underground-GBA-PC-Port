from pathlib import Path
p=Path('work/camera');s=(p/'owned_d3d_window_candidate.c').read_text()
s+='''
__declspec(dllexport) int nf_d3d_window_pump(HWND window,uint64_t*out){
 if(!valid()||!IsWindow(window)||!out||GetWindowThreadProcessId(window,NULL)!=owner)return 1;
 MSG m;unsigned count=0;while(PeekMessageW(&m,NULL,0,0,PM_REMOVE)){if(m.message==WM_QUIT)break;TranslateMessage(&m);DispatchMessageW(&m);count++;}
 RECT r;memset(&r,0,sizeof(r));if(!GetClientRect(window,&r))return 2;
 out[0]=count;out[1]=IsWindowVisible(window);out[2]=IsIconic(window);out[3]=r.right-r.left;out[4]=r.bottom-r.top;out[5]=(uint64_t)(uintptr_t)GetForegroundWindow();out[6]=(uint64_t)(uintptr_t)window;return 0;
}
'''
(p/'owned_d3d_window_pump_candidate.c').write_text(s)
s=(p/'test_d3d_window_scene_candidate.py').read_text().replace('owned-d3d-window-candidate.dll','owned-d3d-window-pump-candidate.dll').replace('d3d-window-scene-','d3d-window-pump-scene-').replace('present_results=[];','telemetry=[];d.nf_d3d_window_pump.argtypes=[P,P];present_results=[];').replace('   present_status=d.nf_d3d_present();','   window_state=(C.c_uint64*7)();assert d.nf_d3d_window_pump(window,window_state)==0;telemetry.append(list(window_state));present_status=d.nf_d3d_present();').replace('r=dict(presentation_results=','r=dict(window_telemetry=telemetry,presentation_results=')
(p/'test_d3d_window_pump_scene_candidate.py').write_text(s)

/* A single diagnostic window. Defer destruction until GL/game cleanup. */
typedef struct {int focused,minimized,resizing,manual_pause,closed;unsigned generation;WNDPROC previous;} NFWindowLifecycle;
static NFWindowLifecycle window_lifecycle;
static int nf_window_running(void){return !window_lifecycle.closed&&window_lifecycle.focused&&!window_lifecycle.minimized&&!window_lifecycle.resizing&&!window_lifecycle.manual_pause;}
static LRESULT CALLBACK nf_window_proc(HWND window,UINT message,WPARAM w,LPARAM l){
 switch(message){
 case WM_CLOSE:window_lifecycle.closed=1;return 0;
 case WM_SETFOCUS:window_lifecycle.focused=1;return 0;
 case WM_KILLFOCUS:window_lifecycle.generation++;window_lifecycle.focused=0;return 0;
 case WM_SIZE:window_lifecycle.minimized=w==SIZE_MINIMIZED;if(window_lifecycle.minimized)window_lifecycle.generation++;break;
 case WM_ENTERSIZEMOVE:window_lifecycle.generation++;window_lifecycle.resizing=1;return 0;
 case WM_EXITSIZEMOVE:window_lifecycle.resizing=0;return 0;
 case WM_KEYDOWN:
  if(w==VK_ESCAPE){window_lifecycle.closed=1;return 0;}
  if(w==VK_SPACE&&!(l&(1L<<30))){window_lifecycle.generation++;window_lifecycle.manual_pause=!window_lifecycle.manual_pause;return 0;}
  break;
 }
 return CallWindowProc(window_lifecycle.previous,window,message,w,l);
}
static int nf_window_attach(HWND window){
 memset(&window_lifecycle,0,sizeof(window_lifecycle));window_lifecycle.focused=GetForegroundWindow()==window;
 window_lifecycle.previous=(WNDPROC)SetWindowLongPtr(window,GWLP_WNDPROC,(LONG_PTR)nf_window_proc);
 return window_lifecycle.previous!=NULL;
}

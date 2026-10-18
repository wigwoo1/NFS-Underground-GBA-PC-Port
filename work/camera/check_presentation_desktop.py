"""Read-only Windows desktop/access evidence; no window or session changes."""
import ctypes as C,json,os,sys
from ctypes import wintypes as W
from pathlib import Path
u=C.WinDLL('user32',use_last_error=True);k=C.WinDLL('kernel32',use_last_error=True)
u.GetThreadDesktop.argtypes=[W.DWORD];u.GetThreadDesktop.restype=W.HANDLE
u.GetProcessWindowStation.restype=W.HANDLE
u.OpenInputDesktop.argtypes=[W.DWORD,W.BOOL,W.DWORD];u.OpenInputDesktop.restype=W.HANDLE
u.CloseDesktop.argtypes=[W.HANDLE]
u.GetUserObjectInformationW.argtypes=[W.HANDLE,C.c_int,C.c_void_p,W.DWORD,C.POINTER(W.DWORD)]
def name(h):
 if not h:return None
 needed=W.DWORD();u.GetUserObjectInformationW(h,2,None,0,C.byref(needed));buf=C.create_unicode_buffer(max(1,needed.value//2));assert u.GetUserObjectInformationW(h,2,buf,C.sizeof(buf),C.byref(needed));return buf.value
sid=W.DWORD();assert k.ProcessIdToSessionId(os.getpid(),C.byref(sid));desktop=u.GetThreadDesktop(k.GetCurrentThreadId());station=u.GetProcessWindowStation();input_desktop=u.OpenInputDesktop(0,False,1);error=C.get_last_error() if not input_desktop else 0
out=dict(pid=os.getpid(),session=sid.value,thread_desktop=name(desktop),window_station=name(station),input_desktop=name(input_desktop),input_desktop_error=error,is_admin=bool(C.windll.shell32.IsUserAnAdmin()))
if input_desktop:u.CloseDesktop(input_desktop)
dwm=C.WinDLL('dwmapi');enabled=W.BOOL();out['dwm_hresult']=dwm.DwmIsCompositionEnabled(C.byref(enabled));out['composition_enabled']=bool(enabled.value)
if len(sys.argv)>1:Path(sys.argv[1]).write_text(json.dumps(out,indent=2))
print(out)

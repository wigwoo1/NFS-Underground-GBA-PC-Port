import ctypes as C,json,sys
from ctypes import wintypes as W
from pathlib import Path
u=C.WinDLL('user32');d=C.WinDLL('dwmapi');target=int(sys.argv[1]);rows=[]
u.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)];u.GetWindowThreadProcessId.restype=W.DWORD
u.GetClientRect.argtypes=[W.HWND,C.POINTER(W.RECT)];u.GetWindowRect.argtypes=[W.HWND,C.POINTER(W.RECT)];u.IsWindowVisible.argtypes=[W.HWND];u.IsIconic.argtypes=[W.HWND]
class MonitorInfo(C.Structure):
 _fields_=[('size',W.DWORD),('monitor',W.RECT),('work',W.RECT),('flags',W.DWORD)]
u.MonitorFromWindow.argtypes=[W.HWND,W.DWORD];u.MonitorFromWindow.restype=W.HANDLE
u.GetMonitorInfoW.argtypes=[W.HANDLE,C.POINTER(MonitorInfo)]
Callback=C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
@Callback
def visit(h,param):
 pid=W.DWORD();tid=u.GetWindowThreadProcessId(h,C.byref(pid))
 if pid.value!=target:return True
 title=C.create_unicode_buffer(512);u.GetWindowTextW(h,title,512);rect=W.RECT();u.GetWindowRect(h,C.byref(rect));cloaked=W.DWORD();d.DwmGetWindowAttribute.argtypes=[W.HWND,W.DWORD,C.c_void_p,W.DWORD];hr=d.DwmGetWindowAttribute(h,14,C.byref(cloaked),4)
 client=W.RECT();client_ok=bool(u.GetClientRect(h,C.byref(client)))
 monitor=MonitorInfo();monitor.size=C.sizeof(monitor);monitor_ok=bool(u.GetMonitorInfoW(u.MonitorFromWindow(h,2),C.byref(monitor)));monitor_rect=[monitor.monitor.left,monitor.monitor.top,monitor.monitor.right,monitor.monitor.bottom] if monitor_ok else None
 rows.append(dict(monitor_rect=monitor_rect,client_pixels=[client.right-client.left,client.bottom-client.top] if client_ok else None,hwnd=int(h),thread=tid,title=title.value,visible=bool(u.IsWindowVisible(h)),minimized=bool(u.IsIconic(h)),rect=[rect.left,rect.top,rect.right,rect.bottom],cloaked=cloaked.value,cloaked_hresult=hr));return True
u.EnumWindows.argtypes=[Callback,W.LPARAM];assert u.EnumWindows(visit,0)
out=dict(pid=target,windows=rows,scope='Read-only current desktop enumeration filtered to owned game PID; visibility not physical frame proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)



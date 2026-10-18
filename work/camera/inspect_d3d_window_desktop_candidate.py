import ctypes as C,json
from pathlib import Path
u=C.WinDLL('user32',use_last_error=True);k=C.WinDLL('kernel32',use_last_error=True);P=C.c_void_p
u.GetThreadDesktop.argtypes=[C.c_uint];u.GetThreadDesktop.restype=P;u.OpenInputDesktop.argtypes=[C.c_uint,C.c_int,C.c_uint];u.OpenInputDesktop.restype=P;u.GetUserObjectInformationW.argtypes=[P,C.c_int,P,C.c_uint,P];u.CloseDesktop.argtypes=[P]
def name(handle):
 b=C.create_unicode_buffer(256);n=C.c_uint();ok=u.GetUserObjectInformationW(handle,2,b,C.sizeof(b),C.byref(n));return dict(ok=bool(ok),name=b.value,error=0 if ok else C.get_last_error())
thread=u.GetThreadDesktop(k.GetCurrentThreadId());inp=u.OpenInputDesktop(0,False,1);error=C.get_last_error() if not inp else 0;session=C.c_uint();k.ProcessIdToSessionId(k.GetCurrentProcessId(),C.byref(session));r=dict(thread_desktop=name(thread),input_desktop=name(inp) if inp else None,input_open_error=error,process_session=session.value,scope='Read-only desktop metadata; does not prove physical scanout or exact occlusion cause.')
if inp:u.CloseDesktop(inp)
Path('work/camera/prototype-runs/d3d-window-desktop-context.json').write_text(json.dumps(r,indent=2));print(r)

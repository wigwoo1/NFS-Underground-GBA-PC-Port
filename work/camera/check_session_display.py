"""Read-only session display dimensions; never changes display mode."""
import ctypes as C,json,sys
from ctypes import wintypes as W
from pathlib import Path
u=C.WinDLL('user32');g=C.WinDLL('gdi32');k=C.WinDLL('kernel32')
u.GetDC.argtypes=[W.HWND];u.GetDC.restype=W.HDC;u.ReleaseDC.argtypes=[W.HWND,W.HDC]
g.GetDeviceCaps.argtypes=[W.HDC,C.c_int];g.GetDeviceCaps.restype=C.c_int
h=u.GetDC(None)
try:caps={n:g.GetDeviceCaps(h,i) for n,i in [('HORZRES',8),('VERTRES',10),('DESKTOPHORZRES',118),('DESKTOPVERTRES',117),('VREFRESH',116)]}
finally:u.ReleaseDC(None,h)
out=dict(system_primary=[u.GetSystemMetrics(0),u.GetSystemMetrics(1)],system_virtual=[u.GetSystemMetrics(76),u.GetSystemMetrics(77),u.GetSystemMetrics(78),u.GetSystemMetrics(79)],remote_session=bool(u.GetSystemMetrics(0x1000)),device_caps=caps,scope='Read-only current-session Windows desktop dimensions/refresh; not independent physical panel or per-frame scanout proof.')
Path(sys.argv[1]).write_text(json.dumps(out,indent=2));print(out)

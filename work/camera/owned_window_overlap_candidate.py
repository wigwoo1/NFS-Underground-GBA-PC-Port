"""Read-only rectangle overlap evidence, not compositor visibility certification."""
import ctypes as C
from ctypes import wintypes as W
u=C.WinDLL('user32',use_last_error=True)
u.GetWindow.argtypes=[W.HWND,W.UINT];u.GetWindow.restype=W.HWND
u.GetWindowRect.argtypes=[W.HWND,C.POINTER(W.RECT)];u.IsWindowVisible.argtypes=[W.HWND];u.IsIconic.argtypes=[W.HWND]
u.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)]
def overlap(a,b):
 return max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
def inspect(hwnd):
 r=W.RECT()
 if not u.GetWindowRect(hwnd,C.byref(r)):return {'available':False}
 bounds=[r.left,r.top,r.right,r.bottom];area=max(0,r.right-r.left)*max(0,r.bottom-r.top)
 above=[];seen=set();h=u.GetWindow(hwnd,3)
 while h and h not in seen and len(seen)<512:
  seen.add(h)
  if u.IsWindowVisible(h) and not u.IsIconic(h):
   rr=W.RECT()
   if u.GetWindowRect(h,C.byref(rr)):
    b=[rr.left,rr.top,rr.right,rr.bottom];a=overlap(bounds,b)
    if a:
     pid=W.DWORD();u.GetWindowThreadProcessId(h,C.byref(pid));above.append(dict(hwnd=int(h),pid=pid.value,bounds=b,overlap_area=a,covers_rectangle=a==area))
  h=u.GetWindow(h,3)
 return dict(available=True,window_bounds=bounds,window_area=area,above_overlaps=above,traversed=len(seen),scope='Visible non-minimized higher Z-order window rectangles; ignores transparency, window regions and compositor policy. No titles or content read.')
if __name__=='__main__':
 assert overlap([0,0,10,10],[5,5,15,15])==25
 assert overlap([0,0,10,10],[10,0,20,10])==0
 print('PASS_WINDOW_RECTANGLE_INTERSECTION')

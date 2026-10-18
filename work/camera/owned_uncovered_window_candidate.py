"""Isolated own-window relocation without focus or Z-order changes."""
import ctypes as C
from ctypes import wintypes as W
from owned_window_overlap_candidate import u,inspect,overlap
from owned_source_d3d_sky_pan_display_candidate import OwnedD3DConsumer as Base
placements=[]
Callback=C.WINFUNCTYPE(W.BOOL,W.HANDLE,W.HDC,C.POINTER(W.RECT),W.LPARAM)
u.EnumDisplayMonitors.argtypes=[W.HDC,C.POINTER(W.RECT),Callback,W.LPARAM]
u.SetWindowPos.argtypes=[W.HWND,W.HWND,C.c_int,C.c_int,C.c_int,C.c_int,W.UINT]
def candidates(monitors,width,height):
 for l,t,r,b in monitors:
  if r-l>=width and b-t>=height:
   for x in sorted(set((l,(l+r-width)//2,r-width))):
    for y in sorted(set((t,(t+b-height)//2,b-height))):yield [x,y,x+width,y+height]
class OwnedD3DConsumer(Base):
 def bind_window(self):
  super().bind_window();before=inspect(self.window);monitors=[]
  def each(h,dc,rect,data):
   r=rect.contents;monitors.append([r.left,r.top,r.right,r.bottom]);return True
  callback=Callback(each);assert u.EnumDisplayMonitors(None,None,callback,0)
  obstacles=[x['bounds'] for x in before.get('above_overlaps',[])]
  options=list(candidates(monitors,960,540))
  if not options:placements.append(dict(changed=False,monitors=monitors,before=before));return
  best=min(options,key=lambda box:sum(overlap(box,x) for x in obstacles))
  old=before['window_bounds'];old_score=sum(overlap(old,x) for x in obstacles);score=sum(overlap(best,x) for x in obstacles)
  changed=score<old_score
  if changed:assert u.SetWindowPos(self.window,None,best[0],best[1],960,540,0x0014)
  placements.append(dict(changed=changed,monitors=monitors,before=before,selected=best,overlap_score=score,after=inspect(self.window),scope='Own window only; NOZORDER|NOACTIVATE. Rectangle heuristic, not pixel visibility certification.'))
if __name__=='__main__':
 assert len(list(candidates([[0,0,1920,1080]],960,540)))==9
 assert list(candidates([[0,0,800,400]],960,540))==[]
 print('PASS_PLACEMENT_CANDIDATE_BOUNDS')

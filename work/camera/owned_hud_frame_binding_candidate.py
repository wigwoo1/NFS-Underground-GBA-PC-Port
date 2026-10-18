"""Private association between a validated immutable frame and native HUD leases.
Does not yet change renderer cache decisions or its ABI.
"""
import ctypes as C,struct
from pathlib import Path
from owned_segmented_frame_candidate import SegmentedFrame
class HudFrameSnapshot:
 def __init__(self,base):
  if type(base) is not bytes or len(base)<40:raise ValueError('Immutable NGF3 owner required')
  h=struct.unpack_from('<6I2Q',base)
  if h[0]!=0x3346474e or not h[6] or h[7]!=h[1]*280896 or h[3]!=5591040 or h[4]!=76800 or h[5]!=76800 or 40+sum(h[2:6])!=len(base):raise ValueError('Invalid HUD snapshot envelope')
  self._base=base;self.epoch=h[6];self.refresh=h[1];self.offset=40+h[2];self.closed=False
  d=self.d=C.CDLL(str((Path(__file__).parent/'owned-hud-snapshot-candidate.dll').resolve()));U=C.c_uint64;P=C.c_void_p
  d.nf_hud_owner_create.argtypes=[P,C.c_size_t,U,C.c_uint];d.nf_hud_owner_create.restype=U;d.nf_hud_owner_view.argtypes=[U,U,P,P];d.nf_hud_owner_release.argtypes=[U,U];d.nf_hud_owner_stats.argtypes=[P]
  retained=C.c_char_p(base);ptr=C.cast(retained,P).value+self.offset
  self.token=d.nf_hud_owner_create(ptr,h[3],self.epoch,self.refresh)
  if not self.token:raise ValueError('Native HUD owner rejected or capacity exhausted')
 def bind(self,frame):
  if self.closed:raise ValueError('HUD snapshot closed')
  if not isinstance(frame,SegmentedFrame) or frame.base is not self._base or frame.tail_offset!=self.offset:raise ValueError('Frame outside retained immutable snapshot')
  # SegmentedFrame has already validated matching epoch/refresh/tail envelope.
  h=struct.unpack_from('<6I2Q',frame.prefix)
  if h[6]!=self.epoch or h[1]!=self.refresh:raise ValueError('Wrong source snapshot identity')
  return HudFrameLease(self,frame)
 def close(self):
  if not self.closed:
   assert self.d.nf_hud_owner_release(self.token,self.epoch);self.closed=True
 def __enter__(self):return self
 def __exit__(self,*args):self.close()
class HudFrameLease:
 def __init__(self,owner,frame):
  self.d=owner.d;self.token=owner.token;self.epoch=owner.epoch;self.frame=frame;self.closed=False;self._pointer=C.c_void_p();refresh=C.c_uint()
  if not self.d.nf_hud_owner_view(self.token,self.epoch,C.byref(self._pointer),C.byref(refresh)):raise ValueError('Stale HUD lease')
  assert refresh.value==owner.refresh
 @property
 def pointer(self):
  if self.closed:raise ValueError('HUD lease closed')
  return self._pointer.value
 def close(self):
  if not self.closed:
   assert self.d.nf_hud_owner_release(self.token,self.epoch);self.closed=True;self.frame=None
 def __enter__(self):return self
 def __exit__(self,*args):self.close()

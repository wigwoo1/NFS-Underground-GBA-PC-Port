"""Recovered surface stream count before horizontal clipping.
Original emits two vertices on behind-to-front near crossing, one on every
other surviving edge; a whole-ring far rejection prevents surface dispatch.
"""
import math

def surface_stream_count(camera,near,*,face_hidden=False,far_depths=None):
 if len(camera)%3 or not 3<=len(camera)//3<=32 or not math.isfinite(near) or not 0<=near<=32767 or not all(math.isfinite(v) for v in camera):raise ValueError('Invalid surface emission inputs')
 if face_hidden:return None
 depths=camera[2::3]
 if far_depths is None:far_depths=depths
 if len(far_depths)!=len(depths) or not all(math.isfinite(z) for z in far_depths):raise ValueError('Incomplete far-depth ownership')
 if any(z>0x5fff for z in far_depths):return None
 n=0
 for i,z in enumerate(depths):
  following=depths[(i+1)%len(depths)]
  if z<near and following<near:continue
  n+=2 if z<near else 1
 return n

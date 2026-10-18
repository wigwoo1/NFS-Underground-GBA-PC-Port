"""Attach authoritative original sky copy to the matching immutable endpoint."""
import struct
SKY_COVERAGE=bytes([1])*15136
def attach_sky(frame,scene):
 b=scene.sky
 if b is None or b.asset is None:raise ValueError('Missing owned sky source')
 b.match_graph(scene.graph);b.asset.verify(b.boundary)
 if len(frame)<40:raise ValueError('Truncated scene frame')
 h=struct.unpack_from('<6I2Q',frame)
 if h[0]!=0x3346474e or (h[6],h[1])!=scene.identity or h[7]!=h[1]*280896 or h[4]!=76800 or h[5]!=76800 or 40+sum(h[2:6])!=len(frame):raise ValueError('Unpaired sky frame')
 offset=40+h[2]+h[3];indices=b.boundary.indices;view=memoryview(frame);coverage=bytes(view[offset+38400+10560:offset+38400+25696])
 # A wholly uncovered plane needs no per-pixel ownership comparisons.
 if coverage.count(0)!=len(coverage):
  if coverage.count(1)==len(coverage):
   # Fully owned sky planes compare in native bytes code, not a pixel loop.
   if view[offset+10560:offset+25696]!=indices:raise ValueError('Conflicting original sky ownership')
   if type(frame) is bytes:return frame
  else:
   for i in range(10560,25696):
    if frame[offset+38400+i] not in (0,1):raise ValueError('Invalid sky coverage')
    if frame[offset+38400+i] and frame[offset+i]!=indices[i-10560]:raise ValueError('Conflicting original sky ownership')
 # One owned output allocation; unchanged frame spans are borrowed only during join.
 return b''.join((view[:offset+10560],indices,view[offset+25696:offset+38400+10560],SKY_COVERAGE,view[offset+38400+25696:]))


"""Attach authoritative original sky copy to the matching immutable endpoint."""
import struct
SKY_COVERAGE=bytes([1])*15136
def _validated_parts(frame,scene,used=None):
 b=scene.sky
 if b is None or b.asset is None:raise ValueError('Missing owned sky source')
 b.match_graph(scene.graph);b.asset.verify(b.boundary)
 view=memoryview(frame).cast('B')
 if used is not None:view=view[:used]
 if len(view)<40:raise ValueError('Truncated scene frame')
 h=struct.unpack_from('<6I2Q',view)
 if h[0]!=0x3346474e or (h[6],h[1])!=scene.identity or h[7]!=h[1]*280896 or h[4]!=76800 or h[5]!=76800 or 40+sum(h[2:6])!=len(view):raise ValueError('Unpaired sky frame')
 offset=40+h[2]+h[3];indices=b.boundary.indices;coverage=bytes(view[offset+38400+10560:offset+38400+25696])
 # A wholly uncovered plane needs no per-pixel ownership comparisons.
 if coverage.count(0)!=len(coverage):
  if coverage.count(1)==len(coverage):
   # Fully owned sky planes compare in native bytes code, not a pixel loop.
   if view[offset+10560:offset+25696]!=indices:raise ValueError('Conflicting original sky ownership')
  else:
   for i in range(10560,25696):
    if view[offset+38400+i] not in (0,1):raise ValueError('Invalid sky coverage')
    if view[offset+38400+i] and view[offset+i]!=indices[i-10560]:raise ValueError('Conflicting original sky ownership')
 return view,offset,indices
def attach_sky(frame,scene):
 view,offset,indices=_validated_parts(frame,scene)
 # One owned output allocation; unchanged frame spans are borrowed only during join.
 return b''.join((view[:offset+10560],indices,view[offset+25696:offset+38400+10560],SKY_COVERAGE,view[offset+38400+25696:]))

def attach_sky_inplace(frame,scene,used=None):
 """Attach sky directly to a writable owned-frame buffer; retain its exact size."""
 view,offset,indices=_validated_parts(frame,scene,used)
 if view.readonly:raise TypeError('In-place sky attachment requires a writable frame buffer')
 # Validation completes before either write, so rejected ownership leaves the frame intact.
 indices_begin=offset+10560;coverage_begin=offset+38400+10560
 view[indices_begin:indices_begin+15136]=indices
 view[coverage_begin:coverage_begin+15136]=SKY_COVERAGE
 return len(view)

"""Exact projection helper reuse; no traversal domain or clipping changes."""
import inspect,textwrap
import owned_portal_continuous as original
source=textwrap.dedent(inspect.getsource(original.edge))
old='coordinate(x,z,scale,center,reciprocal),coordinate(nx,nz,scale,center,reciprocal)'
new='coordinate_at_depth(x,projection_depth(z,scale,reciprocal),center),coordinate_at_depth(nx,projection_depth(nz,scale,reciprocal),center)'
assert source.count(old)==1
namespace=dict(original.edge.__globals__)
exec(compile(source.replace(old,new),'portal-depth-projection','exec'),namespace)
edge=namespace['edge']

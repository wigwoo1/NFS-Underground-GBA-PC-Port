"""Private immutable section views confined to synchronous closed-graph validation."""
import inspect,textwrap,struct
from owned_closed_graph import ClosedGraph
from owned_scene_bundle import chunks as original_chunks
original=ClosedGraph.decode.__func__
def validation_chunks(raw,kind):
 if type(raw) is not bytes:
  yield from original_chunks(raw,kind);return
 view=memoryview(raw);cursor=0
 try:
  while cursor<len(raw):
   if cursor+32>len(raw):raise ValueError('Truncated scene section')
   h=struct.unpack_from('<8I',raw,cursor)
   size=128+h[6] if kind=='graph_objects' else 400 if kind=='associations' else 80+h[6] if kind=='objects' else 244 if kind=='callbacks' else 32+h[5] if kind=='supplements' else 120+struct.unpack_from('<I',raw,cursor+40)[0]
   if size<32 or cursor+size>len(raw):raise ValueError('Truncated scene record')
   yield h,view[cursor:cursor+size]
   cursor+=size
 finally:view.release()
source=textwrap.dedent(inspect.getsource(original));assert source.startswith('@classmethod\n');source=source[len('@classmethod\n'):]
namespace=dict(original.__globals__,chunks=validation_chunks)
exec(compile(source,'private-validation-section-views','exec'),namespace)
decode=namespace['decode']
def install():ClosedGraph.decode=classmethod(decode)
def uninstall():ClosedGraph.decode=classmethod(original)

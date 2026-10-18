"""Bounded immutable ABI type reuse; buffers still freshly allocated per draw."""
import functools,inspect,textwrap
from owned_source_segmented_draw_candidate import OwnedSourceDraw
@functools.lru_cache(maxsize=128)
def array_type(kind,length):return kind*length
method=OwnedSourceDraw.__init__
source=textwrap.dedent(inspect.getsource(method))
old='clone=lambda t,x:(t*len(x))(*x)'
assert source.count(old)==1
source=source.replace(old,'clone=lambda t,x:array_type(t,len(x))(*x)')
namespace=dict(method.__globals__,array_type=array_type)
exec(compile(source,'owned-draw-bounded-array-types','exec'),namespace)
OwnedSourceDraw.__init__=namespace['__init__']

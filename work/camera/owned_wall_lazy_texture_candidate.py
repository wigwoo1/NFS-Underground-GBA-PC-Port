"""Isolated lazy texture payload copies for immutable, validated wall graphs."""
import inspect
import owned_graph_wall_sources as baseline

class TextureSpan:
 __slots__=('source','start','length','value')
 def __init__(self,source,start,length):
  self.source=source;self.start=start;self.length=length;self.value=None
 def resolve(self):
  if self.value is None:self.value=self.source[self.start:self.start+self.length]
  return self.value

def resolve_texture(value):
 return value.resolve() if isinstance(value,TextureSpan) else value

text=inspect.getsource(baseline.wall_sources)
old="texture=graph.materials[at:at+h[8]]"
assert text.count(old)==1
text=text.replace(old,"texture=TextureSpan(graph.materials,at,h[8])")
old="if not height:continue"
assert text.count(old)==1
text=text.replace(old,old+"\n   texture=resolve_texture(texture)")
namespace=dict(vars(baseline),TextureSpan=TextureSpan,resolve_texture=resolve_texture)
exec(compile(text,__file__,'exec'),namespace)
_lazy=namespace['wall_sources']

stats=dict(immutable_calls=0,mutable_fallback_calls=0)

def wall_sources(graph,*,validated=False,descriptors=None,material_cache=None):
 # Mutable owners keep their original snapshot/copy semantics.
 implementation=_lazy if all(type(getattr(graph,x)) is bytes for x in ('materials','geometry','offsets')) else baseline.wall_sources
 stats['immutable_calls' if implementation is _lazy else 'mutable_fallback_calls']+=1
 return implementation(graph,validated=validated,descriptors=descriptors,material_cache=material_cache)


def install():
 import owned_motion_wall_regions as target
 target.wall_sources=wall_sources

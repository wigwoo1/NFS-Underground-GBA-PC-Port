"""Resolve supplemental wall palettes from opaque texel color ownership."""
import struct
from owned_scene_bundle import chunks

def resolve_palette(closed,supplements,sources,descriptor,bounds):
 records=list(chunks(supplements.geometry,'supplements'))
 matching=[raw[464:976] for h,raw in records if h[3]==descriptor and tuple(struct.unpack_from('<8H',raw,192)[1:5])==tuple(bounds)]
 if matching and len(set(matching))==1:return bytes(matching[0])
 graph_palette=closed.graph.context[384:896]
 palettes=[graph_palette]+[raw[464:976] for _,raw in records]
 # Wall indexed expansion makes index0 alpha0; GL_ALPHA_TEST discards it.
 # No opaque palette color is inferred from an unrelated invocation.
 used=set().union(*(set(w.texture)-{0} for w in sources))
 for index in used:
  if len({p[index*2:index*2+2] for p in palettes})!=1:raise ValueError('Unresolved opaque supplemental palette color')
 return bytes(graph_palette)

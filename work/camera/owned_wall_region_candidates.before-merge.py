"""Owned wall source flags and hidden precedence; independent of draw capture."""
import struct
from owned_graph_wall_sources import wall_sources,supplemental_wall_sources
from owned_portal_traversal import traverse

def source_flags(wall):
 return struct.unpack_from('<H',wall.vertices,46)[0]
def hidden(wall):
 index=struct.unpack_from('<H',wall.vertices,42)[0]
 return bool((source_flags(wall) if index==65535 else struct.unpack_from('<H',wall.offsets,14)[0])&1)
def regions(graph,reciprocal):
 graph.validate()
 return tuple(traverse(graph.graph()[0],struct.unpack_from('<12i',graph.context,256),graph.context[304:368],struct.unpack_from('<8H',graph.context,368),reciprocal))
def candidates(graph,reciprocal):
 by_region={}
 for wall in wall_sources(graph):by_region.setdefault(wall.descriptor,[]).append(wall)
 return tuple((ordinal,region,wall) for ordinal,region in enumerate(regions(graph,reciprocal)) for wall in by_region.get(region[0],()) if not hidden(wall))

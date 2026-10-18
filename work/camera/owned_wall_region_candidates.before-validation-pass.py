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
 queue=list(traverse(graph.graph()[0],struct.unpack_from('<12i',graph.context,256),graph.context[304:368],struct.unpack_from('<8H',graph.context,368),reciprocal))
 # Original03005620 groups insertion indices (root is not inserted), retains
 # the first visit with merged bounds and marks later visits with flag8.
 groups={}
 for index,region in enumerate(queue[1:],1):groups.setdefault(region[0],[]).append(index)
 for members in groups.values():
  if len(members)<=1:continue
  first=members[0];target=list(queue[first]);target[1]=min(queue[i][1] for i in members);target[2]=max(queue[i][2] for i in members);queue[first]=tuple(target)
  for index in members[1:]:
   region=list(queue[index]);region[5]|=8;queue[index]=tuple(region)
 return tuple(queue)
def candidates(graph,reciprocal):
 by_region={}
 for wall in wall_sources(graph):by_region.setdefault(wall.descriptor,[]).append(wall)
 return tuple((ordinal,region,wall) for ordinal,region in enumerate(regions(graph,reciprocal)) for wall in by_region.get(region[0],()) if not hidden(wall))

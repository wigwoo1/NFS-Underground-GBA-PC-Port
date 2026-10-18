"""Isolated exact-owner immutable material header index shared by wall decoders."""
import struct,threading,inspect,textwrap
from owned_graph_packet import GraphPacket
from types import MappingProxyType
import owned_graph_wall_sources as sources
import owned_sampled_graph_wall_visibility as visibility
local=threading.local();MAX_BYTES=32*1024*1024;stats=dict(hits=0,misses=0,bypasses=0)
def index(graph):
 raw=graph.materials;payload=sum(len(getattr(graph,name,b'')) for name in ('context','geometry','offsets','materials','faces','viewport_data'));cacheable=type(graph) is GraphPacket and type(raw) is bytes and payload<=MAX_BYTES
 entries=getattr(local,'entries',[])
 if cacheable:
  for i,(owner,value) in enumerate(entries):
   if owner is graph:
    stats['hits']+=1;entries.append(entries.pop(i));return value
  stats['misses']+=1
 else:stats['bypasses']+=1
 rows=[];bases={};at=0
 while at<len(raw):
  start=at;h=struct.unpack_from('<12I',raw,at);body=bytes(raw[at+48:at+120]);bases[h[3]]=bytes(raw[at+48:at+80]);at+=120
  texture_start=at
  if h[9]==1:at+=h[8]
  rows.append((h,body,texture_start,at))
 value=(tuple(rows),MappingProxyType(bases))
 if cacheable:
  entries.append((graph,value))
  while len(entries)>2 or sum(sum(len(getattr(x[0],name)) for name in ('context','geometry','offsets','materials','faces','viewport_data')) for x in entries)>MAX_BYTES:entries.pop(0)
  local.entries=entries
 return value
def materials(graph):
 rows,_=index(graph);result={};shared={}
 for h,body,start,end in rows:
  texture=b''
  if h[9]==1:texture=graph.materials[start:end];shared[h[10]]=texture
  elif h[9]==2:texture=shared[h[10]]
  result[h[3]]=(body[32:40],body[40:72],texture,h[5],h[6],h[7])
 return result
original_sources=sources.wall_sources;original_metadata=visibility.wall_metadata
s=textwrap.dedent(inspect.getsource(original_sources));a=s.index('  materials={};shared={};at=0');b=s.index('  if material_cache is not None:material_cache[1]=materials',a)
s=s[:a]+'  materials=material_index_values(graph)\n'+s[b:]
ns=dict(original_sources.__globals__,material_index_values=materials);exec(compile(s,__file__,'exec'),ns);wall_sources=ns['wall_sources']
s=textwrap.dedent(inspect.getsource(original_metadata));a=s.index(' while cursor<len(graph.materials):');b=s.index(' from types import MappingProxyType',a)
s=s[:a]+' bases=dict(shared_index(graph)[1])\n'+s[b:]
ns=dict(original_metadata.__globals__,shared_index=index);exec(compile(s,__file__,'exec'),ns);wall_metadata=ns['wall_metadata']
def clear():local.entries=[]

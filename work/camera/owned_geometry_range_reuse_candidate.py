"""Isolated bounded exact-content cache for geometry/offset raw memory ranges."""
import inspect,textwrap,struct,threading
import owned_closed_scene_memory as baseline
local=threading.local();stats=dict(hits=0,misses=0,bypasses=0)
MAX_ENTRIES=2;MAX_PAYLOAD_BYTES=4*1024*1024
original=baseline.ClosedSceneMemory.__init__
text=inspect.getsource(original)
start=text.index('  at=offset=0\n');end=text.index('  at=0\n',start)
block=text[start:end]
collector='def _collect(g,offset_base):\n result=[]\n def add(address,data):\n  data=bytes(data)\n  if data:result.append((address,data))\n'+textwrap.indent(textwrap.dedent(block).replace('word(24)','offset_base'),' ')+' return tuple(result)\n'
namespace=dict(baseline.__dict__)
exec(compile(collector,__file__,'exec'),namespace);collect=namespace['_collect']

def geometry_ranges(g,offset_base):
 immutable=all(type(getattr(g,name)) is bytes for name in ('geometry','offsets','context'))
 if not immutable or len(g.geometry)+len(g.offsets)>MAX_PAYLOAD_BYTES:
  stats['bypasses']+=1;return collect(g,offset_base)
 key=(g.geometry,g.offsets,offset_base);entries=getattr(local,'entries',[])
 for i,(prior,ranges,payload) in enumerate(entries):
  if prior==key:
   stats['hits']+=1;entries.append(entries.pop(i));return ranges
 stats['misses']+=1;ranges=collect(g,offset_base)
 payload=len(g.geometry)+len(g.offsets)+sum(len(data) for _,data in ranges)
 if payload>MAX_PAYLOAD_BYTES:return ranges
 entries.append((key,ranges,payload))
 while len(entries)>MAX_ENTRIES or sum(x[2] for x in entries)>MAX_PAYLOAD_BYTES:entries.pop(0)
 local.entries=entries
 return ranges

text=text[:start]+'  self._ranges.extend(geometry_ranges(g,word(24)))\n'+text[end:]
namespace=dict(baseline.__dict__,geometry_ranges=geometry_ranges)
exec(compile(textwrap.dedent(text),__file__,'exec'),namespace)
class ClosedSceneMemory(baseline.ClosedSceneMemory):
 __init__=namespace['__init__']

def clear():local.entries=[]

import struct,json,threading
from types import SimpleNamespace
from pathlib import Path
from owned_closed_scene_memory import ClosedSceneMemory as Original
import owned_geometry_range_reuse_candidate as candidate

def graph(seed=0,offset_base=0x02003000,vertex_address=0x02002000,mutable=False):
 context=bytearray(368);struct.pack_into('<I',context,24,offset_base);struct.pack_into('<I',context,84,0x02004000);struct.pack_into('<I',context,80,0x02005000);context[256]=seed
 vertex=bytearray(68);vertex[0]=seed;struct.pack_into('<H',vertex,42,0)
 geometry=struct.pack('<4I',1,1,0x02001000,vertex_address)+bytes(48)+bytes(vertex)
 kind=bytearray if mutable else bytes
 return SimpleNamespace(graph=SimpleNamespace(context=kind(context),geometry=kind(geometry),offsets=kind(bytes([seed])*32),materials=b'',faces=b''))
def parity(closed):
 memories=[];errors=[]
 for cls in (Original,candidate.ClosedSceneMemory):
  try:memories.append(cls(closed,b'rom'))
  except (ValueError,struct.error) as e:errors.append((type(e).__name__,str(e)))
 if errors:assert len(errors)==2 and errors[0]==errors[1];return
 a,b=memories;assert (a._ranges,a._starts,a.owned_byte_count)==(b._ranges,b._starts,b.owned_byte_count)
 for address,data in a._ranges:assert a.read(address,len(data))==b.read(address,len(data))
 for address,size in ((0x03000000,1),(0,-1),(0,0x100001),(0xffffffff,2)):
  failure=[]
  for memory in memories:
   try:memory.read(address,size)
   except ValueError as e:failure.append(str(e))
  assert len(failure)==2 and failure[0]==failure[1]
 assert a.missing==b.missing
candidate.clear()
for g in (graph(),graph(),graph(seed=1),graph(offset_base=0x02003100),graph(vertex_address=0x02002100),graph(mutable=True),graph(vertex_address=0x02001000)):parity(g)
assert candidate.stats['hits']>0 and candidate.stats['bypasses']>0
for i in range(5):parity(graph(seed=i))
assert len(candidate.local.entries)<=2 and sum(x[2] for x in candidate.local.entries)<=candidate.MAX_PAYLOAD_BYTES
before=tuple(candidate.local.entries);result=[]
def worker():
 assert not hasattr(candidate.local,'entries');parity(graph(seed=9));result.append(len(candidate.local.entries))
t=threading.Thread(target=worker);t.start();t.join();assert result==[1] and tuple(candidate.local.entries)==before
# Payload limit refuses retention even for a valid source snapshot.
limit=candidate.MAX_PAYLOAD_BYTES
try:
 candidate.clear();candidate.MAX_PAYLOAD_BYTES=1;parity(graph());assert not candidate.local.entries
finally:candidate.MAX_PAYLOAD_BYTES=limit;candidate.clear()
out=dict(result='PASS_GEOMETRY_RANGE_CACHE_GUARDS',changed_geometry_offsets_base=True,mutable_bypass=True,conflict_read_errors_exact=True,eviction=True,payload_bound=True,thread_isolation=True,scope='Synthetic mutation/ownership/readguard tests; original conflict merge remains authoritative')
p=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/geometry-range-reuse-20261010');(p/'guards.json').write_text(json.dumps(out,indent=2));print(out['result'])

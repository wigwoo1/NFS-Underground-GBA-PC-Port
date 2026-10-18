import struct,json
from pathlib import Path
from owned_graph_packet import GraphPacket
import owned_shared_wall_material_index_candidate as reuse
def row(identifier,mode,token,texture=b'',marker=1):
 h=[0]*12;h[3]=identifier;h[5:8]=[2,3,4];h[8]=len(texture);h[9]=mode;h[10]=token
 return struct.pack('<12I',*h)+bytes([marker])*72+(texture if mode==1 else b'')
def graph(raw):return GraphPacket(1,0,b'',b'',b'',raw)
def result(fn,g):
 try:return 'ok',fn(g,validated=True,descriptors=set(),material_cache=[g,None])
 except Exception as e:return type(e).__name__,str(e)
for raw in [row(1,1,9,b'ab')+row(2,2,9),row(1,1,9,b'ab')+row(1,1,9,b'cd',2)+row(2,2,9),row(2,2,99),b'truncated']:
 g=graph(raw);reuse.clear();assert result(reuse.original_sources,g)==result(reuse.wall_sources,g)
 # Metadata must not eagerly resolve invalid aliases.
 from types import SimpleNamespace
 def metadata(fn):
  try:return 'ok',fn(SimpleNamespace(),g)
  except Exception as e:return type(e).__name__,str(e)
 assert metadata(reuse.original_metadata)==metadata(reuse.wall_metadata)
g=graph(row(1,1,9,b'ab'));reuse.clear();a=reuse.index(g);b=reuse.index(g);assert a is b
try:a[1][1]=b'bad'
except TypeError:pass
else:raise AssertionError('Mutable cached bases')
for i in range(5):reuse.index(graph(row(i,1,i,b'x')))
assert len(reuse.local.entries)<=2
folder=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/shared-wall-material-index-20261010');out=dict(result='PASS_SHARED_MATERIAL_INDEX_GUARDS',scope='Alias ordering/redefinition/dangling alias delayed error, metadata exception parity, immutable cached bases, distinct graph owners and bounded entries. Further mutable/thread/fullscene qualification required.')
(folder/'guards.json').write_text(json.dumps(out,indent=2));print(out['result'])
